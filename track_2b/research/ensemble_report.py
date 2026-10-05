"""Spread across seeds: stance poll at start and end of every run of a group, as a table and an SVG.

`temperature 0` is not reproducible and personas are drawn per seed, so ONE run is an anecdote. This turns the runs of a group
(e.g. final_70_s1..5) into the distribution the paper and the demo should show.
Usage: python research/ensemble_report.py final_70 final_70_s1 final_70_s2 ...   -> docs/research/ensemble_<group>.{md,svg}
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
       "The range, not the mean, is the honest summary: one run says little.", "", f"![stance by seed](ensemble_{group}.svg)", ""]
(ROOT / "docs" / "research" / f"ensemble_{group}.md").write_text("\n".join(md), encoding="utf-8")

W, H, BAR, GAP, LEFT = 560, 34 + 52 * len(runs), 150, 16, 130
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial,sans-serif" font-size="11">',
       '<rect width="100%" height="100%" fill="#fff"/>',
       f'<text x="{LEFT}" y="16" font-weight="bold">start</text><text x="{LEFT + BAR + GAP + 20}" y="16" font-weight="bold">end</text>']
for i, r in enumerate(runs):
    y = 30 + 52 * i
    svg.append(f'<text x="4" y="{y + 18}">{r["tag"]}</text>')
    for j, key in enumerate(("start", "end")):
        x = LEFT + j * (BAR + GAP + 20)
        for val, col in zip(r[key], (FOR, UND, AGN)):
            w = BAR * val / n
            if w:
                svg.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="26" fill="{col}"/>')
                svg.append(f'<text x="{x + w / 2:.1f}" y="{y + 17}" text-anchor="middle" fill="#fff">{val}</text>')
            x += w
svg.append(f'<text x="4" y="{H - 6}" fill="{FOR}">for</text><text x="40" y="{H - 6}" fill="{UND}">undecided</text><text x="110" y="{H - 6}" fill="{AGN}">against</text>')
svg.append("</svg>")
(ROOT / "docs" / "research" / f"ensemble_{group}.svg").write_text("\n".join(svg), encoding="utf-8")
print(f"wrote docs/research/ensemble_{group}.md and .svg for {len(runs)} runs")
