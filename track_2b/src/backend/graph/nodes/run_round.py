"""Node: execute one simulation round — every NPC perceives, reacts, and acts.

Agent architecture based on Park et al. (2023), "Generative Agents: Interactive
Simulacra of Human Behavior" (arXiv:2304.03442).  Each NPC maintains a memory
stream, retrieves relevant memories, reflects periodically, and follows/revises
an internal plan.

Opinion dynamics based on Peralta, Kertész & Iñiguez (2022),
"Opinion dynamics in social networks: From models to data" (arXiv:2201.01322).
Implements Deffuant bounded confidence (Eq. 1-2), Baumann controversy
amplification (Eq. 6), and keep/compromise/adopt behavioral classification.
"""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass, field
from collections.abc import Coroutine
from typing import Any

from langchain_openai import ChatOpenAI

from config import MAX_X, MAX_Y
import re

from graph.calculator import household_line
from graph.corpus import (
    chunk_policy_document,
    default_top_k,
    detect_setting,
    format_passages,
    passage_labels,
    retrieve_passages,
)
from graph.language import (
    TOWN,
    fallback_utterance,
    glossary_for,
    has_figures,
    strip_ungrounded_numerals,
    swissify,
    translate_utterance,
    ungrounded_numerals,
)
from graph.llm import get_llm, invoke_llm_structured
from graph.memory import (
    create_memory,
    format_memories_for_prompt,
    get_current_plan,
    heuristic_importance,
    maybe_reflect,
    retrieve_memories,
)
from graph.nodes.stance import stance_binding, stance_label, stance_line, stance_summary
from graph.prompts import MBTI_DESC, NPC_ROUND_PROMPT_V2
from graph.utils import clamp, normalize_npc_id
from models.schemas import NPCEvent, NPCRoundResponse
from models.state import SimState

logger = logging.getLogger(__name__)


def _political_label(value: float) -> str:
    """Human-readable political leaning."""
    if value <= -0.6:
        return "strongly progressive"
    if value <= -0.2:
        return "leaning progressive"
    if value <= 0.2:
        return "moderate/centrist"
    if value <= 0.6:
        return "leaning conservative"
    return "strongly conservative"


_TYPE_WEIGHTS = {
    "family": 1.5,
    "friend": 1.2,
    "employer": 1.0,
    "colleague": 0.8,
    "neighbor": 0.5,
}

# --- Opinion dynamics constants (Peralta et al. 2022) ---

# Mood represented as continuous value in [0, 1] for Deffuant dynamics.
# Closed enum must match MoodLiteral / Phaser (unknowns map via _fuzzy_mood_to_ladder).
_MOOD_LADDER = [
    "angry",
    "anxious",
    "worried",
    "neutral",
    "hopeful",
    "excited",
]
_MOOD_TO_CONTINUOUS = {
    m: i / (len(_MOOD_LADDER) - 1) for i, m in enumerate(_MOOD_LADDER)
}
_MOOD_BREAKPOINTS = [i / (len(_MOOD_LADDER) - 1) for i in range(len(_MOOD_LADDER))]

# Deffuant bounded confidence parameters (Eq. 1-2).
_MU_POLITICAL = 0.3  # Convergence rate for political leaning.
_MU_MOOD = 0.4  # Convergence rate for mood (moods shift faster than politics).
_EPSILON_POLITICAL = 0.7  # Confidence bound: only interact if |x_i - x_j| < ε.
_EPSILON_MOOD = 1.1  # No effective bound for mood (emotions are always contagious).

# Baumann controversy amplification (Eq. 6): α parameter per controversy level.
_CONTROVERSY_ALPHA = {"low": 1.0, "medium": 2.0, "high": 3.5}

# Keep/compromise/adopt thresholds from Chacoma & Zanette (2015), Sec. 3.3.
_ADOPT_THRESHOLD = 0.85  # I_ij above this → adopt (copy opinion).
_COMPROMISE_THRESHOLD = 0.25  # I_ij above this → compromise (Deffuant update).

# Keyword-based fuzzy mood mapping. First matching substring wins.
_MOOD_KEYWORDS: list[tuple[str, str]] = [
    ("angry", "angry"),
    ("furious", "angry"),
    ("outrag", "angry"),
    ("anxi", "anxious"),
    ("nervous", "anxious"),
    ("fear", "anxious"),
    ("dread", "anxious"),
    ("frustr", "anxious"),
    ("worr", "worried"),
    ("concern", "worried"),
    ("skeptic", "worried"),
    ("disappoint", "worried"),
    ("uneasy", "worried"),
    ("neutral", "neutral"),
    ("indifferen", "neutral"),
    ("ambivalen", "neutral"),
    ("hope", "hopeful"),
    ("optim", "hopeful"),
    ("cautious", "hopeful"),
    ("content", "hopeful"),
    ("determin", "hopeful"),
    ("resolut", "hopeful"),
    ("pleas", "hopeful"),
    ("satisf", "hopeful"),
    ("confiden", "hopeful"),
    ("excit", "excited"),
    ("thrill", "excited"),
    ("elat", "excited"),
]


def _fuzzy_mood_to_ladder(mood: str) -> str:
    """Map an arbitrary mood string to the closest ``_MOOD_LADDER`` value."""
    low = mood.lower().strip()
    if low in ("determined", "resolute"):
        return "hopeful"
    if low in ("skeptical", "sceptical"):
        return "worried"
    if low in _MOOD_TO_CONTINUOUS:
        return low
    for keyword, ladder_mood in _MOOD_KEYWORDS:
        if keyword in low:
            return ladder_mood
    return "neutral"


def _build_relationship_map(
    relationships: list[dict[str, Any]],
) -> dict[str, list[tuple[str, float, float]]]:
    """Pre-index relationships as {npc_id: [(other_id, affinity, trust), ...]}.

    Deduplicates: if the same pair appears multiple times, only the entry with
    the highest total (affinity + trust) is kept (though they should be unique).
    """
    # First pass: pick the strongest relationship per directed pair.
    best: dict[
        tuple[str, str], tuple[float, float]
    ] = {}  # (src,tgt) → (affinity, trust)
    for rel in relationships:
        src: str = rel.get("source_id", "")
        tgt: str = rel.get("target_id", "")
        affinity = float(rel.get("affinity", 0.0))
        trust = float(rel.get("trust", 0.5))
        for pair in [(src, tgt), (tgt, src)]:
            prev = best.get(pair)
            if prev is None or (affinity + trust) > (prev[0] + prev[1]):
                best[pair] = (affinity, trust)

    # Second pass: build the map from deduplicated entries.
    rel_map: dict[str, list[tuple[str, float, float]]] = {}
    for (src, tgt), (affinity, trust) in best.items():
        rel_map.setdefault(src, []).append((tgt, affinity, trust))
    return rel_map


def _build_neighbor_ids(
    npc: dict[str, Any], all_npcs: list[dict[str, Any]], radius: int = 2
) -> list[str]:
    """Return IDs of NPCs within *radius* tiles (Chebyshev distance)."""
    npc_id: str = npc.get("id", "")
    nx: int = npc.get("x", 0)
    ny: int = npc.get("y", 0)
    neighbors: list[str] = []
    for other in all_npcs:
        oid: str = other.get("id", "")
        if oid == npc_id:
            continue
        dx = abs(other.get("x", 0) - nx)
        dy = abs(other.get("y", 0) - ny)
        if max(dx, dy) <= radius:
            neighbors.append(oid)
    return neighbors


def _find_closest_neighbor(
    npc_id: str,
    all_npcs: list[dict[str, Any]],
    neighbor_ids: list[str],
) -> str | None:
    """Find the closest NPC from neighbor_ids to the given NPC."""
    if not neighbor_ids:
        return None

    npc = next((n for n in all_npcs if n.get("id") == npc_id), None)
    if not npc:
        return neighbor_ids[0] if neighbor_ids else None

    nx, ny = npc.get("x", 0), npc.get("y", 0)
    closest_id = None
    closest_dist = float("inf")

    for other in all_npcs:
        oid = other.get("id", "")
        if oid not in neighbor_ids:
            continue
        dx = abs(other.get("x", 0) - nx)
        dy = abs(other.get("y", 0) - ny)
        dist = max(dx, dy)  # Chebyshev distance
        if dist < closest_dist:
            closest_dist = dist
            closest_id = oid

    return closest_id


def _validate_chat_target(
    event: dict[str, Any],
    speaker_id: str,
    neighbor_ids: list[str],
    all_npcs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate and correct target_npc_id for chat events.

    If the target is not within proximity (neighbor_ids), auto-correct to the
    closest valid neighbor. If no neighbors exist, clear the target.
    """
    if event.get("event_type") != "chat":
        return event

    target_id = event.get("data", {}).get("target_npc_id", "")

    if target_id and target_id in neighbor_ids:
        return event  # Target is valid and within proximity

    # Need to assign/re-assign a target (no target specified, or target out of range)
    new_target = _find_closest_neighbor(speaker_id, all_npcs, neighbor_ids) if neighbor_ids else None

    event = dict(event)
    data = dict(event.get("data", {}))
    data["target_npc_id"] = new_target or ""
    event["data"] = data

    if not target_id and new_target:
        logger.debug("NPC %s chat had no target, auto-assigned to nearby %s", speaker_id, new_target)
    elif target_id and new_target:
        logger.debug("NPC %s chat target %s out of range, corrected to nearby %s", speaker_id, target_id, new_target)
    elif target_id and not new_target:
        logger.debug("NPC %s chat target %s out of range with no neighbors, cleared target", speaker_id, target_id)

    return event


def _format_nearby_npcs(
    neighbor_ids: list[str],
    all_npcs: list[dict[str, Any]],
    npc_rels: list[tuple[str, float, float]],
) -> str:
    """List nearby NPCs with name, role, mood, and relationship annotation."""
    if not neighbor_ids:
        return "Nobody is nearby right now."
    id_set = set(neighbor_ids)
    rel_lookup = {other_id: (affinity, trust) for other_id, affinity, trust in npc_rels}
    lines: list[str] = []
    for other in all_npcs:
        oid = other.get("id")
        if oid in id_set:
            line = f"- {other.get('name', '?')} [{oid}] ({other.get('profession', '?')}) [Rep: {other.get('reputation', 0.5):.2f}]"
            if oid in rel_lookup:
                affinity, trust = rel_lookup[oid]
                line += f" [Known, Like: {affinity:.1f}, Trust: {trust:.1f}]"
            else:
                line += " [stranger]"
            lines.append(line)
    return "\n".join(lines)


def _format_social_targets(
    npc: dict[str, Any],
    npc_rels: list[tuple[str, float, float]],
    neighbor_ids: list[str],
    all_npcs: list[dict[str, Any]],
) -> str:
    """Identify strong social ties not currently nearby, with direction hints."""
    if not npc_rels:
        return "You have no strong social connections in town."

    npc_x, npc_y = npc.get("x", 0), npc.get("y", 0)
    neighbor_set = set(neighbor_ids)
    npc_lookup: dict[str | None, dict[str, Any]] = {n.get("id"): n for n in all_npcs}

    candidates: list[tuple[float, str, str, float, float, str, int]] = []
    for other_id, affinity, trust in npc_rels:
        if other_id in neighbor_set:
            continue
        other = npc_lookup.get(other_id)
        if not other:
            continue
        ox, oy = other.get("x", 0), other.get("y", 0)
        dist = max(abs(ox - npc_x), abs(oy - npc_y))
        # Influence based on trust and absolute affinity (strong feeling either way)
        pull = trust * (abs(affinity) + 0.5)
        dx, dy = ox - npc_x, oy - npc_y
        dirs: list[str] = []
        if dy < 0:
            dirs.append("north")
        if dy > 0:
            dirs.append("south")
        if dx > 0:
            dirs.append("east")
        if dx < 0:
            dirs.append("west")
        direction = "-".join(dirs) if dirs else "here"
        candidates.append(
            (
                pull,
                other.get("name", "?"),
                other_id,
                affinity,
                trust,
                direction,
                dist,
            )
        )

    if not candidates:
        return "All your social connections are nearby already."

    candidates.sort(key=lambda c: c[0], reverse=True)
    lines: list[str] = []
    for _, name, oid, affinity, trust, direction, dist in candidates[:3]:
        lines.append(
            f"- {name} [{oid}] (Like: {affinity:.1f}, Trust: {trust:.1f}) — {dist} tiles {direction}"
        )
    return "\n".join(lines)


def _build_round_context(
    current_round: int, max_rounds: int, events: list[dict[str, Any]]
) -> str:
    """Provide a brief high-level summary of how the simulation is going."""
    if current_round == 0:
        return "The policy was just announced. People are hearing about it for the first time."

    prev_events = [e for e in events if e.get("round") == current_round - 1]
    total_events = len(prev_events)
    protests = sum(1 for e in prev_events if e.get("event_type") == "protest")
    mood_shifts = sum(1 for e in prev_events if e.get("event_type") == "mood_shift")

    parts: list[str] = [f"Last round saw {total_events} total actions across town."]
    if protests:
        parts.append(f"{protests} protest(s) broke out.")
    if mood_shifts:
        parts.append(f"{mood_shifts} people experienced a change in mood.")
    if current_round >= max_rounds - 1:
        parts.append("This is the final round — make it count.")
    return " ".join(parts)


def _policy_summary(entities: list[dict[str, Any]], context_summary: str = "") -> str:
    """Condense parsed policy entities into a readable summary for NPCs."""
    if not entities:
        base = "A new economic policy has been announced, but details are unclear."
        if context_summary:
            return f"{base}\n\nAdditional context:\n{context_summary}"
        return base

    e = entities[0]
    sectors = ", ".join(e.get("sectors", [])[:6]) or "various sectors"
    impacts: list[str] = []
    for imp in e.get("economic_impacts", [])[:4]:
        if isinstance(imp, str):
            impacts.append(f"  - {imp}")
        else:
            desc = imp.get("description", "") or imp.get("desc", "")
            if desc:
                impacts.append(f"  - {desc}")
    impacts_str = "\n".join(impacts) if impacts else "  - Details still emerging"
    controversy = e.get("controversy_level", "medium")

    summary = (
        f"A new policy affecting {sectors} has been announced.\n"
        f"Key expected impacts:\n{impacts_str}\n"
        f"Controversy level: {controversy}"
    )
    if context_summary:
        return f"{summary}\n\nAdditional context:\n{context_summary}"
    return summary


@dataclass
class NPCRoundResult:
    """Output from a single NPC's round."""

    events: list[dict[str, Any]] = field(default_factory=list)
    perception: str = ""


async def _simulate_single_npc(
    npc: dict[str, Any],
    npc_memories: list[dict[str, Any]],
    llm: ChatOpenAI,
    current_round: int,
    max_rounds: int,
    policy_text: str,
    round_context: str,
    neighbor_ids: list[str],
    npc_rels: list[tuple[str, float, float]],
    all_npcs: list[dict[str, Any]],
    name_to_id: dict[str, str],
    objective: str = "",
    policy_chunks: list[dict[str, Any]] | None = None,
    town: str = "Millfield",
) -> NPCRoundResult:
    """Full per-agent cognitive loop (Park et al. 2023):
    Retrieve → Reflect → Plan → Perceive/React/Act → Store memories.
    """
    npc_id: str = npc.get("id", "unknown")
    npc_name: str = npc.get("name", "Unknown")

    # ---- 1. Retrieve memories ----
    neighbor_id_set = set(neighbor_ids)
    neighbor_names = [
        n.get("name", "") for n in all_npcs if n.get("id") in neighbor_id_set
    ]
    query = f"{policy_text} {' '.join(neighbor_names)} {round_context}"
    retrieved = retrieve_memories(npc_memories, query, current_round)
    memories_str = format_memories_for_prompt(retrieved)

    # ---- 2. Reflect (if importance threshold met) ----
    reflection_mems = await maybe_reflect(
        npc_id=npc_id,
        npc_name=npc_name,
        npc_profession=npc.get("profession", ""),
        memories=npc_memories,
        current_round=current_round,
        llm=llm,
        town=town,
    )
    npc_memories.extend(reflection_mems)

    # ---- 3. Get current plan ----
    plan_str = get_current_plan(npc_memories) or ""

    # ---- 4. Build context and run main LLM call ----
    nearby_npcs_str = _format_nearby_npcs(neighbor_ids, all_npcs, npc_rels)
    social_targets_str = _format_social_targets(npc, npc_rels, neighbor_ids, all_npcs)
    mbti = npc.get("mbti", "")
    lang = npc.get("lang", "en")
    # Query in the resident's own language: who they are, why they care, what they remember.
    # (The English LLM policy summary used to dominate this query and matched nothing.)
    query = (
        f"{npc.get('profession', '')} {npc.get('bio', '')[:300]} {npc.get('stance_reason', '')} "
        f"{' '.join(neighbor_names)} {memories_str[:600]}"
    )
    passages = retrieve_passages(policy_chunks or [], query, top_k=default_top_k(policy_chunks or []), lang=lang)
    pack = format_passages(passages)
    labels = passage_labels(passages)
    pack_text = "\n".join(p.get("text", "") for p in passages)  # figures are grounded here only
    # The model cannot do the booklet's own arithmetic (E7), so the resident's personal figure is
    # computed in code and enters both the prompt and the grounding pack.
    personal = household_line("\n".join(c.get("text", "") for c in (policy_chunks or [])), npc.get("income_level", "medium"), lang)
    if personal:
        pack = f"{pack}\n\n{personal}"
        pack_text = f"{pack_text}\n{personal}"
    swiss = town == TOWN["ch"]

    prompt = NPC_ROUND_PROMPT_V2.format(
        npc_name=npc_name,
        npc_profession=npc.get("profession", "local resident"),
        npc_mbti=mbti,
        npc_mbti_style=MBTI_DESC.get(mbti, mbti),
        npc_bio=npc.get("bio", ""),
        npc_beliefs=", ".join(npc.get("beliefs", [])),
        npc_income=npc.get("income_level", "medium"),
        npc_leaning=_political_label(npc.get("political_leaning", 0.0)),
        npc_reputation=f"{npc.get('reputation', 0.5):.2f}",
        npc_x=npc.get("x", 0),
        npc_y=npc.get("y", 0),
        npc_lang=lang,
        stance_line=stance_line(npc),
        stance_binding=stance_binding(npc),
        town=town,
        glossary=glossary_for(lang),
        life_story=(npc.get("life_story") or "")[:1200],
        expert_reflection=(npc.get("expert_reflection") or "")[:600],
        policy_passages=pack,
        policy_summary=policy_text,
        current_round=current_round + 1,
        max_rounds=max_rounds,
        round_context=round_context,
        nearby_npcs=nearby_npcs_str,
        social_targets=social_targets_str,
        retrieved_memories=memories_str,
        current_plan=plan_str or "None yet.",
    )

    try:
        result = await invoke_llm_structured(prompt, NPCRoundResponse, llm=llm, lang=lang)
    except Exception as exc:
        logger.warning("NPC %s structured call failed (%s) — using fallback event", npc_id, exc)
        result = NPCRoundResponse(
            events=[
                NPCEvent(
                    event_type="mood_shift",
                    message=fallback_utterance(lang),
                    new_mood=str(npc.get("mood") or "neutral"),
                    grounded=False,
                )
            ],
            perception="",
        )
    perception = swissify(result.perception, lang) if swiss else result.perception

    # Tag each event with round and NPC id, and validate chat targets.
    sim_events: list[dict[str, Any]] = []
    for ev in result.events:
        ev_dict = ev.model_dump()
        raw_target = ev_dict.get("target_npc_id")
        if raw_target:
            ev_dict["target_npc_id"] = normalize_npc_id(raw_target, name_to_id)
        message = strip_ungrounded_numerals(ev_dict.get("message", "") or "", pack_text)
        dialogue = strip_ungrounded_numerals(ev_dict.get("dialogue", "") or "", pack_text)
        if swiss:  # Swiss Standard German has no ß
            message, dialogue = swissify(message, lang), swissify(dialogue, lang)
        ev_dict["message"] = message
        ev_dict["dialogue"] = dialogue
        # Citations: the model copies labels (P1..); keep only those that exist in THIS pack.
        raw_cites = [str(c) for c in (ev_dict.get("used_source_ids") or [])]
        keys = [f"P{m.group(1)}" for c in raw_cites if (m := re.search(r"(\d+)", c))]
        ev_dict["used_source_ids"] = [labels[k] for k in keys if k in labels]
        ev_dict["invalid_cites"] = len(raw_cites) - len(ev_dict["used_source_ids"])
        snippets = {labels[f"P{i}"]: p.get("text", "")[:240] for i, p in enumerate(passages, 1)}
        ev_dict["sources"] = [{"id": sid, "text": snippets.get(sid, "")} for sid in ev_dict["used_source_ids"]]  # for the UI tooltip
        extra = ungrounded_numerals(f"{message} {dialogue}", pack_text)
        needs_cite = has_figures(f"{message} {dialogue}", pack_text)
        ev_dict["grounded"] = not extra and (bool(ev_dict["used_source_ids"]) or not needs_cite)
        target_id = ev_dict.get("target_npc_id") or ""
        target_npc = next((n for n in all_npcs if n.get("id") == target_id), None)
        if (
            ev_dict.get("event_type") == "chat"
            and target_npc
            and target_npc.get("lang")
            and target_npc.get("lang") != lang
            and (dialogue or message)
        ):
            translated = await translate_utterance(
                dialogue or message, str(target_npc.get("lang")), llm
            )
            ev_dict["translated_dialogue"] = strip_ungrounded_numerals(translated, pack_text)
        sim_event = {
            "round": current_round,
            "npc_id": npc_id,
            "event_type": ev_dict.get("event_type", "chat"),
            "message": ev_dict.get("message", ""),
            "data": ev_dict,
        }
        sim_event = _validate_chat_target(sim_event, npc_id, neighbor_ids, all_npcs)
        sim_events.append(sim_event)

    # ---- 5. Store memories from this round ----
    if perception:
        npc_memories.append(
            create_memory(npc_id, perception, current_round, importance=6, mem_type="observation")
        )
        npc_memories.append(
            create_memory(npc_id, perception, current_round, importance=5, mem_type="plan")
        )
    for ev in sim_events:
        npc_memories.append(
            create_memory(
                npc_id,
                ev.get("message", ""),
                current_round,
                importance=heuristic_importance(ev.get("event_type", "chat")),
                mem_type="observation",
            )
        )

    return NPCRoundResult(events=sim_events, perception=perception)


def _mood_to_continuous(mood: str) -> float:
    """Map a discrete mood string to [0, 1] for Deffuant dynamics."""
    mapped = _fuzzy_mood_to_ladder(mood)
    return _MOOD_TO_CONTINUOUS[mapped]


def _continuous_to_mood(value: float) -> str:
    """Map a continuous [0, 1] value back to the closest discrete mood."""
    value = clamp(value, 0.0, 1.0)
    best_idx = min(range(len(_MOOD_BREAKPOINTS)), key=lambda i: abs(value - _MOOD_BREAKPOINTS[i]))
    return _MOOD_LADDER[best_idx]


def _compute_influence_factor(
    speaker_id: str,
    target_id: str,
    rel_map: dict[str, list[tuple[str, float, float]]],
    speaker_reputation: float,
) -> float:
    """Compute I_ij influence factor from relationship and reputation data."""
    rels = rel_map.get(speaker_id, [])
    rel_match = next(((a, t) for oid, a, t in rels if oid == target_id), None)

    if rel_match:
        affinity, trust = rel_match
        # Reputation and trust amplify influence; affinity makes them more receptive.
        social_mod = (speaker_reputation + trust + (affinity + 1) / 2) / 3
        return min(1.0, 0.4 * (0.4 + 1.2 * social_mod))

    # Stranger influence is primarily driven by reputation.
    return min(1.0, 0.1 * (0.5 + speaker_reputation))


def _apply_opinion_dynamics(
    npcs: list[dict[str, Any]],
    events: list[dict[str, Any]],
    current_round: int,
    rel_map: dict[str, list[tuple[str, float, float]]],
    controversy: str,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, float]], list[dict[str, Any]]]:
    """Apply opinion dynamics from Peralta et al. (2022) to NPC interactions.

    Returns (updated_npcs, updated_relationships, influence_log).
    """
    npc_lookup = {n.get("id", ""): dict(n) for n in npcs}
    # Track relationship updates: (src, tgt) -> {affinity: float, trust: float}
    rel_updates: dict[tuple[str, str], dict[str, float]] = {}

    alpha = _CONTROVERSY_ALPHA.get(controversy, 2.0)
    influence_log: list[dict[str, Any]] = []
    touched: set[str] = set()  # residents who actually conversed; only they drift (E4)

    chat_events = [
        e
        for e in events
        if e.get("round") == current_round and e.get("event_type") == "chat"
    ]

    for ev in chat_events:
        speaker_id = ev.get("npc_id", "")
        target_id = ev.get("data", {}).get("target_npc_id", "")
        if not target_id or target_id not in npc_lookup or speaker_id not in npc_lookup:
            continue

        speaker = npc_lookup[speaker_id]
        target = npc_lookup[target_id]
        s_rep = float(speaker.get("reputation", 0.5))

        i_ij = _compute_influence_factor(speaker_id, target_id, rel_map, s_rep)

        # --- Classify behavior: keep / compromise / adopt (Sec. 3.3) ---
        if i_ij < _COMPROMISE_THRESHOLD:
            influence_log.append(
                {
                    "speaker_id": speaker_id,
                    "target_id": target_id,
                    "influence": round(i_ij, 4),
                    "behavior": "keep",
                    "political_delta": 0.0,
                    "mood_delta": 0.0,
                }
            )
            continue

        old_political = float(target.get("political_leaning", 0.0))
        old_mood = _mood_to_continuous(target.get("mood", "neutral"))
        behavior = "adopt" if i_ij >= _ADOPT_THRESHOLD else "compromise"
        touched.update((speaker_id, target_id))

        # --- Stance update (the variable the Vorlage is actually about) ---
        s_i = (float(speaker.get("stance", 0.0)) + 1.0) / 2.0
        s_j = (float(target.get("stance", 0.0)) + 1.0) / 2.0
        if abs(s_i - s_j) < _EPSILON_POLITICAL:
            new_s = s_i if i_ij >= _ADOPT_THRESHOLD else s_j + _MU_POLITICAL * i_ij * (s_i - s_j)
            centered_s = 2.0 * new_s - 1.0
            new_s = clamp(new_s + 0.05 * math.tanh(alpha * centered_s), 0.0, 1.0)
            npc_lookup[target_id]["stance"] = round(new_s * 2.0 - 1.0, 4)

        # --- Political leaning update ---
        x_i = (float(speaker.get("political_leaning", 0.0)) + 1.0) / 2.0
        x_j = (old_political + 1.0) / 2.0

        if abs(x_i - x_j) < _EPSILON_POLITICAL:
            if i_ij >= _ADOPT_THRESHOLD:
                new_x_j = x_i
            else:
                new_x_j = x_j + _MU_POLITICAL * i_ij * (x_i - x_j)

            centered = 2.0 * new_x_j - 1.0
            controversy_push = 0.05 * math.tanh(alpha * centered)
            new_x_j = clamp(new_x_j + controversy_push, 0.0, 1.0)
            npc_lookup[target_id]["political_leaning"] = round(new_x_j * 2.0 - 1.0, 4)

        # --- Mood update ---
        m_i = _mood_to_continuous(speaker.get("mood", "neutral"))
        m_j = old_mood

        if abs(m_i - m_j) < _EPSILON_MOOD:
            if i_ij >= _ADOPT_THRESHOLD:
                new_m_j = m_i
            else:
                mu_effective = _MU_MOOD * (1.3 if m_i < m_j else 1.0)
                new_m_j = m_j + mu_effective * i_ij * (m_i - m_j)

            new_m_j = clamp(new_m_j, 0.0, 1.0)
            npc_lookup[target_id]["mood"] = _continuous_to_mood(new_m_j)

        # --- Reputation, Affinity, and Trust updates ---
        new_political = float(npc_lookup[target_id].get("political_leaning", 0.0))
        pol_diff = abs(new_political - float(speaker.get("political_leaning", 0.0)))
        is_controversial = ev.get("is_controversial", False)

        # Affinity increases if opinions are similar or converged
        # Multiplier if it's a controversial idea: they really like or hate you for it.
        impact_mult = 3.0 if is_controversial else 1.0

        # If pol_diff is low, they like the speaker more.
        # If behavior is "adopt" or "compromise", they have bonded over the idea.
        if behavior != "keep":
            aff_delta = (0.08 if pol_diff < 0.4 else 0.02) * impact_mult
            trust_delta = 0.05 * impact_mult
        else:
            # They didn't listen. If it was controversial, they might like the speaker LESS.
            aff_delta = -0.05 if is_controversial else -0.01
            trust_delta = -0.02 if is_controversial else 0.0

        # Reputation changes based on how the target reacted.
        # If the target likes the speaker (affinity up), the speaker's reputation grows.
        # If it was a controversial idea and the target HATED it (affinity down), reputation tanks.
        rep_delta = (0.02 if aff_delta > 0 else -0.03) * impact_mult

        # High reputation characters have "social armor": they lose less reputation from single bad interactions
        # but also gain it slower (diminishing returns).
        current_rep = float(speaker.get("reputation", 0.5))
        if rep_delta < 0:
            rep_delta *= 1.2 - current_rep  # Armor: high rep = less loss
        else:
            rep_delta *= 1.1 - current_rep  # Diminishing returns: high rep = less gain

        npc_lookup[speaker_id]["reputation"] = round(
            clamp(current_rep + rep_delta, 0.05, 1.0), 3
        )

        pair = (target_id, speaker_id)  # Update target's view of speaker
        updates = rel_updates.setdefault(pair, {"affinity": 0.0, "trust": 0.0})
        updates["affinity"] += aff_delta
        updates["trust"] += trust_delta

        influence_log.append(
            {
                "speaker_id": speaker_id,
                "target_id": target_id,
                "influence": round(i_ij, 4),
                "behavior": behavior,
                "political_delta": round(new_political - old_political, 4),
                "mood_delta": 0.0,  # Not tracked in log currently
            }
        )

    # Baumann controversy drift, interaction-gated: the old "everyone, every round" version
    # polarised a silent town (research E4: mean |x| 0.51 -> 0.69 in 15 rounds, zero chats).
    if alpha > 1.5:
        for nid in touched:
            npc = npc_lookup[nid]
            x = float(npc.get("political_leaning", 0.0))
            drift = 0.02 * math.tanh(alpha * x)
            npc["political_leaning"] = round(clamp(x + drift, -1.0, 1.0), 4)

    return list(npc_lookup.values()), rel_updates, influence_log


def _deduplicate_moves(
    npcs: list[dict],
    move_updates: dict[str, tuple[int, int]],
) -> dict[str, tuple[int, int]]:
    """Block moves that would land on an occupied tile (stationary NPC wins)."""
    occupied_targets: set[tuple[int, int]] = set()
    for npc in npcs:
        npc_id = npc.get("id", "")
        if npc_id not in move_updates:
            occupied_targets.add((npc.get("x", 0), npc.get("y", 0)))

    deduplicated: dict[str, tuple[int, int]] = {}
    for npc_id, pos in move_updates.items():
        if pos not in occupied_targets:
            occupied_targets.add(pos)
            deduplicated[npc_id] = pos
    return deduplicated


def _compute_economic_indicators(
    npcs: list[dict[str, Any]],
    events: list[dict[str, Any]],
    round_num: int,
    max_rounds: int,
    kind: str = "policy",
) -> dict[str, float]:
    """Derive economic metrics from NPC state and events this round.

    For a vote, ``policy_approval`` is the stance poll (for + half of undecided), not a mood proxy.
    """
    total = len(npcs) or 1

    mood_scores = {
        "excited": 1.0, "hopeful": 0.75, "neutral": 0.5,
        "worried": 0.3, "anxious": 0.2, "angry": 0.0,
    }
    moods = [n.get("mood", "neutral") for n in npcs]
    avg_sentiment = sum(mood_scores.get(m, 0.5) for m in moods) / total

    protests = sum(1 for e in events if e.get("event_type") == "protest")
    price_changes = [e for e in events if e.get("event_type") == "price_change"]
    avg_price_change = (
        sum(e.get("data", {}).get("pct_change", 0) for e in price_changes)
        / max(len(price_changes), 1)
    )

    biz_npcs = [n for n in npcs if n.get("role") in ("business_owner", "shopkeeper")]
    worker_npcs = [n for n in npcs if n.get("role") in ("worker", "farmer")]
    biz_sentiment = sum(mood_scores.get(n.get("mood", "neutral"), 0.5) for n in biz_npcs) / max(len(biz_npcs), 1)
    worker_sentiment = sum(mood_scores.get(n.get("mood", "neutral"), 0.5) for n in worker_npcs) / max(len(worker_npcs), 1)

    protest_rate = protests / total
    st = stance_summary(npcs)
    approval = (avg_sentiment * 0.7 + (1 - protest_rate) * 0.3) * 100
    if kind == "vote" and any("stance" in n for n in npcs):
        approval = (st["for"] + 0.5 * st["undecided"]) / total * 100
    return {
        "consumer_confidence": round(avg_sentiment * 100, 1),
        "business_climate": round(biz_sentiment * 100, 1),
        "worker_welfare": round(worker_sentiment * 100, 1),
        "price_pressure": round(avg_price_change, 1),
        "social_unrest_index": round(protest_rate * 100, 1),
        "policy_approval": round(approval, 1),
        "stance_for": float(st["for"]),
        "stance_against": float(st["against"]),
        "stance_undecided": float(st["undecided"]),
        "stance_mean": st["mean"],
        "stance_spread": st["spread"],
    }


def _apply_post_round(
    npcs: list[dict[str, Any]],
    all_events: list[dict[str, Any]],
    current_round: int,
    max_rounds: int,
    relationships: list[dict[str, Any]],
    rel_map: dict[str, list[tuple[str, float, float]]],
    entities: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, float]]:
    """Apply mood shifts, moves, opinion dynamics, and relationship updates.

    Returns (updated_npcs, updated_rels, influence_log, indicators).
    Shared by run_round and run_round_swarm.
    """
    mood_updates: dict[str, str] = {}
    move_updates: dict[str, tuple[int, int]] = {}

    for ev in all_events:
        if ev["event_type"] == "mood_shift":
            new_mood = ev.get("data", {}).get("new_mood")
            if new_mood:
                mood_updates[ev["npc_id"]] = _fuzzy_mood_to_ladder(new_mood)
        elif ev["event_type"] == "move":
            to_x = ev.get("data", {}).get("to_x")
            to_y = ev.get("data", {}).get("to_y")
            if to_x is not None and to_y is not None:
                move_updates[ev["npc_id"]] = (
                    int(clamp(int(to_x), 0, MAX_X)),
                    int(clamp(int(to_y), 0, MAX_Y)),
                )

    move_updates = _deduplicate_moves(npcs, move_updates)

    for npc in npcs:
        npc_id = npc.get("id", "")
        if npc_id in mood_updates:
            npc["mood"] = mood_updates[npc_id]

    controversy = entities[0].get("controversy_level", "medium") if entities else "medium"
    npcs, rel_updates, influence_log = _apply_opinion_dynamics(
        npcs, all_events, current_round, rel_map, controversy
    )

    updated_rels = []
    for rel in relationships:
        src = rel["source_id"]
        tgt = rel["target_id"]
        pair = (src, tgt)
        if pair in rel_updates:
            rel["affinity"] = round(
                clamp(rel.get("affinity", 0.0) + rel_updates[pair]["affinity"], -1.0, 1.0), 3
            )
            rel["trust"] = round(
                clamp(rel.get("trust", 0.5) + rel_updates[pair]["trust"], 0.0, 1.0), 3
            )
        updated_rels.append(rel)

    updated_npcs = []
    for npc in npcs:
        npc_copy = dict(npc)
        npc_id = npc_copy.get("id", "")
        if npc_id in move_updates:
            npc_copy["x"], npc_copy["y"] = move_updates[npc_id]
        updated_npcs.append(npc_copy)

    kind = entities[0].get("kind", "policy") if entities else "policy"
    indicators = _compute_economic_indicators(updated_npcs, all_events, current_round, max_rounds, kind)
    return updated_npcs, updated_rels, influence_log, indicators


async def run_round(state: SimState) -> dict[str, Any]:
    """Run one simulation round for all 25 NPCs in parallel."""

    llm = get_llm(max_tokens=4096)

    npcs = state["npcs"]
    events = state.get("events", [])
    current_round = state["current_round"]
    max_rounds = state["max_rounds"]
    memory_streams: dict[str, list[dict[str, Any]]] = {
        k: list(v) for k, v in state.get("memory_streams", {}).items()
    }
    callback = state.get("npc_stream_callback")
    relationships = state.get("relationships", [])

    logger.info(
        "run_round: starting round %d/%d  (%d NPCs) …",
        current_round + 1,
        max_rounds,
        len(npcs),
    )

    policy_text = _policy_summary(
        state.get("entities", []),
        state.get("context_summary", ""),
    )
    full_policy = state.get("policy_text") or policy_text
    policy_chunks = chunk_policy_document(full_policy)
    town = TOWN[detect_setting(full_policy)]
    round_context = _build_round_context(current_round, max_rounds, events)
    rel_map = _build_relationship_map(relationships)
    name_to_id = {npc.get("name", ""): npc.get("id", "") for npc in npcs}

    npc_neighbor_ids: dict[str, list[str]] = {}
    npc_rels_map: dict[str, list[tuple[str, float, float]]] = {}
    for npc in npcs:
        npc_id = npc.get("id", "")
        npc_neighbor_ids[npc_id] = _build_neighbor_ids(npc, npcs)
        npc_rels_map[npc_id] = rel_map.get(npc_id, [])

    tasks: list[asyncio.Task[NPCRoundResult]] = []
    for npc in npcs:
        npc_id = npc.get("id", "")
        coro = _simulate_single_npc(
            npc=npc,
            npc_memories=memory_streams.setdefault(npc_id, []),
            llm=llm,
            current_round=current_round,
            max_rounds=max_rounds,
            policy_text=policy_text,
            round_context=round_context,
            neighbor_ids=npc_neighbor_ids[npc_id],
            npc_rels=npc_rels_map[npc_id],
            all_npcs=npcs,
            name_to_id=name_to_id,
            objective=state.get("objective", ""),
            policy_chunks=policy_chunks,
            town=town,
        )
        tasks.append(asyncio.create_task(coro))

    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    results: list[NPCRoundResult] = []
    for npc, outcome in zip(npcs, raw_results):
        if isinstance(outcome, BaseException):
            logger.warning("NPC %s failed this round: %s", npc.get("id"), outcome)
            results.append(NPCRoundResult())
        else:
            results.append(outcome)

    for npc, npc_result in zip(npcs, results):
        npc_id = npc.get("id", "")
        npc["perception"] = npc_result.perception
        npc["current_plan"] = get_current_plan(memory_streams.get(npc_id, [])) or ""
        if callback and npc_result.events:
            await callback(npc_result.events)

    all_events: list[dict[str, Any]] = []
    for r in results:
        all_events.extend(r.events)

    for ev in all_events:
        target_id = ev.get("data", {}).get("target_npc_id")
        if target_id and target_id in memory_streams:
            dialogue = ev.get("data", {}).get("dialogue") or ev.get("message", "")
            memory_streams[target_id].append(
                create_memory(
                    target_id,
                    f"{ev.get('npc_id', 'someone')} said to me: {dialogue}",
                    current_round,
                    importance=heuristic_importance(ev.get("event_type", "chat")),
                    mem_type="observation",
                )
            )

    updated_npcs, updated_rels, influence_log, indicators = _apply_post_round(
        npcs, all_events, current_round, max_rounds, relationships, rel_map,
        state.get("entities", []),
    )
    return {
        "events": all_events,
        "current_round": current_round + 1,
        "npcs": updated_npcs,
        "relationships": updated_rels,
        "memory_streams": memory_streams,
        "influence_events": influence_log,
        "economic_indicators": indicators,
    }
