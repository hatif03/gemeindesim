"""Live end-to-end simulation test — 10 NPCs, 2 rounds."""
from __future__ import annotations
import asyncio
from datetime import datetime
from pathlib import Path
import httpx
import socketio

BACKEND = "http://localhost:8000"
PDF_PATH = Path(__file__).resolve().parent / "data" / "tariff_capital_policy.pdf"


def log(tag: str, msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}", flush=True)


def upload_pdf(client: httpx.Client) -> str:
    with open(PDF_PATH, "rb") as f:
        resp = client.post(
            f"{BACKEND}/context/sources",
            files={"file": (PDF_PATH.name, f, "application/pdf")},
            data={"label": "Tariff 2025"},
        )
    resp.raise_for_status()
    src = resp.json()["id"]
    log("UPLOAD", f"source_id={src}")
    return src


def create_sim(client: httpx.Client, src: str) -> str:
    resp = client.post(
        f"{BACKEND}/simulate",
        json={
            "primary_policy_source_id": src,
            "policy_source_ids": [src],
            "num_rounds": 2,
            "num_npcs": 10,
            "objective": "Assess tariff reform impact on a mid-size American town",
            "trend_source_ids": [],
            "notes_text": "",
        },
    )
    resp.raise_for_status()
    sid = resp.json()["simulation_id"]
    log("SIM", f"sim_id={sid}")
    return sid


async def run(sim_id: str) -> None:
    sio = socketio.AsyncClient(reconnection=False, logger=False, engineio_logger=False)
    done = asyncio.Event()

    @sio.event
    async def connect() -> None:
        log("WS", "connected")
        await sio.emit("start_sim", {"simulation_id": sim_id})

    @sio.event
    async def disconnect() -> None:
        log("WS", "disconnected")
        done.set()

    @sio.on("init")
    async def on_init(data: dict) -> None:
        rels = data.get("relationships", [])
        log("INIT", f"npcs={len(data.get('npcs', []))}  relationships={len(rels)}")
        non_zero = [
            (r["source_id"], r["target_id"], r["affinity"], r["trust"])
            for r in rels
            if r.get("affinity", 0) != 0.0
        ]
        log("INIT", f"  non-zero affinity rels: {len(non_zero)}/{len(rels)}")
        if non_zero:
            log("INIT", f"  sample: {non_zero[:3]}")
        for n in data.get("npcs", [])[:3]:
            log("NPC", f"  {n.get('id')} {n.get('name')} / {n.get('profession', '?')[:50]}")

    @sio.on("round")
    async def on_round(data: dict) -> None:
        evs = data.get("events", [])
        log("ROUND", f"round={data.get('round')}  events={len(evs)}")
        for ev in evs[:2]:
            log("EVENT", f"  {ev.get('npc_id')} -> {ev.get('event_type')}  {str(ev.get('message', ''))[:60]}")

    @sio.on("economic_report")
    async def on_report(data: dict) -> None:
        log("REPORT", f"{str(data.get('headline', ''))[:90]}")
        log("REPORT", f"{str(data.get('summary', ''))[:130]}")
        done.set()

    @sio.on("sim_error")
    async def on_err(data: dict) -> None:
        log("ERROR", data.get("message", ""))
        done.set()

    @sio.on("done")
    async def on_done(_: dict) -> None:
        log("DONE", "waiting for report...")

    await sio.connect(BACKEND, transports=["websocket"])
    try:
        await asyncio.wait_for(done.wait(), timeout=600)
    except asyncio.TimeoutError:
        log("TIMEOUT", "exceeded 10min")
    finally:
        if sio.connected:
            await sio.disconnect()


async def main() -> None:
    log("START", "10 NPCs / 2 rounds -- swarm upgrade test")
    c = httpx.Client(trust_env=False)
    try:
        src = upload_pdf(c)
        sid = create_sim(c, src)
    finally:
        c.close()
    await run(sid)
    log("END", "done")


if __name__ == "__main__":
    asyncio.run(main())
