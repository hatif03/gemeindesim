"""E1: replicate and extend the PROBE-AND-PLAN claims with repeated trials.

Claims under test (docs/PROBE-AND-PLAN.md):
 C1 one tool call per turn works;           C2 parallel tool calls fail (8B: drops 2nd; 70B: pseudo-text);
 C3 thinking leaks <|inner_prefix|> into content, `reasoning` field is null;
 C4 temperature 0 is (near) deterministic; C5 tools+thinking cannot be combined.
New: tool_choice="required" with two cities; thinking+json_object; stochastic (T=0.7) repeat rate.
"""
import asyncio
import json
import re
import collections

from common import M70, M8, RESULTS, Gateway

WEATHER = {"type": "function", "function": {"name": "get_weather", "description": "Current weather for a city",
           "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}},
                          "required": ["city"]}}}
N = 8


def outcome_tools(rec):
    r = rec["resp"]
    tcs = r["tool_calls"] or []
    txt = r["content"] or ""
    pseudo = len(re.findall(r"get_weather\s*\(", txt))
    return f"tool_calls={len(tcs)}" + (f"+pseudo_text={pseudo}" if pseudo else "") + f" finish={r['finish']}"


async def main():
    gw = Gateway("e01_probe", concurrency=3)
    jobs = []
    for model in (M70, M8):
        for temp in (0.0, 0.7):
            for i in range(N if temp else 3):
                jobs += [
                    ("T1_single", model, temp, gw.chat("What is the weather in Zurich right now?", model=model, temperature=temp, tools=[WEATHER], tag="T1")),
                    ("T2_two_cities_auto", model, temp, gw.chat("What is the weather in Zurich and in Bern right now?", model=model, temperature=temp, tools=[WEATHER], tag="T2")),
                    ("T3_explicit_two_calls", model, temp, gw.chat("Return two function calls in the same response (no prose): get_weather for Zurich and get_weather for Bern.", model=model, temperature=temp, tools=[WEATHER], tag="T3")),
                    ("T4_required_two_cities", model, temp, gw.chat("What is the weather in Zurich and in Bern right now?", model=model, temperature=temp, tools=[WEATHER], tool_choice="required", tag="T4")),
                    ("T5_tools_plus_thinking", model, temp, gw.chat("What is the weather in Zurich right now?", model=model, temperature=temp, tools=[WEATHER], thinking=True, max_tokens=800, tag="T5")),
                ]
        # thinking leakage + json
        for i in range(N):
            jobs.append(("T6_thinking_plain", model, 0.0, gw.chat("A bat and a ball cost 1.10 CHF; the bat costs 1.00 CHF more than the ball. What does the ball cost?", model=model, thinking=True, max_tokens=900, tag="T6")))
            jobs.append(("T7_thinking_json", model, 0.0, gw.chat('Ball and bat cost 1.10 CHF, bat is 1.00 more. Output ONLY JSON {"ball_chf": 0.0}', model=model, thinking=True, json_mode=True, max_tokens=900, tag="T7")))
    keys = [(k, m, t) for k, m, t, _ in jobs]
    recs = await asyncio.gather(*[j[3] for j in jobs])
    summ = collections.defaultdict(collections.Counter)
    for (k, m, t), rec in zip(keys, recs):
        r = rec["resp"]
        if k.startswith("T6") or k.startswith("T7"):
            c = r["content"]
            o = ("inner_span" if "<|inner_prefix|>" in c else "no_span") + ("|closed" if "<|inner_suffix|>" in c else "|unclosed" if "<|inner_prefix|>" in c else "")
            o += "|reasoning_field" if r["reasoning"] else "|reasoning_null"
            if k.startswith("T7"):
                tail = c.split("<|inner_suffix|>")[-1]
                try:
                    json.loads(tail.strip()); o += "|json_ok"
                except Exception:
                    o += "|json_bad"
        else:
            o = outcome_tools(rec)
            if rec.get("http") not in (200, None):
                o += f" http={rec['http']}"
            if rec.get("api_failed"):
                o = "API_FAILED"
        summ[(k, m, t)][o] += 1
    out = {f"{k}|{m}|T={t}": dict(v) for (k, m, t), v in sorted(summ.items())}
    (RESULTS / "e01_probe_summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for k, v in out.items():
        print(k, v)

    # C4 determinism: same long resident prompt x5 at T=0
    rows = [json.loads(l) for l in (RESULTS / "sims" / "base70_s1.calls.jsonl").read_text(encoding="utf-8").splitlines()]
    prompt = next(r["prompt"] for r in rows if "Choose 1-3 events" in r["prompt"])
    det = {}
    for model in (M70, M8):
        outs = await asyncio.gather(*[gw.chat(prompt, model=model, json_mode=True, max_tokens=800, tag="determinism") for _ in range(5)])
        texts = [o["resp"]["content"] for o in outs]
        det[model] = {"distinct_outputs_of_5": len(set(texts)), "lengths": [len(t) for t in texts]}
    print("determinism", det)
    (RESULTS / "e01_determinism.json").write_text(json.dumps(det, indent=1), encoding="utf-8")
    await gw.close()


if __name__ == "__main__":
    asyncio.run(main())
