"""E4 (offline): does code-side opinion dynamics polarise residents with NO conversations?

Hypothesis H4: run_round._apply_opinion_dynamics applies Baumann drift
0.02*tanh(alpha*x) to every resident every round, regardless of whether any chat
happened, so 'polarisation' in a run is partly an artefact of the update rule.
"""
import json
import random
import statistics as st

from common import RESULTS
from graph.nodes.run_round import _apply_opinion_dynamics

out = {}
for controversy in ("low", "medium", "high"):
    rows = []
    for seed in range(20):
        rnd = random.Random(seed)
        npcs = [{"id": f"npc_{i:02d}", "political_leaning": round(rnd.uniform(-1, 1), 2),
                 "mood": "neutral", "reputation": 0.5} for i in range(25)]
        start = [n["political_leaning"] for n in npcs]
        for rd in range(15):  # 15 rounds, ZERO chat events
            npcs, _, _ = _apply_opinion_dynamics(npcs, [], rd, {}, controversy)
        end = [n["political_leaning"] for n in npcs]
        rows.append({
            "mean_abs_start": st.mean(abs(x) for x in start),
            "mean_abs_end": st.mean(abs(x) for x in end),
            "frac_extreme_end(|x|>0.9)": sum(abs(x) > 0.9 for x in end) / len(end),
            "frac_moderate_start(|x|<0.3)": sum(abs(x) < 0.3 for x in start) / len(start),
            "frac_moderate_end(|x|<0.3)": sum(abs(x) < 0.3 for x in end) / len(end),
        })
    out[controversy] = {k: round(st.mean(r[k] for r in rows), 3) for k in rows[0]}
    # single moderate resident trajectory
    x, traj = 0.1, [0.1]
    n = [{"id": "a", "political_leaning": 0.1, "mood": "neutral", "reputation": 0.5}]
    for rd in range(15):
        n, _, _ = _apply_opinion_dynamics(n, [], rd, {}, controversy)
        traj.append(n[0]["political_leaning"])
    out[controversy]["traj_x0=0.1"] = traj
print(json.dumps(out, indent=1))
(RESULTS / "e04_drift_artifact.json").write_text(json.dumps(out, indent=1))
