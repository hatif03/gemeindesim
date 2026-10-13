"""Two extra figures for report/report.html (matplotlib only).

    python research/make_report_figures.py

fig09: the recorded demo run (docs/replays/linden_25x5_cscs.replay.json): stance poll and influence outcomes per round.
fig10: where the time goes (numbers from docs/research/LAB-NOTEBOOK.md, E29): latency by call class and the share of Python.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "figures"
FOR, UND, AGN = "#3E7C34", "#A89A78", "#B83A52"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

# ---------------------------------------------------------------- fig09
rep = json.loads((ROOT / "docs/replays/linden_25x5_cscs.replay.json").read_text(encoding="utf-8"))
cfg = json.loads((ROOT / "docs/replays/linden_25x5_cscs.config.json").read_text(encoding="utf-8"))
m = cfg["metrics"]


def tally(npcs):
    f = sum(1 for n in npcs if n["stance"] > 0.15)
    a = sum(1 for n in npcs if n["stance"] < -0.15)
    return f, len(npcs) - f - a, a


rows = [tally(rep["initMsg"]["npcs"])] + [tally(r["npcs"]) for r in rep["rounds"]]
labels = ["start"] + [f"round {r['round'] + 1}" for r in rep["rounds"]]
beh = [{"keep": 0, "compromise": 0, "adopt": 0} for _ in rep["rounds"]]
for i, r in enumerate(rep["rounds"]):
    for e in r.get("influence_events") or []:
        beh[i][e["behavior"]] += 1

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 3.9), gridspec_kw={"width_ratios": [1.25, 1]})
x = range(len(rows))
a1.bar(x, [r[0] for r in rows], color=FOR, label="for")
a1.bar(x, [r[1] for r in rows], bottom=[r[0] for r in rows], color=UND, label="undecided")
a1.bar(x, [r[2] for r in rows], bottom=[r[0] + r[1] for r in rows], color=AGN, label="against")
a1.set_xticks(list(x), labels), a1.set_ylabel("residents (n = 25)")
a1.set_title("Stance poll per round (code-owned stance)", fontweight="bold", fontsize=10.5)
a1.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
for s in ("top", "right"):
    a1.spines[s].set_visible(False)
ks = ["keep", "compromise", "adopt"]
cols = ["#B5B1A4", "#6F9BC9", "#3B6EA5"]
bottom = [0] * len(beh)
for k, c in zip(ks, cols):
    vals = [b[k] for b in beh]
    a2.bar(range(1, len(beh) + 1), vals, bottom=bottom, color=c, label=k)
    bottom = [b + v for b, v in zip(bottom, vals)]
a2.set_xlabel("round"), a2.set_ylabel("influence events (speaker to listener)")
a2.set_title("Opinion dynamics outcomes (Deffuant, in code)", fontweight="bold", fontsize=10.5)
a2.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
for s in ("top", "right"):
    a2.spines[s].set_visible(False)
fig.suptitle(f"Recorded demo run: 25 residents, {len(rep['rounds'])} rounds, CSCS, Apertus 70B: {m['calls']} calls, "
             f"{m['prompt_tokens'] / 1000:.0f} k tokens in, {m['completion_tokens'] / 1000:.0f} k out, {cfg['wall_s']:.0f} s, "
             f"{m['rate_limited']} retries, {m['failed']} failed", fontsize=10, y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig09-demo-run.png", dpi=170, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------- fig10 (E29, 70B, mean latency per call class, seconds)
classes = [("persona text", 14.2), ("resident turn", 8.1), ("reflection", 3.6), ("impact judgement", 2.1), ("translation", 1.7)]
fig, (b1, b2) = plt.subplots(1, 2, figsize=(11.5, 3.2), gridspec_kw={"width_ratios": [1.3, 1]})
b1.barh([c for c, _ in classes][::-1], [v for _, v in classes][::-1], color="#3B6EA5")
for i, (c, v) in enumerate(classes[::-1]):
    b1.text(v + 0.2, i, f"{v} s", va="center", fontsize=9)
b1.set_xlabel("mean latency per call, 70B on CSCS (E29)")
b1.set_title("Where a call's time goes: output tokens", fontweight="bold", fontsize=10.5)
b1.set_xlim(0, 17)
for s in ("top", "right"):
    b1.spines[s].set_visible(False)
b2.bar(["70B\n(60.5 s wall)", "8B\n(26.1 s wall)"], [2.2, 5.0], color=["#3E7C34", "#3E7C34"])
for i, v in enumerate([2.2, 5.0]):
    b2.text(i, v + 0.15, f"{v} %", ha="center", fontsize=9.5)
b2.set_ylim(0, 8), b2.set_ylabel("process CPU share of wall time (%)")
b2.set_title("Python is not the bottleneck", fontweight="bold", fontsize=10.5)
for s in ("top", "right"):
    b2.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig10-time-budget.png", dpi=170, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote fig09-demo-run.png fig10-time-budget.png")
