"""Draws the diagrams and charts used by docs/MENTOR-BRIEF.md and docs/ARCHITECTURE.md as PNGs (render everywhere, no viewer quirks).

    python research/make_figures.py        # needs matplotlib (research-only; not a backend dependency)

Numbers are copied from docs/research/03-results.md, which is computed from research/results/.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

MODEL, CODE, USER, CHECK = "#DCE8F5", "#DDEBD3", "#F3E9CE", "#F5D9D3"
EDGE = {MODEL: "#3B6EA5", CODE: "#3E7C34", USER: "#A0824A", CHECK: "#B83A52"}
FOR, UND, AGN = "#3E7C34", "#A89A78", "#B83A52"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def box(ax, x, y, w, h, title, body="", kind=CODE, fs=9.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=kind, ec=EDGE[kind], lw=1.6))
    ax.text(x + w / 2, y + h - 0.16, title, ha="center", va="top", fontsize=fs + 0.5, fontweight="bold")
    if body:
        ax.text(x + w / 2, y + h - 0.52, body, ha="center", va="top", fontsize=fs - 1.2, linespacing=1.35)


def arrow(ax, p, q, text="", rad=0.0, color="#555"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, lw=1.4, color=color, connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.12, text, ha="center", fontsize=8, color=color)


def legend(ax, y):
    items = [(USER, "user input"), (MODEL, "Apertus (model voices)"), (CODE, "code owns"), (CHECK, "code check / guardrail")]
    x = 0.4
    for kind, label in items:
        ax.add_patch(FancyBboxPatch((x, y), 0.35, 0.22, boxstyle="round,pad=0.01", fc=kind, ec=EDGE[kind], lw=1.4))
        ax.text(x + 0.5, y + 0.11, label, va="center", fontsize=9)
        x += 3.3


# ---------------------------------------------------------------- figure 1: pipeline
def fig_pipeline():
    fig, ax = plt.subplots(figsize=(17, 10.5))
    ax.set_xlim(0, 17), ax.set_ylim(0, 10.5), ax.axis("off")
    ax.text(0.3, 10.2, "GemeindeSim end to end: the model voices, code owns stance, arithmetic and sources", fontsize=15, fontweight="bold", va="top")
    legend(ax, 9.45)

    ax.text(0.3, 9.1, "1  SET-UP (once per run)", fontsize=11, fontweight="bold", color="#5B3A1E")
    w, h, y = 3.0, 1.75, 7.1
    box(ax, 0.3, y, w, h, "Vote text", "DE / FR / EN\npasted or PDF\n(Abstimmungsbüchlein)", USER)
    box(ax, 3.7, y, w, h, "Index (code)", "sentence chunks, language\nper chunk, BM25 search,\nballot question pinned", CODE)
    box(ax, 7.1, y, w, h, "Parse policy", "summary, who is affected,\nideological valence of\nthe question (one number)", MODEL)
    box(ax, 10.5, y, w, h, "Residents", "code draws name, role, income,\nleaning, DE/FR; model writes\nthe persona text", CODE)
    box(ax, 13.9, y, 2.8, h, "Stance (code)", "valence·leaning\n+ 0.5·judged impact\n− 0.6·household cost", CODE)
    for a, b in [(3.3, 3.7), (6.7, 7.1), (10.1, 10.5), (13.5, 13.9)]:
        arrow(ax, (a, y + h / 2), (b, y + h / 2))
    ax.text(15.3, 6.62, "model only judges impact and writes\nthe best argument for / against", ha="center", fontsize=8, color=EDGE[MODEL])

    ax.text(0.3, 6.45, "2  EVERY ROUND, FOR EVERY RESIDENT (≤ 4 requests in flight)", fontsize=11, fontweight="bold", color="#5B3A1E")
    y2, h2, w2 = 4.35, 1.85, 2.6
    box(ax, 0.3, y2, w2, h2, "Retrieve (code)", "passages in the resident's\nlanguage → labels [P1]…\n+ personal CHF figure", CODE)
    box(ax, 3.2, y2, w2, h2, "Prompt (code)", "persona, memories, pack,\n'your position: for/against',\nlast-paragraph speech binding", CODE)
    box(ax, 6.1, y2, w2, h2, "ONE completion", "Apertus, JSON mode,\nthinking off, one language,\n1–3 events", MODEL)
    box(ax, 9.0, y2, w2, h2, "Checks (code)", "citations must exist · numbers\nnot in the pack stripped ·\nSwiss spelling (no ß)", CHECK)
    box(ax, 11.9, y2, w2, h2, "Dynamics (code)", "who talked to whom: keep /\ncompromise / adopt (Deffuant)\nonly for residents who chatted", CODE)
    box(ax, 14.8, y2, 1.9, h2, "Poll", "for / undecided /\nagainst +\nindicators", CODE)
    for a in (2.9, 5.8, 8.7, 11.6, 14.5):
        arrow(ax, (a, y2 + h2 / 2), (a + 0.3, y2 + h2 / 2))
    ax.text(8.3, 3.95, "repeat for each round (3 by default): new memories, new stance, same loop; after the last round the report is written", fontsize=8.5, color="#555", ha="center")

    ax.text(0.3, 3.55, "3  END OF RUN AND SCREEN", fontsize=11, fontweight="bold", color="#5B3A1E")
    y3, h3 = 1.35, 1.75
    box(ax, 0.3, y3, 3.6, h3, "Report", "Apertus writes it in the residents'\nlanguage from the events and the\nstance summary", MODEL)
    box(ax, 4.4, y3, 3.8, h3, "Report guardrails (code)", "no asserted outcome, no vote advice,\nlocal disclaimer, Swiss spelling\n(0/30 outcomes in the final runs)", CHECK)
    box(ax, 8.7, y3, 8.0, h3, "UI (Next.js + Phaser)", "town map and resident profiles (stance + reason) · stance poll with start → now ·\nevent feed with citation chips that open the passage · report modal", USER)
    arrow(ax, (3.9, y3 + h3 / 2), (4.4, y3 + h3 / 2))
    arrow(ax, (8.2, y3 + h3 / 2), (8.7, y3 + h3 / 2))
    ax.text(0.3, 0.55, "Not covered by this pipeline: the 1:1 chat with a resident (graph/chat.py) uses memories only — no stance, retrieval, number gate or spelling pass yet.",
            fontsize=9, color=EDGE[CHECK])
    fig.savefig(OUT / "fig01-pipeline.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- figure 2: stance
def fig_stance():
    fig, ax = plt.subplots(figsize=(16, 7.4))
    ax.set_xlim(0, 16), ax.set_ylim(0, 7.4), ax.axis("off")
    ax.text(0.3, 7.15, "Where a resident's stance comes from, and how it moves", fontsize=15, fontweight="bold", va="top")
    rows = [
        (5.3, "Ideology", "valence of the question × the resident's left-right leaning   (weight 1.0)", CODE),
        (4.0, "Judged impact", "model: benefit / mixed / harm for this household\n(+1 / 0 / -1)   (weight 0.5)", MODEL),
        (2.7, "Household cost", "calculator: booklet worked example × income band 0.6 / 1.0 / 1.8\nsaturates at 500 CHF a year   (weight -0.6)", CODE),
        (1.4, "Noise", "Gaussian, sd 0.15   (a knob, not calibrated)", CODE),
    ]
    for y, t, bd, k in rows:
        box(ax, 0.3, y, 5.6, 1.05, t, bd, k, fs=9.5)
        arrow(ax, (5.9, y + 0.52), (6.6, 3.7))
    box(ax, 6.6, 2.5, 3.0, 2.4, "Initial stance", "clamp(sum, -1, +1)\n\n> +0.15  for\n< -0.15  against\notherwise undecided", CODE)
    box(ax, 10.3, 5.2, 5.4, 1.4, "Each round: who spoke to whom", "influence I of speaker on listener, from\nreputation and closeness (relationship map)", CODE)
    box(ax, 10.3, 0.9, 5.4, 3.9, "Update of the listener's stance",
        "I < 0.25 : keep (no change)\n\n0.25 <= I < 0.85 : compromise (Deffuant)\n   s_j <- s_j + 0.3 * I * (s_i - s_j)\n   only if |s_i - s_j| < 0.7\n\nI >= 0.85 : adopt the speaker's stance\n\n+ controversy push 0.05 * tanh(alpha * x)\nOnly residents who actually conversed move.", CODE, fs=9.5)
    arrow(ax, (9.6, 3.7), (10.3, 3.2))
    arrow(ax, (13.0, 5.2), (13.0, 4.8))
    ax.text(0.3, 0.75, 'The model never reports a stance: asked directly it said "yes" for all 15 residents (E11).', fontsize=9.5, color=EDGE[CHECK])
    ax.text(0.3, 0.35, "The weights 1.0 / 0.5 / 0.6, the noise and the thresholds are assumptions, not calibrated.", fontsize=9.5, color=EDGE[CHECK])
    fig.savefig(OUT / "fig02-stance.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- charts
def fig_speech():
    fig, ax = plt.subplots(figsize=(8.5, 4.3))
    labels = ["v2.1\n(stance line only)", "v2.2\n(+ last-paragraph\nbinding)", "final code"]
    seventy, eight = [0.50, 0.80, 0.91], [0.51, 0.745, 0.87]
    xs = range(3)
    ax.bar([x - 0.2 for x in xs], seventy, 0.4, label="Apertus 70B", color="#3B6EA5")
    ax.bar([x + 0.2 for x in xs], eight, 0.4, label="Apertus 8B", color="#9BB7D4")
    for x, a, b, ta, tb in zip(xs, seventy, eight, ["0.46–0.55", "0.80", "0.91"], ["0.50–0.52", "0.73–0.76", "0.87"]):
        ax.text(x - 0.2, a + 0.02, ta, ha="center", fontsize=9), ax.text(x + 0.2, b + 0.02, tb, ha="center", fontsize=9)
    ax.set_xticks(list(xs), labels), ax.set_ylim(0, 1.08), ax.set_ylabel("share of lines whose position\nmatches the code-owned stance")
    ax.set_title("Binding speech to stance (E14–E15, final measurement 5 seeds)", fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", frameon=False), ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT / "fig03-speech-matches-stance.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_yesbias():
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    names = ["real Swiss votes\n(54, mean)", "70B persona-less\n(DE prompt)", "70B persona-less\n(FR prompt)", "8B persona-less\n(DE prompt)", "8B persona-less\n(FR prompt)"]
    vals = [46.5, 83, 65, 70, 67]
    cols = ["#444444", "#3B6EA5", "#3B6EA5", "#9BB7D4", "#9BB7D4"]
    ax.barh(names[::-1], vals[::-1], color=cols[::-1])
    for i, v in enumerate(vals[::-1]):
        ax.text(v + 1, i, f"{v:g} %", va="center", fontsize=10)
    ax.axvline(46.5, color="#444", ls="--", lw=1)
    ax.set_xlim(0, 100), ax.set_xlabel("mean yes-share given only ballot title and date")
    ax.set_title("Yes-bias: the simulated electorate says yes far more than Swiss voters (E8)", fontsize=11, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT / "fig04-yes-bias.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_signal():
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    names = ["70B\nwith personas", "8B\nwith personas", "70B, no persona,\nwith Federal\nCouncil line", "8B, no persona,\nwith Federal\nCouncil line", "Federal Council\nposition alone\n(no model)"]
    de = [0.25, -0.02, 0.47, 0.67, 0.63]
    fr = [0.38, 0.02, 0.54, 0.56, 0.63]
    xs = range(5)
    ax.bar([x - 0.2 for x in xs], de, 0.4, label="German prompt", color="#3B6EA5")
    ax.bar([x + 0.2 for x in xs], fr, 0.4, label="French prompt", color="#9BB7D4")
    ax.bar([4 - 0.2, 4 + 0.2], [0.63, 0.63], 0.4, color="#444")
    for x, a, b in zip(xs, de, fr):
        ax.text(x - 0.2, max(a, 0) + 0.015, f"{a:.2f}", ha="center", fontsize=8.5), ax.text(x + 0.2, max(b, 0) + 0.015, f"{b:.2f}", ha="center", fontsize=8.5)
    ax.set_xticks(list(xs), names, fontsize=8.5), ax.set_ylabel("Spearman with real yes-share\n(54 federal votes)")
    ax.set_title("Personas add little signal; the Federal Council line alone (0.63) is as good as the best condition (E8)", fontsize=10.5, fontweight="bold")
    ax.legend(frameon=False, loc="upper left"), ax.spines[["top", "right"]].set_visible(False), ax.set_ylim(-0.08, 0.8)
    fig.savefig(OUT / "fig05-real-votes-signal.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_throughput():
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
    n = [1, 2, 4, 5, 6, 8]
    ok70 = [6 / 6, 6 / 6, 8 / 8, 4 / 10, 5 / 12, 5 / 16]
    ok8 = [6 / 6, 6 / 6, 8 / 8, 4 / 10, 4 / 12, 4 / 16]
    a.plot(n, ok70, "o-", color="#3B6EA5", label="70B"), a.plot(n, ok8, "s--", color="#9BB7D4", label="8B")
    a.axvline(4, color="#B83A52", lw=1, ls=":"), a.text(4.1, 0.08, "app default now: 4\n(was 6)", color="#B83A52", fontsize=8.5)
    a.set_ylim(0, 1.08), a.set_xlabel("requests in flight"), a.set_ylabel("share of requests answered (not 429)")
    a.set_title("Rate limit: 4 in flight is the ceiling", fontsize=10.5, fontweight="bold"), a.legend(frameon=False)
    b.plot([1, 2, 4], [40, 75, 156], "o-", color="#3B6EA5", label="70B"), b.plot([1, 2, 4], [158, 292, 555], "s--", color="#9BB7D4", label="8B")
    b.set_xlabel("requests in flight"), b.set_ylabel("aggregate tokens / second"), b.set_xticks([1, 2, 4])
    b.set_title("Throughput (idle key)", fontsize=10.5, fontweight="bold"), b.legend(frameon=False)
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT / "fig06-throughput.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_fixes():
    fig, ax = plt.subplots(figsize=(9, 4.4))
    names = ["cited ids that\nexist", "ballot question\nin the prompt", "reports that\nassert 'passed'", "speech matches\ncode stance"]
    before, after = [0.0, 0.13, 0.67, 0.50], [1.0, 1.0, 0.0, 0.91]
    xs = range(4)
    ax.bar([x - 0.2 for x in xs], before, 0.4, label="before (original code; speech column: v2.1)", color="#B8B0A0")
    ax.bar([x + 0.2 for x in xs], after, 0.4, label="final code", color="#3E7C34")
    for x, b_, a_, tb, ta in zip(xs, before, after, ["0 / 159", "0.13", "2 of 3", "0.46–0.55"], ["100 %", "1.00", "0 of 5", "0.91"]):
        ax.text(x - 0.2, b_ + 0.02, tb, ha="center", fontsize=9), ax.text(x + 0.2, a_ + 0.02, ta, ha="center", fontsize=9)
    ax.set_xticks(list(xs), names), ax.set_ylim(0, 1.12), ax.set_ylabel("share (70B, same seeds)")
    ax.set_title("What the engineering fixes bought (3 baseline vs 5 final runs, E3d)", fontsize=11, fontweight="bold")
    ax.text(2, 0.82, "(lower is better)", ha="center", fontsize=8.5, color="#B83A52")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2), ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT / "fig07-fixes.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    for f in (fig_pipeline, fig_stance, fig_speech, fig_yesbias, fig_signal, fig_throughput, fig_fixes):
        f()
    print("wrote", *sorted(p.name for p in OUT.glob("*.png")))
