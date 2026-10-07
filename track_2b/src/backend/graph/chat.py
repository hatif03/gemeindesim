"""NPC chat response generation (ephemeral, doesn't affect sim state).

This module provides the ability for users to have direct 1:1 conversations
with NPCs. The chat is "forked" from the current simulation state - meaning
the NPC has access to all its memories and context, but the conversation
itself is ephemeral and doesn't affect the main simulation.

The chat goes through the same safeguards as a simulation round (research E21+): the resident's position comes from the
code-owned stance, the answer is grounded in retrieved passages of the vote text (labels the model cites are validated
against that pack), figures that are not in the pack or the calculator are stripped, and Swiss spelling is enforced.
"""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Any

from config import LLM_VOICE_NAME
from graph.calculator import household_line
from graph.corpus import chunk_policy_document, default_top_k, detect_setting, format_passages, passage_labels, retrieve_passages
from graph.language import TOWN, glossary_for, strip_ungrounded_numerals, swissify, translate_utterance
from graph.llm import ainvoke_text, astream_text, get_llm, strip_think_tags
from graph.memory import format_memories_for_prompt, retrieve_memories
from graph.nodes.stance import stance_label
from graph.prompts import MBTI_DESC, NPC_CHAT_PROMPT

logger = logging.getLogger(__name__)

# Retrieval is the weak link on a real booklet (recall@4 11/14, research E17); with the whole text in the prompt the 70B answered 13/14 and the
# provider's prefix cache served 94 % of the tokens (E26). So the chat gets the complete text as the FIRST part of the prompt (identical for every
# resident, hence cacheable) when it is longer than a few passages and not too long; labelled passages stay for the citations.
CHAT_STUFF_MIN_CHARS = 6_000
CHAT_STUFF_MAX_CHARS = int(os.environ.get("CHAT_STUFF_MAX_CHARS", "100000"))  # 0 switches it off

_META_PREFIXES = (
    "we need to", "the user has", "produce a response", "the instruction",
    "as the npc", "i need to", "let me", "okay so", "alright,",
)


@lru_cache(maxsize=8)
def _chunks(policy_text: str) -> list[dict[str, Any]]:
    return chunk_policy_document(policy_text)


def _format_conversation_history(history: list[dict[str, str]]) -> str:
    """Format conversation history for the prompt.

    Args:
        history: List of {role: "user"|"npc", content: str} messages.

    Returns:
        Formatted string showing the conversation so far.
    """
    if not history:
        return "(This is the start of the conversation)"

    lines: list[str] = []
    # Only include last 6 messages to keep context manageable
    for msg in history[-6:]:
        speaker = "You" if msg.get("role") == "npc" else "Stranger"
        lines.append(f"{speaker}: {msg.get('content', '')}")

    return "\n".join(lines)


def chat_stance_line(npc: dict[str, Any]) -> str:
    """Label and reason only: the round's stance_line carries '(+0.12; -1 = ...)', which a chatting resident copies into the answer."""
    reason = (npc.get("stance_reason") or "").strip()
    label = stance_label(float(npc.get("stance", 0.0)))
    return f"{label}. Your reason: {reason}" if reason else label


def chat_binding(npc: dict[str, Any]) -> str:
    """Last paragraph of the chat prompt. The round binding ('in every line you ...') made residents answer a factual question with their
    position (research E25, first live run: undecided residents repeated 'I am still undecided' to every question), so the chat version
    puts the question first and lets the stance colour the answer."""
    x = float(npc.get("stance", 0.0))
    label = stance_label(x)
    base = (
        f"REMINDER before you answer: answer the question that was asked first, in 1-3 sentences. Your own position on the vote is {label}: "
        "let it colour your tone, and state it when it is relevant or when you are asked how you feel; do not repeat it for a question about a fact."
    )
    if label == "undecided":
        pro, con = (npc.get("support_reason") or "").strip(), (npc.get("oppose_reason") or "").strip()
        if pro and con:
            base += f" If asked how you feel, say you are undecided and name one reason in favour ({pro}) and one against ({con}) in your own words."
    elif label == "for":
        base += " If asked how you feel, you support the measure and say why."
    else:
        base += " If asked how you feel, you oppose the measure and say why."
    return base


def _clean(content: str) -> str:
    """Drop reasoning spans, salvage the spoken sentence if reasoning leaked, remove wrapping quotes."""
    content = strip_think_tags(content)
    if content and content.lower()[:60].lstrip().startswith(_META_PREFIXES):
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if s.strip()]
        for sentence in reversed(sentences):
            if not sentence.lower().startswith(_META_PREFIXES):
                content = sentence
                break
        else:
            content = ""
    if content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
    if content.startswith("'") and content.endswith("'"):
        content = content[1:-1]
    return content.strip()


def _prepare(
    npc: dict[str, Any],
    user_message: str,
    conversation_history: list[dict[str, str]],
    memory_stream: list[dict[str, Any]],
    policy_context: str,
) -> dict[str, Any]:
    """Everything before the model call: memories, passages, the calculator line, the prompt, and what the answer is checked against."""
    # Build a query from the user message + recent conversation for memory retrieval
    recent_context = " ".join(msg.get("content", "") for msg in conversation_history[-2:])
    query = f"{user_message} {recent_context}".strip()

    # Retrieve relevant memories (use a copy to avoid mutating the original)
    # Use high round number so recency doesn't dominate scoring
    retrieved = retrieve_memories(
        memories=[m.copy() for m in memory_stream],
        query=query,
        current_round=99,
        top_k=5,
    )

    memories_str = format_memories_for_prompt(retrieved)
    history_str = _format_conversation_history(conversation_history)

    lang = npc.get("lang", "en")
    chunks = _chunks(policy_context or "")
    town = TOWN[detect_setting(policy_context or "")] if policy_context else ("Linden" if npc.get("country") == "Switzerland" else "Millfield")
    swiss = town == TOWN["ch"]

    # Passages of the vote text in the resident's language, chosen by the question and who the resident is.
    passage_query = f"{user_message} {npc.get('profession', '')} {npc.get('stance_reason', '')}"
    passages = retrieve_passages(chunks, passage_query, top_k=default_top_k(chunks), lang=lang) if chunks else []
    pack = format_passages(passages) if passages else "(no passages available)"
    labels = passage_labels(passages)
    pack_text = "\n".join(p.get("text", "") for p in passages)
    stuff = bool(policy_context) and CHAT_STUFF_MIN_CHARS < len(policy_context) <= CHAT_STUFF_MAX_CHARS
    document = f"Official document (complete text, for reference):\n{policy_context}\n\n---\n\n" if stuff else ""
    if stuff:
        pack_text = f"{policy_context}\n{pack_text}"  # figures anywhere in the document are grounded
    personal = household_line("\n".join(c.get("text", "") for c in chunks), npc.get("income_level", "medium"), lang) if chunks else None
    if personal:
        pack, pack_text = f"{pack}\n\nAbout YOUR OWN household (not the other person's): {personal}", f"{pack_text}\n{personal}"

    mbti = npc.get("mbti", "")
    prompt = NPC_CHAT_PROMPT.format(
        npc_name=npc.get("name", "Unknown"),
        npc_profession=npc.get("profession", "resident"),
        npc_mbti=mbti,
        npc_mbti_style=MBTI_DESC.get(mbti, mbti),
        npc_bio=npc.get("bio", "A resident."),
        npc_beliefs=", ".join(npc.get("beliefs", [])) or "None stated",
        npc_mood=npc.get("mood", "neutral"),
        npc_lang=lang,
        document=document,
        town=town,
        glossary=glossary_for(lang),
        policy_passages=pack,
        policy_summary=(policy_context or "")[:800] if not chunks else ("See the document and the passages above." if stuff else "See the passages above."),
        stance_line=chat_stance_line(npc),
        stance_binding=chat_binding(npc),
        retrieved_memories=memories_str,
        conversation_history=history_str,
        user_message=user_message,
    )

    logger.info(
        "NPC chat: %s responding to '%s...' (memories=%d, passages=%d, stance=%s)",
        npc.get("name", "?"),
        user_message[:30],
        len(retrieved),
        len(passages),
        stance_label(float(npc.get("stance", 0.0))),
    )
    return {"prompt": prompt, "labels": labels, "passages": passages, "pack_text": pack_text, "grounded": bool(chunks), "swiss": swiss, "lang": lang}


_BRACKETS = re.compile(r"\s*\[([^\]]*)\]")


def _tidy(text: str) -> str:
    text = re.sub(r"(\s*,){2,}", ",", text)  # "[P1], [P2]" leaves ",,"
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def _check(text: str, ctx: dict[str, Any]) -> tuple[str, list[str]]:
    """The guardrails on a piece of the answer: remove bracketed text (reading the valid citation labels first), then keep only figures that come
    from the passages / the calculator, and Swiss spelling. Works on a whole answer or on one sentence of a streamed one."""
    cited = [f"P{m}" for grp in _BRACKETS.findall(text) for m in re.findall(r"P(\d+)", grp)]
    text = _tidy(_BRACKETS.sub("", text))
    if ctx["grounded"]:
        text = strip_ungrounded_numerals(text, ctx["pack_text"])
    if ctx["swiss"]:
        text = swissify(text, ctx["lang"])
    return text, cited


def _sources(cited: list[str], ctx: dict[str, Any]) -> list[dict[str, str]]:
    labels = ctx["labels"]
    snippets = {labels[f"P{i}"]: p.get("text", "")[:240] for i, p in enumerate(ctx["passages"], 1)}
    seen: list[str] = []
    for k in cited:
        if k in labels and labels[k] not in seen:  # only labels that exist in THIS pack
            seen.append(labels[k])
    return [{"id": sid, "text": snippets.get(sid, "")} for sid in seen]


async def _translate(content: str, user_lang: str | None, ctx: dict[str, Any], llm: Any) -> str | None:
    if not (user_lang and user_lang != ctx["lang"] and content):
        return None
    translated = await translate_utterance(content, user_lang, llm)
    return strip_ungrounded_numerals(translated, ctx["pack_text"]) if ctx["grounded"] else translated


async def generate_npc_chat_reply(
    npc: dict[str, Any],
    user_message: str,
    conversation_history: list[dict[str, str]],
    memory_stream: list[dict[str, Any]],
    policy_context: str,
    user_lang: str | None = None,
) -> dict[str, Any]:
    """Generate an in-character, grounded reply to a user message.

    Returns {"text", "sources": [{"id", "text"}], "stance": "for|against|undecided", "translated": str | None}.
    Nothing is persisted back to the simulation.
    """
    ctx = _prepare(npc, user_message, conversation_history, memory_stream, policy_context)
    # Use a smaller max_tokens since chat responses should be concise
    llm = get_llm(max_tokens=1024, model=LLM_VOICE_NAME or None)
    response = await ainvoke_text(llm, ctx["prompt"])
    content, cited = _check(_clean(response.content), ctx)  # type: ignore[arg-type]
    sources = _sources(cited, ctx)
    translated = await _translate(content, user_lang, ctx, llm)
    logger.info("NPC chat: %s responded with %d chars, %d valid citations", npc.get("name", "?"), len(content), len(sources))
    return {"text": content, "sources": sources, "stance": stance_label(float(npc.get("stance", 0.0))), "translated": translated}


_SPAN = re.compile(r"<\|inner_prefix\|>.*?<\|inner_suffix\|>", re.DOTALL)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜÉÈÀ0-9«\"(])")


async def stream_npc_chat_reply(
    npc: dict[str, Any],
    user_message: str,
    conversation_history: list[dict[str, str]],
    memory_stream: list[dict[str, Any]],
    policy_context: str,
    on_chunk: Any,
    user_lang: str | None = None,
) -> dict[str, Any]:
    """Like `generate_npc_chat_reply`, but the answer is sent sentence by sentence while the model is still writing.

    The guardrails run on each complete sentence BEFORE it is sent (numbers outside the sources are stripped, bracketed text removed, Swiss spelling),
    so the user never sees text that the checks would have changed; tokens are not shown raw. First text arrives after the first sentence
    (≈ 1–2 s) instead of after the whole answer. `on_chunk(text)` is awaited for every cleaned sentence; the return value equals the non-streamed one."""
    ctx = _prepare(npc, user_message, conversation_history, memory_stream, policy_context)
    llm = get_llm(max_tokens=1024, model=LLM_VOICE_NAME or None, stream_usage=True)
    buffer, emitted, cited_all = "", [], []

    async def emit(sentence: str) -> None:
        sentence = sentence.strip()
        if not sentence or sentence.lower().startswith(_META_PREFIXES):  # leaked reasoning is dropped, as in the non-streamed path
            return
        text, cited = _check(sentence, ctx)
        cited_all.extend(cited)
        if text:
            emitted.append(text)
            await on_chunk(text)

    async for piece in astream_text(llm, ctx["prompt"]):
        buffer += piece
        if "<|inner_prefix|>" in buffer and "<|inner_suffix|>" not in buffer:
            continue  # a reasoning span is still open: wait for its end
        buffer = _SPAN.sub("", buffer)  # not strip_think_tags: it strips whitespace and would glue the next piece to the sentence
        parts = _SENTENCE_END.split(buffer)
        for done in parts[:-1]:
            await emit(done)
        buffer = parts[-1]
    await emit(buffer)
    content = " ".join(emitted).strip()
    if content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
    translated = await _translate(content, user_lang, ctx, llm)
    sources = _sources(cited_all, ctx)
    logger.info("NPC chat (streamed): %s responded with %d chars in %d sentences, %d valid citations", npc.get("name", "?"), len(content), len(emitted), len(sources))
    return {"text": content, "sources": sources, "stance": stance_label(float(npc.get("stance", 0.0))), "translated": translated}


async def generate_npc_chat_response(
    npc: dict[str, Any],
    user_message: str,
    conversation_history: list[dict[str, str]],
    memory_stream: list[dict[str, Any]],
    policy_context: str,
) -> str:
    """Spoken words only (kept for callers that do not need the sources)."""
    reply = await generate_npc_chat_reply(npc, user_message, conversation_history, memory_stream, policy_context)
    return reply["text"]
