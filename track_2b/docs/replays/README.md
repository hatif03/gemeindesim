# Saved replays

| file | what it is |
| --- | --- |
| `linden_25x5_cscs.replay.json` | **Demo replay.** 25 residents (13 DE, 12 FR), 5 rounds, recorded from the running app (the Socket.IO stream the UI receives) on the CSCS inference API, Apertus 1.5 70B (`swiss-ai/Apertus-v1.5-70B`), standard graph. 316 calls, 0 retries, 0 failed, wall 237 s. Carries init, 5 rounds with per-round metrics, and the report. |
| `linden_25x5_cscs.config.json` | The exact request that produced it (document, objective, rounds, residents, kind) and the run metrics. |
| `linden_25x5_cscs.document.txt` | The exact document to paste into the notes field (balanced Linden text, German then French). |
| `final_70_s3.replay.json` | Earlier research run (5 residents, 3 rounds, gateway). |

## Configuration to show before loading the replay

* Document: paste `linden_25x5_cscs.document.txt` (the same text is `data/steuerfuss_linden_balanced_de.txt` + `_fr.txt`).
* Situation kind: **vote**. Objective: *How the Steuerfuss and school credit land on households and shops*.
* Residents: **25** (the backend caps at 25), rounds: **5**. Map: default.
* Endpoint: CSCS inference API, model `swiss-ai/Apertus-v1.5-70B` (`.env`, key never shown).

Then use the replay control on the landing page and pick `linden_25x5_cscs.replay.json`.

Re-record: `uv run --project src/backend python research/record_demo.py NAME --file data/steuerfuss_linden_balanced_de.txt --file data/steuerfuss_linden_balanced_fr.txt --npcs 25 --rounds 5` (the app must be running on `localhost:8000`).
