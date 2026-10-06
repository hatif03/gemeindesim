"""Convert a logged research run (results/sims/<tag>.json) into a UI replay (SavedSimulation).

    python research/make_replay.py final_70_s3          # -> docs/replays/final_70_s3.replay.json

Load it on the landing page with the replay file control. The replay carries the init message, the rounds and the report.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tag = sys.argv[1]
run = json.loads((ROOT / "research/results/sims" / f"{tag}.json").read_text(encoding="utf-8"))

rels = [{"rel_type": "neighbor", "strength": 0.5, **r} for r in run["relationships"]]
n_rounds = len(run["rounds"])
replay = {
    "version": 1,
    "savedAt": "2026-10-05T00:00:00Z",
    "policyText": f"GemeindeSim run {tag} ({run['args']['model']}, seed {run['args']['seed']}): Linden tax multiplier 118 to 124 % and school credit",
    "maxRounds": n_rounds,
    "initMsg": {"type": "init", "npcs": run["npcs0"], "relationships": rels, "max_rounds": n_rounds},
    "report": run["report"],
    "rounds": [
        {
            "type": "round",
            "round": r["round"],
            "events": r["events"],
            "npcs": r["npcs"],
            "influence_events": r["influence"],
            "economic_indicators": r["indicators"],
            "relationships": rels,
            "max_rounds": n_rounds,
        }
        for r in run["rounds"]
    ],
}
out = ROOT / "docs/replays" / f"{tag}.replay.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(replay, ensure_ascii=False, indent=1), encoding="utf-8")
print(out, f"{out.stat().st_size // 1024} kB,", n_rounds, "rounds,", sum(len(r["events"]) for r in run["rounds"]), "events")
print("REPORT HEADLINE:", run["report"].get("headline"))
