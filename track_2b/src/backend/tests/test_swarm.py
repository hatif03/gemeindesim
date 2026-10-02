"""Tests for the swarm feature: swarm_orchestrator + run_round_swarm."""

from __future__ import annotations

import pytest
from models.schemas import OrchestratorPlan
from graph.nodes.run_round import NPCRoundResult

# OrchestratorPlan is still used in test_orchestrator_plan_schema_valid below.


# ─── Helper factories ─────────────────────────────────────────────────────────

def make_npc(npc_id, political_leaning=0.0, income_level="medium", role="worker", mood="neutral"):
    return {
        "id": npc_id, "name": f"NPC-{npc_id}", "role": role,
        "income_level": income_level, "political_leaning": political_leaning,
        "mood": mood, "x": 0, "y": 0, "beliefs": [], "reputation": 0.5,
        "mbti": "INTJ", "profession": "worker", "bio": "", "persona": "",
        "gender": "M", "country": "US", "interested_topics": [],
        "controversial_ideas": [], "category": "",
    }


def make_state(npcs, initiator_ids=None):
    return {
        "npcs": npcs,
        "initiator_ids": initiator_ids or [],
        "events": [],
        "current_round": 0,
        "max_rounds": 3,
        "policy_text": "",
        "notes_text": "",
        "trend_summary": "",
        "context_summary": "",
        "indicator_snapshots": [],
        "source_summaries": [],
        "policy_sources": [],
        "trend_sources": [],
        "objective": "",
        "entities": [],
        "relationships": [],
        "economic_indicators": {},
        "memory_streams": {},
        "num_npcs": len(npcs),
    }


# ─── 1. OrchestratorPlan schema ───────────────────────────────────────────────

def test_orchestrator_plan_schema_valid():
    plan = OrchestratorPlan(initiator_ids=["a", "b"])
    assert plan.initiator_ids == ["a", "b"]


# ─── 2. Heuristic picks most politically extreme NPC ─────────────────────────

@pytest.mark.asyncio
async def test_orchestrator_fallback_picks_most_opinionated():
    npcs = [
        make_npc("npc_a", political_leaning=0.1),
        make_npc("npc_b", political_leaning=-0.9),
        make_npc("npc_c", political_leaning=0.5),
        make_npc("npc_d", political_leaning=-0.2),
        make_npc("npc_e", political_leaning=0.0),
    ]
    state = make_state(npcs)

    from graph.nodes.swarm_orchestrator import swarm_orchestrator
    result = await swarm_orchestrator(state)

    # npc_b has the highest abs(political_leaning) = 0.9 → must be chosen
    assert "npc_b" in result["initiator_ids"]


# ─── 3. Heuristic always returns valid IDs ───────────────────────────────────

@pytest.mark.asyncio
async def test_orchestrator_valid_plan_returned():
    npcs = [make_npc("npc_1"), make_npc("npc_2"), make_npc("npc_3")]
    state = make_state(npcs)

    from graph.nodes.swarm_orchestrator import swarm_orchestrator
    result = await swarm_orchestrator(state)

    valid_ids = {n["id"] for n in npcs}
    assert all(nid in valid_ids for nid in result["initiator_ids"])
    assert len(result["initiator_ids"]) >= 1


# ─── 4. All returned IDs are valid NPC IDs ───────────────────────────────────

@pytest.mark.asyncio
async def test_orchestrator_filters_invalid_ids():
    npcs = [
        make_npc("npc_1", political_leaning=0.8),
        make_npc("npc_2", political_leaning=0.6),
        make_npc("npc_3", political_leaning=0.4),
    ]
    state = make_state(npcs)

    from graph.nodes.swarm_orchestrator import swarm_orchestrator
    result = await swarm_orchestrator(state)

    valid_ids = {n["id"] for n in npcs}
    assert all(nid in valid_ids for nid in result["initiator_ids"])
    assert len(result["initiator_ids"]) >= 1


# ─── 5. run_round_swarm return shape ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_round_swarm_return_shape(monkeypatch):
    async def mock_simulate(npc, **kwargs):
        return NPCRoundResult(events=[], perception="ok")

    monkeypatch.setattr("graph.nodes.run_round_swarm._simulate_single_npc", mock_simulate)
    monkeypatch.setattr("graph.nodes.run_round_swarm.get_llm", lambda *a, **kw: None)

    npcs = [make_npc("npc_1"), make_npc("npc_2"), make_npc("npc_3")]
    state = make_state(npcs, initiator_ids=["npc_1"])

    from graph.nodes.run_round_swarm import run_round_swarm
    result = await run_round_swarm(state)

    expected_keys = {
        "events", "current_round", "npcs", "relationships",
        "memory_streams", "influence_events", "economic_indicators",
    }
    assert expected_keys.issubset(result.keys())


# ─── 6. run_round_swarm increments current_round ─────────────────────────────

@pytest.mark.asyncio
async def test_run_round_swarm_increments_round(monkeypatch):
    async def mock_simulate(npc, **kwargs):
        return NPCRoundResult(events=[], perception="ok")

    monkeypatch.setattr("graph.nodes.run_round_swarm._simulate_single_npc", mock_simulate)
    monkeypatch.setattr("graph.nodes.run_round_swarm.get_llm", lambda *a, **kw: None)

    npcs = [make_npc("npc_1"), make_npc("npc_2"), make_npc("npc_3")]
    state = make_state(npcs, initiator_ids=["npc_1"])

    from graph.nodes.run_round_swarm import run_round_swarm
    result = await run_round_swarm(state)

    assert result["current_round"] == 1


# ─── 7. Phase A events are injected into reactor memory ──────────────────────

@pytest.mark.asyncio
async def test_phase_a_events_injected_into_reactor_memory(monkeypatch):
    initiator_id = "npc_initiator"
    reactor_id = "npc_reactor"

    chat_event = {
        "event_type": "chat",
        "npc_id": initiator_id,
        "message": "Hello reactor!",
        "data": {
            "target_npc_id": reactor_id,
            "dialogue": "Hello reactor!",
        },
    }

    async def mock_simulate(npc, **kwargs):
        if npc["id"] == initiator_id:
            return NPCRoundResult(events=[chat_event], perception="spoke")
        return NPCRoundResult(events=[], perception="")

    monkeypatch.setattr("graph.nodes.run_round_swarm._simulate_single_npc", mock_simulate)
    monkeypatch.setattr("graph.nodes.run_round_swarm.get_llm", lambda *a, **kw: None)

    npcs = [make_npc(initiator_id), make_npc(reactor_id)]
    state = make_state(npcs, initiator_ids=[initiator_id])

    from graph.nodes.run_round_swarm import run_round_swarm
    result = await run_round_swarm(state)

    reactor_memories = result["memory_streams"].get(reactor_id, [])
    assert reactor_memories, "reactor should have at least one memory entry from Phase A"
    assert any(
        initiator_id in m.get("description", "") for m in reactor_memories
    ), "reactor's memory should mention the initiator NPC"
