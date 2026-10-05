from __future__ import annotations

import operator
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, NotRequired, TypedDict


class SimState(TypedDict):
    policy_text: str
    notes_text: str
    trend_summary: str
    context_summary: str
    indicator_snapshots: list[dict[str, Any]]
    source_summaries: list[str]
    policy_sources: list[str]
    trend_sources: list[str]
    objective: str
    entities: list[dict[str, Any]]
    npcs: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    events: Annotated[list[dict[str, Any]], operator.add]
    current_round: int
    max_rounds: int
    num_npcs: int
    map_id: NotRequired[str]
    economic_indicators: dict[str, float]
    # Declared so LangGraph keeps it: undeclared keys are silently dropped, which left the frontend's
    # influence view and the keep/compromise/adopt log permanently empty (research E3/F41).
    influence_events: NotRequired[list[dict[str, Any]]]
    memory_streams: dict[str, list[dict[str, Any]]]
    npc_stream_callback: NotRequired[Callable[[list[dict[str, Any]]], Awaitable[None]] | None]
    npc_added_callback: NotRequired[Callable[[dict[str, Any]], Awaitable[None]] | None]
    setup_progress_callback: NotRequired[Callable[[str, int, int], Awaitable[None]] | None]
    initiator_ids: NotRequired[list[str]]  # swarm mode only; NPC IDs chosen as round initiators
    situation_kind: NotRequired[str]
