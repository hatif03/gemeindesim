"""Regression tests for bugs found in production despite existing tests passing."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock


# ── Bug 1: _flatten_schema removes $ref / $defs ──────────────────────────────

def test_flatten_schema_removes_defs_and_refs():
    """Apertus echoed the schema back when it saw $ref pointers. Flattening must eliminate them."""
    schema = {
        "type": "object",
        "properties": {"item": {"$ref": "#/$defs/MyType"}},
        "$defs": {"MyType": {"type": "string", "enum": ["a", "b"]}},
    }
    from graph.llm import _flatten_schema
    result = _flatten_schema(schema)

    assert "$defs" not in result
    assert "$ref" not in str(result)
    assert result["properties"]["item"] == {"type": "string", "enum": ["a", "b"]}


def test_flatten_schema_nested_refs_fully_resolved():
    """Chains of $ref pointers are fully inlined."""
    schema = {
        "type": "object",
        "properties": {"outer": {"$ref": "#/$defs/Outer"}},
        "$defs": {
            "Outer": {
                "type": "object",
                "properties": {"inner": {"$ref": "#/$defs/Inner"}},
            },
            "Inner": {"type": "integer"},
        },
    }
    from graph.llm import _flatten_schema
    result = _flatten_schema(schema)

    assert "$ref" not in str(result)
    assert "$defs" not in result
    assert result["properties"]["outer"]["properties"]["inner"] == {"type": "integer"}


def test_flatten_schema_real_pydantic_model_has_no_refs():
    """A Pydantic model with nested types generates $defs/$ref — flatten must clean it."""
    from pydantic import BaseModel
    from graph.llm import _flatten_schema

    class Inner(BaseModel):
        value: int

    class Outer(BaseModel):
        name: str
        inner: Inner

    raw = Outer.model_json_schema()
    assert "$defs" in raw, "precondition: pydantic should produce $defs for nested models"

    flat = _flatten_schema(raw)
    assert "$defs" not in flat
    assert "$ref" not in str(flat)
    # The inlined inner model should still have the value field
    assert flat["properties"]["inner"]["properties"]["value"]["type"] == "integer"


# ── Bug 2: economic report max_tokens must be sufficient ─────────────────────

@pytest.mark.asyncio
async def test_economic_report_uses_sufficient_max_tokens(monkeypatch):
    """Economic report called invoke_llm_structured with max_tokens=2048 — reasoning
    alone consumed it, leaving no room for JSON. Must be >= 4000."""
    from models.schemas import EconomicReportNarrative

    captured: dict = {}

    async def mock_invoke(prompt, response_model, max_tokens=None, **kwargs):
        captured["max_tokens"] = max_tokens
        return EconomicReportNarrative(
            headline="h", summary="s", livelihood_impact="l", top_impacts=[], notable_events=[]
        )

    monkeypatch.setattr("services.economic_report.invoke_llm_structured", mock_invoke)

    from services.economic_report import generate_economic_report
    await generate_economic_report(
        policy_text="test",
        objective="test",
        entities=[],
        source_summaries=[],
        indicator_snapshots=[],
        final_npcs=[],
        events=[],
        completed_rounds=1,
        max_rounds=3,
    )

    assert captured.get("max_tokens", 0) >= 4000, (
        f"max_tokens={captured.get('max_tokens')} is too small — "
        "thinking/JSON output needs headroom"
    )


# ── Bug 3: _META_PREFIXES guard strips leaked reasoning ───────────────────────

@pytest.mark.asyncio
async def test_chat_strips_meta_prefix_leaked_reasoning(monkeypatch):
    """NPC chat leaked system-prompt reasoning when max_tokens was too small.
    The _META_PREFIXES guard must salvage the last usable sentence."""
    leaked = (
        "Let me produce a response in character. "
        "The user has asked about the tariff policy. "
        "I think the tariffs are harmful to farmers like me!"
    )

    mock_resp = MagicMock()
    mock_resp.content = leaked
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_resp)

    monkeypatch.setattr("graph.chat.get_llm", lambda **kwargs: mock_llm)

    from graph.chat import generate_npc_chat_response
    result = await generate_npc_chat_response(
        npc={
            "id": "npc_1", "name": "Alice", "profession": "farmer",
            "mbti": "INTJ", "bio": "A farmer.", "beliefs": [], "mood": "neutral",
        },
        user_message="What do you think?",
        conversation_history=[],
        memory_stream=[],
        policy_context="",
    )

    assert not result.lower().startswith("let me"), (
        f"Meta-prefix reasoning leaked into response: {result!r}"
    )
    # The salvaged last sentence should contain the actual opinion
    assert "harmful" in result.lower() or "farmers" in result.lower() or result == ""


@pytest.mark.asyncio
async def test_chat_passes_through_normal_dialogue(monkeypatch):
    """Normal dialogue (no meta-prefix) passes through the guard unchanged."""
    normal = "I don't trust these new tariffs one bit."

    mock_resp = MagicMock()
    mock_resp.content = normal
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_resp)

    monkeypatch.setattr("graph.chat.get_llm", lambda **kwargs: mock_llm)

    from graph.chat import generate_npc_chat_response
    result = await generate_npc_chat_response(
        npc={
            "id": "npc_1", "name": "Alice", "profession": "farmer",
            "mbti": "INTJ", "bio": "A farmer.", "beliefs": [], "mood": "neutral",
        },
        user_message="What do you think?",
        conversation_history=[],
        memory_stream=[],
        policy_context="",
    )

    assert result == normal


# ── Bug 4: plan-type memory created so get_current_plan returns non-None ──────

def test_perception_stored_as_plan_memory():
    """_simulate_single_npc only created 'observation' memories — get_current_plan()
    searches for mem_type='plan' so it always returned None. Both types must be created."""
    from graph.memory import create_memory, get_current_plan

    memories: list = []
    npc_id = "npc_test"
    perception = "The new tariffs are worrying me. I plan to protest."
    current_round = 0

    # Mirror the fixed code block in _simulate_single_npc
    memories.append(
        create_memory(npc_id, perception, current_round, importance=6, mem_type="observation")
    )
    memories.append(
        create_memory(npc_id, perception, current_round, importance=5, mem_type="plan")
    )

    mem_types = [m.get("mem_type") for m in memories]
    assert "observation" in mem_types
    assert "plan" in mem_types, (
        "Bug regression: perception must be stored as mem_type='plan' "
        "so get_current_plan() can find it"
    )
    assert get_current_plan(memories) == perception, (
        "get_current_plan() returned None — plan memory is missing or has wrong mem_type"
    )


@pytest.mark.asyncio
async def test_simulate_single_npc_produces_plan_memory(monkeypatch):
    """End-to-end check: _simulate_single_npc leaves a plan-type memory in npc_memories."""
    from models.schemas import NPCRoundResponse

    async def mock_invoke(prompt, response_model, **kwargs):
        return NPCRoundResponse(
            events=[], perception="I will protest the new tariff policy."
        )

    monkeypatch.setattr("graph.nodes.run_round.invoke_llm_structured", mock_invoke)
    monkeypatch.setattr(
        "graph.nodes.run_round.maybe_reflect", AsyncMock(return_value=[])
    )

    from graph.nodes.run_round import _simulate_single_npc
    from graph.memory import get_current_plan

    npc = {
        "id": "npc_test", "name": "Bob", "role": "farmer", "profession": "farmer",
        "income_level": "low", "political_leaning": -0.7, "mood": "anxious",
        "x": 0, "y": 0, "beliefs": [], "reputation": 0.5, "mbti": "INTJ",
        "bio": "", "persona": "", "gender": "M", "country": "US",
        "interested_topics": [], "controversial_ideas": [], "category": "",
    }
    memories: list = []

    await _simulate_single_npc(
        npc=npc,
        npc_memories=memories,
        llm=None,
        current_round=0,
        max_rounds=3,
        policy_text="new tariff",
        round_context="Round 1 of 3.",
        neighbor_ids=[],
        npc_rels=[],
        all_npcs=[npc],
        name_to_id={"Bob": "npc_test"},
        objective="test",
    )

    plan = get_current_plan(memories)
    assert plan is not None, (
        "Bug regression: get_current_plan() returned None. "
        "_simulate_single_npc must store perception as mem_type='plan'."
    )
    assert "protest" in plan.lower()


def test_schema_to_example_produces_instance_not_schema():
    """_schema_to_example returns a concrete instance shape, not schema metadata.
    Bug: Apertus echoed the schema object back when shown raw JSON schema definitions."""
    from graph.llm import _schema_to_example

    schema = {
        "type": "object",
        "properties": {
            "ids": {"type": "array", "items": {"type": "string"}},
            "count": {"type": "integer"},
            "label": {"type": "string"},
        },
    }
    example = _schema_to_example(schema)

    assert isinstance(example, dict)
    assert isinstance(example["ids"], list)
    assert example["count"] == 0
    # Must not contain schema metadata keys
    assert "properties" not in example
    assert "type" not in example
    assert "$ref" not in str(example)


def test_schema_to_example_enum_uses_first_value():
    """Enum fields show the first valid value so Apertus knows what's allowed."""
    from graph.llm import _schema_to_example

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["pending", "running", "done"]},
        },
    }
    example = _schema_to_example(schema)
    assert example["status"] == "pending"


# ── Bug 5: generate_npcs returns 0 relationships ──────────────────────────────

@pytest.mark.asyncio
async def test_generate_relationships_returns_list():
    """_generate_relationships uses heuristic affinity — no LLM call needed."""
    npcs = [
        {"id": "npc_1", "name": "Alice", "profession": "farmer", "income_level": "low",
         "political_leaning": -0.5, "x": 0, "y": 0},
        {"id": "npc_2", "name": "Bob", "profession": "teacher", "income_level": "medium",
         "political_leaning": 0.1, "x": 1, "y": 0},
        {"id": "npc_3", "name": "Carol", "profession": "doctor", "income_level": "high",
         "political_leaning": 0.8, "x": 2, "y": 0},
    ]

    from graph.nodes.npc_orchestrator import _generate_relationships
    result = await _generate_relationships(npcs, "[]", llm=None)

    assert len(result) == 3, f"Expected 3 relationships, got {len(result)}"
    ids = {(r["source_id"], r["target_id"]) for r in result}
    assert ("npc_1", "npc_2") in ids or ("npc_2", "npc_1") in ids
    assert all(r.get("source_id") != r.get("target_id") for r in result)


def test_relationship_record_has_affinity_and_trust():
    """RelationshipRecord must include affinity and trust — _build_relationship_map reads them.
    Bug: prompt example only showed source_id/target_id, so Apertus omitted these fields."""
    from models.schemas import RelationshipRecord
    rel = RelationshipRecord(source_id="a", target_id="b")
    assert hasattr(rel, "affinity")
    assert hasattr(rel, "trust")
    assert 0.0 <= rel.affinity <= 1.0
    assert 0.0 <= rel.trust <= 1.0


# ── Bug 6: invoke_llm_structured prompt triggers meta-text instead of JSON ────

def test_invoke_llm_structured_prompt_is_imperative():
    """Prompt must say 'Output ONLY ... filled in' not 'replace placeholder values'.
    Bug: Apertus wrote reasoning text ('We need to...') instead of JSON when told to 'replace'."""
    import inspect
    from graph.llm import invoke_llm_structured
    src = inspect.getsource(invoke_llm_structured)
    assert "Output ONLY the following JSON with the placeholder values filled in" in src, (
        "Prompt instruction must be imperative — Apertus writes meta-text when asked to 'replace'"
    )


# ── Bug 7: trailing commas in Apertus JSON cause parse failure ─────────────────────

def test_strip_trailing_commas_object():
    """Trailing comma before } must be removed."""
    from graph.llm import _strip_trailing_commas
    assert _strip_trailing_commas('{"a": 1, "b": 2,}') == '{"a": 1, "b": 2}'


def test_strip_trailing_commas_array():
    """Trailing comma before ] must be removed."""
    from graph.llm import _strip_trailing_commas
    assert _strip_trailing_commas('["x", "y",]') == '["x", "y"]'


def test_strip_trailing_commas_nested():
    """Trailing commas in nested structures are all removed."""
    from graph.llm import _strip_trailing_commas
    raw = '{"events": [{"type": "chat",},],}'
    result = _strip_trailing_commas(raw)
    import json
    parsed = json.loads(result)
    assert parsed["events"][0]["type"] == "chat"


def test_extract_json_handles_trailing_commas():
    """_extract_json_from_response must parse JSON that has trailing commas."""
    from graph.llm import _extract_json_from_response
    content = '{"events": [{"event_type": "chat", "message": "hello",},], "perception": "ok",}'
    result = _extract_json_from_response(content)
    assert result["perception"] == "ok"
    assert result["events"][0]["message"] == "hello"


# ── Bug 8: invoke_llm_structured retries on Apertus no-JSON responses ──────────────

@pytest.mark.asyncio
async def test_invoke_llm_structured_retries_on_failure(monkeypatch):
    """invoke_llm_structured retries up to 3 times when Apertus returns no JSON.
    Bug: single-shot call caused swarm_orchestrator and run_round to lose NPCs
    whenever Apertus output plain reasoning text instead of JSON."""
    from pydantic import BaseModel
    from graph.llm import get_llm

    class Simple(BaseModel):
        value: str

    call_count = 0

    async def mock_ainvoke(prompt):
        nonlocal call_count
        call_count += 1
        mock_resp = MagicMock()
        if call_count < 3:
            mock_resp.content = "We need to think about this carefully."  # no JSON
        else:
            mock_resp.content = '{"value": "hello"}'
        return mock_resp

    mock_llm = MagicMock()
    mock_llm.bind = MagicMock(side_effect=Exception("no json_object mode"))
    mock_llm.ainvoke = mock_ainvoke

    monkeypatch.setattr("graph.llm.get_llm", lambda **kw: mock_llm)

    from graph.llm import invoke_llm_structured
    result = await invoke_llm_structured("do something", Simple, llm=mock_llm)

    assert result.value == "hello"
    assert call_count == 3  # failed twice, succeeded on third


@pytest.mark.asyncio
async def test_invoke_llm_structured_raises_after_3_failures(monkeypatch):
    """After 3 failed attempts, the exception is raised (not silently swallowed)."""
    from pydantic import BaseModel

    class Simple(BaseModel):
        value: str

    async def mock_ainvoke(prompt):
        mock_resp = MagicMock()
        mock_resp.content = "No JSON here."
        return mock_resp

    mock_llm = MagicMock()
    mock_llm.bind = MagicMock(side_effect=Exception("no json_object mode"))
    mock_llm.ainvoke = mock_ainvoke

    from graph.llm import invoke_llm_structured
    with pytest.raises(Exception):
        await invoke_llm_structured("do something", Simple, llm=mock_llm)


# ── Bug 9: swarm_orchestrator is now purely heuristic — picks highest-scoring NPCs ──

@pytest.mark.asyncio
async def test_swarm_orchestrator_uses_real_npc_ids_in_example():
    """swarm_orchestrator uses a pure heuristic (no LLM). npc_b (activist, angry,
    |leaning|=0.9) must score highest and appear in initiator_ids."""
    npcs = [
        {"id": "npc_a", "name": "Alice", "role": "worker", "income_level": "low",
         "political_leaning": 0.1, "mood": "neutral", "profession": "farmer"},
        {"id": "npc_b", "name": "Bob", "role": "activist", "income_level": "medium",
         "political_leaning": -0.9, "mood": "angry", "profession": "activist"},
        {"id": "npc_c", "name": "Carol", "role": "politician", "income_level": "high",
         "political_leaning": 0.8, "mood": "anxious", "profession": "mayor"},
        {"id": "npc_d", "name": "Dave", "role": "worker", "income_level": "low",
         "political_leaning": -0.2, "mood": "neutral", "profession": "mechanic"},
        {"id": "npc_e", "name": "Eve", "role": "worker", "income_level": "medium",
         "political_leaning": 0.0, "mood": "neutral", "profession": "nurse"},
    ]
    state = {
        "npcs": npcs, "events": [], "current_round": 0, "max_rounds": 3,
        "entities": [], "context_summary": "", "initiator_ids": [],
        "policy_text": "", "notes_text": "", "trend_summary": "",
        "indicator_snapshots": [], "source_summaries": [], "policy_sources": [],
        "trend_sources": [], "objective": "", "relationships": [],
        "economic_indicators": {}, "memory_streams": {}, "num_npcs": 5,
    }

    from graph.nodes.swarm_orchestrator import swarm_orchestrator
    result = await swarm_orchestrator(state)

    valid_ids = {n["id"] for n in npcs}
    assert all(i in valid_ids for i in result["initiator_ids"]), "All IDs must be real NPC IDs"
    # npc_b: activist + angry + |leaning|=0.9 → must be top initiator
    assert "npc_b" in result["initiator_ids"], "npc_b must be chosen (highest composite score)"


# ── Relational memory injection ──────────────────────────


@pytest.mark.asyncio
async def test_chat_injection_includes_actor_name_and_rel(monkeypatch):
    """Chat memory should include actor name and relationship label, not just npc_id."""
    from graph.nodes.run_round import NPCRoundResult

    async def mock_simulate(npc, **kwargs):
        return NPCRoundResult(events=[], perception="")

    monkeypatch.setattr("graph.nodes.run_round_swarm._simulate_single_npc", mock_simulate)
    monkeypatch.setattr("graph.nodes.run_round_swarm.get_llm", lambda *a, **kw: None)

    initiator = {"id": "npc_init", "name": "Brad Young", "profession": "union organizer",
                 "x": 0, "y": 0, "mood": "angry", "political_leaning": -0.8, "income_level": "low",
                 "reputation": 0.5, "beliefs": [], "mbti": "ENTJ", "bio": "", "persona": "",
                 "gender": "M", "country": "US", "interested_topics": [], "controversial_ideas": [],
                 "category": "", "role": "activist"}
    reactor = {"id": "npc_react", "name": "Glenn Gonzalez", "profession": "CEO",
               "x": 1, "y": 0, "mood": "neutral", "political_leaning": 0.7, "income_level": "high",
               "reputation": 0.7, "beliefs": [], "mbti": "ENTJ", "bio": "", "persona": "",
               "gender": "M", "country": "US", "interested_topics": [], "controversial_ideas": [],
               "category": "", "role": "business_owner"}

    # Pre-inject the chat event into phase_a_events by making initiator produce it
    chat_event = {
        "event_type": "chat", "npc_id": "npc_init", "message": "We need to act now.",
        "data": {"target_npc_id": "npc_react", "dialogue": "We need to act now."},
    }

    call_count = [0]
    async def mock_simulate_with_event(npc, **kwargs):
        call_count[0] += 1
        if npc["id"] == "npc_init":
            return NPCRoundResult(events=[chat_event], perception="spoke")
        return NPCRoundResult(events=[], perception="")

    monkeypatch.setattr("graph.nodes.run_round_swarm._simulate_single_npc", mock_simulate_with_event)

    state = {
        "npcs": [initiator, reactor], "initiator_ids": ["npc_init"],
        "events": [], "current_round": 0, "max_rounds": 2,
        "policy_text": "", "notes_text": "", "trend_summary": "", "context_summary": "",
        "indicator_snapshots": [], "source_summaries": [], "policy_sources": [], "trend_sources": [],
        "objective": "", "entities": [], "relationships": [
            {"source_id": "npc_init", "target_id": "npc_react", "affinity": -0.5, "trust": 0.3}
        ],
        "economic_indicators": {}, "memory_streams": {}, "num_npcs": 2,
    }

    from graph.nodes.run_round_swarm import run_round_swarm
    result = await run_round_swarm(state)

    reactor_mems = result["memory_streams"].get("npc_react", [])
    assert reactor_mems, "reactor should have memory from Phase A chat"
    mem_text = reactor_mems[0].get("description", "")
    assert "Brad Young" in mem_text, f"Memory should include actor name, got: {mem_text}"
    assert "rival" in mem_text, f"Memory should include relationship label, got: {mem_text}"


@pytest.mark.asyncio
async def test_protest_injected_to_related_reactor(monkeypatch):
    """Protest events should be injected into related reactors' memories."""
    from graph.nodes.run_round import NPCRoundResult

    protest_event = {
        "event_type": "protest", "npc_id": "npc_init",
        "message": "I storm city hall demanding fair wages.",
        "data": {},
    }

    async def mock_simulate(npc, **kwargs):
        if npc["id"] == "npc_init":
            return NPCRoundResult(events=[protest_event], perception="protesting")
        return NPCRoundResult(events=[], perception="")

    monkeypatch.setattr("graph.nodes.run_round_swarm._simulate_single_npc", mock_simulate)
    monkeypatch.setattr("graph.nodes.run_round_swarm.get_llm", lambda *a, **kw: None)

    initiator = {"id": "npc_init", "name": "Brad Young", "profession": "organizer",
                 "x": 0, "y": 0, "mood": "angry", "political_leaning": -0.8, "income_level": "low",
                 "reputation": 0.5, "beliefs": [], "mbti": "ENTJ", "bio": "", "persona": "",
                 "gender": "M", "country": "US", "interested_topics": [], "controversial_ideas": [],
                 "category": "", "role": "activist"}
    related_reactor = {"id": "npc_related", "name": "Aaron Wood", "profession": "steelworker",
                       "x": 2, "y": 0, "mood": "worried", "political_leaning": -0.5, "income_level": "low",
                       "reputation": 0.4, "beliefs": [], "mbti": "ISTJ", "bio": "", "persona": "",
                       "gender": "M", "country": "US", "interested_topics": [], "controversial_ideas": [],
                       "category": "", "role": "worker"}
    unrelated_reactor = {"id": "npc_unrelated", "name": "Carol Smith", "profession": "CEO",
                         "x": 10, "y": 10, "mood": "neutral", "political_leaning": 0.8, "income_level": "high",
                         "reputation": 0.8, "beliefs": [], "mbti": "INTJ", "bio": "", "persona": "",
                         "gender": "F", "country": "US", "interested_topics": [], "controversial_ideas": [],
                         "category": "", "role": "business_owner"}

    state = {
        "npcs": [initiator, related_reactor, unrelated_reactor],
        "initiator_ids": ["npc_init"],
        "events": [], "current_round": 0, "max_rounds": 2,
        "policy_text": "", "notes_text": "", "trend_summary": "", "context_summary": "",
        "indicator_snapshots": [], "source_summaries": [], "policy_sources": [], "trend_sources": [],
        "objective": "", "entities": [],
        "relationships": [
            {"source_id": "npc_init", "target_id": "npc_related", "affinity": 0.7, "trust": 0.8},
            # npc_unrelated has no relationship with npc_init
        ],
        "economic_indicators": {}, "memory_streams": {}, "num_npcs": 3,
    }

    from graph.nodes.run_round_swarm import run_round_swarm
    result = await run_round_swarm(state)

    related_mems = result["memory_streams"].get("npc_related", [])
    unrelated_mems = result["memory_streams"].get("npc_unrelated", [])

    assert any("Brad Young" in m.get("description", "") for m in related_mems), \
        "Related reactor should hear about protest"
    assert not any("Brad Young" in m.get("description", "") for m in unrelated_mems), \
        "Unrelated reactor should NOT hear about protest"


# ── Heuristic affinity ──────────────────────────────

def test_affinity_same_profession_is_positive():
    from graph.nodes.npc_orchestrator import _affinity_heuristic
    a = {"profession": "steel worker", "income_level": "low", "political_leaning": 0.0, "x": 0, "y": 0}
    b = {"profession": "steel fabricator", "income_level": "low", "political_leaning": 0.0, "x": 1, "y": 0}
    affinity, trust = _affinity_heuristic(a, b)
    assert affinity > 0, "Same-industry workers should have positive affinity"

def test_affinity_opposing_politics_is_negative():
    from graph.nodes.npc_orchestrator import _affinity_heuristic
    a = {"profession": "activist", "income_level": "low", "political_leaning": -1.0, "x": 0, "y": 0}
    b = {"profession": "business owner", "income_level": "high", "political_leaning": 1.0, "x": 10, "y": 10}
    affinity, trust = _affinity_heuristic(a, b)
    assert affinity < 0, "Opposing politics + different income + far apart → negative affinity"

def test_affinity_trust_correlates_with_affinity():
    from graph.nodes.npc_orchestrator import _affinity_heuristic
    # High affinity pair
    a = {"profession": "factory worker", "income_level": "low", "political_leaning": -0.1, "x": 0, "y": 0}
    b = {"profession": "factory worker", "income_level": "low", "political_leaning": 0.1, "x": 1, "y": 0}
    aff_high, trust_high = _affinity_heuristic(a, b)
    # Low affinity pair
    c = {"profession": "CEO", "income_level": "high", "political_leaning": 0.9, "x": 20, "y": 20}
    d = {"profession": "activist", "income_level": "low", "political_leaning": -0.9, "x": 0, "y": 0}
    aff_low, trust_low = _affinity_heuristic(c, d)
    assert trust_high > trust_low, "Higher affinity should produce higher trust"

def test_affinity_values_in_range():
    from graph.nodes.npc_orchestrator import _affinity_heuristic
    import random
    random.seed(42)
    for _ in range(20):
        a = {"profession": "worker", "income_level": random.choice(["low","medium","high"]),
             "political_leaning": random.uniform(-1,1), "x": random.randint(0,20), "y": random.randint(0,20)}
        b = {"profession": "farmer", "income_level": random.choice(["low","medium","high"]),
             "political_leaning": random.uniform(-1,1), "x": random.randint(0,20), "y": random.randint(0,20)}
        aff, trust = _affinity_heuristic(a, b)
        assert -1.0 <= aff <= 1.0
        assert 0.1 <= trust <= 0.95


# ── Centrality-based orchestrator ──────────────────────────────

def test_orchestrator_centrality_boosts_connected_npc():
    """A well-connected NPC should outscore an equally opinionated but isolated one."""
    from graph.nodes.swarm_orchestrator import _compute_initiator_scores
    npcs = [
        {"id": "hub", "political_leaning": 0.5, "income_level": "low",
         "role": "worker", "mood": "angry"},
        {"id": "isolated", "political_leaning": 0.5, "income_level": "low",
         "role": "worker", "mood": "angry"},
    ]
    relationships = [
        {"source_id": "hub", "target_id": "other1", "affinity": 0.5, "trust": 0.5},
        {"source_id": "hub", "target_id": "other2", "affinity": 0.5, "trust": 0.5},
        {"source_id": "hub", "target_id": "other3", "affinity": 0.5, "trust": 0.5},
        # isolated has no relationships
    ]
    scores = _compute_initiator_scores(npcs, relationships)
    assert scores["hub"] > scores["isolated"], "Connected NPC should score higher"

def test_orchestrator_angry_mood_boosts_score():
    """Angry NPC should score higher than same NPC with neutral mood."""
    from graph.nodes.swarm_orchestrator import _compute_initiator_scores
    npcs = [
        {"id": "angry", "political_leaning": 0.3, "income_level": "medium",
         "role": "worker", "mood": "angry"},
        {"id": "neutral", "political_leaning": 0.3, "income_level": "medium",
         "role": "worker", "mood": "neutral"},
    ]
    scores = _compute_initiator_scores(npcs, [])
    assert scores["angry"] > scores["neutral"]
