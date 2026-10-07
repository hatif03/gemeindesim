# 08 — Plan: using the CSCS inference API

Written 6 October 2026, after E20–E27 (`07-cscs-vs-livemap.md`, `LAB-NOTEBOOK.md`). **Update 7 Oct: the mentors confirmed that the judges run the app on the CSCS API.** The defaults (`.env.example`, `docker-compose.yml`) are therefore the CSCS values, and one build works on both endpoints (`../ENDPOINTS.md`). The CSCS key we used is personal and is not part of the submission; the judges bring their own.
Every change below is a switch with a safe default.

## 1. Which previous limitation does it solve?

| # | limitation we documented on 5 Oct | on CSCS | verdict | what we do about it |
| --- | --- | --- | --- | --- |
| L1 | ≈ 4 requests in flight (429 above) | none found to 96 in flight | **solved** | `LLM_CONCURRENCY=16` profile (`env.cscs.example`); keep 4 as the default |
| L2 | slow (70B 10–11 s per call, a 3-round town takes ≈ 2 min) | 70B 3.8 s per call; a 5-resident 3-round run took ≈ 60 s (E27); a 25-resident town 105 s | **solved for demos** | record the demo video on CSCS; keep replays as the safety net |
| L3 | one run is an anecdote, no budget to repeat | three parallel runs took 62 s (E27); five 3-round runs ≈ 2–3 min | **solved** | in-app **"Run 5×: show the spread"** (built, `POST /ensemble`, `/spread` page) |
| L4 | long context only tested to ≈ 105k | recall to 233k tokens on **both** endpoints (CSCS: 8B 30/30, 70B 26/30; 3 facts: 70B 9/10, 8B 5/10; CSCS is 2–3× faster) and a 94 % prefix-cache hit on a shared booklet | **tested; a speed gain, not a new capability** | whole-booklet mode for ≤ 25k-token booklets: 13/14 vs 11/14 in the QA (E26); **on in the 1:1 chat** (≤ 100k characters), off in the loop |
| L5 | thinking span left in `content`, `reasoning` null | 8B-thinking fills `reasoning` and keeps it under `json_object`; 70B-thinking still leaves the span | **partly solved** | keep `strip_think_tags`; use the 8B-thinking only if a visible reasoning trace is wanted (it is slow and 504-prone at > 2 in flight) |
| L6 | no parallel tool calls | same | **not solved** | unchanged: no tools in the loop |
| L7 | `temperature 0` not reproducible | same on real prompts, with or without `seed` | **not solved** | log every call; report ranges over runs |
| L8 | yes-bias | same on all four models, thinking included | **not solved** | code-owned stance stays the answer |
| L9 | weak Swiss facts, authority deference | same checkpoints, not a deployment property | **not solved** | calculator, retrieval and the no-recommendation line stay |
| L10 | 1:1 chat was ungrounded | not endpoint-related, but now affordable to test live | **fixed in code** | grounded chat (stance, passages, citations, number gate, Swiss spelling) |
| L11 | in-app multi-seed control missing | needs speed | **built** | see L3 |
| L12 | replays did not carry the report | not endpoint-related | **fixed in code** | recordings now include the report |
| L13 | no embedding model for hybrid retrieval | 404 / 403 | **not solved** | optional local small embedding model (below) |
| L14 | no independent judge family | 403 for Gemma/Nemotron/GLM/Kimi | **not solved** | Apertus judging Apertus stays a stated limitation; use logprobs and hand grading |

## 2. What changed in the code today (all behind defaults that keep livemap behaviour)

| change | where | default | test |
| --- | --- | --- | --- |
| Grounded 1:1 chat (stance line + binding, retrieved passages, `[P#]` citations validated and shown as chips, numeral gate, Swiss spelling, optional reply translated to the user's language) | `graph/chat.py`, `graph/prompts.py`, `routers/simulate.py`, both chat modals | on | 4 tests (`test_chat_grounding.py`) + live E25 |
| 5-run spread (`POST /ensemble`, `GET /ensemble/{id}`, button on the Run node, `/spread` page) | `routers/ensemble.py`, `NodeCanvas`, `app/spread` | opt-in button | 2 tests |
| Saved replays carry the report; loader restores it | `useSimulation.ts`, `types/backend.ts`, `research/make_replay.py` | on | tsc via Docker build |
| `LLM_VOICE_NAME`: a different model for what the user reads (report, chat) | `config.py`, `chat.py`, `economic_report.py`, compose | empty = same model | – |
| Retry 502/503/504 on the same model twice before any downgrade | `graph/llm.py` | on | 1 test |
| Harness runs on any endpoint (`RESEARCH_SUBDIR`, `RESEARCH_M70/M8`, `RESEARCH_CONCURRENCY`, `research/cscs_env.sh`) | `research/common.py` | unchanged | – |
| `env.cscs.example`, compose passes `LLM_FALLBACK_NAME`, `LLM_VOICE_NAME` | `track_2b/` | – | – |

## 3. Plan

### 3.1 Before submission (small, no new risk)
1. **Record the demo video on CSCS** (the run is ≈ 1 min instead of ≈ 2–4): `cp env.cscs.example` lines into `.env`, `docker compose up -d`, follow `docs/DEMO-SCRIPT.md`. Keep the replay as the fallback.
2. **State both endpoints in the report and the judge briefing**: measured on two hosted deployments; CSCS is a Swiss national research infrastructure whose documentation says prompts are not recorded; neither is a local deployment, so the on-prem claim stays "configured, probe ready".
3. **Re-run the final measurement on CSCS** (E25, 5 seeds × 2 sizes) and quote it next to the livemap numbers: it is a replication on another deployment.
4. **Mentor brief**: update the topics with E20–E27 (gateway flags, reasoning parser, 4-in-flight, `T=0`).
5. **Do not** switch defaults to CSCS, adopt `json_schema` (E23), or put the thinking models in the resident loop.

### 3.2 After the first demo, evidence-gated (each has a stop rule)
| idea | experiment | adopt if | cost |
| --- | --- | --- | --- |
| Whole-booklet mode (`CONTEXT_MODE=stuff` for documents ≤ 25k tokens, booklet as the cached prompt prefix, retrieved passages still labelled for citations) | real booklet through the app (PDF upload, E27) with and without the full text in the prompt: speech match, cited-passage relevance, figure grounding, wall time | citations stay valid and relevance rises without persona dilution | 1 day |
| 8B loop + 70B voice (`LLM_NAME` = 8B, `LLM_VOICE_NAME` = 70B) | 3 paired seeds: speech match, report guardrails, wall time | report quality of the 70B at the cost of the 8B loop | ½ day |
| Larger towns (25 residents, `MAX_NPCS` 25 → 50) | E25 25-resident run: wall time, event diversity, UI legibility | town stays legible and ≤ 3 min | ½ day |
| Compare-conditions at n = 10 paired seeds on the 70B (upgrade of E19: n = 3, 8B) | `run_sim.py --recommendation/--corpus`, 4 conditions × 10 seeds | – (measurement) | ½ day, ≈ 40 min of calls |
| Logprob-based stance fidelity and classifier calibration (replace argmax judges by probabilities) | re-score E13/E14 with `top_logprobs` | agreement with hand labels beats argmax | 1 day |
| Local small embedding model for hybrid retrieval (no endpoint offers one) | E17 recall@4 with BM25 + multilingual embedding | recall@4 ≥ 13/14 | 1 day, +500 MB dependency |

### 3.3 Not recommended
Strict `json_schema` on CSCS (8B degenerates), the 70B-thinking in the loop (no reasoning parser, slow), tools anywhere (no parallel calls), a different model family as judge (403), relying on `seed` for reproducibility.

## 4. Risks and how they are handled

| risk | mitigation |
| --- | --- |
| The key is personal and shared; fair-use limits unknown beyond 96 in flight | `LLM_CONCURRENCY` 16, not 96; ensembles capped at 120 residents per request; never in the submission defaults |
| Key leaks | `.env.cscs` is git-ignored (`.env.*`); the raw logs contain no headers; scan before every push |
| 504 under mixed load | retry twice on the same model (done); thinking models ≤ 2 in flight |
| A judge cannot reproduce CSCS results | livemap results stay the primary numbers; CSCS is reported as a replication with the same scripts and seeds |
| "Sovereign" over-claim | wording: measured on two hosted endpoints; CSCS documents no recording of prompts; local/air-gapped remains configured, not measured |
| CSCS numbers vary by day | dated, n stated, same-day controls stored in `research/results/livemap_2026-10-06/` |
