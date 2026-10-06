"""Pool instrumented runs into baseline-vs-v2.1 comparison tables (markdown).

Usage: python research/summarize_sims.py
Groups are fixed below; run_sim.py/analyze_sims.py produced the inputs.
"""
import json
import sys
import statistics as st
from collections import Counter

from analyze_sims import score
from common import RESULTS

GROUPS = {
    "70B baseline": ["base70_s1", "base70_s2", "base70_s3"],
    "70B v2.1": ["v21_70_s1", "v21_70_s2", "v21_70_s3"],
    "8B baseline": ["base8_s1", "base8_s2"],
    "8B v2.1": ["v21_8_s1", "v21_8_s2"],
}
if "final" in sys.argv[1:]:  # final code: standard graph (5 seeds) and swarm graph, the Docker default (3 seeds)
    GROUPS = {
        "70B baseline (v1)": ["base70_s1", "base70_s2", "base70_s3"],
        "70B final": [f"final_70_s{i}" for i in range(1, 6)],
        "70B final, swarm": [f"final_sw70_s{i}" for i in range(1, 4)],
        "8B baseline (v1)": ["base8_s1", "base8_s2"],
        "8B final": [f"final_8_s{i}" for i in range(1, 6)],
        "8B final, swarm": [f"final_sw8_s{i}" for i in range(1, 4)],
    }
if "cscs" in sys.argv[1:]:  # run with RESEARCH_SUBDIR=cscs: the same final code on the CSCS inference API (research E23-E25)
    GROUPS = {
        "70B CSCS": [f"cscs70_s{i}" for i in range(1, 6)],
        "8B CSCS": [f"cscs8_s{i}" for i in range(1, 6)],
        "70B CSCS, 25 residents": ["cscs70_n25_s1"],
    }
NUM = [
    ("t_sim_s", "simulation wall time (s)"), ("calls", "LLM calls"), ("lat_mean", "mean call latency (s)"),
    ("events", "events"), ("chat_share", "chat share of events"), ("intro_rate", "chats that start with a self-introduction"),
    ("lang_ok", "utterance in resident's language"), ("eszett", "ß in generated Swiss-German text (count)"),
    ("cite_valid_rate", "cited ids that exist in the pack"), ("events_with_valid_cite", "events with ≥ 1 valid citation"),
    ("retrieval_question_chunk_rate", "ballot question present in resident prompt"),
]


def fmt(xs):
    return f"{st.mean(xs):.2f}" if len(xs) == 1 else f"{st.mean(xs):.2f} ({min(xs):.2f}–{max(xs):.2f})"


rows = {g: [score(t) for t in tags] for g, tags in GROUPS.items()}
print("| metric | " + " | ".join(GROUPS) + " |")
print("|---|" + "---|" * len(GROUPS))
for k, label in NUM:
    print(f"| {label} | " + " | ".join(fmt([r[k] for r in rows[g]]) for g in GROUPS) + " |")
for k, label in (("report_mixed_lang", "report mixes languages"), ("report_asserts_outcome", "report asserts the measure passed")):
    print(f"| {label} (runs) | " + " | ".join(f"{sum(bool(r[k]) for r in rows[g])}/{len(rows[g])}" for g in GROUPS) + " |")


def ev_types(g):
    c = Counter()
    for r in rows[g]:
        c.update(r["types"])
    n = len(rows[g])
    return ", ".join(f"{k} {v / n:.1f}" for k, v in sorted(c.items(), key=lambda x: -x[1]))


print("| event types per run (mean) | " + " | ".join(ev_types(g) for g in GROUPS) + " |")


def stance_row(g):
    out = []
    for r in rows[g]:
        a, b = r["stance_initial"], r["stance_final"]
        out.append(f"{a['for']}/{a['against']}/{a['undecided']}→{b['for']}/{b['against']}/{b['undecided']}")
    return "; ".join(out)


print("| stance for/against/undecided, initial→final (per run) | " + " | ".join(stance_row(g) for g in GROUPS) + " |")


def influence(g):
    c = Counter()
    for r in rows[g]:
        d = json.loads((RESULTS / "sims" / f"{r['tag']}.json").read_text(encoding="utf-8"))
        for rd in d["rounds"]:
            for i in rd.get("influence") or []:
                c[i["behavior"]] += 1
    return dict(c) or "none recorded"


print("| influence outcomes logged (all runs) | " + " | ".join(str(influence(g)) for g in GROUPS) + " |")
(RESULTS / "sims_comparison.json").write_text(json.dumps({g: rows[g] for g in GROUPS}, indent=1, default=str), encoding="utf-8")
