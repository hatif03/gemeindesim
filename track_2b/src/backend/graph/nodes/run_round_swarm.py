"""Node: two-phase swarm round execution.

Phase A: initiator NPCs act concurrently.
Mid-round: Phase A events are injected into reactor memory streams.
Phase B: reactor NPCs act concurrently (they see Phase A events).

All heavy logic (opinion dynamics, memory, move dedup) is reused from run_round.py.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from graph.corpus import chunk_policy_document, detect_setting
from graph.language import TOWN
from graph.llm import get_llm
from graph.memory import create_memory, get_current_plan, heuristic_importance
from graph.nodes.run_round import (
    NPCRoundResult,
    _apply_post_round,
    _build_neighbor_ids,
    _build_relationship_map,
    _build_round_context,
    _policy_summary,
    _simulate_single_npc,
)
from models.state import SimState

logger = logging.getLogger(__name__)


async def _run_phase(
    npcs: list[dict[str, Any]],
    memory_streams: dict[str, list[dict[str, Any]]],
    llm: Any,
    current_round: int,
    max_rounds: int,
    policy_text: str,
    round_context: str,
    npc_neighbor_ids: dict[str, list[str]],
    npc_rels_map: dict[str, list[tuple[str, float, float]]],
    all_npcs: list[dict[str, Any]],
    name_to_id: dict[str, str],
    objective: str,
    policy_chunks: list[dict[str, Any]] | None = None,
    town: str = "Millfield",
) -> list[NPCRoundResult]:
    """Run _simulate_single_npc concurrently for a group of NPCs."""
    tasks = [
        asyncio.create_task(
            _simulate_single_npc(
                npc=npc,
                npc_memories=memory_streams.setdefault(npc["id"], []),
                llm=llm,
                current_round=current_round,
                max_rounds=max_rounds,
                policy_text=policy_text,
                round_context=round_context,
                neighbor_ids=npc_neighbor_ids.get(npc["id"], []),
                npc_rels=npc_rels_map.get(npc["id"], []),
                all_npcs=all_npcs,
                name_to_id=name_to_id,
                objective=objective,
                policy_chunks=policy_chunks,
                town=town,
            )
        )
        for npc in npcs
    ]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    results: list[NPCRoundResult] = []
    for npc, outcome in zip(npcs, raw):
        if isinstance(outcome, BaseException):
            logger.warning("NPC %s failed this phase: %s", npc.get("id"), outcome)
            results.append(NPCRoundResult())
        else:
            results.append(outcome)
    return results


async def _collect_phase_results(
    npcs: list[dict[str, Any]],
    results: list[NPCRoundResult],
    memory_streams: dict[str, list[dict[str, Any]]],
    callback: Callable[[list[dict[str, Any]]], Awaitable[None]] | None,
) -> list[dict[str, Any]]:
    """Extract events, update perception/plan, fire callbacks concurrently."""
    events: list[dict[str, Any]] = []
    cb_tasks: list[Awaitable[None]] = []
    for npc, result in zip(npcs, results):
        events.extend(result.events)
        npc["perception"] = result.perception
        npc["current_plan"] = get_current_plan(memory_streams.get(npc["id"], [])) or ""
        if callback and result.events:
            cb_tasks.append(callback(result.events))
    if cb_tasks:
        await asyncio.gather(*cb_tasks)
    return events


async def run_round_swarm(state: SimState) -> dict[str, Any]:
    """Two-phase swarm round: initiators act first, reactors respond."""

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

    initiator_id_set = set(state.get("initiator_ids") or [])
    initiators = [n for n in npcs if n.get("id") in initiator_id_set]
    reactors = [n for n in npcs if n.get("id") not in initiator_id_set]
    # Edge case: no initiator IDs set — treat everyone as initiator, no reactors
    if not initiators:
        initiators = npcs
        reactors = []

    logger.info(
        "run_round_swarm: round %d/%d  initiators=%d  reactors=%d",
        current_round + 1, max_rounds, len(initiators), len(reactors),
    )

    policy_text = _policy_summary(state.get("entities", []), state.get("context_summary", ""))
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

    objective = state.get("objective", "")

    # ── Phase A: initiators act ──────────────────────────────────────────────
    phase_a_results = await _run_phase(
        initiators, memory_streams, llm, current_round, max_rounds,
        policy_text, round_context, npc_neighbor_ids, npc_rels_map,
        npcs, name_to_id, objective, policy_chunks, town,
    )
    phase_a_events = await _collect_phase_results(initiators, phase_a_results, memory_streams, callback)

    # ── Mid-round inject: Phase A events → reactor memories ─────────────────
    reactor_ids = {n.get("id", "") for n in reactors}

    # Build lookups for relational memory injection
    npc_lookup = {npc["id"]: npc for npc in npcs}
    rel_lookup: dict[tuple[str, str], tuple[float, float]] = {}
    for rel in relationships:
        src, tgt = rel.get("source_id", ""), rel.get("target_id", "")
        val = (float(rel.get("affinity", 0.0)), float(rel.get("trust", 0.5)))
        rel_lookup[(src, tgt)] = val
        rel_lookup[(tgt, src)] = val  # bidirectional

    BROADCAST_TYPES = {"protest", "price_change", "mood_shift"}

    for ev in phase_a_events:
        actor_id = ev.get("npc_id", "")
        actor_name = npc_lookup.get(actor_id, {}).get("name", actor_id)
        ev_type = ev.get("event_type", "")

        if ev_type == "chat":
            target_id = ev.get("data", {}).get("target_npc_id", "")
            if target_id and target_id in reactor_ids:
                dialogue = ev.get("data", {}).get("dialogue") or ev.get("message", "")
                rel = rel_lookup.get((actor_id, target_id))
                if rel:
                    affinity, _ = rel
                    rel_label = (
                        "close ally" if affinity > 0.5
                        else "rival" if affinity < -0.3
                        else "acquaintance"
                    )
                    memory_text = f"{actor_name} ({rel_label}, affinity={affinity:.1f}) said: {dialogue}"
                else:
                    memory_text = f"{actor_name} (a stranger) said: {dialogue}"
                memory_streams.setdefault(target_id, []).append(
                    create_memory(
                        target_id,
                        memory_text,
                        current_round,
                        importance=heuristic_importance(ev_type),
                        mem_type="observation",
                    )
                )

        elif ev_type in BROADCAST_TYPES:
            msg = ev.get("message", "")
            for reactor in reactors:
                reactor_id = reactor["id"]
                rel = rel_lookup.get((actor_id, reactor_id))
                if rel and abs(rel[0]) > 0.2:  # only inject if meaningful relationship
                    memory_text = f"{actor_name} was heard to: {msg}"
                    memory_streams.setdefault(reactor_id, []).append(
                        create_memory(
                            reactor_id,
                            memory_text,
                            current_round,
                            importance=heuristic_importance(ev_type) * 0.7,
                            mem_type="observation",
                        )
                    )

    # ── Phase B: reactors respond (with augmented context) ───────────────────
    augmented_context = round_context
    if phase_a_events:
        augmented_context = (
            f"{round_context} "
            f"{len(phase_a_events)} early actions have already occurred in town this round."
        )

    phase_b_results = await _run_phase(
        reactors, memory_streams, llm, current_round, max_rounds,
        policy_text, augmented_context, npc_neighbor_ids, npc_rels_map,
        npcs, name_to_id, objective, policy_chunks, town,
    ) if reactors else []
    phase_b_events = await _collect_phase_results(reactors, phase_b_results, memory_streams, callback)

    logger.info(
        "run_round_swarm: round %d  phase_a=%d events  phase_b=%d events",
        current_round + 1, len(phase_a_events), len(phase_b_events),
    )

    all_events = phase_a_events + phase_b_events

    # ── Cross-NPC memory: Phase B chat targets ───────────────────────────────
    for ev in phase_b_events:
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
