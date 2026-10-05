"""Spread across seeds: stance poll at start and end of every run of a group, as a table and a PNG.

`temperature 0` is not reproducible and personas are drawn per seed, so ONE run is an anecdote. This turns the runs of a group
(e.g. final_70_s1..5) into the distribution the paper and the demo should show.
Usage: python research/ensemble_report.py final_70 final_70_s1 final_70_s2 ...   -> docs/research/ensemble_<group>.{md,png}
"""
import json
import statistics as st
import sys

from common import ROOT, RESULTS

group, tags = sys.argv[1], sys.argv[2:]
FOR, UND, AGN = "#3E7C34", "#A89A78", "#B83A52"


def poll(npcs):
    xs = [float(n.get("stance", 0.0)) for n in npcs]
    return (sum(x > 0.15 for x in xs), sum(abs(x) <= 0.15 for x in xs), sum(x < -0.15 for x in xs))


runs = []
for t in tags:
    d = json.loads((RESULTS / "sims" / f"{t}.json").read_text(encoding="utf-8"))
    runs.append({"tag": t, "start": poll(d["npcs0"]), "end": poll(d["rounds"][-1]["npcs"]), "events": sum(len(r["events"]) for r in d["rounds"]),
                 "mean_end": st.mean(float(n.get("stance", 0.0)) for n in d["rounds"][-1]["npcs"])})
n = sum(runs[0]["start"])
md = [f"# Spread across seeds: {group}", "",
      f"{len(runs)} runs of the same town (Linden, {n} residents, 3 rounds); personas and the stance prior are drawn per seed, "
      "so the town differs from run to run. Stance poll shown as for / undecided / against.", "",
      "| run | start | end | mean stance at end | events |", "| --- | --- | --- | --- | --- |"]
for r in runs:
    md.append(f"| {r['tag']} | {r['start'][0]}/{r['start'][1]}/{r['start'][2]} | {r['end'][0]}/{r['end'][1]}/{r['end'][2]} | {r['mean_end']:+.2f} | {r['events']} |")
fs = [r["end"][0] / n for r in runs]
md += ["", f"Share *for* at the end: mean {st.mean(fs):.2f}, range {min(fs):.2f}–{max(fs):.2f}; share *against*: "
       f"mean {st.mean(r['end'][2] / n for r in runs):.2f}, range {min(r['end'][2] / n for r in runs):.2f}–{max(r['end'][2] / n for r in runs):.2f}. "
       "The range, not the mean, is the honest summary: one run says little.", "", f"![stance by seed](ensemble_{group}.png)", ""]
(ROOT / "docs" / "research" / f"ensemble_{group}.md").write_text("\n".join(md), encoding="utf-8")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # research-only dependency (not in the backend environment)

fig, ax = plt.subplots(figsize=(9, 1.0 + 0.62 * len(runs)))
for i, r in enumerate(runs):
    y = len(runs) - 1 - i
    for j, key in enumerate(("start", "end")):
        left = 0.0
        for val, col in zip(r[key], (FOR, UND, AGN)):
            if val:
                x0 = j * 1.25 + left
                ax.barh(y, val / n, left=x0, height=0.7, color=col, edgecolor="white")
                ax.text(x0 + val / n / 2, y, str(val), ha="center", va="center", color="white", fontweight="bold")
            left += val / n
ax.set_yticks(range(len(runs)), [r["tag"] for r in runs][::-1])
ax.set_xticks([0.5, 1.75], ["start (round 0)", "end (last round)"])
ax.set_xlim(-0.02, 2.27), ax.tick_params(axis="x", length=0)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.set_title(f"Stance poll by seed: {group} ({n} residents)", fontsize=11, fontweight="bold")
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (FOR, UND, AGN)]
ax.legend(handles, ["for", "undecided", "against"], ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12))
fig.savefig(ROOT / "docs" / "research" / f"ensemble_{group}.png", dpi=170, bbox_inches="tight", facecolor="white")
print(f"wrote docs/research/ensemble_{group}.md and .png for {len(runs)} runs")
