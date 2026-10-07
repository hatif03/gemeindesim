"""E32: do the `round` messages and the final `metrics` event carry the run metrics? (backend on http://localhost:8002; run from track_2b/)"""
import asyncio, json, httpx, socketio
url = "http://localhost:8002"
txt = open('data/steuerfuss_linden_de.txt', encoding='utf-8').read() + "\n\n" + open('data/steuerfuss_linden_fr.txt', encoding='utf-8').read()
async def main():
    async with httpx.AsyncClient(timeout=60) as c:
        sim = (await c.post(f"{url}/simulate", json={"notes_text": txt, "num_rounds": 2, "num_npcs": 3, "situation_kind": "vote"})).json()["simulation_id"]
    sio = socketio.AsyncClient(); done = asyncio.Event(); got = {"rounds": [], "metrics_event": None}
    @sio.on("round")
    async def _(d): got["rounds"].append(d.get("metrics"))
    @sio.on("metrics")
    async def __(d): got["metrics_event"] = d; done.set()
    await sio.connect(url, transports=["websocket"]); await sio.emit("start_sim", {"simulation_id": sim})
    await asyncio.wait_for(done.wait(), 300)
    print("round messages with metrics:", [bool(m) for m in got["rounds"]], "calls per round msg:", [m["calls"] for m in got["rounds"] if m])
    m = got["metrics_event"]; print("final metrics event:", {k: m[k] for k in ("calls","prompt_tokens","completion_tokens","cache_hit_rate","max_context_use","in_flight_limit","model","endpoint")})
asyncio.run(main())
