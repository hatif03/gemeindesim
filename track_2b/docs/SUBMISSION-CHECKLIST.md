# Submission checklist (deadline 16 Oct 2026, 12:00 CEST, no extension)

Requirements are from `docs/HACKATHON.md`. **Done** = verified in this repository; **You** = needs a person.

| # | Requirement | Status | Detail / action |
| --- | --- | --- | --- |
| 1 | Public GitHub repo from the project template, project inside `track_2b/` | **You** | Branch `submission/v2` holds everything. Push it, make the repo **public**, and make sure the default branch contains it (or open the PR and merge). Do not rename `track_2b/`. |
| 2 | `make run` works on a clean checkout (Docker) | **Done, re-verify once at the end** | A clean clone failed in the original repo (frontend image: missing Linux native packages in both lockfiles). Fixed; see `docs/research/LAB-NOTEBOOK.md` (E18). Re-run `git clone` + `make run` on the final commit. |
| 3 | Env vars `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` | **Done** | `track_2b/.env.example`; compose passes them through. Never commit `.env` (it is git-ignored; the research logs were scanned for the key: none). |
| 4 | `data/` ≤ 100 MB | **Done** | A few kB (`data/`). `research/` is ≈ 40 MB of logs and is not under `data/`; if you want the repo smaller, gzip `research/results/sims/*.calls.jsonl`. |
| 5 | `technical_report.md` + **`TeamName_Report.pdf` (≤ 6 pages) in `track_2b/`** | **You: name; Done: content** | `GemeindeSim_Report.pdf` was generated from `report/report.html`; rename to `<YourTeamName>_Report.pdf` and re-render with `python research/build_report_pdf.py` after editing the team name in `report/report.html`. Confirm ≤ 6 pages. |
| 6 | Deployability story documented (on-prem / air-gapped / sovereign cloud) | **Done** | `technical_report.md` §2 and the PDF. Honest status: configured (`LLM_BASE_URL`), the gateway behaviours are **not** re-measured on a local deployment; `research/probe_endpoint.py` is ready for a GPU host. |
| 7 | Demo video ≤ 2 minutes | **You** | Shot list and narration in `docs/DEMO-SCRIPT.md`. Record a replay first (see the script), do not show `.env`. |
| 8 | Submit the URLs at http://hackapertus.ch/online-hack/submissions | **You** | Repo URL, video URL, report PDF (it is in the repo). Do this by 15 Oct, not 16 Oct. |
| 9 | Devpost registration, Discord | **You** | Register at https://hackapertus.devpost.com/; join the Discord. |
| 10 | Optional HF dataset from `HackApertus/online_hack_template` | optional | `research/results/` (raw calls) could be the dataset: the E8 results and the 18+ experiment logs. |
| 11 | Open-source terms (§6): licence | **Done** | `LICENSE` (Apache-2.0, template); `technical_report.md` states CC-BY-4.0 as the template requires. Swissvotes data used under its terms (cite Swissvotes, Univ. Bern); official booklets are **not** vendored. |

## Final-day sequence (15 Oct)

1. `git pull` the final branch into a fresh directory, copy `.env`, run `make run`, wait for healthy, open http://localhost:3000.
2. Run the Linden DE+FR sample once (5 residents, 3 rounds). Expect: stance panel, citation chips, a German report with no outcome.
3. `cd track_2b/src/backend && uv run pytest --deselect tests/test_e2e.py` (120 offline tests).
4. Check the PDF page count and that the numbers equal `docs/research/03-results.md`.
5. Submit.

## Claims you may make / may not make

* May: measured limits of Apertus 1.5 (parallel tools, thinking vs JSON, `T=0` non-determinism, 4 in flight, yes-bias,
  authority deference, weak Swiss facts); the design principle (model voices, code owns stance / numbers / sources); the
  fixes with before/after numbers; a what-if explainer that compares conditions.
* May not: that it predicts votes; that sovereign deployment was tested; that stance weights are calibrated; that the German and
  French were native-reviewed until the review sheet has come back and been applied.
