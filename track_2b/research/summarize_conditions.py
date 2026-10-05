"""E19 summary: stance poll under different input conditions, paired by seed.

Runs are named cond_<condition>_s<seed> (see the chain in docs/research/LAB-NOTEBOOK.md). For every condition: mean stance at the
start and end, the share of residents for / against at the end, and the paired difference to the 'asis' condition (same seed =
same random attributes, so differences are not just different draws; the LLM text still differs, hence the spread).
Usage: python research/summarize_conditions.py asis rec_yes rec_no balanced   (seeds are discovered from the files)
"""
import json
import statistics as st
import sys

from common import RESULTS

conds = sys.argv[1:]


def load(c):
    out = {}
    for p in sorted((RESULTS / "sims").glob(f"cond_{c}_s*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        s0 = [float(n.get("stance", 0)) for n in d["npcs0"]]
        s1 = [float(n.get("stance", 0)) for n in d["rounds"][-1]["npcs"]]
        out[int(p.stem.rsplit("_s", 1)[1])] = {"start": st.mean(s0), "end": st.mean(s1), "for": sum(x > .15 for x in s1) / len(s1),
                                               "against": sum(x < -.15 for x in s1) / len(s1)}
    return out


data = {c: load(c) for c in conds}
base = data[conds[0]]
print(f"| condition | n runs | mean stance start | mean stance end | share for (end) | share against (end) | paired Δ start vs {conds[0]} | paired Δ end vs {conds[0]} |")
print("| --- | --- | --- | --- | --- | --- | --- | --- |")
for c in conds:
    d = data[c]
    seeds = sorted(set(d) & set(base))
    ds = [d[s]["start"] - base[s]["start"] for s in seeds]
    de = [d[s]["end"] - base[s]["end"] for s in seeds]
    f = lambda xs: f"{st.mean(xs):+.2f} ({min(xs):+.2f}..{max(xs):+.2f})" if xs and c != conds[0] else "–"
    print(f"| {c} | {len(d)} | {st.mean(v['start'] for v in d.values()):+.2f} | {st.mean(v['end'] for v in d.values()):+.2f} | "
          f"{st.mean(v['for'] for v in d.values()):.2f} | {st.mean(v['against'] for v in d.values()):.2f} | {f(ds)} | {f(de)} |")
