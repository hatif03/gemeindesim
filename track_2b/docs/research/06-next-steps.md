# 06 — Status and next steps

Deadline: **16 Oct 2026, 12:00 CEST** (submit by the 15th). Verified items are described in `LAB-NOTEBOOK.md`; people-dependent items are in
[`../SUBMISSION-CHECKLIST.md`](../SUBMISSION-CHECKLIST.md).

## Done (this work)

| item | state |
| --- | --- |
| Undecided residents | Fixed in the model prompt (two-sided binding): 70B "mixed" 0.47 → 0.74; final runs: undecided lines 0.73 (70B), 0.54 (8B). 8B remains the weak case |
| Branch + commit | `submission/v2` (nothing pushed) |
| Clean-checkout `make run` | Was broken in the original repo; fixed and verified from a fresh clone (UI 200 on both ports, API 200); full live run through the UI captured |
| UI shows the new mechanism | Stance poll panel, stance + reason in the resident profile, citation chips with the passage text, stance shift in the report, economy bars hidden for votes. Verified on the live run (`docs/screenshots/06`, `07`) |
| Pitch restated | `FOR-JUDGES.md`, `technical_report.md`, `PROBE-AND-PLAN.md` erratum; claim-by-claim in `04-pitch-audit.md` |
| Final measurement on final code | 5 seeds × 2 sizes standard graph + 3 × 2 swarm graph; stance spread; compare-conditions demonstration (E19) |
| Real booklet | Tested on a 48-page Federal Council booklet (German): recall@4 11/14, QA 12/14, 3/3 abstentions. **French edition not tested** |
| 6-page PDF | `GemeindeSim_Report.pdf` (3 pages) built from `report/report.html` with `research/build_report_pdf.py` — rename with your team name |
| Demo video | Script and pre-flight checklist: `DEMO-SCRIPT.md`. **Recording is yours** |
| Native-speaker review | Pack ready: `docs/review/` (49 items, rubric, CSV) + `research/summarize_review.py`. **Needs your reviewer** |
| Local vLLM probe | `research/probe_endpoint.py` validated on the hosted 8B; **not run on a local model** (no GPU) |
| Run-it-N-times | Offline: `research/ensemble_report.py` (table + PNG). **In the app since 6 Oct:** "Run 5x: show the spread" (`POST /ensemble`, `/spread`); needs a fast endpoint |
| Second endpoint (6 Oct) | CSCS inference API measured with the same scripts (E20-E28): no 429 to 96 in flight, 70B simulation 126 s -> 61 s, every v2 fix replicates. `07-cscs-vs-livemap.md`, `08-cscs-plan.md` |
| 1:1 chat | **Grounded since 6 Oct** (stance, passages, citation chips, number gate, Swiss spelling, whole text for 6 000-100 000 characters); tested live (E25, E28) |

## Still open

1. **Native-speaker corrections** → run `summarize_review.py` on the returned sheet, apply to `graph/language.py` (glossary, fixed lines), `graph/prompts.py`,
   `data/steuerfuss_linden_*.txt`; re-run `make_review_pack.py` for a second round if the scores are low.
2. **Record the video**, push the branch, make the repo public, rename the PDF, submit (checklist).
3. **Local Apertus**: run `probe_endpoint.py` against a vLLM on any GPU host; paste the table into `03-results.md` and the report's deployability paragraph.
4. **French booklet / more booklets**: retrieval is the bottleneck (recall@4 11/14); whole-text prompts fix it for the chat (E26, E28); a hybrid with a local multilingual embedding model is untested (no endpoint offers one); add a French edition to E17.
5. **Hand-built, statistics-based personas** (LLM personas are homogeneous); calibrate the stance prior on municipal vote results.
6. **UI error handling**: the editor's run button shows an alert on failure; other screens only log API errors (the 422 for a long text was silent).
7. **In-app compare-conditions control** (the 5-run spread exists; comparing texts is still harness + docs). Upgrade E19 to 10 paired seeds on the 70B (now ≈ 40 minutes of calls on CSCS).
8. **CSCS follow-ups** (`08-cscs-plan.md`): whole-booklet mode in the loop (persona dilution untested), 8B loop + 70B voice, 25-resident towns in the UI, logprob-based classifiers, local small embedding model for hybrid retrieval.

## Known defects not fixed

* `price_pressure` indicator is always 0; `invoke_llm_think` is unused.
* Derived arithmetic ("240 / 12 = 20") and spelled-out numbers are not recognised by the numeral gate (10/12 on the edge cases).
* 8B never emits `move` meaningfully; stance dynamics move little in 3 rounds (the poll is unchanged in 4 of 5 final 70B runs).
* Stance-prior weights, E8 persona proportions: assumptions, not calibrated.
* The swarm graph is supported and measured but off by default (+27 % time, no gain).
