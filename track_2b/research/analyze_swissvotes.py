"""Analyse E8 results: agreement of simulated yes-shares with real Swiss vote outcomes."""
import json
import statistics as st
import sys
from collections import defaultdict

from common import RESULTS

d = json.loads((RESULTS / (sys.argv[1] if len(sys.argv) > 1 else "e08_swissvotes_results.json")).read_text(encoding="utf-8"))
votes = {v["anr"]: v for v in d["votes"]}
res = [r for r in d["results"] if r["vote"] is not None]
print("results", len(d["results"]), "unparsed", len(d["results"]) - len(res))


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(a, b):
    if len(a) < 3:
        return float("nan")
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")


spear = lambda a, b: pearson(rank(a), rank(b))

# sim yes-share per (model, cond, lang, br, vote)
cells = defaultdict(list)
for r in res:
    cells[(r["model"].split("-")[-1], r["cond"], r["lang"], r["br"], r["anr"])].append(r["vote"])
conds = sorted({k[:4] for k in cells})


def era(v):
    y = int(v["date"][:4])
    return "<=2024" if y <= 2024 else "2025" if y == 2025 else "2026"


print(f"\n{'model':5s} {'cond':14s} lang br | n_votes  bias(sim-real,pp)  pearson  spearman  dir_acc  base_no  | rho<=2024  rho2025-26")
rows = []
for c in conds:
    anrs = [k[4] for k in cells if k[:4] == c]
    sim = [100 * st.mean(cells[c + (a,)]) for a in anrs]
    real = [votes[a]["yes"] for a in anrs]
    dir_acc = st.mean((s > 50) == votes[a]["accepted"] for s, a in zip(sim, anrs))
    base_no = st.mean(not votes[a]["accepted"] for a in anrs)
    early = [(s, r) for s, r, a in zip(sim, real, anrs) if era(votes[a]) == "<=2024"]
    late = [(s, r) for s, r, a in zip(sim, real, anrs) if era(votes[a]) != "<=2024"]
    rho = lambda z: spear([x for x, _ in z], [y for _, y in z]) if len(z) > 4 else float("nan")
    print(f"{c[0]:5s} {c[1]:14s} {c[2]:3s} {int(c[3])}  | {len(anrs):6d}  {st.mean(sim) - st.mean(real):+10.1f}  {pearson(sim, real):8.2f} {spear(sim, real):8.2f} {dir_acc:8.2f} {base_no:8.2f}  | {rho(early):8.2f} {rho(late):9.2f}")
    rows.append({"cond": c, "n": len(anrs), "bias": st.mean(sim) - st.mean(real), "pearson": pearson(sim, real),
                 "spearman": spear(sim, real), "dir_acc": dir_acc, "rho_early": rho(early), "rho_late": rho(late)})

# Roestigraben: DE-FR gap per vote, sim vs real (demo conds only)
print("\nRoestigraben (sim DE-FR yes-share gap vs real DE-cantons minus FR-cantons gap)")
for model, cond in sorted({(c[0], c[1]) for c in conds}):
    gaps_s, gaps_r, flips, agree = [], [], 0, 0
    for a in votes:
        k_de, k_fr = (model, cond, "de", False, a), (model, cond, "fr", False, a)
        if k_de in cells and k_fr in cells and votes[a]["yes_de"] is not None and votes[a]["yes_fr"] is not None:
            s_de, s_fr = 100 * st.mean(cells[k_de]), 100 * st.mean(cells[k_fr])
            gaps_s.append(s_de - s_fr)
            gaps_r.append(votes[a]["yes_de"] - votes[a]["yes_fr"])
            agree += (s_de > 50) == (s_fr > 50)
    if gaps_s:
        print(f"  {model:4s} {cond:14s} n={len(gaps_s)}  corr(gap_sim,gap_real)={pearson(gaps_s, gaps_r):+.2f}  mean|gap_sim|={st.mean(abs(g) for g in gaps_s):.1f}pp "
              f"mean real gap={st.mean(gaps_r):+.1f}pp  cross-language majority agreement={agree / len(gaps_s):.2f}")

# Federal Council deference: with vs without BR recommendation, persona-less
print("\nFederal Council recommendation effect (persona-less): share of votes following BR position")
for model in ("70b", "8b"):
    for lang in ("de", "fr"):
        for br in (False, True):
            ks = [(model, "none", lang, br, a) for a in votes if (model, "none", lang, br, a) in cells and votes[a]["br_pos"] in ("1", "2")]
            if ks:
                f = st.mean(((cells[k][0] == 1) == (votes[k[4]]["br_pos"] == "1")) for k in ks)
                print(f"  {model:4s} {lang} BR-shown={br!s:5}  follows BR on {f:.2f} of {len(ks)} votes; yes-rate {st.mean(cells[k][0] for k in ks):.2f}")
json.dump(rows, open(RESULTS / "e08_summary.json", "w"), indent=1)


# ---------------------------------------------------------------- baselines and recalibration
print("\n== Baselines (54 votes) ==")
anrs_all = sorted(votes)
real_all = [votes[a]["yes"] for a in anrs_all]
br = [1.0 if votes[a]["br_pos"] == "1" else 0.0 if votes[a]["br_pos"] == "2" else 0.5 for a in anrs_all]
dir_br = st.mean(((b > 0.5) == votes[a]["accepted"]) for a, b in zip(anrs_all, br) if b != 0.5)
print(f"Federal-Council-position-only predictor: direction accuracy {dir_br:.2f} (n={sum(b != 0.5 for b in br)}), spearman vs real yes-share {spear(br, real_all):.2f}")
print(f"always-No direction accuracy {st.mean(not votes[a]['accepted'] for a in anrs_all):.2f};  mean real yes-share {st.mean(real_all):.1f}%")

print("\n== MAE of yes-share (pp) and affine recalibration: fit on votes <=2024, test on 2025-26 ==")
def fit(x, y):  # least squares y = a + b x
    mx, my = st.mean(x), st.mean(y)
    b = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (sum((xi - mx) ** 2 for xi in x) or 1)
    return my - b * mx, b
rows2 = []
for c in conds:
    anrs = [k[4] for k in cells if k[:4] == c]
    sim = {a: 100 * st.mean(cells[c + (a,)]) for a in anrs}
    tr = [a for a in anrs if era(votes[a]) == "<=2024"]
    te = [a for a in anrs if era(votes[a]) != "<=2024"]
    a_, b_ = fit([sim[a] for a in tr], [votes[a]["yes"] for a in tr])
    mae_raw = st.mean(abs(sim[a] - votes[a]["yes"]) for a in te)
    mae_cal = st.mean(abs(a_ + b_ * sim[a] - votes[a]["yes"]) for a in te)
    mae_const = st.mean(abs(st.mean(votes[x]["yes"] for x in tr) - votes[a]["yes"]) for a in te)
    dir_cal = st.mean(((a_ + b_ * sim[a]) > 50) == votes[a]["accepted"] for a in te)
    print(f"{c[0]:4s} {c[1]:14s} {c[2]} br={int(c[3])}  test n={len(te)}  MAE raw {mae_raw:5.1f}  recalibrated {mae_cal:5.1f}  constant-mean {mae_const:5.1f}  slope b={b_:+.2f}  dir_acc(recal) {dir_cal:.2f}")
    rows2.append({"cond": c, "mae_raw": mae_raw, "mae_cal": mae_cal, "mae_const": mae_const, "slope": b_, "dir_cal": dir_cal})
json.dump(rows2, open(RESULTS / "e08_recalibration.json", "w"), indent=1)
