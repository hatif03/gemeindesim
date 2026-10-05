"""E11b: does the v2 stance initialisation restore diversity? (follow-up to E11, where 15/15 said yes)

Runs the REAL v2 `elicit_impact` on the 15 baseline residents (70B-generated personas), then
computes the code-owned stance prior under several ideological valences of the measure.
Reports: impact distribution, by role/income, and stance split / entropy / spread.
Usage: python research/exp11b_impact.py base70_s1 base70_s2 base70_s3
"""
import asyncio
import json
import random
import sys
from collections import Counter

from common import RESULTS, read_sample

from graph.corpus import chunk_policy_document
from graph.llm import get_llm
from graph.nodes.stance import elicit_impact, stance_prior, stance_summary

NOTES = "--- Author notes / pasted text ---\n" + read_sample("steuerfuss_linden_de.txt").strip() + "\n\n" + read_sample("steuerfuss_linden_fr.txt").strip()


async def main(tags):
    npcs = []
    for t in tags:
        npcs += [dict(n, src=t) for n in json.loads((RESULTS / "sims" / f"{t}.json").read_text(encoding="utf-8"))["npcs0"]]
    chunks = chunk_policy_document(NOTES)
    llm = get_llm(max_tokens=400)
    imp = await asyncio.gather(*[elicit_impact(n, chunks, "Linden", llm) for n in npcs])
    out = {"impacts": [], "by_valence": {}}
    for n, r in zip(npcs, imp):
        out["impacts"].append({"src": n["src"], "id": n["id"], "role": n["role"], "income": n["income_level"], "lang": n["lang"],
                               "lean": n["political_leaning"], "impact": r.impact, "support": r.support_reason, "oppose": r.oppose_reason})
    print("impact overall:", dict(Counter(x["impact"] for x in out["impacts"])))
    print("by role  :", {role: dict(Counter(x["impact"] for x in out["impacts"] if x["role"] == role)) for role in sorted({x["role"] for x in out["impacts"]})})
    print("by income:", {i: dict(Counter(x["impact"] for x in out["impacts"] if x["income"] == i)) for i in ("low", "medium", "high")})
    for v in (-0.8, -0.4, 0.0, 0.4):
        rng = random.Random(7)
        ss = [{"stance": stance_prior(v, x["lean"], x["impact"], rng)} for x in out["impacts"]]
        out["by_valence"][str(v)] = stance_summary(ss)
        print(f"valence {v:+.1f}:", out["by_valence"][str(v)])
    (RESULTS / "e11b_impact.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in out["impacts"][:4]:
        print("  e.g.", x["role"], x["income"], x["impact"], "| +", x["support"][:90], "| -", x["oppose"][:90])


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
