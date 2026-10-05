# Demo video script (≤ 2:00)

The video is the only thing many judges will watch, so it leads with the finding, not the architecture. Record at 1080p,
browser at 100 %, English narration, German/French shown on screen. Total target 1:50.

## Before recording (10 minutes)

1. `make run` from the repository root, wait for the backend to be healthy, open http://localhost:3000.
2. **Record a replay once, then play the replay on camera** (live 70B rounds take ≈ 2 minutes and the gateway latency varies).
   In the editor switch on the **record** toggle of the Run node, run the simulation, and press **SAVE JSON** at the top of the
   simulation screen when it finishes. To replay, use the file-load control on the landing page and pick the saved
   `gemeindesim-*.json` (`public/example-replay.json` shows the format).
3. Use the **balanced Linden text**: paste `data/steuerfuss_linden_balanced_de.txt` and `_fr.txt` into the notes field,
   5 residents, 3 rounds, situation kind "vote".
4. Pick the run where the starting stance poll is mixed (for example 3 / 1 / 1), not unanimous, and where one resident
   with an *against* stance has a computed figure in their lines (e.g. "144 CHF" or "432 CHF").
5. Close other tabs; the API key must not be visible anywhere in the recording (do not show `.env`).

## Shots

| time | on screen | say |
| --- | --- | --- |
| 0:00–0:12 | Black card, one line: **"We asked Apertus how 15 Swiss residents would vote. 15 said yes."** (E11) | "A civic simulator is only as good as its residents. When we asked Apertus directly, every resident said yes, whatever their job, income or politics. Even with no persona at all." |
| 0:12–0:30 | Title screen → policy editor with the German + French Linden text → press run | "GemeindeSim reads a Swiss vote in German and French and spawns a small town. The model does what it is good at: speaking in role in two languages. The application owns everything that decides outcomes: stance, arithmetic, sources." |
| 0:30–1:00 | Live map. Zoom on the event feed: a German line next to a French reply. Hover a citation chip `[14]` to show the passage text. Click a resident: profile shows stance bar, reason, computed cost | "Each resident's stance comes from their household cost, which we calculate, their politics and the model's judgement of impact. Their lines cite real passages, we check every citation. Before we added that check, none of 159 citations pointed at a real passage." |
| 1:00–1:20 | Stance panel moving over the rounds; open the influence graph | "Conversations move opinions through a transparent update rule, not by asking the model to change its mind. When we let the model re-answer at the end, it turned three of four opponents into yes." |
| 1:20–1:40 | End-of-run report: show the conditional wording and the stance-shift line | "The report describes who is affected and why. It never says the measure passed, we measured that going from twelve of thirty reports to zero, and it never recommends a vote." |
| 1:40–1:55 | One slide with five lines: *no parallel tool calls · thinking + JSON skips reasoning · temperature 0 not reproducible · 4 requests in flight · yes-biased, follows an official recommendation 98 %* and **"Not a vote predictor: 54 real Swiss votes tested"** | "We also used it as a test bench for Apertus. These limits are measured, reproducible and in the repo, with the 54-vote test." |
| 1:55–2:00 | Repo URL + `LLM_BASE_URL` | "One environment variable points it at any OpenAI-compatible Apertus, a Swiss cloud or your own server." |

## Rules of thumb

* Say "fictional town", "what-if explainer", never "predicts the vote".
* Do not claim sovereign parity: say it is configured, and the probe script is ready for a local deployment.
* If asked about German and French quality: it was reviewed by a native speaker (fill in after the review).
* Fallback if the live run misbehaves: play the saved replay; the stance panel and report still work from it.
