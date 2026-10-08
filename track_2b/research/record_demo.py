"""Record a demo replay from the RUNNING app (the same Socket.IO stream the UI receives).

    uv run --project src/backend python research/record_demo.py TAG --file data/steuerfuss_linden_balanced_de.txt --file data/steuerfuss_linden_balanced_fr.txt \
        --npcs 30 --rounds 4

Writes docs/replays/TAG.replay.json (load it on the landing page with the replay control) and TAG.config.json (the exact request,
to paste/enter in the UI before loading the replay). The key is never written.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
import socketio

ROOT = Path(__file__).resolve().parent.parent


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--file", action="append", required=True)
    ap.add_argument("--npcs", type=int, default=30)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--kind", default="vote")
    ap.add_argument("--objective", default="How the Steuerfuss and school credit land on households and shops")
    ap.add_argument("--api", default="http://localhost:8000")
    args = ap.parse_args()

    notes = "\n\n".join((ROOT / f).read_text(encoding="utf-8").strip() for f in args.file)
    req = {"notes_text": notes, "objective": args.objective, "num_rounds": args.rounds, "num_npcs": args.npcs,
           "map_id": "ccity", "situation_kind": args.kind}
    async with aiohttp.ClientSession() as s, s.post(f"{args.api}/simulate", json=req) as r:
        r.raise_for_status()
        sim_id = (await r.json())["simulation_id"]

    init: dict = {}
    rounds: list = []
    report: dict | None = None
    metrics: dict | None = None
    done = asyncio.Event()
    finished = asyncio.Event()
    err: list[str] = []
    t0 = time.perf_counter()
    sio = socketio.AsyncClient()

    @sio.on("init")
    async def _init(d):
        init.update(d, type="init")
        print(f"[{time.perf_counter() - t0:5.0f}s] init: {len(d['npcs'])} residents")

    @sio.on("round")
    async def _round(d):
        rounds.append({"type": "round", **d})
        print(f"[{time.perf_counter() - t0:5.0f}s] round {d['round']}: {len(d['events'])} events")

    @sio.on("economic_report")
    async def _rep(d):
        nonlocal report
        report = d
        print(f"[{time.perf_counter() - t0:5.0f}s] report")

    @sio.on("metrics")
    async def _met(d):
        nonlocal metrics
        metrics = d
        finished.set()

    @sio.on("sim_error")
    async def _err(d):
        err.append(d.get("message", "?"))
        finished.set()

    @sio.on("done")
    async def _done(_d):
        done.set()

    await sio.connect(args.api, transports=["websocket"])
    await sio.emit("start_sim", {"simulation_id": sim_id})
    await asyncio.wait_for(finished.wait(), timeout=3600)
    await sio.disconnect()
    if err or not rounds:
        raise SystemExit(f"failed: {err}")

    saved = {
        "version": 1,
        "savedAt": datetime.now(timezone.utc).isoformat(),
        "policyText": f"{args.tag}: {', '.join(args.file)}",
        "maxRounds": args.rounds,
        "initMsg": init,
        "rounds": rounds,
        "report": report,
    }
    out = ROOT / "docs/replays" / f"{args.tag}.replay.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(saved, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "docs/replays" / f"{args.tag}.config.json").write_text(
        json.dumps({**req, "files": args.file, "metrics": metrics, "wall_s": round(time.perf_counter() - t0, 1)}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(out, f"{out.stat().st_size // 1024} kB, wall {time.perf_counter() - t0:.0f}s")
    print("REPORT:", (report or {}).get("headline"))


if __name__ == "__main__":
    asyncio.run(main())
