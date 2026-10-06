"""The ensemble endpoint turns one anecdote into a distribution."""

import pytest

from routers import ensemble


def _run(f, a, u):
    return {"initial": {"for": f, "against": a, "undecided": u, "mean": 0.0, "n": f + a + u},
            "final": {"for": f, "against": a, "undecided": u, "mean": (f - a) / (f + a + u), "n": f + a + u}, "events": 30}


def test_summarise_reports_the_range_not_only_the_mean():
    s = ensemble.summarise([_run(0, 3, 2), _run(4, 1, 0), _run(3, 2, 0)])
    assert s["share_for"] == {"mean": 0.467, "min": 0.0, "max": 0.8}
    assert s["share_against"]["max"] == 0.6 and s["runs"] == 3


@pytest.mark.asyncio
async def test_one_failed_run_does_not_lose_the_others(monkeypatch):
    calls = {"n": 0}

    async def fake(policy):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("gateway timeout")
        return _run(2, 2, 1)

    monkeypatch.setattr(ensemble, "_one", fake)
    body = ensemble.EnsembleInput(notes_text="x" * 60, runs=3, parallel=1)
    ensemble.ensembles["t"] = {"status": "running", "runs": [None] * 3, "completed": 0, "errors": [], "summary": None, "total": 3}
    await ensemble._run("t", body)
    rec = ensemble.ensembles["t"]
    assert rec["status"] == "complete" and rec["completed"] == 3
    assert len([r for r in rec["runs"] if r]) == 2 and "run 2" in rec["errors"][0]
    assert rec["summary"]["runs"] == 2
