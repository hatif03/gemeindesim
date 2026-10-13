# Technical report — GemeindeSim

A deeper write-up than the README: what we built, how it works, and what the
numbers say.

- **Track:** Track 2B — Own Project (GemeindeSim)
- **Event:** Hack Apertus online stage, October 2026
- **Team:** hatif03
- **Demo:** video (max. 2 min): link in the submission form; a recorded 25-resident, 5-round run on CSCS can be replayed without calling the model (LOAD, `docs/replays/linden_25x5_cscs.replay.json`, see `docs/replays/README.md`); screenshots in `docs/screenshots/`
- **Report PDF:** `GemeindeSim_Report.pdf` (6 pages, built from `report/report.html`)

## 1. Summary

GemeindeSim is a generative-agent town simulation (Park et al. 2023 memory/retrieve/reflect/plan/act; Peralta et al. 2022 opinion dynamics) running on Apertus 1.5-70B. Users paste a Swiss municipal policy (bilingual Steuerfuss sample in `data/`) or an English tariff scenario. Residents act on a Phaser map with chat, move, protest, mood, and price events. Apertus emits schema-valid JSON; the application owns retrieval, dashboard arithmetic, validation, and social math.

Headline eval (measured, `research/`, logged calls): on 49 real resident prompts the instruction-placeholder example gives 49/49 schema-valid first attempts on both sizes (the original gate: 86 % on the 70B); 112/112 utterances in the resident's language; on identical seeds v2.1 vs the first version: cited ids that exist 0 → 99–100 %, ballot question present in the resident prompt 13–30 % → 100 %, reports asserting an invented outcome 12/30 → 0/30. Model limits we measured: no parallel tool calls (11/11), thinking unusable with JSON mode, `T=0` not reproducible, 4 requests in flight, yes-biased and authority-deferential electorate on 54 real Swiss votes. Details: `docs/research/`.

Judge briefing: `docs/FOR-JUDGES.md`.

## 2. Architecture

Two Docker services: FastAPI/LangGraph backend (`:8000`) and Next.js/Phaser frontend (`:3000` / `:8080`). Closed corpus on disk (`data/` mounted read-only). No open-web retrieval.

```text
policy upload → chunk/retrieve → parse → NPCs → N× run_round → Socket.IO → Phaser + report
```

### Target architecture (mandatory)

**Primary:** **(c) Sovereign Swiss cloud** — app containers + on-disk corpus; inference via a Swiss-hosted OpenAI-compatible endpoint (`LLM_BASE_URL`: the CSCS inference API `https://api.inference.cscs.ch/v1` used for judging, or the hackathon gateway `https://hackapertus.livemap.sh/v1`; one build runs on both, `docs/ENDPOINTS.md`).

**Also supported:** **(a) On-premise** / **(b) Air-gapped** by pointing `LLM_BASE_URL` to local vLLM serving `swiss-ai/Apertus-v1.5-70B`. **Status:** configuration only. The application's only outbound call is `LLM_BASE_URL`, and a clean-clone Docker stack starts and serves; but the model behaviours reported below were measured on the hosted gateway, and a local deployment was not run (no GPU available). `research/probe_endpoint.py` reproduces the behaviour table (tool calls, thinking, determinism, in-flight limit) on any OpenAI-compatible endpoint and was validated on the hosted 8B, so the sovereign claim can be completed in minutes on a GPU host.

## 3. Use of Apertus

- **Model:** `apertus-v1.5-70b` (gateway id); `apertus-v1.5-8b` on overflow
- **How:** `json` mode (thinking off, `response_format: json_object`, a three-event example with `<instruction>` placeholders in the resident's language) for rounds, personas, stance arguments and the economic report. No thinking pre-pass is wired (the helper exists, unused); thinking is never combined with JSON mode (it silently skips the reasoning, research E1). One language per completion; cross-language chat uses a separate translation call. The model **voices**; the application **owns** the stance, the household arithmetic (a deterministic calculator) and the sources (validated citation labels).
- **Where:** Hack Apertus hosted endpoint for development; production story = Swiss provider or on-prem vLLM.

Concurrency is an adaptive limiter (`LLM_CONCURRENCY=auto`: slow start from 4, halve on 429/5xx; the hosted gateway returns 429 above ≈ 4 in flight, CSCS showed no limit to 96) around async completions, not native parallel `tool_calls`; a 429 is retried on the same model. Dashboard metrics are computed in code. Probe details: `docs/PROBE-AND-PLAN.md` (replicated and corrected in `docs/research/`).

## 4. Data

Synthetic bilingual Linden Steuerfuss/school-credit excerpts (`data/steuerfuss_linden_{de,fr}.txt`) and an English Millfield tariff sample (`data/tariff_millfield_en.txt`). Redistributable, fictional. No personal data. Official Swiss PDFs are not vendored.

## 5. Evaluation

Offline pytest (`cd src/backend && uv run pytest --deselect tests/test_e2e.py`; the new regression tests in `tests/test_research_fixes.py` each pin a finding). The earlier "schema fixtures 20/20" validated hand-written objects, not model output, and is no longer cited.

Measured on the live hackathon gateway (5 October 2026; every call logged in `research/results/`; method and caveats in `docs/research/05-paper-draft.md`):

| Question | Result |
| --- | --- |
| Structured output on 49 real resident prompts | 49/49 first-attempt valid (both sizes) with `<instruction>` example; old gate 86 % on the 70B (nulls in string fields) |
| Language fidelity | 112/112 utterances in the resident's language |
| Retrieval / grounding, baseline → final code (16 runs) | ballot question in prompt 13–30 % → 100 %; valid citation labels 0 → 100 % |
| Real 48-page Federal Council booklet | recall@4 11/14 (old retriever 10/14); grounded QA 12/14 (hand-graded), 3/3 unanswerable questions abstained; retrieval is the bottleneck |
| Speech vs stance (465 lines, two classifiers) | resident's words match their code stance 0.46–0.55 → **0.85–0.92** (undecided residents: 0.5–0.7) |
| Report (6 objectives × 5 samples) | invented outcome 12/30 → 0/30; explicit vote advice 0/30 before and after |
| Swiss civic facts (15 questions) | 70B 12/15, 8B 9/15; both wrong on *Steuerfuss* and on 4 000 × 6 % |
| Stance when asked directly | 15/15 "yes" under every persona condition, also with a balanced booklet (stance is therefore code-owned) |
| 54 real federal votes, ballot title only | simulated yes-share 34–37 pp too high; Spearman 0.25–0.38 (70B personas); Federal Council position alone: 0.63 |
| Throughput | 4 requests in flight; 70B ≈ 156 tok/s, 8B ≈ 555 tok/s at that limit |

Baseline vs final code on identical seeds (5 residents × 3 rounds; standard graph 70B n = 5, 8B n = 5; swarm graph n = 3 + 3; baseline n = 3 + 2): events 27 → 33 (70B), 15 → 32 (8B); self-introductions 27 % → 0 %; reports asserting a result or mixing languages 2/3 and 3/3 → 0/16; influence log 0 → 49–77 outcomes per group (it had been silently dropped). The stance poll differs a lot from seed to seed (share *for* at the end 0.00–0.80 on the 70B), so the demo shows a distribution, not one run.

**Deployment bug found on 13 Oct while recording the demo.** The production image started two uvicorn workers; the simulation record and the Socket.IO session live in process memory, so a run could land on a different worker than its start request and fail with "Simulation not found" (about every other run). Fixed: one worker (`src/backend/Dockerfile`); verified with repeated runs on the rebuilt stack.

**Deployment check.** A clean clone of the original repository could not build the frontend image (no Linux native packages in either lockfile); fixed and verified from a fresh clone (UI and API serve; concurrency 4). `SWARM` now defaults to `false` (swarm: +27 % wall time, no gain). A local Apertus was not run (no GPU); `research/probe_endpoint.py` produces the behaviour table for any OpenAI-compatible endpoint and was validated on the hosted 8B.

**Second endpoint (6 Oct).** The same scripts were run on the CSCS inference API (Swiss National Supercomputing Centre; Apertus v1.5 70B, 8B and separate thinking models; the provider documents that prompts are not recorded) and, the same day, on the hackathon gateway as a control (`docs/research/07-cscs-vs-livemap.md`). Requests in flight: livemap ceiling 4-5 (429 above), CSCS no 429 in 2 496 requests up to 96; the 5-resident, 3-round simulation took 61 s instead of 126 s on the 70B. All v2 fixes replicate (valid citations 1.00, no self-introductions, reports without asserted outcome 0/5, speech matches the code stance 0.85-0.88), and so do Swiss knowledge (11/15, 9/15) and the real-vote result (Spearman 0.25 / 0.37 for the 70B with personas, to within 0.01 of livemap). What does not change: the yes-bias on all four CSCS models, the single tool call, `temperature 0` on real prompts (2.7 distinct outputs of 3 on both), `seed` has no effect. Strict `json_schema` degenerates on the CSCS 8B (11/24 valid) and is not used. Both are hosted endpoints; no local deployment was measured. The 1:1 chat with a resident is grounded like a round (stance, cited passages, number gate, Swiss spelling; with the complete text for documents of 6 000-100 000 characters: the real-booklet revenue question 5/5 instead of 0/5).

**Engineering checks (7 Oct).** Python is 2.2–5.0 % of the wall time (process CPU 1.3 s of 60 s on the 70B); the wall time is the longest chain of dependent calls at ≈ 60 tokens/s. Calls are async; the chat streams sentence by sentence only after the number gate and citation check (first text 1.5 s, whole answer 2.4 s). Token counts come from the endpoint's `usage` and are shown in the "Run metrics" panel (25 residents × 2 rounds: 143 calls, 168 k in / 51 k out, mean latency 6.6 s; context use ≤ 1.1 % of 262 k). Retrieval vs usual baselines on 14 booklet questions: BM25 recall@4 0.79, dense e5-large 1.00, hybrid (RRF) 1.00 (n = 14, indicative; optional `EMBEDDING_MODEL`, off by default). Details: `docs/ENGINEERING-QA.md`, `docs/ENDPOINTS.md`, `docs/research/LAB-NOTEBOOK.md` E29–E32.

### 5.7 Experiment index (every experiment is a script in `research/`, raw logs in `research/results/`)

Numbers are copied from `docs/research/LAB-NOTEBOOK.md` (append-only; correction C1 changed the baseline self-introduction metric from 0.29 to 0.27). More than 20,000 logged calls and trials in 91 logs, 32 experiment scripts, 48 instrumented simulations.

| ID | Question | Setup | Result |
| --- | --- | --- | --- |
| E0 | Is the offline test suite really offline, and how long does it take? | pytest, 69 tests, two runs, --durations | 69 passed; first run 420 s, second 50 s. One test (test_e2e.py::test_full_pipeline, 45 s) calls the live gateway, so the suite is not offline. |
| E1 | Do the PROBE-AND-PLAN claims on tool calls, thinking and determinism replicate? | 70B and 8B; n = 11 (3 at T=0, 8 at T=0.7); thinking n = 8 | Parallel tool calls fail 11/11 on both models. Thinking + json_object gives wrong 0.10 (no span, 16/16). T=0 not deterministic: 70B 3, 8B 5 distinct outputs of 5. |
| E2/E2b | Which example and format conditions make resident JSON valid and diverse? | 49 logged resident prompts, 70B and 8B, 4 conditions; first run void (429s) | response_format hypothesis refuted (strict JSON 100% without it). Filled example: 2 events/turn but 8B parrots 0.53. Instruction placeholders: 8B 1.0 to 1.8 events/turn, parroting 0. |
| E3 (baseline, E3a-E3d) | How does the shipped pipeline behave, and did the v2 fixes help? | Linden DE+FR, 5 residents, 3 rounds, T=0; 70B n = 3 / 5, 8B n = 2 / 5 | Baseline: 0/159 cited ids valid; 2/3 70B reports asserted a pass. Final: ids 1.00, 0/5 asserted, wall 126 s vs 334 s (unexplained). C1 corrected baseline self-intro to 0.27. |
| E4 | Does the opinion update polarise residents with no conversation? | 25 residents, 15 rounds, zero chats, 20 seeds, per controversy level | Confirmed: mean abs leaning 0.506 to 0.686 (medium) and 0.723 (high); 35.4% and 38.6% end above 0.9; low unchanged. v2: drift only for residents who conversed. |
| E5 | What does retrieval actually hand the resident? | 15 resident prompts of base70_s1; offline parse; six key facts | The vote question (118 to 124 %) reached only 4/15 prompts; other key facts 14-15/15. Language filter a no-op (all 9 chunks tagged de); chunks cut mid-word; corpus about 1.6k characters. |
| E6 | Does the numeral-grounding gate handle edge cases? | 12 hand-built cases against the Linden corpus, offline | Correct on only 8/12: flags correct derived arithmetic; hallucinated '2 Millionen CHF' and '4 Franken' pass via list numbers; spelled-out numbers missed. After v2: 10/12. |
| E7 | How good is Swiss civic knowledge and Swiss orthography? | 15 questions, 70B and 8B, regex rubric; ß test 3 samples x 4 prompts | 70B 12/15, 8B 9/15. Both define Steuerfuss wrongly and fail 4 000 CHF x 6 % (70B 280, 8B 360; correct 240). ß per 1 000 characters: 70B 2.6, 8B 1.2. |
| E8 | Does a silicon electorate predict real Swiss federal votes? | 54 votes 2021-2026, ballot title only, 70B and 8B, 3 672 calls | No: yes-bias +34 to +37 pp (70B, DE). Spearman 0.25 / 0.38 (70B), -0.02 / 0.02 (8B); Federal Council position alone 0.63; recalibrated MAE 12.4 pp vs 14.1 constant. |
| E9/E9b | Does the report assert invented outcomes or give vote advice? | 70B, logged report prompt, 6 objectives x 5 samples = 30; replay with v2 template | Vote advice 0/30. Baseline asserted an invented outcome in 12/30 (lower bound; 4/5 for default and 'did it pass?'). v2 template: 0/30 asserted, German 30/30. |
| E10 | What is the gateway's real parallel-request limit and throughput? | Raw requests, no retries, idle key, 1-8 in flight, both models | Effective limit is 4, not 5: at 5 in flight only 4/10 succeeded. 70B 156 tok/s at 4 in flight, 8B 555; app default 6 was too high. |
| E11/E11b/E11c | Do personas differentiate stance, and does a balanced corpus fix unanimity? | 15 residents from 70B baseline runs; T=0 and T=0.7; persona ablations; balanced corpus | Negative: 15/0/0 yes with full persona, role-only and no persona. Balanced corpus 14/0/0 (+1 failed call), T=0.7 27 yes, 2 no. Impact judged benefit for 14/15. |
| E12 | Does long-context needle recall hold up to about 105k tokens? | 70B and 8B, DE and FR, 5 lengths x 3 depths = 60 calls | 60/60 correct. 70B 31-36 s per call at about 100k tokens, 8B 8-9 s. Single easy needle only; persona dilution untested. |
| E13/E13b | Does the LLM agree with the code-owned stance? | 15 residents (v2.1), then 25 residents (final); re-asked with own memories | Agreement 0.40 in v2.1 (code no 4, LLM no 1); 0.64 in final. 7 of 10 code-against residents turn undecided or yes. |
| E14/E14b | Does resident dialogue tilt toward yes, and match the code stance? | 238 utterances (E14), 465 lines (E14b); two LLM classifiers, 70B and 8B | No yes tilt: v2.1 70B dialogue 0.54-0.61 against vs 0.09-0.16 for. Held-for residents sounded for 17-42%. Final speech match 0.91 / 0.88 (70B standard). |
| E15/E15b | Can speech be bound to the code stance, and does prompt position matter? | Replay of 75 prompts, 3 conditions (E15); in-loop 3 x 70B, 2 x 8B (E15b) | Reminder as last paragraph best (0.84 / 0.85, 70B). In loop: 70B 0.46-0.55 to 0.80, 8B 0.50-0.52 to 0.73-0.76. Undecided did not improve (70B 0.53 to 0.58). |
| E16/E16b | Can an undecided resident sound undecided? | Replay of 41 undecided prompts, 70B and 8B; U0-U3, then U1p, U1h | U1 raised mixed 0.47 to 0.72 but copied arguments verbatim 62-67%. U1p: 70B mixed 0.74 / 0.72, copying 0.05; 8B mixed+neutral 0.53 to 0.68. Opening phrase and hints failed. |
| E17 | Does the pipeline work on a real federal booklet? | 28 Sept 2025 booklet, 83k characters, 209 chunks, 14 questions, 70B, hand-graded | recall@4 10/14 (v1) vs 11/14 (v2, not significant); QA correct 11/14 and 12/14; unanswerable 3/3 abstained. Retrieval is the bottleneck; French untested. |
| E18/E18b | Does a clean clone build and run through the real UI? | Fresh clone, docker compose up, repo's Playwright script against UI and API | Failed at first: frontend image build error (lockfile without Linux packages), type error, concurrency default 6, swarm default, POST /simulate HTTP 422 (4 000-character cap). All fixed. |
| E19 | Can the harness compare what-if conditions such as a council recommendation? | 8B, 4 conditions x 3 paired seeds = 12 runs, standard graph | Yes or No recommendation shifts stance small and inconsistently (ranges include zero). Balanced corpus lowers stance in all 3 seeds (paired end -0.28). n = 3, 8B only. |
| E20 | Which models and capabilities does CSCS offer compared with livemap? | n = 5 per cell (3 for probes); four Apertus models; livemap same day | Key reaches only four Apertus v1.5 models (others 403); no embedding model. Same tool and thinking limits; only 8B-thinking fills the reasoning field. json_schema, seed, logprobs work on livemap too. |
| E21 | Does CSCS have a rate limit, and what throughput does it give? | 1-96 in flight, short and 2 400-token prompts, 250 tokens out, no retries | 0 non-200 in 2 496 requests; 70B 66 to 4 359 tok/s at 96 in flight. Livemap ceiling 5 in flight. Long jobs gave HTTP 504, notably on 8B-thinking. |
| E22 | Does long context work up to 233k tokens on CSCS? | 80 calls, DE and FR haystacks, 48k-233k tokens, single and three-fact questions | Single needle: 8B 30/30, 70B 26/30 (DE 11/15, digit corruption). Three facts: 70B 9/10, 8B 5/10. Livemap control n = 1 per cell, 2-3x slower. |
| E23 | Is temperature 0 reproducible, and does strict json_schema work on real prompts? | 24 resident prompts x 3 repeats, T=0, both endpoints and sizes | Not reproducible: 2.5-2.75 distinct outputs of 3; seed no effect. json_schema on CSCS 8B valid only 11/24 (endless whitespace), 70B 23/24, livemap 24/24; shipped json_object 72/72. |
| E24 | Is the yes-bias a property of the weights or of the deployment? | 15 residents, Linden vote, T=0, four CSCS models, logprob view | Bias persists: 14 yes / 1 no with persona, 15 yes without, on 70B, 8B, 70B-thinking. 8B-thinking had unparsed answers (6 of 30 hit token limit). 70B P(yes) 0.93. |
| E25 | Does the grounded 1:1 chat answer correctly without vote advice? | 5 residents x 5 scripted questions, 25 answers per run, backend on CSCS, 3 iterations | Run 1: 8 flagged figures, undecided residents repeated their position. Final: 0 errors, 0 invented figures, unknown fact declined 5/5, 0/5 vote recommendations, fact cited 5/5. |
| E26 | Is stuffing the whole booklet better than retrieval? | 83k-character booklet, 14+3 questions, 70B and 8B, top 4, top 8, whole; hand graded | 70B correct 11 (top 4), 12 (top 8), 13 (whole); 8B 11, 12, 12. Unanswerable 3/3 abstained; 94% of booklet tokens cached. Stuffing loses citation chips. |
| E27 | Do the v2 fixes replicate on CSCS with the final code? | 5 seeds x 2 sizes plus one 25-resident town; same code and seeds as livemap | 70B wall 61 s vs 126 s livemap; 8B 23 s vs 28 s. Cited ids 1.00. Speech match 0.85 / 0.87 (70B) vs 0.91 / 0.88. 25 residents: 105 s, 200 calls, 163 events. |
| E28 | Does the real booklet work through the whole app (PDF, simulation, chat)? | 48-page booklet via POST /context/sources, 5 residents, 2 rounds, 25 chat answers | 95 s, 0 errors. Retrieval alone: lost-revenue question 'not in the text' 5/5. Whole text in prompt: 5/5 answered 1.8 billion CHF, 0 invented figures, but only 2/5 carry a citation chip. |
| E29 | Is Python the bottleneck of the simulation? | One instrumented 5-resident, 3-round run per size on CSCS; micro-benchmarks | Process CPU 2.2% (70B, wall 60.5 s) and 5.0% (8B, wall 26.1 s). Output tokens explain 81% of mean latency. Booklet retrieval 12.1 ms to 2.5 ms after caching. |
| E30 | How does our retrieval compare with BM25, dense and hybrid baselines? | 14 gold questions, real booklet, 209 chunks of 480 characters, CPU fastembed | recall@4: BM25 as shipped 0.79, hybrid BM25 + e5-large 1.00, MiniLM dense 0.71 (worse than BM25). n = 14, one-question differences are noise. Option off by default. |
| E31 | Can one build run on both endpoints, and does the limiter adapt? | 25 residents x 2 rounds, both endpoints, LLM_CONCURRENCY=auto, 3 limiter iterations | Both id directions: 0 errors. Final limiter: CSCS 95-97 s, gateway 654 s (656 s at limit 4): more in flight added latency, not throughput. CSCS 6.7-7.3x faster. |
| E32 | Can we count tokens, show metrics and stream the chat safely? | 25 residents, 2 rounds on CSCS; 25 streamed chat answers | 143 calls, 168 k tokens in, 51 k out, 16% cached, p95 14.4 s, 0 retries. Chat first text 1.5 s (median), whole answer 2.4 s; quality unchanged. |

### 5.8 The demo run

Recorded from the running app (the Socket.IO stream the UI receives), Apertus 70B on the CSCS inference API, balanced Linden text in German and French, 25 residents (13 DE, 12 FR), 5 rounds, standard graph: 316 calls, 416 k tokens in and 97 k out (25 % cached), mean latency 9.0 s, p95 24.6 s, 0 retries, 0 failures, 237 s wall (limiter 4 to 32). All 150 resident dialogue lines were grounded with 0 invalid citations; the household figures 144 and 432 CHF come from the calculator. The poll moved from 8 for / 10 against / 7 undecided to 10 / 9 / 6. Three candidate runs were recorded (25 x 5 twice, 25 x 4); the one with the most mixed start was kept. The backend caps residents at 25. Files: `docs/replays/`, recorder `research/record_demo.py`.

## 6. Limitations

Model: no parallel tool calls in one completion (11/11); thinking markers stay in `content` and thinking is skipped under JSON mode; `temperature 0` is not reproducible; a strong *yes* default and near-total deference to an official recommendation (8B: 98 %); elementary Swiss facts and arithmetic are unreliable, so numbers come from the corpus or the calculator. Application: **not a vote predictor** (54 real votes; only a weak signal after bias correction); the stance prior weights are assumptions, not calibrated; the Linden sample (1.6 k characters per language) does not stress retrieval; n is small (3 and 2 simulations per group, 15 residents in population tests). German/French register still needs native-speaker review (Swiss orthography is enforced in code). Gateway behaviour must be re-probed on a local vLLM before claiming sovereign parity. Open defects: `price_pressure` indicator is always 0, `invoke_llm_think` is unused. Swarm remains code-side initiator scoring.

## 7. Reproducibility

`make run` from the repository root with `track_2b/.env` (`LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`). Python 3.12, Docker. Tests: `cd track_2b/src/backend && uv run pytest`.

## 8. Next steps

2-minute demo video; on-prem vLLM against the Swiss-AI container; native-speaker pass on DE/FR lines. Optional later: Italian, Swiss-German dialect, activation probes (`swiss-ai/apertus-probes`) when weights are local.

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced.

## References

- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. arXiv:2304.03442.
- Park, J. S., Zou, C. Q., Shaw, A., Hill, B. M., Cai, C., Morris, M. R., Willer, R., Liang, P., & Bernstein, M. S. (2024). Generative Agent Simulations of 1,000 People. arXiv:2411.10109.
- Peralta, A. F., Kertész, J., & Iñiguez, G. (2022). Opinion dynamics in social networks: From models to data. arXiv:2201.01322.
- Ramnath, K. et al. (2025). A Survey on Automatic Prompt Optimization. arXiv:2502.16923.
- Apertus 1.5 getting started: https://blog.nlp-lab.ai/2026/10/01/Apertus15GettingStarted.html
- Apertus Charter: https://www.apertus-ai.org/pages/charter/
- Data transparency: https://github.com/swiss-ai/apertus-data-transparency
