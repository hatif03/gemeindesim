"""The 1:1 chat goes through the same safeguards as a simulation round: code-owned stance, retrieved passages,
validated citations, numeral gate, Swiss spelling."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

DATA = Path(__file__).resolve().parents[2].parent / "data"
POLICY = (DATA / "steuerfuss_linden_de.txt").read_text(encoding="utf-8")
NPC = {
    "id": "npc_1", "name": "Lea", "profession": "Ladenbesitzerin", "mbti": "ENFP", "bio": "Führt einen Bioladen.",
    "beliefs": [], "mood": "worried", "lang": "de", "country": "Switzerland", "income_level": "medium",
    "stance": -0.5, "stance_reason": "Die Steuererhöhung belastet meinen Betrieb.",
}


def _llm(monkeypatch, text):
    seen = {}

    async def ainvoke(prompt):
        seen["prompt"] = prompt
        r = MagicMock()
        r.content = text
        return r

    llm = MagicMock()
    llm.ainvoke = AsyncMock(side_effect=ainvoke)
    monkeypatch.setattr("graph.chat.get_llm", lambda **kw: llm)
    return seen


@pytest.mark.asyncio
async def test_chat_prompt_carries_stance_passages_and_binding(monkeypatch):
    seen = _llm(monkeypatch, "Ich bin dagegen.")
    from graph.chat import generate_npc_chat_reply

    reply = await generate_npc_chat_reply(NPC, "Wie hoch wird der Steuerfuss?", [], [], POLICY)
    p = seen["prompt"]
    assert "against. Your reason: Die Steuererhöhung belastet meinen Betrieb." in p  # code-owned stance and reason
    assert "-0.50" not in p  # the number is not shown: residents copy it into their answer
    assert "[P1]" in p and "118" in p  # retrieved passages of the vote text
    assert p.rstrip().split("\n")[-1].startswith("REMINDER")  # speech binding is the last paragraph
    assert reply["stance"] == "against"


@pytest.mark.asyncio
async def test_chat_validates_citations_and_strips_markers(monkeypatch):
    _llm(monkeypatch, "Der Steuerfuss steigt auf 124 % [P1]. Das stimmt auch laut [P9].")
    from graph.chat import generate_npc_chat_reply

    reply = await generate_npc_chat_reply(NPC, "Wie hoch wird der Steuerfuss?", [], [], POLICY)
    assert "[P" not in reply["text"]
    assert len(reply["sources"]) == 1  # P9 does not exist in the pack and is dropped
    assert "124" in reply["sources"][0]["text"] or "118" in reply["sources"][0]["text"] or reply["sources"][0]["text"]


@pytest.mark.asyncio
async def test_chat_strips_figures_not_in_the_text_and_swissifies(monkeypatch):
    _llm(monkeypatch, "Die Gemeinde spart 37 Prozent, das ist grosse Straße.")
    from graph.chat import generate_npc_chat_reply

    reply = await generate_npc_chat_reply(NPC, "Und die Einsparungen?", [], [], POLICY)
    assert "37" not in reply["text"]
    assert "ß" not in reply["text"]


@pytest.mark.asyncio
async def test_chat_without_policy_text_still_answers(monkeypatch):
    seen = _llm(monkeypatch, "Ich weiss es nicht.")
    from graph.chat import generate_npc_chat_reply

    reply = await generate_npc_chat_reply({**NPC, "stance": 0.0}, "Hallo?", [], [], "")
    assert reply["text"] == "Ich weiss es nicht."
    assert "(no passages available)" in seen["prompt"]
    assert reply["sources"] == []


@pytest.mark.asyncio
async def test_chat_strips_all_bracketed_text_and_keeps_valid_labels(monkeypatch):
    _llm(monkeypatch, "Der Steuerfuss steigt auf 124 % [P1-P2] [Not in text] [chiffre calculé].")
    from graph.chat import generate_npc_chat_reply

    reply = await generate_npc_chat_reply(NPC, "Wie hoch wird der Steuerfuss?", [], [], POLICY)
    assert "[" not in reply["text"] and "]" not in reply["text"]
    assert len(reply["sources"]) >= 1  # the P1 inside "[P1-P2]" is a valid label of the pack


@pytest.mark.asyncio
async def test_chat_binding_answers_the_question_first_and_does_not_force_the_stance(monkeypatch):
    seen = _llm(monkeypatch, "Ich bin noch unentschieden.")
    from graph.chat import generate_npc_chat_reply

    undecided = {**NPC, "stance": 0.0, "support_reason": "Das Schulhaus ist nötig.", "oppose_reason": "Die Steuer steigt."}
    await generate_npc_chat_reply(undecided, "Wann wurde die alte Turnhalle gebaut?", [], [], POLICY)
    last = seen["prompt"].rstrip().split("\n")[-1]
    assert last.startswith("REMINDER") and "answer the question that was asked first" in last
    assert "do not repeat it for a question about a fact" in last
    assert "Das Schulhaus ist nötig." in last and "Die Steuer steigt." in last
    assert "In every line" not in seen["prompt"]  # the round binding is not used in the chat


@pytest.mark.asyncio
async def test_chat_removes_the_punctuation_left_by_citation_markers(monkeypatch):
    _llm(monkeypatch, "Das steht in den Passagen [P1], [P2], und gilt fuer alle [P1] .")
    from graph.chat import generate_npc_chat_reply

    reply = await generate_npc_chat_reply(NPC, "Gilt das fuer alle?", [], [], POLICY)
    assert ",," not in reply["text"] and " ." not in reply["text"] and "  " not in reply["text"]


@pytest.mark.asyncio
async def test_chat_puts_a_mid_sized_document_first_and_leaves_short_ones_alone(monkeypatch):
    long_policy = POLICY + "\n\n" + ("Zusatzbestimmung zum Gemeindereglement, Artikel 7: Die Gebuehren bleiben unveraendert. " * 120)
    assert 6_000 < len(long_policy) <= 100_000
    seen = _llm(monkeypatch, "Ok.")
    from graph import chat
    from graph.chat import generate_npc_chat_reply

    await generate_npc_chat_reply(NPC, "Was kostet das?", [], [], long_policy)
    assert seen["prompt"].startswith("Official document (complete text, for reference):")
    await generate_npc_chat_reply(NPC, "Was kostet das?", [], [], POLICY)
    assert not seen["prompt"].startswith("Official document")  # the Linden sample is shorter than a few passages
    monkeypatch.setattr(chat, "CHAT_STUFF_MAX_CHARS", 0)
    await generate_npc_chat_reply(NPC, "Was kostet das?", [], [], long_policy)
    assert not seen["prompt"].startswith("Official document")  # switched off


def _stream(monkeypatch, pieces):
    async def fake(llm, prompt):
        for p in pieces:
            yield p

    monkeypatch.setattr("graph.chat.astream_text", fake)
    monkeypatch.setattr("graph.chat.get_llm", lambda **kw: MagicMock())


@pytest.mark.asyncio
async def test_streamed_chat_sends_checked_sentences_not_raw_tokens(monkeypatch):
    _stream(monkeypatch, ["Der Steuerfuss steigt auf 124 % [P", "1]. Die Gemeinde spart 37 Prozent. ", "Ich unterstuetze das", " Vorhaben [Note]."])
    from graph.chat import stream_npc_chat_reply

    sent = []

    async def on_chunk(t):
        sent.append(t)

    reply = await stream_npc_chat_reply(NPC, "Wie hoch?", [], [], POLICY, on_chunk)
    assert len(sent) == 3  # one per sentence, in order
    assert "[P" not in "".join(sent) and "[Note" not in "".join(sent) and "37" not in "".join(sent)  # the checks ran BEFORE anything was sent
    assert sent[0].startswith("Der Steuerfuss steigt auf 124 %")
    assert reply["text"] == " ".join(sent) and len(reply["sources"]) == 1


@pytest.mark.asyncio
async def test_streamed_chat_waits_for_a_reasoning_span_and_drops_leaked_reasoning(monkeypatch):
    _stream(monkeypatch, ["<|inner_prefix|>Let me think. ", "The user asks. <|inner_suffix|>Ich weiss es nicht. ", "Let me explain. Es steht nicht im Text."])
    from graph.chat import stream_npc_chat_reply

    sent = []

    async def on_chunk(t):
        sent.append(t)

    reply = await stream_npc_chat_reply(NPC, "Wann?", [], [], POLICY, on_chunk)
    assert sent == ["Ich weiss es nicht.", "Es steht nicht im Text."]
    assert reply["text"] == "Ich weiss es nicht. Es steht nicht im Text."
