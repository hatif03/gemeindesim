"""E21: rate limit, latency and throughput of the CSCS inference API as a function of requests in flight (same design as E10).

Raw requests, no retries, idle key. Two request shapes: SHORT (small prompt, ≤ 250 tokens out) and APP (≈ 3k-token prompt like a
resident turn, ≤ 250 tokens out). Escalates 1, 2, 4, 8, 12, 16, 24, 32 in flight per model; stops a model when two consecutive levels
show more than 30 % non-200 answers. Raw rows: research/results/cscs/exp21_throughput.jsonl (no key logged).

    . research/cscs_env.sh && uv run --project src/backend python research/exp21_cscs_throughput.py
"""
import asyncio
import json
import os
import statistics as st
import time
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parent / "results" / "cscs"
OUT.mkdir(parents=True, exist_ok=True)
BASE, KEY = os.environ["CSCS_BASE_URL"].rstrip("/"), os.environ["CSCS_API_KEY"]
H = {"Authorization": f"Bearer {KEY}"}
SHORT = "Nenne vier Vorteile und vier Nachteile einer Steuererhöhung für ein Schulhaus, je ein Satz."
CTX = "Gemeinde Linden: Der Steuerfuss steigt von 118 % auf 124 %; Kredit 4.8 Millionen CHF für das Schulhaus Linden-Dorf. " * 60
APP = CTX + "\n\nDu bist eine Ladenbesitzerin in Linden. Antworte in vier Sätzen auf Deutsch, wie du zur Vorlage stehst und warum."
LEVELS = [int(x) for x in os.environ.get("E21_LEVELS", "1,2,4,8,12,16,24,32").split(",")]
MODELS = os.environ.get("E21_MODELS", "swiss-ai/Apertus-v1.5-70B,swiss-ai/Apertus-v1.5-8B").split(",")
SHAPES = os.environ.get("E21_SHAPES", "short,app").split(",")
SUFFIX = os.environ.get("E21_SUFFIX", "")  # e.g. E21_LEVELS=48,64,96 E21_SUFFIX=_high for the escalation run


async def one(client, model, prompt, sem):
    async with sem:
        t0 = time.perf_counter()
        try:
            r = await client.post(f"{BASE}/chat/completions", headers=H, json={"model": model, "temperature": 0, "max_tokens": 250,
                                  "messages": [{"role": "user", "content": prompt}]})
            j = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            return {"http": r.status_code, "lat": time.perf_counter() - t0, "tok": (j.get("usage") or {}).get("completion_tokens", 0),
                    "ptok": (j.get("usage") or {}).get("prompt_tokens", 0), "body": None if r.status_code == 200 else r.text[:160]}
        except httpx.HTTPError as exc:
            return {"http": 0, "lat": time.perf_counter() - t0, "tok": 0, "ptok": 0, "body": repr(exc)[:160]}


async def main():
    rows, summary = [], []
    async with httpx.AsyncClient(timeout=300, trust_env=False) as client:
        for model in MODELS:
            for shape, prompt in [x for x in (("short", SHORT), ("app", APP)) if x[0] in SHAPES]:
                bad_streak = 0
                for c in LEVELS:
                    sem = asyncio.Semaphore(c)
                    n = max(8, 2 * c)
                    t0 = time.perf_counter()
                    rs = await asyncio.gather(*[one(client, model, prompt, sem) for _ in range(n)])
                    wall = time.perf_counter() - t0
                    ok = [r for r in rs if r["http"] == 200]
                    codes = {}
                    for r in rs:
                        codes[r["http"]] = codes.get(r["http"], 0) + 1
                    row = {"model": model, "shape": shape, "in_flight": c, "n": n, "ok": len(ok), "codes": codes,
                           "p50_s": round(st.median(r["lat"] for r in ok), 2) if ok else None,
                           "p95_s": round(sorted(r["lat"] for r in ok)[max(0, int(len(ok) * 0.95) - 1)], 2) if ok else None,
                           "agg_tok_s": round(sum(r["tok"] for r in ok) / wall, 1), "prompt_tok": ok[0]["ptok"] if ok else None, "wall_s": round(wall, 1)}
                    summary.append(row)
                    rows += [{**r, "model": model, "shape": shape, "in_flight": c} for r in rs]
                    print(row, flush=True)
                    bad_streak = bad_streak + 1 if len(ok) < 0.7 * n else 0
                    (OUT / f"exp21_throughput{SUFFIX}.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
                    if bad_streak >= 2:
                        print("stopping this model/shape: >30 % failures twice")
                        break
                    await asyncio.sleep(3)
    with (OUT / f"exp21_throughput{SUFFIX}.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
