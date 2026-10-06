"""E24: is the yes-bias a property of the weights or of the deployment? Direct stance elicitation (E11 design) on every Apertus v1.5 model
the CSCS key can use, including the separate `-thinking` models, plus a logprob view the hackathon gateway never gave us.

Residents = the 15 personas of the final 70B runs (final_70_s1..3 npcs0), Linden vote, full persona and no persona, T=0.
  plain       yes / no / undecided as JSON (json_object where the model allows it)
  logprob     one-word answer; probability mass on yes / no / undecided from the first token's top-20 logprobs
Raw calls: research/results/cscs/e24_stance_models.jsonl.

    . research/cscs_env.sh && uv run --project src/backend python research/exp24_cscs_stance_models.py
"""
import asyncio
import json
import math
import re
import statistics as st
from collections import Counter
from pathlib import Path

import httpx

from common import BASE, KEY, RESULTS
from exp11_stance import POLICY, persona_block, prompt

SIMS = Path(__file__).resolve().parent / "results" / "sims"
MODELS = ["swiss-ai/Apertus-v1.5-70B", "swiss-ai/Apertus-v1.5-8B", "swiss-ai/Apertus-v1.5-70B-thinking", "swiss-ai/Apertus-v1.5-8B-thinking"]
H = {"Authorization": f"Bearer {KEY}"}
SEMS: dict[str, asyncio.Semaphore] = {}  # the 8B-thinking deployment answered 504 above ~2 requests in flight (E21t)
LOG = RESULTS / "e24_stance_models.jsonl"


async def call(client, body, tag):
    for attempt in range(6):
        sem = SEMS.setdefault(body["model"], asyncio.Semaphore(2 if body["model"].endswith("8B-thinking") else 8))
        async with sem:
            r = await client.post(f"{BASE}/chat/completions", json=body, headers=H)
        j = r.json()
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"tag": tag, "attempt": attempt, "http": r.status_code, "req": body, "resp": j}, ensure_ascii=False) + "\n")
        if r.status_code not in (429, 500, 502, 503, 504):
            break
        await asyncio.sleep(min(30, 3 * 2**attempt))
    return j


def content_of(j):
    m = ((j.get("choices") or [{}])[0].get("message")) or {}
    c = m.get("content") or ""
    return c.split("<|inner_suffix|>")[-1], bool(m.get("reasoning")), j.get("usage", {}).get("completion_tokens", 0)


def one_word_prompt(n, cond):
    lang = n["lang"] if n["lang"] in POLICY else "de"
    head = persona_block(n, cond)
    if lang == "fr":
        return (f"{head}\nTu habites à Linden et tu votes sur l'objet suivant.\n{POLICY['fr']}\n"
                "Comment votes-tu ? Réponds par UN SEUL mot : yes, no ou undecided.")
    return (f"{head}\nDu wohnst in Linden und stimmst über die folgende Vorlage ab.\n{POLICY['de']}\n"
            "Wie stimmst du? Antworte mit EINEM Wort: yes, no oder undecided.")


async def main():
    npcs = []
    for t in ("final_70_s1", "final_70_s2", "final_70_s3"):
        d = json.loads((SIMS / f"{t}.json").read_text(encoding="utf-8"))
        npcs += [dict(n, src=t) for n in d["npcs0"]]
    out = []
    async with httpx.AsyncClient(timeout=300, trust_env=False) as client:
        async def plain(model, n, cond):
            think = model.endswith("-thinking")
            body = {"model": model, "temperature": 0, "max_tokens": 2500 if think else 150, "messages": [{"role": "user", "content": prompt(n, cond)}],
                    "response_format": {"type": "json_object"}}
            j = await call(client, body, f"plain|{model}|{n['src']}|{n['id']}|{cond}")
            c, had_reasoning, tok = content_of(j)
            m = re.search(r'"stance"\s*:\s*"(yes|no|undecided)"', c)
            return {"kind": "plain", "model": model, "cond": cond, "src": n["src"], "id": n["id"], "lean": n.get("political_leaning"),
                    "income": n.get("income_level"), "stance": m.group(1) if m else None, "reasoning_field": had_reasoning, "tokens": tok}

        async def lp(model, n, cond):
            body = {"model": model, "temperature": 0, "max_tokens": 4, "logprobs": True, "top_logprobs": 20,
                    "messages": [{"role": "user", "content": one_word_prompt(n, cond)}]}
            j = await call(client, body, f"lp|{model}|{n['src']}|{n['id']}|{cond}")
            ch = (j.get("choices") or [{}])[0]
            toks = ((ch.get("logprobs") or {}).get("content") or [{}])[0].get("top_logprobs") or []
            mass = {"yes": 0.0, "no": 0.0, "undecided": 0.0}
            for t in toks:
                w = t["token"].strip().lower()
                k = "yes" if w == "yes" else "no" if w == "no" else "undecided" if w.startswith("und") else None
                if k:
                    mass[k] += math.exp(t["logprob"])
            tot = sum(mass.values())
            return {"kind": "lp", "model": model, "cond": cond, "src": n["src"], "id": n["id"], "lean": n.get("political_leaning"),
                    "income": n.get("income_level"), "mass_total": round(tot, 3),
                    "p": {k: round(v / tot, 3) for k, v in mass.items()} if tot > 0.5 else None,
                    "first": (ch.get("message") or {}).get("content", "")[:20]}

        jobs = [plain(m, n, c) for m in MODELS for n in npcs for c in ("full", "none")]
        jobs += [lp(m, n, c) for m in MODELS[:2] for n in npcs for c in ("full", "none")]
        out = await asyncio.gather(*jobs)
    (RESULTS / "e24_stance_models.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("model                                   cond   n   yes/no/undecided/none    reasoning_field  mean tokens")
    for m in MODELS:
        for cond in ("full", "none"):
            r = [x for x in out if x["kind"] == "plain" and x["model"] == m and x["cond"] == cond]
            c = Counter(x["stance"] for x in r)
            print(f"{m:38s} {cond:5s} {len(r):3d}   {c.get('yes', 0)}/{c.get('no', 0)}/{c.get('undecided', 0)}/{c.get(None, 0)}                "
                  f"{sum(x['reasoning_field'] for x in r):3d}              {st.mean(x['tokens'] for x in r):.0f}")
    print("\nlogprob view: mean P(yes), P(no), P(undecided) over residents; spread of P(yes) (min..max); corr(P(yes), leaning)")
    for m in MODELS[:2]:
        for cond in ("full", "none"):
            r = [x for x in out if x["kind"] == "lp" and x["model"] == m and x["cond"] == cond and x["p"]]
            if not r:
                print(m, cond, "no usable logprobs")
                continue
            py = [x["p"]["yes"] for x in r]
            lean = [x["lean"] for x in r]
            if len(set(lean)) > 1 and len(set(py)) > 1:
                mx, my = st.mean(lean), st.mean(py)
                corr = sum((a - mx) * (b - my) for a, b in zip(lean, py)) / math.sqrt(sum((a - mx) ** 2 for a in lean) * sum((b - my) ** 2 for b in py))
            else:
                corr = float("nan")
            print(f"{m:30s} {cond:5s} n={len(r)} P(yes)={st.mean(py):.3f} P(no)={st.mean(x['p']['no'] for x in r):.3f} "
                  f"P(undec)={st.mean(x['p']['undecided'] for x in r):.3f}  P(yes) {min(py):.2f}..{max(py):.2f}  corr with leaning {corr:+.2f}")


if __name__ == "__main__":
    asyncio.run(main())
