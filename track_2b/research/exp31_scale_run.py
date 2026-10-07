"""E31: a larger town through the real backend (Socket.IO), with the adaptive limiter; prints wall time and the run's metrics.

    # backend on http://localhost:8001 with the endpoint under test (LLM_CONCURRENCY=auto), e.g. CSCS or the hackathon gateway
    uv run --project src/backend python research/exp31_scale_run.py http://localhost:8001 25     # run from track_2b/
"""
import asyncio, json, sys, time, httpx, socketio
url, n = sys.argv[1], int(sys.argv[2])
txt = open('data/steuerfuss_linden_de.txt', encoding='utf-8').read() + "\n\n" + open('data/steuerfuss_linden_fr.txt', encoding='utf-8').read()
async def main():
    async with httpx.AsyncClient(timeout=60) as c:
        sim = (await c.post(f"{url}/simulate", json={"notes_text": txt, "num_rounds": 2, "num_npcs": n, "situation_kind": "vote"})).json()["simulation_id"]
    sio = socketio.AsyncClient(); done = asyncio.Event(); err = {}
    last = {}
    @sio.on("round")
    async def _(d): last.update(d.get("metrics") or {})
    @sio.on("done")
    async def __(d=None): done.set()
    @sio.on("sim_error")
    async def ___(d): err.update(d); done.set()
    await sio.connect(url, transports=["websocket"])
    t0 = time.time(); await sio.emit("start_sim", {"simulation_id": sim})
    await asyncio.wait_for(done.wait(), 1500)
    print("wall", round(time.time() - t0), "s", err or "ok")
    async with httpx.AsyncClient() as c:
        m = (await c.get(f"{url}/simulate/{sim}/metrics")).json()
    print({k: m[k] for k in ("calls","prompt_tokens","completion_tokens","cache_hit_rate","mean_latency_s","p95_latency_s","rate_limited","gateway_retries","downgraded","failed","in_flight_limit","endpoint","model")})
asyncio.run(main())
