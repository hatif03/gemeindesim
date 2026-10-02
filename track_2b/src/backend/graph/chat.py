"""NPC chat response generation (ephemeral, doesn't affect sim state).

This module provides the ability for users to have direct 1:1 conversations
with NPCs. The chat is "forked" from the current simulation state - meaning
the NPC has access to all its memories and context, but the conversation
itself is ephemeral and doesn't affect the main simulation.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from graph.llm import get_llm, strip_think_tags
from graph.memory import format_memories_for_prompt, get_current_plan, retrieve_memories
from graph.prompts import MBTI_DESC, NPC_CHAT_PROMPT

logger = logging.getLogger(__name__)


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


async def generate_npc_chat_response(
    npc: dict[str, Any],
    user_message: str,
    conversation_history: list[dict[str, str]],
    memory_stream: list[dict[str, Any]],
    policy_context: str,
) -> str:
    """Generate an in-character response from an NPC to a user message.

    This creates an ephemeral chat interaction. The NPC's memories and state
    are used for context, but nothing is persisted back to the simulation.

    Args:
        npc: The NPC's current state dict (from SimulationRecord.final_npcs).
        user_message: The message the user just sent.
        conversation_history: Previous messages in this chat session.
        memory_stream: The NPC's memory stream (copied, not mutated).
        policy_context: Summary of the policy being simulated.

    Returns:
        The NPC's response as a string (just their dialogue, no narration).
    """
    # Build a query from the user message + recent conversation for memory retrieval
    recent_context = " ".join(
        msg.get("content", "") for msg in conversation_history[-2:]
    )
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
    current_plan = get_current_plan(memory_stream) or "No specific plans right now."
    history_str = _format_conversation_history(conversation_history)

    # Build the prompt
    mbti = npc.get("mbti", "")
    prompt = NPC_CHAT_PROMPT.format(
        npc_name=npc.get("name", "Unknown"),
        npc_profession=npc.get("profession", "resident"),
        npc_mbti=mbti,
        npc_mbti_style=MBTI_DESC.get(mbti, mbti),
        npc_bio=npc.get("bio", "A resident."),
        npc_beliefs=", ".join(npc.get("beliefs", [])) or "None stated",
        npc_mood=npc.get("mood", "neutral"),
        npc_lang=npc.get("lang", "en"),
        town=npc.get("country") == "Switzerland" and "Linden" or "Millfield",
        retrieved_memories=memories_str,
        policy_summary=policy_context[:800] if policy_context else "No policy context.",
        conversation_history=history_str,
        user_message=user_message,
    )

    logger.info(
        "NPC chat: %s responding to '%s...' (memories=%d)",
        npc.get("name", "?"),
        user_message[:30],
        len(retrieved),
    )

    # Use a smaller max_tokens since chat responses should be concise
    llm = get_llm(max_tokens=1024)
    response = await llm.ainvoke(prompt)

    content: str = response.content  # type: ignore[assignment]

    # Strip reasoning spans — only the spoken words should remain.
    content = strip_think_tags(content)

    _META_PREFIXES = (
        "we need to", "the user has", "produce a response", "the instruction",
        "as the npc", "i need to", "let me", "okay so", "alright,",
    )
    if content and content.lower()[:60].lstrip().startswith(_META_PREFIXES):
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if s.strip()]
        for sentence in reversed(sentences):
            if not sentence.lower().startswith(_META_PREFIXES):
                content = sentence
                break
        else:
            content = ""

    # Remove any accidental quotation marks wrapping the response
    if content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
    if content.startswith("'") and content.endswith("'"):
        content = content[1:-1]

    content = content.strip()

    logger.info(
        "NPC chat: %s responded with %d chars", npc.get("name", "?"), len(content)
    )

    return content
