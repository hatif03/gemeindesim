"""E11: do generated personas differentiate stance on the Linden vote? Is random political_leaning predictive?

Residents = the real personas produced by the app (npcs0 of base70_s* runs). We elicit an explicit
stance (yes/no/undecided + certainty) under persona-ablation conditions, in the resident's language.
Conditions:  full | no_leaning (drop political leaning + MBTI) | role_only | none | full_T07 (3 samples)
Usage: python research/exp11_stance.py base70_s1 base70_s2 base70_s3
"""
import asyncio
import json
import math
import re
import sys
from collections import Counter

from common import M70, RESULTS, Gateway, read_sample

POLICY = {"de": read_sample("steuerfuss_linden_de.txt"), "fr": read_sample("steuerfuss_linden_fr.txt")}
LEAN = lambda x: ("stark progressiv" if x <= -0.6 else "eher progressiv" if x <= -0.2 else "moderat/zentristisch" if x <= 0.2 else "eher konservativ" if x <= 0.6 else "stark konservativ")


def persona_block(n, cond):
    if cond == "none":
        return ""
    if cond == "role_only":
        return f"Du bist {n['name']}, {n['profession']} in Linden. Einkommen: {n['income_level']}.\n"
    s = (f"Du bist {n['name']}, {n['profession']} in Linden. Einkommen: {n['income_level']}.\n"
         f"{n.get('bio','')}\nÜberzeugungen: {', '.join(n.get('beliefs', []))}\n")
    if cond != "no_leaning":
        s += f"Persönlichkeit {n.get('mbti','')}; politische Haltung: {LEAN(n.get('political_leaning', 0))}.\n"
    return s


def prompt(n, cond):
    lang = n["lang"] if n["lang"] in POLICY else "de"
    head = persona_block(n, cond)
    if lang == "fr":
        return (f"{head}\nTu habites à Linden et tu votes sur l'objet suivant.\n{POLICY['fr']}\n"
                'Comment votes-tu ? Réponds uniquement en JSON : {"stance": "yes" | "no" | "undecided", "certainty": 0.0-1.0, "reason": "une phrase en français"}')
    return (f"{head}\nDu wohnst in Linden und stimmst über die folgende Vorlage ab.\n{POLICY['de']}\n"
            'Wie stimmst du? Antworte nur mit JSON: {"stance": "yes" | "no" | "undecided", "certainty": 0.0-1.0, "reason": "ein Satz auf Deutsch"}')


def entropy(c):
    t = sum(c.values())
    return -sum(v / t * math.log2(v / t) for v in c.values() if v) if t else 0


async def main(tags):
    gw = Gateway("e11_stance", concurrency=3)
    npcs = []
    for t in tags:
        d = json.loads((RESULTS / "sims" / f"{t}.json").read_text(encoding="utf-8"))
        npcs += [dict(n, src=t) for n in d["npcs0"]]
    print("residents", len(npcs))

    async def one(n, cond, temp, k):
        rec = await gw.chat(prompt(n, cond), model=M70, temperature=temp, max_tokens=150, json_mode=True, tag=f"{n['src']}|{n['id']}|{cond}|{k}")
        m = re.search(r'"stance"\s*:\s*"(yes|no|undecided)"', rec["resp"]["content"])
        c = re.search(r'"certainty"\s*:\s*([0-9.]+)', rec["resp"]["content"])
        return {"src": n["src"], "id": n["id"], "role": n["role"], "lang": n["lang"], "lean": n.get("political_leaning"),
                "income": n.get("income_level"), "cond": cond, "k": k, "stance": m.group(1) if m else None,
                "certainty": float(c.group(1)) if c else None, "reason": rec["resp"]["content"][-200:]}

    jobs = [one(n, c, 0.0, 0) for n in npcs for c in ("full", "no_leaning", "role_only", "none")]
    jobs += [one(n, "full", 0.7, k) for n in npcs for k in (1, 2, 3)]
    res = await asyncio.gather(*jobs)
    await gw.close()
    (RESULTS / "e11_stance.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for cond in ("full", "no_leaning", "role_only", "none"):
        r = [x for x in res if x["cond"] == cond and x["k"] == 0]
        cnt = Counter(x["stance"] for x in r)
        print(f"{cond:11s} n={len(r)} {dict(cnt)} entropy={entropy(cnt):.2f} bits  mean certainty={sum(x['certainty'] or 0 for x in r)/len(r):.2f}")
    full = {(x["src"], x["id"]): x["stance"] for x in res if x["cond"] == "full" and x["k"] == 0}
    for cond in ("no_leaning", "role_only", "none"):
        agree = [full[(x["src"], x["id"])] == x["stance"] for x in res if x["cond"] == cond and x["k"] == 0]
        print(f"agreement full vs {cond}: {sum(agree)/len(agree):.2f}")
    # sampling stability at T=0.7
    byres = {}
    for x in res:
        if x["cond"] == "full":
            byres.setdefault((x["src"], x["id"]), []).append(x["stance"])
    stable = sum(len(set(v)) == 1 for v in byres.values()) / len(byres)
    print(f"stance identical across 4 draws (T=0 + 3x T=0.7): {stable:.2f}")
    # leaning vs stance
    import statistics as st
    for s in ("yes", "no", "undecided"):
        ls = [x["lean"] for x in res if x["cond"] == "full" and x["k"] == 0 and x["stance"] == s and x["lean"] is not None]
        if ls:
            print(f"mean political_leaning of residents saying {s}: {st.mean(ls):+.2f} (n={len(ls)})")
    print("by role (full):", {r: dict(Counter(x['stance'] for x in res if x['cond'] == 'full' and x['k'] == 0 and x['role'] == r)) for r in sorted({x['role'] for x in res})})


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
