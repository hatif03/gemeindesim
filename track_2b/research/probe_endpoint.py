"""Deployment probe: the Apertus behaviours that matter for GemeindeSim, against ANY OpenAI-compatible endpoint.

Why: every gateway finding in docs/research (single tool call per completion, thinking inside `content`, thinking vs
JSON mode, non-deterministic temperature 0, requests in flight) was measured on the hosted hackathon gateway only. The
sovereign-deployment claim (on-prem / air-gapped / Swiss cloud) is only as strong as this table measured on the target
deployment, e.g. a local vLLM serving swiss-ai/Apertus-v1.5-8B or -70B. No GPU was available while this was written.

Usage (hosted gateway, same numbers as research E1/E10):
    python research/probe_endpoint.py --base-url https://hackapertus.livemap.sh/v1 --model apertus-v1.5-8b --key-env LLM_API_KEY
Local vLLM (no key needed):
    python research/probe_endpoint.py --base-url http://localhost:8000/v1 --model swiss-ai/Apertus-v1.5-8B
Writes research/results/probe_<model>.json and prints a markdown table to paste into docs/research/.
Run on an otherwise idle endpoint; the throughput part stops at --max-concurrency.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics as st
import time
from pathlib import Path

import httpx

WEATHER = {"type": "function", "function": {"name": "get_weather", "description": "Current weather for a city",
           "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}
BAT = "A bat and a ball cost 1.10 CHF; the bat costs 1.00 CHF more than the ball. What does the ball cost?"


class Client:
    def __init__(self, base, model, key):
        self.base, self.model = base.rstrip("/"), model
        self.h = {"Authorization": f"Bearer {key}"} if key else {}
        self.c = httpx.AsyncClient(timeout=300, trust_env=False)

    async def chat(self, prompt, **kw):
        body = {"model": self.model, "temperature": kw.pop("temperature", 0.0), "max_tokens": kw.pop("max_tokens", 400),
                "messages": [{"role": "user", "content": prompt}], "chat_template_kwargs": {"enable_thinking": kw.pop("thinking", False)}}
        if kw.pop("json_mode", False):
            body["response_format"] = {"type": "json_object"}
        body.update(kw)
        t0 = time.perf_counter()
        r = await self.c.post(f"{self.base}/chat/completions", json=body, headers=self.h)
        dt = time.perf_counter() - t0
        try:
            j = r.json()
        except ValueError:
            j = {}
        ch = (j.get("choices") or [{}])[0]
        m = ch.get("message") or {}
        return {"http": r.status_code, "lat": dt, "content": m.get("content") or "", "tool_calls": m.get("tool_calls") or [],
                "reasoning": (m.get("provider_specific_fields") or {}).get("reasoning") or m.get("reasoning_content"),
                "tokens": (j.get("usage") or {}).get("completion_tokens", 0)}


async def main(a):
    key = os.environ.get(a.key_env, "") if a.key_env else ""
    cl = Client(a.base_url, a.model, key)
    out = {"base_url": a.base_url, "model": a.model, "date": time.strftime("%Y-%m-%d %H:%M")}
    n = a.n

    # 1 tool calls
    async def tools(prompt, **kw):
        rs = await asyncio.gather(*[cl.chat(prompt, tools=[WEATHER], **kw) for _ in range(n)])
        return [len(r["tool_calls"]) for r in rs], [len(re.findall(r"get_weather\s*\(", r["content"])) for r in rs]
    out["single_call"] = await tools("What is the weather in Zurich right now?")
    out["two_cities_auto"] = await tools("What is the weather in Zurich and in Bern right now?")
    out["explicit_two_calls"] = await tools("Return two function calls in the same response (no prose): get_weather for Zurich and get_weather for Bern.")
    out["two_cities_required"] = await tools("What is the weather in Zurich and in Bern right now?", tool_choice="required")

    # 2 thinking
    think = await asyncio.gather(*[cl.chat(BAT, thinking=True, max_tokens=1200) for _ in range(n)])
    out["thinking_span_in_content"] = [("<|inner_prefix|>" in r["content"]) for r in think]
    out["thinking_reasoning_field_filled"] = [bool(r["reasoning"]) for r in think]
    tj = await asyncio.gather(*[cl.chat(BAT + ' Output ONLY JSON {"ball_chf": 0.0}', thinking=True, json_mode=True, max_tokens=1200) for _ in range(n)])
    out["thinking_plus_json_has_span"] = [("<|inner_prefix|>" in r["content"]) for r in tj]
    out["thinking_plus_json_answers"] = [re.findall(r"[0-9.]+", r["content"].split("<|inner_suffix|>")[-1])[:1] for r in tj]
    tt = await asyncio.gather(*[cl.chat("What is the weather in Zurich right now?", thinking=True, tools=[WEATHER]) for _ in range(n)])
    out["tools_plus_thinking_http"] = [r["http"] for r in tt]

    # 3 determinism
    det = await asyncio.gather(*[cl.chat("Schreibe drei Sätze über die Steuererhöhung in der Gemeinde Linden.", max_tokens=200) for _ in range(5)])
    out["determinism_distinct_of_5"] = len({r["content"] for r in det})

    # 4 throughput / rate limit
    tp = []
    for c in [x for x in (1, 2, 4, 5, 6, 8, 12, 16) if x <= a.max_concurrency]:
        sem = asyncio.Semaphore(c)

        async def one():
            async with sem:
                return await cl.chat("Nenne vier Vorteile und vier Nachteile einer Steuererhöhung für ein Schulhaus, je ein Satz.", max_tokens=250)

        t0 = time.perf_counter()
        rs = await asyncio.gather(*[one() for _ in range(max(6, 2 * c))])
        wall = time.perf_counter() - t0
        ok = [r for r in rs if r["http"] == 200]
        tp.append({"concurrency": c, "ok": len(ok), "n": len(rs), "http429": sum(r["http"] == 429 for r in rs),
                   "p50_latency_s": round(st.median(r["lat"] for r in ok), 2) if ok else None,
                   "agg_tok_per_s": round(sum(r["tokens"] for r in ok) / wall, 1)})
        await asyncio.sleep(2)
    out["throughput"] = tp
    await cl.c.aclose()

    Path(__file__).resolve().parent.joinpath("results", f"probe_{a.model.replace('/', '_')}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    one_call = lambda xs: f"{sum(1 for x in xs if x == 1)}/{len(xs)} one call"
    print(f"\n| behaviour ({a.model} @ {a.base_url}, n={n}) | result |\n| --- | --- |")
    print(f"| single tool call | {one_call(out['single_call'][0])} |")
    print(f"| two cities, auto | {one_call(out['two_cities_auto'][0])}; text pseudo-calls {sum(out['two_cities_auto'][1])} |")
    print(f"| explicit 'two calls' | tool_calls {out['explicit_two_calls'][0]}; text pseudo-calls {out['explicit_two_calls'][1]} |")
    print(f"| tool_choice=required, two cities | {one_call(out['two_cities_required'][0])} |")
    print(f"| thinking span in `content` | {sum(out['thinking_span_in_content'])}/{n}; `reasoning` field filled {sum(out['thinking_reasoning_field_filled'])}/{n} |")
    print(f"| thinking + json_object | span present {sum(out['thinking_plus_json_has_span'])}/{n}; answers {out['thinking_plus_json_answers']} (correct 0.05) |")
    print(f"| tools + thinking | HTTP {sorted(set(out['tools_plus_thinking_http']))} |")
    print(f"| temperature 0 determinism | {out['determinism_distinct_of_5']} distinct outputs of 5 identical prompts |")
    for t in tp:
        print(f"| in flight {t['concurrency']} | ok {t['ok']}/{t['n']}, 429 {t['http429']}, p50 {t['p50_latency_s']} s, {t['agg_tok_per_s']} tok/s |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--key-env", default="", help="name of the env var holding the API key (omit for local servers)")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--max-concurrency", type=int, default=8)
    asyncio.run(main(ap.parse_args()))
