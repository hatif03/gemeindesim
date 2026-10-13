# Technical report — GemeindeSim

A deeper write-up than the README: what we built, how it works, and what the
numbers say.

- **Track:** Track 2B — Own Project (GemeindeSim)
- **Event:** Hack Apertus online stage, October 2026
- **Team:** 1ne (project: GemeindeSim)
- **Demo:** submission video (2 min): https://youtu.be/ZdXAJjCUhZI; complete live run with commentary: https://youtu.be/BZnqYIDV63Q; a recorded 25-resident, 5-round run on CSCS can be replayed without calling the model (LOAD, `docs/replays/linden_25x5_cscs.replay.json`, see `docs/replays/README.md`); screenshots in `docs/screenshots/`
- **Report PDF:** `1ne_Report.pdf` (6 pages, built from `report/report.html`)

## 1. Summary

GemeindeSim is a generative-agent town simulation (Park et al. 2023 memory/retrieve/reflect/plan/act; Peralta et al. 2022 opinion dynamics) running on Apertus 1.5-70B. Users paste a Swiss municipal policy (bilingual Steuerfuss sample in `data/`) or an English tariff scenario. Residents act on a Phaser map with chat, move, protest, mood, and price events. Apertus emits schema-valid JSON; the application owns retrieval, dashboard arithmetic, validation, and social math.

Headline eval (measured, `research/`, logged calls): on 49 real resident prompts the instruction-placeholder example gives 49/49 schema-valid first attempts on both sizes (the original gate: 86 % on the 70B); 112/112 utterances in the resident's language; on identical seeds v2.1 vs the first version: cited ids that exist 0 → 99–100 %, ballot question present in the resident prompt 13–30 % → 100 %, reports asserting an invented outcome 12/30 → 0/30. Model limits we measured: no parallel tool calls (11/11), thinking unusable with JSON mode, `T=0` not reproducible, 4 requests in flight, yes-biased and authority-deferential electorate on 54 real Swiss votes. Details: `docs/research/`.

Judge briefing: `docs/FOR-JUDGES.md`.

### 1.1 Similar applications and what they are used for

Simulated people and AI-assisted listening are used in research and, increasingly, in government and market research. Reference numbers point to the list at the end.

| Application | What it is used for | What is known about it |
| --- | --- | --- |
| Singapore GovTech Echo, Sept 2026 [44] | AI personas, built from past focus-group transcripts, react to a draft government announcement before it is released | the closest government case; early testing, still validated against real focus groups; “personas generate hypotheses, not conclusions” |
| Social Simulacra, Stanford, 2022 [2] | an LLM generates thousands of community members so designers can test a community design before launch | the origin of the “populated prototype” idea we follow |
| Generative agents and the 1,052-person study, Stanford, 2023 and 2024 [1, 3] | agents with memory, reflection and interview-grounded personas simulate individuals and small societies | match survey answers at 85 % of participants' own two-week consistency; the authors' spin-off sells it (company claims only) |
| Predicting experiment results, Nature 2026 [13] | GPT-4 simulates 70 US survey experiments to pre-test messages | direction and rank right (r = 0.85), effect sizes systematically too large: good for comparing, not for levels |
| AI-mediated deliberation: Habermas Machine, DeepMind 2024 [28]; Consult, UK government 2025 [45] | write group statements that people prefer 56 % of the time; sort 2,000+ consultation answers (F1 0.76) | they work on real people's words, not simulated ones; no public deployment of the first |
| Synthetic respondents in market research: Aaru, Electric Twin, Ipsos, Qualtrics [46] | persona panels to test ads, products and campaign messages | accuracy figures are the vendors' own; the independent test (Pew 2026 [40]) found 11–13 points average error |
| Human pre-testing of ballot wording: UK Electoral Commission 2012 and 2015 [47]; citizen panels in Oregon and Sion (VS) [48] | 203 interviews and 10 focus groups changed the wording of the Scottish referendum question; panels write the voter-pamphlet statement | the gold standard GemeindeSim is a cheap first pass for: it costs weeks and thousands of francs per question |

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

License: CC-BY-4.0 (all Hack Apertus projects are open-sourced); code Apache-2.0. Vendor and press items are marked as such.

**Generative agents and social simulation**

1. Park, O'Brien, Cai, Morris, Liang, Bernstein (2023). Generative Agents: Interactive Simulacra of Human Behavior. [arxiv.org/abs/2304.03442](https://arxiv.org/abs/2304.03442)
2. Park, Popowski, Cai, Morris, Liang, Bernstein (2022). Social Simulacra: Creating Populated Prototypes for Social Computing Systems. UIST. [arxiv.org/abs/2208.04024](https://arxiv.org/abs/2208.04024)
3. Park, Zou, et al. (2024). Generative Agent Simulations of 1,000 People. [arxiv.org/abs/2411.10109](https://arxiv.org/abs/2411.10109)
4. Yang et al. (2024). OASIS: Open Agent Social Interaction Simulations with One Million Agents. [arxiv.org/abs/2411.11581](https://arxiv.org/abs/2411.11581)
5. Piao et al. (2025). AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents. [arxiv.org/abs/2502.08691](https://arxiv.org/abs/2502.08691)
6. Rossetti et al. (2024). Y Social: an LLM-powered Social Media Digital Twin. [arxiv.org/abs/2408.00818](https://arxiv.org/abs/2408.00818)
7. Anthis et al. (2025). LLM Social Simulations Are a Promising Research Method. ICML. [arxiv.org/abs/2504.02234](https://arxiv.org/abs/2504.02234)

**Opinion dynamics**

8. Deffuant, Neau, Amblard, Weisbuch (2000). Mixing beliefs among interacting agents. Advances in Complex Systems 3. [doi.org/10.1142/S0219525900000078](https://doi.org/10.1142/S0219525900000078)
9. Peralta, Kertész, Iñiguez (2022). Opinion dynamics in social networks: from models to data. [arxiv.org/abs/2201.01322](https://arxiv.org/abs/2201.01322)
10. Chuang et al. (2023). Simulating Opinion Dynamics with Networks of LLM-based Agents. [arxiv.org/abs/2311.09618](https://arxiv.org/abs/2311.09618)
11. Törnberg, Valeeva, Uitermark, Bail (2023). Simulating Social Media Using LLMs to Evaluate Alternative News Feed Algorithms. [arxiv.org/abs/2310.05984](https://arxiv.org/abs/2310.05984)

**LLM respondents, voting and survey experiments**

12. Argyle et al. (2022). Out of One, Many: Using Language Models to Simulate Human Samples. Political Analysis. [arxiv.org/abs/2209.06899](https://arxiv.org/abs/2209.06899)
13. Ashokkumar, Hewitt, Ghezae, Willer (2026). Large language models can predict the results of social science experiments. Nature 656. [ai4pb.stanford.edu/projects/predicting-results-of-social-science-experiments-using-large-language-models](https://ai4pb.stanford.edu/projects/predicting-results-of-social-science-experiments-using-large-language-models)
14. Bisbee, Clinton, Dorff, Kenkel, Larson (2024). Synthetic Replacements for Human Survey Data? The Perils of Large Language Models. Political Analysis 32(4). [cambridge.org/core/product/B92267DC26195C7F36E63EA04A47D2FE](https://cambridge.org/core/product/B92267DC26195C7F36E63EA04A47D2FE)
15. Barmettler (2026). Progressive in Principle, Centrist in Practice: LLM Political Bias Is Instrument-Dependent (48 Swiss federal referenda, four languages). [arxiv.org/abs/2606.00048](https://arxiv.org/abs/2606.00048)
16. Reveilhac (2025). ChatGPT as a voting application in direct democracy. Swiss Political Science Review. [doi.org/10.1111/spsr.12650](https://doi.org/10.1111/spsr.12650)
17. Yang, Dailisan, Korecki, Hausladen, Helbing (2024). LLM Voting: Human Choices and AI Collective Decision Making. AIES. [arxiv.org/abs/2402.01766](https://arxiv.org/abs/2402.01766)
18. Bachmann, van der Weijden, Heitz, Sarasua, Bernstein (2025). Adaptive political surveys and GPT-4. PLoS One. [arxiv.org/abs/2503.09311](https://arxiv.org/abs/2503.09311)
19. Stammbach, Widmer, Cho, Gulcehre, Ash (2024). Aligning Large Language Models with Diverse Political Viewpoints. EMNLP. [arxiv.org/abs/2406.14155](https://arxiv.org/abs/2406.14155)
20. Egli, Mamié, Dolev, Müller (2023). Voting Booklet Bias: Stance Detection in Swiss Federal Communication. [arxiv.org/abs/2306.08999](https://arxiv.org/abs/2306.08999)
21. von der Heyde, Haensch, Wenz (2025). Vox Populi, Vox AI? Using Language Models to Estimate German Public Opinion; and (2024) United in Diversity? Contextual Biases in LLM-Based Predictions of the 2024 European Parliament Elections. [arxiv.org/abs/2407.08563](https://arxiv.org/abs/2407.08563), [arxiv.org/abs/2409.09045](https://arxiv.org/abs/2409.09045)
22. Ma et al. (2025). Algorithmic Fidelity of Large Language Models in Generating Synthetic German Public Opinions. ACL. [arxiv.org/abs/2412.13169](https://arxiv.org/abs/2412.13169)
23. Gudiño-Rosero, Grandi, Hidalgo (2024). Large Language Models (LLMs) as Agents for Augmented Democracy. [arxiv.org/abs/2405.03452](https://arxiv.org/abs/2405.03452)
24. Kreutner, Lutz, Strohmaier (2026). Persona-driven Simulation of Voting Behavior in the European Parliament with LLMs. EACL. [arxiv.org/abs/2506.11798](https://arxiv.org/abs/2506.11798)
25. Gong, Sanders, Schneier (2026). Characterizing the ability of LLMs to recapitulate Americans' distributional responses to public opinion polling questions. [arxiv.org/abs/2603.20229](https://arxiv.org/abs/2603.20229)

**Policy simulation and deliberation**

26. Barnett, Kieslich, Diakopoulos (2024). Simulating Policy Impacts: A Generative Scenario Writing Method to Evaluate the Perceived Effects of Regulation. AIES. [arxiv.org/abs/2405.09679](https://arxiv.org/abs/2405.09679)
27. Rountree, Gastil (2026). The Case for Using Generative AI to Run Deliberation Simulations. Journal of Deliberative Democracy. [delibdemjournal.org/article/id/1625](https://delibdemjournal.org/article/id/1625)
28. Tessler et al. (2024). AI can help humans find common ground in democratic deliberation (Habermas Machine). Science 386; coverage: MIT Technology Review. [technologyreview.com/2024/10/17/1105810](https://technologyreview.com/2024/10/17/1105810)
29. Chen (2026). Human-Simulation Interaction: From Prediction to Exploration in LLM Agent Simulations for Policy. PoliSim@CHI. [arxiv.org/abs/2608.07496](https://arxiv.org/abs/2608.07496)
30. European Commission Joint Research Centre (2023). FABLES: LLM-driven agent populations for policy scenarios. [publications.jrc.ec.europa.eu/repository/handle/JRC135070](https://publications.jrc.ec.europa.eu/repository/handle/JRC135070)

**Critiques and limits**

31. Wang, Morgenstern, Dickerson (2024). Large language models that replace human participants can harmfully misportray and flatten identity groups. Nature Machine Intelligence. [arxiv.org/abs/2402.01908](https://arxiv.org/abs/2402.01908)
32. Park, Schoenegger, Zhu (2024). Diminished Diversity-of-Thought in a Standard Large Language Model. [arxiv.org/abs/2302.07267](https://arxiv.org/abs/2302.07267)
33. Santurkar et al. (2023). Whose Opinions Do Language Models Reflect? [arxiv.org/abs/2303.17548](https://arxiv.org/abs/2303.17548)
34. Agnew et al. (2024). The Illusion of Artificial Inclusion. CHI. [arxiv.org/abs/2401.08572](https://arxiv.org/abs/2401.08572)
35. Larooij, Törnberg (2025). Do Large Language Models Solve the Problems of Agent-Based Modeling? A Critical Review of Generative Social Simulations. [arxiv.org/abs/2504.03274](https://arxiv.org/abs/2504.03274)
36. Ye, Cao, Chen, Ferrara (2026). Stop Drawing Scientific Claims from LLM Social Simulations Without Robustness Audits. [arxiv.org/abs/2605.18890](https://arxiv.org/abs/2605.18890)
37. Lukauskas, Šarkauskaitė (2026). Plausible but Not Valid: A Psychometric Audit of LLMs as Synthetic Survey Respondents. [arxiv.org/abs/2608.14606](https://arxiv.org/abs/2608.14606)
38. Flechtner (2026). The Deliberative Deficit. AIES; Yao et al. (2025). Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate. [arxiv.org/abs/2608.10186](https://arxiv.org/abs/2608.10186), [arxiv.org/abs/2509.23055](https://arxiv.org/abs/2509.23055)
39. Luo, Arora, Guirado (2026). We Need Strong Preconditions For Using Simulations In Policy; Jang et al. (2026). From Simulated Citizens to Simulated Deliberation. [arxiv.org/abs/2604.07838](https://arxiv.org/abs/2604.07838), [arxiv.org/abs/2609.07573](https://arxiv.org/abs/2609.07573)
40. Pew Research Center (30 Sept 2026). How synthetic polling results change based on the AI model. [pewresearch.org/data-labs/2026/09/30/how-synthetic-polling-results-change-based-on-the-ai-model](https://pewresearch.org/data-labs/2026/09/30/how-synthetic-polling-results-change-based-on-the-ai-model)
41. University of Salford and UCL (2026). Most AI models predicted a Reform win in Makerfield; the voters delivered a Labour landslide. [salford.ac.uk/news/most-ai-models-predicted-a-reform-win-in-makerfield-the-voters-delivered-a-labour-landslide](https://salford.ac.uk/news/most-ai-models-predicted-a-reform-win-in-makerfield-the-voters-delivered-a-labour-landslide)
42. Durmus et al. (2023). Towards Measuring the Representation of Subjective Global Opinions in Language Models; AlKhamissi et al. (2024). Investigating Cultural Alignment of Large Language Models. [arxiv.org/abs/2306.16388](https://arxiv.org/abs/2306.16388), [arxiv.org/abs/2402.13231](https://arxiv.org/abs/2402.13231)
43. Hu, Collier (2024). Quantifying the Persona Effect in LLM Simulations; Atil et al. (2024). Non-Determinism of "Deterministic" LLM Settings. [arxiv.org/abs/2402.10811](https://arxiv.org/abs/2402.10811), [arxiv.org/abs/2408.04667](https://arxiv.org/abs/2408.04667)

**Deployments and practice**

44. Singapore GovTech (11 Sept 2026). Using AI to test government messages (Echo). [tech.gov.sg/technews/using-ai-to-test-government-messages](https://tech.gov.sg/technews/using-ai-to-test-government-messages)
45. UK Government, i.AI (2025). Government-built Humphrey AI tool reviews responses to consultation for the first time (Consult). [gov.uk/government/news/government-built-humphrey-ai-tool-reviews-responses-to-consultation-for-first-time-in-bid-to-save-millions](https://gov.uk/government/news/government-built-humphrey-ai-tool-reviews-responses-to-consultation-for-first-time-in-bid-to-save-millions)
46. Market-research vendors (company claims, not independent): Aaru (TechCrunch, 5 Dec 2025), Electric Twin (tech.eu, 12 Feb 2026), Simile, Ipsos PersonaBot, Qualtrics. [techcrunch.com/2025/12/05/ai-synthetic-research-startup-aaru-raised-a-series-a-at-a-1b-headline-valuation](https://techcrunch.com/2025/12/05/ai-synthetic-research-startup-aaru-raised-a-series-a-at-a-1b-headline-valuation)
47. Ipsos for the UK Electoral Commission (2012). Scottish independence referendum question testing. [ipsos.com/en-uk/referendum-scottish-independence-question-testing](https://ipsos.com/en-uk/referendum-scottish-independence-question-testing)
48. Citizens' Initiative Review (Oregon, from 2010) and the Sion (VS) pilot on a federal initiative (Nov 2019). [participedia.net/case/6439](https://participedia.net/case/6439)
49. MIT Technology Review (2025). A small US city experiments with AI to find out what residents want (Bowling Green, KY). [technologyreview.com/2025/04/15/1115125](https://technologyreview.com/2025/04/15/1115125)

**Swiss context**

50. Federal Supreme Court (10 Apr 2019): annulment of the 2016 Heiratsstrafe vote (Blick). [blick.ch/politik/bundesgericht-erklaert-abstimmung-ueber-heiratsstrafe-fuer-ungueltig-wie-lange-kann-sich-die-cvp-freuen-id15266130.html](https://blick.ch/politik/bundesgericht-erklaert-abstimmung-ueber-heiratsstrafe-fuer-ungueltig-wie-lange-kann-sich-die-cvp-freuen-id15266130.html)
51. Geschäftsprüfungskommission des Nationalrats (21 Nov 2023). Report on authority communication before votes. [parlament.ch/centers/documents/de/Bericht%20GPK-N%20vom%2021.11.2023%20D.pdf](https://parlament.ch/centers/documents/de/Bericht%20GPK-N%20vom%2021.11.2023%20D.pdf)
52. swissinfo. VOTO analysis of the 25 Nov 2018 "Swiss law first" vote. [swissinfo.ch/eng/voto-analysis_-swiss-law-first--initiative-challenged-many-voters/44675792](https://swissinfo.ch/eng/voto-analysis_-swiss-law-first--initiative-challenged-many-voters/44675792)
53. Federal Supreme Court, 1P.377/2003 (4 Nov 2003): objective and complete explanations in a municipal vote. [servat.unibe.ch/dfr/bger/2003/031104_1P-377-2003.html](https://servat.unibe.ch/dfr/bger/2003/031104_1P-377-2003.html)
54. swissinfo (2024). It's often the voting booklet that decides yes or no (Strijbis study, commissioned by a campaign-communication body). [swissinfo.ch/eng/swiss-politics/its-often-the-voting-booklet-that-decides-yes-or-no/87490263](https://swissinfo.ch/eng/swiss-politics/its-often-the-voting-booklet-that-decides-yes-or-no/87490263)
55. SRF (2022). Einfachere Sprache: Ist das Abstimmungsbüchlein für viele zu komplex? [srf.ch/news/abstimmungen-15-mai-2022/einfachere-sprache-ist-das-abstimmungsbuechlein-fuer-viele-zu-komplex](https://srf.ch/news/abstimmungen-15-mai-2022/einfachere-sprache-ist-das-abstimmungsbuechlein-fuer-viele-zu-komplex)
56. gfs.bern for the Federal Chancellery (2025), via Netzwoche. KI in der Behördenkommunikation. [netzwoche.ch/news/2025-05-21/ki-in-der-behoerdenkommunikation-ist-okay-aber-nicht-bedingungslos](https://netzwoche.ch/news/2025-05-21/ki-in-der-behoerdenkommunikation-ist-okay-aber-nicht-bedingungslos)
57. Menzi (2021). Swiss Yearbook of Administrative Sciences 12(1): many voters do not understand voting proposals. [doi.org/10.5334/ssas.157](https://doi.org/10.5334/ssas.157)
58. SRF (2019). Aargau study of municipal assemblies; SRF on assembly attendance and the share of municipalities with a parliament. [srf.ch/news/grosse-studie-im-aargau-gemeindeversammlungen-sind-besser-als-ihr-ruf](https://srf.ch/news/grosse-studie-im-aargau-gemeindeversammlungen-sind-besser-als-ihr-ruf)
59. Bern University of Applied Sciences: smartinfo (2026-2028); OST: Fact Attack 2026 (Hack Apertus track 2A); Swissvotes, University of Bern. [bfh.ch/de/forschung/forschungsprojekte/2026-405-463-889](https://bfh.ch/de/forschung/forschungsprojekte/2026-405-463-889), [github.com/JJukic/Apertus-Team-Fact-Attack-2026](https://github.com/JJukic/Apertus-Team-Fact-Attack-2026), [swissvotes.ch](https://swissvotes.ch)
60. Federal Chancellery (28 Sept 2025). Erläuterungen des Bundesrates (the real booklet used in the evaluation). [bk.admin.ch](https://bk.admin.ch)

**Apertus, retrieval and methods**

61. Apertus: Swiss AI Initiative (2025). Apertus technical report; ETH Zurich press release; CSCS (2026), Apertus 1.5. [arxiv.org/abs/2509.14233](https://arxiv.org/abs/2509.14233), [cscs.ch/science/computer-science-hpc/2026/apertus-15-building-the-next-generation-of-open-ai-infrastructure](https://cscs.ch/science/computer-science-hpc/2026/apertus-15-building-the-next-generation-of-open-ai-infrastructure)
62. Robertson, Zaragoza (2009). The Probabilistic Relevance Framework: BM25 and Beyond. [doi.org/10.1561/1500000019](https://doi.org/10.1561/1500000019)
63. Wang et al. (2024). Multilingual E5 Text Embeddings: A Technical Report. [arxiv.org/abs/2402.05672](https://arxiv.org/abs/2402.05672)
64. Cormack, Clarke, Büttcher (2009). Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. SIGIR. [doi.org/10.1145/1571941.1572114](https://doi.org/10.1145/1571941.1572114)
65. Gao et al. (2023). Enabling Large Language Models to Generate Text with Citations. [arxiv.org/abs/2305.14627](https://arxiv.org/abs/2305.14627)
