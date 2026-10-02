"""Live notes-only simulation: Linden DE/FR, 5 NPCs, 1 round."""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import httpx
import socketio

BACKEND = "http://localhost:8000"
DATA = Path(__file__).resolve().parents[3] / "data"


def log(tag: str, msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}", flush=True)


def notes_text() -> str:
    de = (DATA / "steuerfuss_linden_de.txt").read_text(encoding="utf-8")
    fr = (DATA / "steuerfuss_linden_fr.txt").read_text(encoding="utf-8")
    return de.strip() + "\n\n" + fr.strip()


def create_sim(client: httpx.Client) -> str:
    resp = client.post(
        f"{BACKEND}/simulate",
        json={
            "notes_text": notes_text(),
            "num_rounds": 1,
            "num_npcs": 5,
            "objective": "How the Steuerfuss and school credit land on households and shops",
            "trend_source_ids": [],
            "policy_source_ids": [],
            "situation_kind": "vote",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    sid = resp.json()["simulation_id"]
    log("SIM", f"sim_id={sid}")
    return sid


async def run(sim_id: str) -> int:
    sio = socketio.AsyncClient(reconnection=False, logger=False, engineio_logger=False)
    done = asyncio.Event()
    status = {"ok": 0}

    @sio.event
    async def connect() -> None:
        log("WS", "connected")
        await sio.emit("start_sim", {"simulation_id": sim_id})

    @sio.on("setup_progress")
    async def on_progress(data: dict) -> None:
        log("SETUP", f"{data.get('label')} {data.get('current')}/{data.get('total')}")

    @sio.on("policy_analysis")
    async def on_policy(data: dict) -> None:
        ents = data.get("entities") or []
        log("POLICY", f"entities={len(ents)}")
        if ents:
            e = ents[0]
            log(
                "POLICY",
                f"  controversy={e.get('controversy_level')} kind={e.get('kind')} "
                f"sectors={e.get('sectors')}",
            )

    @sio.on("init")
    async def on_init(data: dict) -> None:
        npcs = data.get("npcs", [])
        log("INIT", f"npcs={len(npcs)} rels={len(data.get('relationships', []))}")
        for n in npcs:
            log(
                "NPC",
                f"  {n.get('id')} {n.get('name')} lang={n.get('lang')} "
                f"role={n.get('role')} {str(n.get('profession', ''))[:40]}",
            )

    @sio.on("round")
    async def on_round(data: dict) -> None:
        evs = data.get("events", [])
        types = [e.get("event_type") for e in evs]
        log("ROUND", f"round={data.get('round')} events={len(evs)} types={types}")
        for ev in evs:
            msg = str(ev.get("message", ""))[:90]
            log("EVENT", f"  {ev.get('npc_id')} {ev.get('event_type')} {msg}")

    @sio.on("economic_report")
    async def on_report(data: dict) -> None:
        log("REPORT", str(data.get("headline", ""))[:120])
        log("REPORT", str(data.get("summary", ""))[:200])
        status["ok"] = 1
        done.set()

    @sio.on("sim_error")
    async def on_err(data: dict) -> None:
        log("ERROR", str(data.get("message", data)))
        done.set()

    @sio.on("done")
    async def on_done(_: dict) -> None:
        log("DONE", "graph finished; waiting for report")

    await sio.connect(BACKEND, transports=["websocket"])
    try:
        await asyncio.wait_for(done.wait(), timeout=480)
    except asyncio.TimeoutError:
        log("TIMEOUT", "exceeded 8min")
    finally:
        if sio.connected:
            await sio.disconnect()
    return status["ok"]


async def main() -> None:
    log("START", "Linden DE/FR  5 NPCs / 1 round")
    health = httpx.get(f"{BACKEND}/docs", timeout=10.0)
    health.raise_for_status()
    c = httpx.Client(trust_env=False)
    try:
        sid = create_sim(c)
    finally:
        c.close()
    ok = await run(sid)
    log("END", "ok" if ok else "failed")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
