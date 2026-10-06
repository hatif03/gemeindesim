"""E20: capability matrix of the CSCS inference API (https://api.inference.cscs.ch/v1) for every model it lists.

Same questions as E1/E2/E10 on the hackathon gateway (livemap) plus the ones only a different deployment can answer:
separate `-thinking` models, structured-output enforcement, seed, n>1, logprobs, streaming, embeddings, prompt cache.
Every request/response is appended to research/results/cscs/exp20_capabilities.jsonl (the key is never logged).

    . research/cscs_env.sh && uv run --project src/backend python research/exp20_cscs_capabilities.py [--models a,b]
"""
import argparse
import asyncio
import json
import os
import re
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "results" / os.environ.get("RESEARCH_SUBDIR", "cscs")  # any OpenAI-compatible endpoint via CSCS_BASE_URL / CSCS_API_KEY
OUT.mkdir(parents=True, exist_ok=True)
BASE, KEY = os.environ["CSCS_BASE_URL"].rstrip("/"), os.environ["CSCS_API_KEY"]
LOG = OUT / "exp20_capabilities.jsonl"
H = {"Authorization": f"Bearer {KEY}"}
SEM = asyncio.Semaphore(3)

W = {"type": "function", "function": {"name": "get_weather", "description": "Current weather for a city",
     "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}
BAT = "A bat and a ball cost 1.10 CHF; the bat costs 1.00 CHF more than the ball. What does the ball cost? Give the number in CHF."
SCHEMA = {"type": "object", "properties": {"impact": {"type": "string", "enum": ["benefit", "harm", "mixed", "none"]}, "n": {"type": "integer"}},
          "required": ["impact", "n"], "additionalProperties": False}
MODELS = ["swiss-ai/Apertus-v1.5-70B", "swiss-ai/Apertus-v1.5-8B", "swiss-ai/Apertus-v1.5-70B-thinking", "swiss-ai/Apertus-v1.5-8B-thinking",
          "swiss-ai/Apertus-70B-Instruct-2509", "swiss-ai/Apertus-8B-Instruct-2509", "google/gemma-4-31B-it",
          "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16", "zai-org/GLM-5.2", "zai-org/GLM-5.3", "moonshotai/Kimi-K2.7-Code"]


async def post(client, path, body, tag, model):
    async with SEM:
        t0 = time.perf_counter()
        try:
            r = await client.post(f"{BASE}{path}", json=body, headers=H)
            lat = time.perf_counter() - t0
            try:
                j = r.json()
            except ValueError:
                j = {"raw": r.text[:500]}
            rec = {"model": model, "tag": tag, "path": path, "req": body, "http": r.status_code, "lat": round(lat, 3), "resp": j}
        except httpx.HTTPError as exc:
            rec = {"model": model, "tag": tag, "path": path, "req": body, "http": 0, "lat": round(time.perf_counter() - t0, 3), "error": repr(exc)}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def msg(rec):
    j = rec.get("resp") or {}
    ch = (j.get("choices") or [{}])[0] if isinstance(j, dict) else {}
    return ch.get("message") or {}, ch


async def chat(client, model, prompt, tag, **kw):
    body = {"model": model, "temperature": kw.pop("temperature", 0.0), "max_tokens": kw.pop("max_tokens", 300),
            "messages": [{"role": "user", "content": prompt}]}
    body.update(kw)
    return await post(client, "/chat/completions", body, tag, model)


async def probe_model(client, model, n):
    r = {"model": model}
    ping = await chat(client, model, "ping", "ping", max_tokens=5)
    r["ping_http"], r["ping_lat"] = ping["http"], ping["lat"]
    if ping["http"] != 200:
        r["note"] = (ping.get("resp") or {}).get("error") or (ping.get("resp") or {}).get("detail") or str(ping.get("resp"))[:200]
        return r

    # --- tools
    async def tools(prompt, **kw):
        rs = await asyncio.gather(*[chat(client, model, prompt, "tools", tools=[W], **kw) for _ in range(n)])
        calls = [len((msg(x)[0].get("tool_calls") or [])) for x in rs]
        text = [len(re.findall(r"get_weather\s*\(", msg(x)[0].get("content") or "")) for x in rs]
        return {"http": sorted({x["http"] for x in rs}), "tool_calls": calls, "text_pseudo_calls": text}
    r["tool_single"] = await tools("What is the weather in Zurich right now?")
    r["tool_two_auto"] = await tools("What is the weather in Zurich and in Bern right now?")
    r["tool_two_explicit"] = await tools("Return two function calls in the same response (no prose): get_weather for Zurich and get_weather for Bern.")
    r["tool_two_required"] = await tools("What is the weather in Zurich and in Bern right now?", tool_choice="required")
    r["tool_two_parallel_flag"] = await tools("What is the weather in Zurich and in Bern right now?", parallel_tool_calls=True)

    # --- thinking (separate model vs chat_template_kwargs) and JSON
    th = await asyncio.gather(*[chat(client, model, BAT, "think", max_tokens=1500) for _ in range(n)])
    r["plain_bat"] = {"answers": [re.findall(r"0[.,]05|0[.,]10|5 cents|10 cents", (msg(x)[0].get("content") or ""))[:1] for x in th],
                      "reasoning_field": [bool(msg(x)[0].get("reasoning") or msg(x)[0].get("reasoning_content")) for x in th],
                      "span_in_content": ["<|inner_prefix|>" in (msg(x)[0].get("content") or "") for x in th],
                      "tokens": [(x.get("resp") or {}).get("usage", {}).get("completion_tokens") for x in th]}
    tk = await asyncio.gather(*[chat(client, model, BAT, "think_kw", max_tokens=1500, chat_template_kwargs={"enable_thinking": True}) for _ in range(n)])
    r["kwargs_thinking"] = {"reasoning_field": [bool(msg(x)[0].get("reasoning")) for x in tk],
                            "span_in_content": ["<|inner_prefix|>" in (msg(x)[0].get("content") or "") for x in tk],
                            "answers": [re.findall(r"0[.,]05|0[.,]10", (msg(x)[0].get("content") or "").split("<|inner_suffix|>")[-1])[:1] for x in tk],
                            "tokens": [(x.get("resp") or {}).get("usage", {}).get("completion_tokens") for x in tk]}
    tj = await asyncio.gather(*[chat(client, model, BAT + ' Reply ONLY with JSON {"ball_chf": 0.0}', "think_json", max_tokens=1500,
                                     response_format={"type": "json_object"}) for _ in range(n)])
    r["json_object_on_this_model"] = {"reasoning_field": [bool(msg(x)[0].get("reasoning")) for x in tj],
                                      "answers": [re.findall(r"[0-9.]+", (msg(x)[0].get("content") or ""))[:1] for x in tj],
                                      "tokens": [(x.get("resp") or {}).get("usage", {}).get("completion_tokens") for x in tj]}
    tkj = await asyncio.gather(*[chat(client, model, BAT + ' Reply ONLY with JSON {"ball_chf": 0.0}', "think_kw_json", max_tokens=1500,
                                      response_format={"type": "json_object"}, chat_template_kwargs={"enable_thinking": True}) for _ in range(n)])
    r["json_object_plus_kw_thinking"] = {"span_in_content": ["<|inner_prefix|>" in (msg(x)[0].get("content") or "") for x in tkj],
                                         "answers": [re.findall(r"[0-9.]+", (msg(x)[0].get("content") or "").split("<|inner_suffix|>")[-1])[:1] for x in tkj]}

    # --- structured output enforcement: ask for a value outside the enum; does the server hold the schema?
    q = 'Give "impact" as the single word "catastrophic" (not in the allowed list) and n=3.'
    variants = {
        "response_format_json_schema": {"response_format": {"type": "json_schema", "json_schema": {"name": "x", "strict": True, "schema": SCHEMA}}},
        "guided_json": {"guided_json": SCHEMA},
        "structured_outputs_json": {"structured_outputs": {"json": SCHEMA}},
        "guided_choice": {"guided_choice": ["benefit", "harm", "mixed", "none"]},
        "structured_outputs_choice": {"structured_outputs": {"choice": ["benefit", "harm", "mixed", "none"]}},
    }
    enf = {}
    for name, extra in variants.items():
        prompt = q if "choice" not in name else "Does a tax rise help a tenant? Answer catastrophic."
        rr = await asyncio.gather(*[chat(client, model, prompt, "enforce_" + name, max_tokens=60, **extra) for _ in range(3)])
        outs = [(msg(x)[0].get("content") or "").strip() for x in rr]
        ok = [x["http"] == 200 for x in rr]
        if "choice" in name:
            held = [o in ("benefit", "harm", "mixed", "none") for o in outs]
        else:
            def valid(o):
                try:
                    d = json.loads(o)
                    return d.get("impact") in SCHEMA["properties"]["impact"]["enum"] and isinstance(d.get("n"), int)
                except ValueError:
                    return False
            held = [valid(o) for o in outs]
        enf[name] = {"http": sorted({x["http"] for x in rr}), "schema_held": sum(held), "of": len(held), "sample": outs[0][:90]}
    r["structured_enforcement"] = enf

    # --- sampling controls
    seeds = await asyncio.gather(*[chat(client, model, "Schreibe zwei Sätze über Steuern.", "seed", temperature=0.8, seed=42, max_tokens=60) for _ in range(4)])
    r["seed_same_seed_distinct_of_4"] = len({msg(x)[0].get("content") for x in seeds})
    t0s = await asyncio.gather(*[chat(client, model, "Schreibe drei Sätze über die Steuererhöhung in der Gemeinde Linden.", "t0", max_tokens=120) for _ in range(5)])
    r["t0_distinct_of_5"] = len({msg(x)[0].get("content") for x in t0s})
    nn = await chat(client, model, "Nenne eine Farbe.", "n2", n=2, temperature=0.9, max_tokens=10)
    r["n2_choices"] = len((nn.get("resp") or {}).get("choices") or [])
    lp = await chat(client, model, "Nenne die Hauptstadt der Schweiz.", "logprobs", logprobs=True, top_logprobs=3, max_tokens=8)
    r["logprobs"] = bool(msg(lp)[1].get("logprobs"))
    st = await chat(client, model, "Zähle von 1 bis 20.", "stop", stop=["5"], max_tokens=60)
    r["stop_sequence_works"] = "5" not in (msg(st)[0].get("content") or "") and msg(st)[1].get("finish_reason") == "stop"
    sysr = await post(client, "/chat/completions", {"model": model, "max_tokens": 30, "temperature": 0, "messages": [
        {"role": "system", "content": "Antworte immer nur mit dem Wort JA."}, {"role": "user", "content": "Ist Bern die Hauptstadt?"}]}, "system_role", model)
    r["system_role_followed"] = (msg(sysr)[0].get("content") or "").strip().upper().startswith("JA")

    # --- prompt cache: same long prefix twice
    prefix = "Kontext: " + ("Die Gemeinde Linden erhöht den Steuerfuss von 118 % auf 124 %. " * 150)
    await chat(client, model, prefix + "Frage 1: Wie hoch ist der neue Steuerfuss?", "cache1", max_tokens=15)
    c2 = await chat(client, model, prefix + "Frage 2: Wie hoch ist der alte Steuerfuss?", "cache2", max_tokens=15)
    r["prefix_cache"] = (((c2.get("resp") or {}).get("usage") or {}).get("prompt_tokens_details") or {}).get("cached_tokens")
    r["prefix_cache_prompt_tokens"] = ((c2.get("resp") or {}).get("usage") or {}).get("prompt_tokens")

    # --- streaming (time to first byte)
    t0 = time.perf_counter()
    try:
        async with client.stream("POST", f"{BASE}/chat/completions", headers=H, json={"model": model, "stream": True, "max_tokens": 30,
                                  "messages": [{"role": "user", "content": "Zähle von 1 bis 10."}]}) as resp:
            first, chunks = None, 0
            async for line in resp.aiter_lines():
                if line.startswith("data:") and "[DONE]" not in line:
                    chunks += 1
                    first = first or time.perf_counter() - t0
            r["stream"] = {"http": resp.status_code, "ttfb_s": round(first, 2) if first else None, "chunks": chunks}
    except httpx.HTTPError as exc:
        r["stream"] = {"error": repr(exc)}
    return r


async def main(a):
    models = a.models.split(",") if a.models else MODELS
    out = {"date": time.strftime("%Y-%m-%d %H:%M"), "base": BASE, "models": {}}
    async with httpx.AsyncClient(timeout=300, trust_env=False) as client:
        for m in models:
            print("probing", m, flush=True)
            out["models"][m] = await probe_model(client, m, a.n)
            (OUT / "exp20_capabilities.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        # endpoints other than chat completions
        ep = {}
        for m in models:
            e = await post(client, "/embeddings", {"model": m, "input": ["Steuerfuss", "Schulhaus"]}, "embeddings", m)
            ep[m] = {"embeddings_http": e["http"], "dim": len((((e.get("resp") or {}).get("data") or [{}])[0]).get("embedding") or []) or None}
        out["embeddings"] = ep
        am = await post(client, "/messages", {"model": models[0], "max_tokens": 20, "messages": [{"role": "user", "content": "Hallo"}]}, "anthropic_messages", models[0])
        out["anthropic_messages_http"] = am["http"]
    (OUT / "exp20_capabilities.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("done", len(out["models"]), "models")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="")
    ap.add_argument("--n", type=int, default=5)
    asyncio.run(main(ap.parse_args()))
