"""Run the same vote several times and report the SPREAD of the stance poll.

Personas and the stance prior are drawn per run and temperature 0 is not reproducible, so one run is an anecdote (research
E3d/E13b: the share of residents *for* at the end ranged 0.00-0.80 across five seeds). This endpoint turns "run it once" into a
distribution. It needs a fast endpoint: five 5-resident runs take a few minutes at 16 requests in flight (research E21), and
far too long at the hackathon gateway's 4.
"""

import asyncio
import logging
import statistics as st
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import Field

from graph.builder import build_graph
from graph.nodes.stance import stance_summary
from models.schemas import PolicyInput
from models.state import SimState
from routers.simulate import _resolved_policy_source_ids

logger = logging.getLogger(__name__)
router = APIRouter()
ensembles: dict[str, dict[str, Any]] = {}


class EnsembleInput(PolicyInput):
    runs: int = Field(default=5, ge=2, le=10)
    parallel: int = Field(default=3, ge=1, le=5)


def _state(policy: PolicyInput) -> SimState:
    return {  # same fields as a streamed simulation, without the socket callbacks
        "policy_text": "", "notes_text": policy.notes_text, "trend_summary": "", "context_summary": "",
        "indicator_snapshots": [], "source_summaries": [], "policy_sources": _resolved_policy_source_ids(policy),
        "trend_sources": policy.trend_source_ids, "objective": policy.objective, "max_rounds": policy.num_rounds,
        "num_npcs": policy.num_npcs, "map_id": policy.map_id, "entities": [], "npcs": [], "relationships": [], "events": [],
        "current_round": 0, "economic_indicators": {}, "memory_streams": {}, "situation_kind": policy.situation_kind,
    }  # type: ignore[typeddict-item]


async def _one(policy: PolicyInput) -> dict[str, Any]:
    initial: list[dict[str, Any]] = []
    final: list[dict[str, Any]] = []
    events = 0
    async for chunk in build_graph().astream(_state(policy)):
        if "generate_npcs" in chunk:
            initial = chunk["generate_npcs"].get("npcs", [])
        elif "run_round" in chunk:
            final = chunk["run_round"].get("npcs", final)
            events += len(chunk["run_round"].get("events", []))
    return {"initial": stance_summary(initial), "final": stance_summary(final or initial), "events": events}


def summarise(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribution of the end-of-run poll across runs (share of residents for / against, mean stance)."""
    def stat(xs: list[float]) -> dict[str, float]:
        return {"mean": round(st.mean(xs), 3), "min": round(min(xs), 3), "max": round(max(xs), 3)}

    n = [r["final"]["n"] or 1 for r in runs]
    return {
        "share_for": stat([r["final"]["for"] / k for r, k in zip(runs, n)]),
        "share_against": stat([r["final"]["against"] / k for r, k in zip(runs, n)]),
        "mean_stance": stat([r["final"]["mean"] for r in runs]),
        "runs": len(runs),
    }


async def _run(ens_id: str, body: EnsembleInput) -> None:
    rec = ensembles[ens_id]
    sem = asyncio.Semaphore(body.parallel)

    async def one(i: int) -> None:
        async with sem:
            try:
                rec["runs"][i] = await _one(body)
            except Exception as exc:  # one failed run must not lose the others
                logger.exception("ensemble %s run %d failed", ens_id, i)
                rec["errors"].append(f"run {i + 1}: {exc}")
            rec["completed"] += 1

    await asyncio.gather(*[one(i) for i in range(body.runs)])
    done = [r for r in rec["runs"] if r]
    rec["summary"] = summarise(done) if done else None
    rec["status"] = "complete" if done else "error"


@router.post("/ensemble")
async def start_ensemble(body: EnsembleInput):
    if body.num_npcs * body.runs > 120:
        raise HTTPException(status_code=422, detail="num_npcs * runs is capped at 120 to keep the endpoint fair to share.")
    ens_id = str(uuid.uuid4())
    ensembles[ens_id] = {"status": "running", "runs": [None] * body.runs, "completed": 0, "errors": [], "summary": None, "total": body.runs}
    asyncio.create_task(_run(ens_id, body))
    return {"ensemble_id": ens_id}


@router.get("/ensemble/{ens_id}")
async def get_ensemble(ens_id: str):
    rec = ensembles.get(ens_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Ensemble not found.")
    return {**rec, "runs": [r for r in rec["runs"] if r]}
