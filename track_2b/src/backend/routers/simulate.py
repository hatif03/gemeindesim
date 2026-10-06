import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

import socketio
from fastapi import APIRouter, HTTPException

from graph.builder import build_graph
from config import SWARM
from graph.builder_swarm import build_swarm_graph
from graph.chat import generate_npc_chat_reply
from graph.nodes.stance import stance_summary
from models.schemas import EconomicReportResponse, PolicyInput
from models.state import SimState
from services.context_store import get_source
from services.economic_report import generate_economic_report

logger = logging.getLogger(__name__)

router = APIRouter()

# Socket.IO server (async mode for FastAPI/uvicorn).
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

SimulationStatus = Literal["pending", "running", "complete", "error"]


@dataclass
class SimulationRecord:
    policy: PolicyInput
    status: SimulationStatus = "pending"
    policy_text: str = ""
    trend_summary: str = ""
    context_summary: str = ""
    indicator_snapshots: list[dict[str, Any]] = field(default_factory=list)
    source_summaries: list[str] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    final_npcs: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    current_round: int = 0
    error_message: str | None = None
    economic_report: EconomicReportResponse | None = None
    memory_streams: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    initial_stance: dict[str, Any] | None = None


simulations: dict[str, SimulationRecord] = {}

_POLICY_SOURCE_KINDS = frozenset({"pdf", "text", "book", "video"})


def _resolved_policy_source_ids(policy: PolicyInput) -> list[str]:
    if policy.policy_source_ids:
        return list(policy.policy_source_ids)
    if policy.primary_policy_source_id:
        return [policy.primary_policy_source_id]
    return []


@router.post("/simulate")
async def start_simulation(policy: PolicyInput):
    policy_ids = _resolved_policy_source_ids(policy)
    for source_id in policy_ids:
        src = get_source(source_id)
        if src is None or src.get("kind") not in _POLICY_SOURCE_KINDS:
            raise HTTPException(
                status_code=404,
                detail="One or more policy sources were not found or are not a supported type (pdf).",
            )

    trend_sources = [get_source(source_id) for source_id in policy.trend_source_ids]
    if any(src is None or src.get("kind") != "csv" for src in trend_sources):
        raise HTTPException(
            status_code=404, detail="One or more CSV trend sources were not found."
        )

    simulation_id = str(uuid.uuid4())
    simulations[simulation_id] = SimulationRecord(policy=policy)
    logger.info(
        "POST /simulate → id=%s  rounds=%d  policy_sources=%d  trends=%d",
        simulation_id,
        policy.num_rounds,
        len(policy_ids),
        len(policy.trend_source_ids),
    )
    return {"simulation_id": simulation_id}


async def _handle_round_update(
    update: dict,
    record: "SimulationRecord",
    simulation_id: str,
    sid: str,
    max_rounds: int,
) -> None:
    """Shared handler for run_round and run_round_swarm chunk updates."""
    record.current_round = update.get("current_round", record.current_round)
    record.final_npcs = update.get("npcs", record.final_npcs)
    record.events.extend(update.get("events", []))
    record.memory_streams = update.get("memory_streams", record.memory_streams)
    record.relationships = update.get("relationships", record.relationships)
    round_num = update["current_round"] - 1
    logger.info(
        "sim=%s  round %d  events=%d",
        simulation_id,
        round_num,
        len(update["events"]),
    )
    await sio.emit(
        "round",
        {
            "round": round_num,
            "events": update["events"],
            "npcs": update["npcs"],
            "influence_events": update.get("influence_events", []),
            "economic_indicators": update.get("economic_indicators", {}),
            "relationships": update.get("relationships", []),
            "max_rounds": max_rounds,
        },
        to=sid,
    )


@sio.event
async def start_sim(sid: str, data: dict) -> None:
    """Client emits 'start_sim' with {simulation_id} to begin streaming."""
    simulation_id = data.get("simulation_id", "")
    logger.info("sio start_sim  sid=%s  sim=%s", sid, simulation_id)

    record = simulations.get(simulation_id)
    if record is None:
        await sio.emit("sim_error", {"message": "Simulation not found"}, to=sid)
        return

    policy = record.policy
    record.status = "running"
    record.error_message = None
    record.economic_report = None
    record.current_round = 0
    record.events = []
    record.entities = []
    record.final_npcs = []
    record.relationships = []
    record.policy_text = ""
    record.trend_summary = ""
    record.context_summary = ""
    record.indicator_snapshots = []
    record.source_summaries = []

    graph = build_swarm_graph() if SWARM else build_graph()
    logger.info("sim=%s  mode=%s", simulation_id, "swarm" if SWARM else "standard")

    async def stream_npc_events(events: list) -> None:
        try:
            await sio.emit("npc_events", {"events": events}, to=sid)
        except Exception:
            pass

    async def stream_npc_added(npc: dict) -> None:
        try:
            await sio.emit("npc_added", {"npc": npc}, to=sid)
        except Exception:
            pass

    async def stream_setup_progress(label: str, current: int, total: int) -> None:
        try:
            await sio.emit(
                "setup_progress",
                {"label": label, "current": current, "total": total},
                to=sid,
            )
        except Exception:
            pass

    initial_state: SimState = {
        "policy_text": "",
        "notes_text": policy.notes_text,
        "trend_summary": "",
        "context_summary": "",
        "indicator_snapshots": [],
        "source_summaries": [],
        "policy_sources": _resolved_policy_source_ids(policy),
        "trend_sources": policy.trend_source_ids,
        "objective": policy.objective,
        "max_rounds": policy.num_rounds,
        "num_npcs": policy.num_npcs,
        "map_id": policy.map_id,
        "entities": [],
        "npcs": [],
        "relationships": [],
        "events": [],
        "current_round": 0,
        "economic_indicators": {},
        "memory_streams": {},
        "npc_stream_callback": stream_npc_events,
        "npc_added_callback": stream_npc_added,
        "setup_progress_callback": stream_setup_progress,
        "situation_kind": policy.situation_kind,
    }

    try:
        async for chunk in graph.astream(initial_state):
            if "build_context" in chunk:
                update = chunk["build_context"]
                record.policy_text = update.get("policy_text", "")
                record.trend_summary = update.get("trend_summary", "")
                record.context_summary = update.get("context_summary", "")
                record.indicator_snapshots = update.get("indicator_snapshots", [])
                record.source_summaries = update.get("source_summaries", [])
                await sio.emit(
                    "setup_progress",
                    {"label": "Analyzing policy...", "current": 0, "total": 0},
                    to=sid,
                )

            elif "parse_policy" in chunk:
                update = chunk["parse_policy"]
                record.entities = update.get("entities", [])
                logger.info(
                    "sim=%s  parse_policy  entities=%d",
                    simulation_id,
                    len(update["entities"]),
                )
                await sio.emit(
                    "policy_analysis", {"entities": update["entities"]}, to=sid
                )

            elif "generate_npcs" in chunk:
                update = chunk["generate_npcs"]
                record.final_npcs = update.get("npcs", [])
                record.initial_stance = stance_summary(record.final_npcs)
                record.relationships = update.get("relationships", [])
                logger.info(
                    "sim=%s  generate_npcs  npcs=%d  rels=%d",
                    simulation_id,
                    len(update["npcs"]),
                    len(update["relationships"]),
                )
                await sio.emit(
                    "init",
                    {
                        "npcs": update["npcs"],
                        "relationships": update["relationships"],
                        "max_rounds": policy.num_rounds,
                    },
                    to=sid,
                )

            elif "run_round" in chunk:
                await _handle_round_update(
                    chunk["run_round"], record, simulation_id, sid, policy.num_rounds
                )

            elif "swarm_orchestrator" in chunk:
                logger.info(
                    "sim=%s  swarm_orchestrator  initiators=%d",
                    simulation_id,
                    len(chunk["swarm_orchestrator"].get("initiator_ids", [])),
                )

            elif "run_round_swarm" in chunk:
                await _handle_round_update(
                    chunk["run_round_swarm"], record, simulation_id, sid, policy.num_rounds
                )

        record.status = "complete"
        logger.info("sim=%s  done", simulation_id)
        await sio.emit("done", {}, to=sid)

        try:
            report = await generate_economic_report(
                policy_text=record.policy_text,
                objective=record.policy.objective,
                entities=record.entities,
                source_summaries=record.source_summaries,
                indicator_snapshots=record.indicator_snapshots,
                final_npcs=record.final_npcs,
                events=record.events,
                completed_rounds=record.current_round,
                max_rounds=record.policy.num_rounds,
                situation_kind=record.policy.situation_kind,
                stance_summary={"initial": record.initial_stance, "final": stance_summary(record.final_npcs)},
            )
            record.economic_report = report
            await sio.emit("economic_report", report.model_dump(), to=sid)
            logger.info("sim=%s  economic_report emitted", simulation_id)
        except Exception:
            logger.exception("sim=%s  economic_report generation failed", simulation_id)

    except Exception as exc:
        record.status = "error"
        record.error_message = str(exc)
        logger.exception("Simulation %s failed", simulation_id)
        try:
            await sio.emit(
                "sim_error", {"message": f"Simulation failed: {exc}"}, to=sid
            )
        except Exception:
            pass


@router.get(
    "/simulate/{simulation_id}/economic-report", response_model=EconomicReportResponse
)
async def get_economic_report(simulation_id: str):
    record = simulations.get(simulation_id)
    if record is None or record.status != "complete":
        raise HTTPException(status_code=404, detail="Completed simulation not found.")

    if record.economic_report is not None:
        return record.economic_report

    record.economic_report = await generate_economic_report(
        policy_text=record.policy_text,
        objective=record.policy.objective,
        entities=record.entities,
        source_summaries=record.source_summaries,
        indicator_snapshots=record.indicator_snapshots,
        final_npcs=record.final_npcs,
        events=record.events,
        completed_rounds=record.current_round,
        max_rounds=record.policy.num_rounds,
        situation_kind=record.policy.situation_kind,
        stance_summary={"initial": record.initial_stance, "final": stance_summary(record.final_npcs)},
    )
    return record.economic_report


@sio.event
async def chat_with_npc(sid: str, data: dict) -> None:
    """Handle user chatting with an NPC (ephemeral, doesn't affect sim state).

    The conversation is "forked" from the current simulation state - the NPC
    has access to all its memories and context, but the chat itself is
    ephemeral and maintained on the frontend.
    """
    simulation_id = data.get("simulation_id", "")
    npc_id = data.get("npc_id", "")
    user_message = data.get("message", "")
    conversation_history = data.get("history", [])

    logger.info(
        "sio chat_with_npc  sid=%s  sim=%s  npc=%s  msg='%s...'",
        sid,
        simulation_id,
        npc_id,
        user_message[:30] if user_message else "",
    )

    record = simulations.get(simulation_id)
    if not record:
        await sio.emit(
            "npc_chat_error",
            {"npc_id": npc_id, "message": "Simulation not found"},
            to=sid,
        )
        return

    # Find the NPC in the current state
    npc = next((n for n in record.final_npcs if n.get("id") == npc_id), None)
    if not npc:
        await sio.emit(
            "npc_chat_error",
            {"npc_id": npc_id, "message": "NPC not found"},
            to=sid,
        )
        return

    try:
        reply = await generate_npc_chat_reply(
            npc=npc,
            user_message=user_message,
            conversation_history=conversation_history,
            memory_stream=record.memory_streams.get(npc_id, []),
            policy_context=record.policy_text,
            user_lang=data.get("user_lang"),
        )

        await sio.emit(
            "npc_chat_response",
            {
                "npc_id": npc_id,
                "response": reply["text"],
                "sources": reply["sources"],
                "stance": reply["stance"],
                "translated": reply["translated"],
            },
            to=sid,
        )
    except Exception as e:
        logger.exception("Chat with NPC %s failed: %s", npc_id, e)
        await sio.emit(
            "npc_chat_error",
            {"npc_id": npc_id, "message": f"Chat failed: {e}"},
            to=sid,
        )
