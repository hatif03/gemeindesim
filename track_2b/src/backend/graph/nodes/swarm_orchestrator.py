"""Node: swarm orchestrator — picks which NPCs initiate the first action each round."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from models.state import SimState

logger = logging.getLogger(__name__)


def _compute_initiator_scores(
    npcs: list[dict],
    relationships: list[dict],
) -> dict[str, float]:
    """Score each NPC for likelihood to initiate action this round.

    Weights:
      0.30 × |political_leaning|   — how strongly they care
      0.25 × degree_centrality     — how connected (info spreads through them)
      0.25 × policy_exposure       — how directly their livelihood is hit
      0.20 × mood_urgency          — angry/anxious → act first
    """
    # Degree centrality from relationship graph
    degrees: Counter = Counter()
    for rel in relationships:
        degrees[rel.get("source_id", "")] += 1
        degrees[rel.get("target_id", "")] += 1
    max_degree = max(degrees.values(), default=1)
    centrality = {nid: count / max_degree for nid, count in degrees.items()}

    income_exposure = {"low": 1.0, "medium": 0.5, "high": 0.2}
    role_exposure = {
        "activist": 1.0, "worker": 0.9, "farmer": 0.85, "business_owner": 0.8,
        "politician": 0.7, "shopkeeper": 0.6, "municipal_employee": 0.6,
        "teacher": 0.55, "driver": 0.5, "tenant": 0.45, "student": 0.4, "retiree": 0.3,
    }
    mood_urgency = {
        "angry": 1.0, "anxious": 0.8, "determined": 0.7, "worried": 0.6,
        "skeptical": 0.5, "excited": 0.4, "neutral": 0.3, "hopeful": 0.2,
    }

    scores: dict[str, float] = {}
    for npc in npcs:
        nid = npc["id"]
        political = abs(npc.get("political_leaning", 0.0))
        c = centrality.get(nid, 0.0)
        exposure = (
            income_exposure.get(npc.get("income_level", "medium"), 0.5)
            + role_exposure.get(npc.get("role", "worker"), 0.5)
        ) / 2.0
        urgency = mood_urgency.get(npc.get("mood", "neutral"), 0.3)
        scores[nid] = 0.30 * political + 0.25 * c + 0.25 * exposure + 0.20 * urgency
    return scores


async def swarm_orchestrator(state: SimState) -> dict[str, Any]:
    """Pick ~30% of NPCs as initiators for the round loop.

    Runs once after generate_npcs, before run_round_swarm.
    The chosen initiator_ids are stored in state and reused every round.
    """
    npcs = state["npcs"]
    if not npcs:
        return {"initiator_ids": []}

    num_initiators = max(2, round(len(npcs) * 0.3))
    scores = _compute_initiator_scores(npcs, state.get("relationships", []))
    sorted_npcs = sorted(npcs, key=lambda n: scores.get(n["id"], 0.0), reverse=True)
    initiators = [n["id"] for n in sorted_npcs[:num_initiators]]
    logger.info(
        "swarm_orchestrator: chose %d initiators (top scores: %s)",
        len(initiators),
        {n["id"]: round(scores.get(n["id"], 0), 3) for n in sorted_npcs[:3]},
    )
    return {"initiator_ids": initiators}
