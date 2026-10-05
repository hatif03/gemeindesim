"""E10: latency / throughput / rate-limit behaviour of the hackathon gateway (raw, NO retries).

Replays one real resident prompt at concurrency levels, per model. Must run with the key idle.
Outputs per level: success rate, 429 rate, p50/p95 latency, completion tokens/s (aggregate).
"""
import asyncio
import json
import statistics as st
import time

import httpx

from common import BASE, KEY, M70, M8, RESULTS


async def one(client, model, prompt):
    body = {"model": model, "temperature": 0, "max_tokens": 500, "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}, "chat_template_kwargs": {"enable_thinking": False}}
    t0 = time.perf_counter()
    try:
        r = await client.post(BASE + "/chat/completions", json=body, headers={"Authorization": f"Bearer {KEY}"})
        dt = time.perf_counter() - t0
        tok = (r.json().get("usage") or {}).get("completion_tokens", 0) if r.status_code == 200 else 0
        return {"http": r.status_code, "lat": dt, "tok": tok}
    except Exception as exc:  # noqa: BLE001
        return {"http": 0, "lat": time.perf_counter() - t0, "tok": 0, "err": repr(exc)}


async def main():
    rows = [json.loads(l) for l in (RESULTS / "sims" / "base70_s1.calls.jsonl").read_text(encoding="utf-8").splitlines()]
    prompt = next(r["prompt"] for r in rows if "Choose 1-3 events" in r["prompt"])
    out = []
    async with httpx.AsyncClient(timeout=180, trust_env=False) as client:
        for model in (M8, M70):
            for c in (1, 2, 4, 5, 6, 8):
                n = max(6, 2 * c)
                sem = asyncio.Semaphore(c)

                async def guarded():
                    async with sem:
                        return await one(client, model, prompt)

                t0 = time.perf_counter()
                res = await asyncio.gather(*[guarded() for _ in range(n)])
                wall = time.perf_counter() - t0
                ok = [r for r in res if r["http"] == 200]
                row = {"model": model, "concurrency": c, "n": n, "ok": len(ok), "http429": sum(r["http"] == 429 for r in res),
                       "other_err": sum(r["http"] not in (200, 429) for r in res),
                       "p50_lat": round(st.median(r["lat"] for r in ok), 2) if ok else None,
                       "p95_lat": round(sorted(r["lat"] for r in ok)[int(0.95 * (len(ok) - 1))], 2) if ok else None,
                       "agg_tok_per_s": round(sum(r["tok"] for r in ok) / wall, 1), "wall_s": round(wall, 1)}
                out.append(row)
                print(row, flush=True)
                await asyncio.sleep(3)
    (RESULTS / "e10_throughput.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
