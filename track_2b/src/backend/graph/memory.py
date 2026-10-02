"""Memory stream, retrieval, and reflection for NPC agents.

Architecture based on Park et al. (2023), "Generative Agents: Interactive
Simulacra of Human Behavior" (arXiv:2304.03442).  Adapted for a short-run
policy simulation (5 rounds) rather than multi-day open-world play.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from langchain_openai import ChatOpenAI

from config import MEMORY_TOP_K, RECENCY_DECAY, REFLECTION_THRESHOLD
from graph.llm import invoke_llm_structured
from graph.prompts import REFLECTION_PROMPT
from models.schemas import MemType, ReflectionResponse

logger = logging.getLogger(__name__)

# Jaccard similarity stop words — stripped before comparison.
_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "for",
    "and", "or", "but", "on", "at", "by", "with", "from", "as", "it", "that",
    "this", "i", "my", "me", "he", "she", "they", "we", "you", "his", "her",
    "its", "our", "your", "their", "has", "have", "had", "do", "does", "did",
    "be", "been", "being", "not", "no", "so", "if", "then", "than", "about",
})

# Heuristic importance scores by event type (avoids an LLM call per memory).
_EVENT_IMPORTANCE: dict[str, int] = {
    "protest": 8,
    "price_change": 7,
    "mood_shift": 7,
    "chat": 5,
    "move": 2,
}


# ---------------------------------------------------------------------------
# Memory creation
# ---------------------------------------------------------------------------

def create_memory(
    npc_id: str,
    description: str,
    round_num: int,
    importance: int,
    mem_type: MemType = "observation",
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Create a MemoryObject dict with a unique ID."""
    return {
        "id": f"{npc_id}_mem_{uuid4().hex[:6]}",
        "npc_id": npc_id,
        "description": description,
        "round_created": round_num,
        "round_last_accessed": round_num,
        "importance": max(1, min(10, importance)),
        "mem_type": mem_type,
        "evidence_ids": evidence_ids or [],
    }


def heuristic_importance(event_type: str) -> int:
    """Map an event type to an importance score (1-10)."""
    return _EVENT_IMPORTANCE.get(event_type, 4)


# ---------------------------------------------------------------------------
# Memory retrieval (Section 3.1 of the paper)
# ---------------------------------------------------------------------------

def _relevance(query: str, description: str) -> float:
    """Jaccard keyword similarity (substitute for embedding cosine similarity)."""
    q_words = set(query.lower().split()) - _STOP_WORDS
    d_words = set(description.lower().split()) - _STOP_WORDS
    if not q_words or not d_words:
        return 0.1
    intersection = q_words & d_words
    union = q_words | d_words
    return max(len(intersection) / len(union), 0.1)


def retrieve_memories(
    memories: list[dict[str, Any]],
    query: str,
    current_round: int,
    top_k: int = MEMORY_TOP_K,
    recency_decay: float = RECENCY_DECAY,
) -> list[dict[str, Any]]:
    """Score and return the top-K most relevant memories.

    Scoring formula (paper Sec. 3.1):
        score = recency * importance * relevance

    Side-effect: updates ``round_last_accessed`` on returned memories.
    """
    if not memories:
        return []

    scored: list[tuple[float, dict[str, Any]]] = []
    for mem in memories:
        recency = recency_decay ** (current_round - mem["round_last_accessed"])
        importance = mem["importance"] / 10.0
        relevance = _relevance(query, mem["description"])
        scored.append((recency * importance * relevance, mem))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:top_k]

    # Update last-accessed on retrieved memories.
    for _, mem in top:
        mem["round_last_accessed"] = current_round

    return [mem for _, mem in top]


# ---------------------------------------------------------------------------
# Formatting for prompts
# ---------------------------------------------------------------------------

def format_memories_for_prompt(memories: list[dict[str, Any]]) -> str:
    """Render retrieved memories as a numbered list for LLM context."""
    if not memories:
        return "No memories yet — this is your first experience with the policy."
    lines: list[str] = []
    for i, mem in enumerate(memories, 1):
        tag = f"[round {mem['round_created']}, {mem['mem_type']}]"
        lines.append(f"{i}. {tag} {mem['description']}")
    return "\n".join(lines)


def get_current_plan(memories: list[dict[str, Any]]) -> str | None:
    """Return the most recent plan description, or None."""
    plans = [m for m in memories if m.get("mem_type") == "plan"]
    if not plans:
        return None
    # Most recent by round_created, then by highest importance (active > decayed).
    plans.sort(key=lambda m: (m["round_created"], m["importance"]), reverse=True)
    return plans[0]["description"]


# ---------------------------------------------------------------------------
# Reflection (Section 3.3 of the paper)
# ---------------------------------------------------------------------------

def _should_reflect(memories: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    """Check if cumulative importance since last reflection exceeds threshold.

    Returns (should_reflect, recent_memories_since_last_reflection).
    """
    # Find the most recent reflection round.
    last_reflection_round = -1
    for mem in memories:
        if mem.get("mem_type") == "reflection":
            last_reflection_round = max(last_reflection_round, mem["round_created"])

    recent = [m for m in memories if m["round_created"] > last_reflection_round]
    total_importance = sum(m["importance"] for m in recent)
    return total_importance >= REFLECTION_THRESHOLD, recent


async def maybe_reflect(
    npc_id: str,
    npc_name: str,
    npc_profession: str,
    memories: list[dict[str, Any]],
    current_round: int,
    llm: ChatOpenAI,
    town: str = "Millfield",
) -> list[dict[str, Any]]:
    """Generate reflection memories if the importance threshold is met."""
    should, recent = _should_reflect(memories)
    if not should:
        return []

    # Format recent memories for the reflection prompt.
    mem_text = "\n".join(
        f"- [round {m['round_created']}] {m['description']}" for m in recent
    )
    evidence_ids = [m["id"] for m in recent]

    prompt = REFLECTION_PROMPT.format(
        npc_name=npc_name,
        npc_profession=npc_profession,
        town=town,
        recent_memories=mem_text,
    )

    result = await invoke_llm_structured(prompt, ReflectionResponse, llm=llm)
    insights = result.insights[:3]

    new_memories: list[dict[str, Any]] = []
    for insight in insights:
        new_memories.append(
            create_memory(
                npc_id=npc_id,
                description=insight,
                round_num=current_round,
                importance=8,
                mem_type="reflection",
                evidence_ids=evidence_ids,
            )
        )
    logger.info("Reflection for %s produced %d insights", npc_name, len(new_memories))
    return new_memories


