"""Regression tests for the fixes motivated by the research experiments (docs/research).

Each test names the experiment/finding it pins. Offline only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[3] / "data"


def _linden() -> str:
    de = (DATA / "steuerfuss_linden_de.txt").read_text(encoding="utf-8").strip()
    fr = (DATA / "steuerfuss_linden_fr.txt").read_text(encoding="utf-8").strip()
    return "--- Author notes / pasted text ---\n" + de + "\n\n" + fr


# ── E6: numeral gate ────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "utterance,flagged",
    [
        ("Der Steuerfuss steigt auf 124 %.", False),
        ("Bei 80'000 CHF Einkommen sind es 240 CHF.", False),
        ("Der Kredit beträgt 4,8 Millionen.", False),
        ("Sparauftrag von 400’000 CHF.", False),
        ("économies de 400 000 CHF", False),
        ("Das sind 6 Punkte mehr.", False),
        ("Seit 2019 unverändert.", False),
        ("Rund 4'800'000 CHF für das Schulhaus.", False),  # 4,8 Millionen in another notation
        ("Die Steuern steigen um 15 %.", True),
        ("Die Gemeinde spart 2 Millionen CHF.", True),  # list numbering must not ground "2"
        ("Ich zahle 4 Franken mehr, bei 124 %.", True),
    ],
)
def test_numeral_gate_cases(utterance, flagged):
    from graph.language import ungrounded_numerals

    assert bool(ungrounded_numerals(utterance, _linden())) is flagged


def test_strip_does_not_corrupt_grounded_numbers():
    from graph.language import strip_ungrounded_numerals

    out = strip_ungrounded_numerals("Ich zahle 4 Franken mehr, bei 124 %.", _linden())
    assert "124 %" in out and "[n] Franken" in out


def test_swissify_removes_eszett_only_for_german():
    from graph.language import swissify

    assert swissify("Maßnahme und große Kosten") == "Massnahme und grosse Kosten"
    assert swissify("Straße", "fr") == "Straße"


# ── E5: corpus ──────────────────────────────────────────────────────────────

def test_chunks_are_tagged_per_chunk_language_and_never_cut_words():
    from graph.corpus import chunk_policy_document

    chunks = chunk_policy_document(_linden())
    assert {c["lang"] for c in chunks} == {"de", "fr"}
    assert not any(c["text"][0].islower() for c in chunks)  # no mid-word cut at the start
    assert all(c["source_id"].startswith("Author_notes_pasted_text") for c in chunks)


def test_question_chunk_is_always_retrieved_in_resident_language():
    from graph.corpus import chunk_policy_document, retrieve_passages

    chunks = chunk_policy_document(_linden())
    for lang in ("de", "fr"):
        got = retrieve_passages(chunks, "Bäckerei Mehl Kundschaft Strom", top_k=3, lang=lang)
        assert any(c["is_question"] for c in got)
        assert all(c["lang"] == lang for c in got)


def test_french_query_matches_accented_inflected_terms():
    from graph.corpus import chunk_policy_document, retrieve_passages

    chunks = chunk_policy_document(_linden())
    got = retrieve_passages(chunks, "impots deficit commerces", top_k=2, lang="fr")
    assert any("déficit" in c["text"] or "impôt" in c["text"] for c in got)


def test_passage_labels_are_short_and_map_back():
    from graph.corpus import chunk_policy_document, format_passages, passage_labels, retrieve_passages

    ps = retrieve_passages(chunk_policy_document(_linden()), "Steuerfuss", top_k=3, lang="de")
    labels = passage_labels(ps)
    assert list(labels) == ["P1", "P2", "P3"]
    assert "[P1]" in format_passages(ps)


# ── E4: drift only for residents who conversed ──────────────────────────────

def test_no_chat_means_no_drift():
    from graph.nodes.run_round import _apply_opinion_dynamics

    npcs = [{"id": "a", "political_leaning": 0.1, "mood": "neutral", "reputation": 0.5, "stance": 0.1}]
    for rd in range(15):
        npcs, _, _ = _apply_opinion_dynamics(npcs, [], rd, {}, "high")
    assert npcs[0]["political_leaning"] == 0.1 and npcs[0]["stance"] == 0.1


def test_chat_moves_target_stance_toward_speaker():
    from graph.nodes.run_round import _apply_opinion_dynamics

    npcs = [
        {"id": "a", "political_leaning": 0.0, "mood": "neutral", "reputation": 0.9, "stance": 0.8},
        {"id": "b", "political_leaning": 0.0, "mood": "neutral", "reputation": 0.5, "stance": -0.2},
    ]
    rel = {"a": [("b", 0.9, 0.9)], "b": [("a", 0.9, 0.9)]}
    ev = [{"round": 0, "npc_id": "a", "event_type": "chat", "data": {"target_npc_id": "b"}}]
    out, _, log = _apply_opinion_dynamics(npcs, ev, 0, rel, "low")
    b = next(n for n in out if n["id"] == "b")
    assert b["stance"] > -0.2 and log[0]["behavior"] != "keep"


# ── A7: model emits nulls ───────────────────────────────────────────────────

def test_event_accepts_null_strings_and_string_citation():
    from models.schemas import NPCRoundResponse

    r = NPCRoundResponse.model_validate(
        {"events": [{"event_type": "chat", "message": "x", "target_npc_id": None, "dialogue": None,
                     "used_source_ids": "P1", "to_x": None}]}
    )
    assert r.events[0].dialogue == "" and r.events[0].used_source_ids == ["P1"]


# ── E9: report sanitiser ────────────────────────────────────────────────────

def test_sanitiser_drops_advice_and_outcome_sentences_but_keeps_the_rest():
    from services.economic_report import _strip_vote_advice

    text = ("Die Vorlage würde Haushalte belasten. Die Vorlage wurde angenommen. "
            "Wir empfehlen ein Ja. Kleine Läden würden profitieren.")
    out = _strip_vote_advice(text)
    assert "angenommen" not in out and "empfehlen" not in out
    assert out == "Die Vorlage würde Haushalte belasten. Kleine Läden würden profitieren."


def test_layoff_and_closure_patterns_cover_german_and_french():
    from services.economic_report import CLOSURE_RE, LAYOFF_RE

    assert LAYOFF_RE.search("Der Betrieb musste Mitarbeitende entlassen")
    assert LAYOFF_RE.search("des licenciements sont à craindre")
    assert CLOSURE_RE.search("Der Laden musste schliessen")
    assert CLOSURE_RE.search("la boutique a fermé")


# ── stance ──────────────────────────────────────────────────────────────────

def test_stance_prior_follows_impact_and_ideology_not_a_constant():
    import random

    from graph.nodes.stance import stance_prior

    rng = random.Random(0)
    # computed burden pulls a neutral, "benefit" resident down; a heavy burden flips the sign
    assert stance_prior(0.0, 0.0, "benefit", 0.0, random.Random(1)) > stance_prior(0.0, 0.0, "benefit", 0.9, random.Random(1))
    assert stance_prior(0.0, 0.0, "mixed", 0.9, random.Random(1)) < -0.2
    # a left-favoured measure (valence -0.5): progressive resident (-0.8) gains, conservative (+0.8) loses
    assert stance_prior(-0.5, -0.8, "benefit", rng=rng) > 0.5
    assert stance_prior(-0.5, 0.8, "harm", rng=rng) < -0.5
    # impact breaks ties when ideology is neutral
    assert stance_prior(0.0, 0.0, "benefit", rng=rng) > 0.2 > -0.2 > stance_prior(0.0, 0.0, "harm", rng=rng)


def test_stance_summary_counts_and_entropy():
    from graph.nodes.stance import stance_summary

    s = stance_summary([{"stance": 0.9}, {"stance": -0.8}, {"stance": 0.0}, {"stance": 0.5}])
    assert (s["for"], s["against"], s["undecided"]) == (2, 1, 1)
    assert 0 < s["entropy_bits"] <= 2


# ── F7: rate limit policy ───────────────────────────────────────────────────

async def test_429_retries_same_model_and_does_not_downgrade(monkeypatch):
    import graph.llm as L

    class RateLimited(Exception):
        status_code = 429

    calls = {"n": 0}

    class FakeBound:
        async def ainvoke(self, prompt):
            calls["n"] += 1
            if calls["n"] < 3:
                raise RateLimited("429")
            return type("R", (), {"content": "{}"})()

    class FakeLLM:
        def bind(self, **kw):
            return FakeBound()

    async def no_sleep(_):
        return None

    monkeypatch.setattr(L.asyncio, "sleep", no_sleep)
    L.STATS.clear()
    r = await L._ainvoke(FakeLLM(), "x")
    assert r.content == "{}" and calls["n"] == 3
    assert L.STATS["rate_limited"] == 2 and "downgraded_to_fallback_model" not in L.STATS


def test_default_concurrency_respects_gateway_limit():
    from config import LLM_CONCURRENCY

    assert LLM_CONCURRENCY <= 4


# ── E7: calculator replaces the model's arithmetic ──────────────────────────

@pytest.mark.parametrize("income,expected", [("low", "144"), ("medium", "240"), ("high", "432")])
def test_household_line_scales_booklet_example(income, expected):
    from graph.calculator import household_line

    for lang in ("de", "fr"):
        line = household_line(_linden(), income, lang)
        assert line and expected in line


def test_household_line_is_none_without_a_worked_example():
    from graph.calculator import household_line

    assert household_line("Tariffs on steel rise by 25 %.", "medium", "en") is None


def test_computed_figure_passes_the_numeral_gate():
    from graph.calculator import household_line
    from graph.language import ungrounded_numerals

    pack = _linden() + "\n" + household_line(_linden(), "high", "de")
    assert not ungrounded_numerals("Für mich sind es etwa 432 CHF mehr pro Jahr.", pack)


@pytest.mark.parametrize(
    "sentence,asserted",
    [
        ("Die Vorlage wurde angenommen.", True),
        ("Voters approved a tax increase and school loan.", True),
        ("The proposal to raise the tax rate passed.", True),
        ("La proposition a été acceptée.", True),
        ("Bei Annahme der Vorlage würde der Steuerfuss steigen.", False),
        ("If approved, households would pay about 240 CHF more.", False),
        ("Die Vorlage würde Haushalte belasten.", False),
    ],
)
def test_outcome_detector(sentence, asserted):
    from services.economic_report import _asserts_outcome

    assert _asserts_outcome(sentence) is asserted


# ── E2/E2b: instruction-placeholder example ─────────────────────────────────

@pytest.mark.parametrize("lang", ["de", "fr", "en"])
def test_resident_example_has_three_event_types_and_validates_as_shape(lang):
    from models.schemas import NPCRoundResponse

    ex = NPCRoundResponse.prompt_example(lang)
    assert [e["event_type"] for e in ex["events"]] == ["chat", "mood_shift", "move"]
    assert all("<" in e["message"] for e in ex["events"])  # instructions, never copyable content


def test_event_coerces_integer_citations():
    from models.schemas import NPCEvent

    assert NPCEvent(event_type="chat", message="x", used_source_ids=[1, 2]).used_source_ids == ["1", "2"]


def test_structured_prompt_uses_language_example_and_keeps_umlauts(monkeypatch):
    import asyncio

    import graph.llm as L
    from models.schemas import NPCRoundResponse

    seen = {}

    async def fake(llm, prompt):
        seen["prompt"] = prompt
        return type("R", (), {"content": '{"events": [{"event_type": "protest", "message": "x"}]}'})()

    monkeypatch.setattr(L, "_ainvoke", fake)
    out = asyncio.run(L.invoke_llm_structured("p", NPCRoundResponse, llm=object(), lang="de"))
    assert out.events[0].event_type == "protest"
    assert "<deine genauen Worte, auf Deutsch>" in seen["prompt"] and (chr(92) + "u00") not in seen["prompt"]


# ── F41: influence log must survive LangGraph; persona text is Swiss ────────

def test_sim_state_declares_influence_events():
    from models.state import SimState

    assert "influence_events" in SimState.__annotations__


def test_swissify_persona_only_touches_german_residents():
    from graph.language import swissify_persona

    de = swissify_persona({"lang": "de", "bio": "Große Straße", "beliefs": ["Maßnahmen"]})
    fr = swissify_persona({"lang": "fr", "bio": "Große Straße"})
    assert de["bio"] == "Grosse Strasse" and de["beliefs"] == ["Massnahmen"] and fr["bio"] == "Große Straße"


async def test_german_report_is_swiss_orthography_everywhere(monkeypatch):
    from models.schemas import EconomicReportNarrative, ReportImpact
    from services.economic_report import generate_economic_report

    async def fake(prompt, response_model, max_tokens=None, **kw):
        return EconomicReportNarrative(
            headline="Große Sorgen", summary="Bewohner äußern Sorge.", livelihood_impact="Maßnahmen belasten.",
            top_impacts=[ReportImpact(title="Größe", description="Straße", direction="mixed", severity="low")],
            notable_events=["Bewohner äußern sich"],
        )

    monkeypatch.setattr("services.economic_report.invoke_llm_structured", fake)
    r = await generate_economic_report(
        policy_text="Vorlage", objective="", entities=[{"kind": "vote"}], source_summaries=[], indicator_snapshots=[],
        final_npcs=[{"mood": "neutral", "lang": "de"}], events=[], completed_rounds=1, max_rounds=3, situation_kind="vote")
    blob = r.model_dump_json()
    assert "ß" not in blob and "Grosse Sorgen" in blob and "äussern" in blob


# ── E14/E15: speech bound to the code stance ────────────────────────────────

def test_stance_binding_names_position_and_carries_the_argument():
    from graph.nodes.stance import stance_binding

    for_ = stance_binding({"stance": 0.71, "stance_reason": "Der Neubau sichert die Zukunft."})
    against = stance_binding({"stance": -0.4, "stance_reason": ""})
    torn = stance_binding({"stance": 0.0})
    assert "for (+0.71)" in for_ and "SUPPORT" in for_ and "Der Neubau sichert die Zukunft." in for_
    assert "against (-0.40)" in against and "OPPOSE" in against and "argument you carry" not in against
    assert "torn" in torn


def test_resident_prompt_ends_with_the_binding_before_the_json_example():
    from graph.prompts import NPC_ROUND_PROMPT_V2

    assert NPC_ROUND_PROMPT_V2.rstrip().endswith("{stance_binding}")


# ── E17: real booklets ──────────────────────────────────────────────────────

def test_default_top_k_grows_with_the_corpus():
    from graph.corpus import default_top_k

    assert default_top_k([{}] * 16) == 4 and default_top_k([{}] * 209) == 6


def test_two_ballot_questions_are_both_pinned():
    from graph.corpus import retrieve_passages

    chunks = [
        {"source_id": "d#0", "lang": "de", "text": "Wollen Sie das E-ID-Gesetz annehmen? Abstimmungsfrage", "is_question": True},
        {"source_id": "d#1", "lang": "de", "text": "Wollen Sie den Bundesbeschluss über Liegenschaftssteuern annehmen? Abstimmungsfrage", "is_question": True},
        {"source_id": "d#2", "lang": "de", "text": "Kosten von 180 Millionen Franken für Betrieb", "is_question": False},
        {"source_id": "d#3", "lang": "de", "text": "Mindereinnahmen von 1,8 Milliarden Franken", "is_question": False},
    ]
    got = retrieve_passages(chunks, "Mindereinnahmen Milliarden", top_k=3, lang="de")
    assert {c["source_id"] for c in got} >= {"d#0", "d#1"} and len(got) == 3
