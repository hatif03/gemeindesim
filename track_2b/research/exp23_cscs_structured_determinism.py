"""E23: determinism and structured output on the app's REAL resident prompts, CSCS inference API.

Replays resident-turn prompts logged by the final runs on the hackathon gateway (research/results/sims/final_70_s*.calls.jsonl):
  J_json      as shipped (example in prompt, json_object), T=0, 3 repeats  -> distinct outputs per prompt (determinism), validity
  J_seed      same + seed=1, T=0, 3 repeats                               -> does `seed` make the 70B reproducible?
  S_schema    prompt without the example suffix + response_format json_schema (strict, NPCRoundResponse), T=0
  S_both      prompt with example + json_schema
Scored like E2b: strict-JSON, schema-valid, events, types, placeholder/`to_x=0` echo, language.

    . research/cscs_env.sh && uv run --project src/backend python research/exp23_cscs_structured_determinism.py [--n 24]
"""
import argparse
import asyncio
import json
import re
import statistics as st
from pathlib import Path

from common import M70, M8, RESULTS, Gateway
from exp02b_structured import SUFFIX, score
from graph.llm import _flatten_schema
from models.schemas import NPCRoundResponse

SIMS = Path(__file__).resolve().parent / "results" / "sims"
SCHEMA = _flatten_schema(NPCRoundResponse.model_json_schema())
RF = {"type": "json_schema", "json_schema": {"name": "round", "strict": True, "schema": SCHEMA}}


def prompts(n):
    out = []
    for f in sorted(SIMS.glob("final_70_s*.calls.jsonl")):
        for l in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            if "Choose 1-3 events" in r.get("prompt", ""):
                out.append(r["prompt"])
    step = max(1, len(out) // n)
    return out[::step][:n]


async def main(n):
    gw = Gateway("e23_structured_determinism", concurrency=8)
    ps = prompts(n)
    print("prompts", len(ps))
    jobs, keys = [], []
    for model in (M70, M8):
        for i, p in enumerate(ps):
            lang = re.search(r"Language: (\w\w)\.", p).group(1)
            base = SUFFIX.sub("", p)
            for rep in range(3):
                jobs.append(gw.chat(p, model=model, json_mode=True, max_tokens=1500, tag=f"J_json|{model}|{i}|{rep}"))
                keys.append(("J_json", model, i, rep, lang))
                jobs.append(gw.chat(p, model=model, json_mode=True, max_tokens=1500, seed=1, tag=f"J_seed|{model}|{i}|{rep}"))
                keys.append(("J_seed", model, i, rep, lang))
            jobs.append(gw.chat(base, model=model, max_tokens=1500, extra={"response_format": RF}, tag=f"S_schema|{model}|{i}"))
            keys.append(("S_schema", model, i, 0, lang))
            jobs.append(gw.chat(p, model=model, max_tokens=1500, extra={"response_format": RF}, tag=f"S_both|{model}|{i}"))
            keys.append(("S_both", model, i, 0, lang))
    recs = await asyncio.gather(*jobs)
    await gw.close()
    rows = []
    for (cond, model, i, rep, lang), rec in zip(keys, recs):
        c = rec["resp"]["content"]
        rows.append({"cond": cond, "model": model, "i": i, "rep": rep, "http": rec.get("http"), "content": c,
                     "lat": rec.get("latency_s"), **score(c, lang, "")})
    (RESULTS / "e23_structured_determinism.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("cond      model                       n    http200  strict  valid  events/turn  types/turn  to_x0_echo  placeholder  distinct/3 (mean)  all-3-identical")
    for cond in ("J_json", "J_seed", "S_schema", "S_both"):
        for model in (M70, M8):
            r = [x for x in rows if x["cond"] == cond and x["model"] == model]
            if not r:
                continue
            ok = [x for x in r if x["http"] == 200]
            val = [x for x in r if x["valid"]]
            det = ""
            if cond.startswith("J_"):
                groups = {}
                for x in r:
                    groups.setdefault(x["i"], []).append(x["content"])
                d = [len(set(v)) for v in groups.values()]
                det = f"{st.mean(d):.2f}              {sum(1 for v in d if v == 1)}/{len(d)}"
            print(f"{cond:9s} {model:27s} {len(r):3d}  {len(ok):3d}      {sum(x['strict_json'] for x in r):3d}     {len(val):3d}    "
                  f"{(st.mean(x['n_events'] for x in val) if val else 0):.2f}         {(st.mean(x['n_types'] for x in val) if val else 0):.2f}        "
                  f"{sum(x['xy_zero_echo'] for x in val):3d}         {sum(x['placeholder_echo'] for x in val):3d}         {det}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    asyncio.run(main(ap.parse_args().n))
