# Engineering questions from the mentor (7 Oct 2026): what we do, what we measured, why

Each answer has the same shape: **short answer**, **what the app does** (with the code), **evidence** (experiment ids refer to
[`research/LAB-NOTEBOOK.md`](research/LAB-NOTEBOOK.md)), and the **justification** for using or not using the technique. Where a question showed a gap, we say what we
changed. Numbers are from logged runs on the CSCS inference API (70B unless stated); the hackathon gateway behaves the same except where noted.

| # | question | short answer |
| --- | --- | --- |
| 1 | Is Python itself slow and the cause of our issues? | No. Python CPU is **2 %** of the wall time of a run (5 % on the 8B); the wait is the model generating tokens |
| 2 | Do we use asynchronous calls? | Yes, end to end; the run is as parallel as its dependency chain allows |
| 3 | Do we stream responses? | Yes to the screen (setup, events, report, chat sentences); **no** token streaming for the JSON turns, and why |
| 4 | Prompt caching? | The endpoint caches automatically; we measured it and did **not** reorder prompts for it, and why. The 1:1 chat is cache-friendly by design |
| 5 | Context compaction / context-window management? | Bounded by construction (top-k memories and passages, reflections as compaction): a prompt uses **1.1 %** of the window at most |
| 6 | Have we validated RAG against standard practice? | Now yes (E30): our BM25 vs dense and hybrid on a real booklet. Hybrid is better; it is available as an option, off by default |
| 7 | Subagents? Tool-result pagination / truncation? | Each resident is an isolated agent run in parallel; no tool loop, so nothing to paginate; every result set is already bounded |
| 8 | Token counting? Metrics in the frontend? | Added: counted from the endpoint's own `usage`, shown in a "Run metrics" panel and at `GET /simulate/{id}/metrics` |
| 9 | Are the livemap and CSCS endpoints interchangeable? | Yes, with one build: model ids are mapped per endpoint and concurrency adapts (details in [`ENDPOINTS.md`](ENDPOINTS.md)) |

---

## 1. Is Python slow, and is that behind our issues?

**Short answer.** No. We measured it instead of arguing it (E29, `research/exp29_python_overhead.py`; `run_sim.py` now records per-call start/end times and process CPU time).

| measurement (one 5-resident, 3-round run) | 70B | 8B |
| --- | --- | --- |
| wall time | 60.5 s | 26.1 s |
| **process CPU time** (all Python, JSON, TLS, HTTP client included) | **1.33 s (2.2 %)** | **1.31 s (5.0 %)** |
| LLM calls / sum of their latencies | 44 / 249 s | 45 / 96 s |
| time with at least one call in flight | 100 % | 99.9 % |
| mean / peak calls in flight | 3.9 / 5 | 3.4 / 5 |

* **The wait is generation.** Across 464 logged 70B calls, latency is explained to **81 %** by the number of output tokens (≈ 58–64 tokens/s on the 70B, ≈ 154 tokens/s on the 8B; correlation of latency with completion tokens within a run: 1.00), to
  about 12 % by processing the prompt, plus a 0.6 s constant. A resident turn writes ≈ 340 tokens.
* **The wall time is the critical path, not the CPU.** The dependent chain is: persona text (14 s, ≈ 1 000 tokens) → impact judgement (2 s) → per round: reflection (3.6 s) → resident turn (8–11 s) → translation (1.7 s). Three rounds of that chain plus the
  setup are ≈ 60 s, which is what we measure. More concurrency cannot shorten a chain; **5 residents give at most 5 calls in flight** (that is why a limit of 16 or 96 changes nothing at that size, and why 25 residents take only about 1.7× as long as 5: 105 s vs 61 s for three rounds).
* **The pure-Python parts are microscopic** (median of 200 runs): retrieval 0.1 ms (Linden text) and 2.5 ms per query on the 83 k-character booklet (it was 12.1 ms until we cached the term counts of each chunk: a free 5× in `graph/corpus.py`),
  the numeral gate 0.1–0.5 ms per utterance, JSON extraction + Pydantic validation of a turn 0.03–0.12 ms, chunking the booklet once 17–56 ms.

**Justification.** Rewriting any part in a faster language would save at most 2–5 % of the wall time. The levers that *do* exist are all about tokens and the endpoint: fewer output tokens (the persona text is 23 % of the critical path), model size (the 8B is 2.3× faster), overlapping
the translation call with the next step, and the endpoint (CSCS vs livemap: 126 s → 61 s for the same run). Python would only start to matter for a corpus of many thousands of chunks, where the BM25 would need a precomputed inverted index (noted, not needed now).

## 2. Asynchronous programming

**Short answer.** Yes, everywhere a call leaves the process.

* FastAPI and the Socket.IO server are async (`main.py`, `routers/simulate.py`); the LLM client is LangChain's async `ainvoke` / `astream` over httpx (`graph/llm.py`).
* Concurrency inside a run: all residents of a round run as parallel tasks (`graph/nodes/run_round.py`, `asyncio.create_task` + `gather`); personas are generated in parallel and shown as they finish (`npc_orchestrator.py`, `as_completed`); the impact judgements run in parallel (`stance.py`);
  the 5-run spread runs several simulations at once (`routers/ensemble.py`).
* A **limiter** (`graph.llm.Limiter`) bounds requests in flight and **adapts**: it starts at 4, doubles after a clean streak, halves on a 429 or a gateway timeout, remembers the ceiling that worked, and steps back one level when a rise of the limit makes every answer more than 2× slower per token (a server that queues
  instead of rejecting). Transient 429/502/503/504 are retried on the same model. This is what makes one build work on both endpoints (E29, `ENDPOINTS.md`).

**Evidence.** Throughput scales almost linearly with requests in flight on CSCS (E21: 66 → 4 359 tokens/s from 1 to 96); the 25-resident run took 89–97 s with the limiter going 4 → 32 and no error.
**What stays sequential, and why:** rounds (round *r+1* needs the stances after round *r*), and the calls of one resident (the translation needs the turn, the turn needs the reflection). These are data dependencies, not missing `await`s.

## 3. Response streaming

**Short answer.** The application streams to the screen; the model's tokens are streamed only where it helps and is safe.

* **To the user, yes:** Socket.IO events arrive while the run is going: setup progress, each resident as it is created (`npc_added`), the events of each round (`npc_events`, `round`), the report, the metrics, and since 7 Oct the **chat answer sentence by sentence** (`npc_chat_chunk`).
* **Model tokens, chat: yes, checked.** `stream_npc_chat_reply` (`graph/chat.py`) reads the model's stream, cuts it into sentences, runs the guardrails on each complete sentence (figures outside the sources stripped, bracketed text removed, Swiss spelling) **before** sending it, and the final message carries
  the validated citations and the translation. The user never sees text the checks would have changed. Measured live (E32, 25 answers): first text after **1.5 s** (median), whole answer after 2.4 s; quality unchanged (0 invented figures, 0/5 vote recommendations). The gain is modest because the answers are short (2–3 sentences).
* **Model tokens, resident turns and report: no.** They are JSON objects that must be complete before they can be validated (schema, citation labels, numeral gate, stance binding); a half JSON is not displayable, and the first token does not start anything useful. The turns of one round already arrive as they finish.

## 4. Prompt caching

**Short answer.** The endpoint does prefix caching (vLLM automatic prefix cache). We measured it and use it where it is free.

* **Measured:** CSCS reports `cached_tokens`: 94 % of a 24.5 k-token booklet prompt was served from cache when the same text came first (E26); in our resident loop **17–24 %** of prompt tokens are cached (E27) because the prompt starts with the persona. The hackathon gateway does not report the field.
* **What it is worth in the loop:** a call is 81 % generation and ≈ 12 % prompt processing, so even a perfect cache saves at most ≈ 1 s of a 5.5 s call, and a realistic one (the instructions and the JSON example are 34 % of the prompt, the persona 29 %) ≈ 0.3 s.
* **Decision, loop: not reordered.** Moving the 2.7 k-character instruction block to the front would make a third of the prompt cacheable, but it moves the instructions away from the end of the prompt, where the speech-binding paragraph must stay (E15: a last-paragraph reminder lifted speech–stance agreement from 0.5 to 0.9). A ≈ 5 % latency gain does not justify re-validating
  that behaviour. Caching mostly saves GPU time (cost), not the user's wait.
* **Decision, chat: yes.** When the document is between 6 000 and 100 000 characters it is placed **first** in every chat prompt, identical for every resident, so the cache serves it (E26/E28).

## 5. Context compaction and context-window management

**Short answer.** The context is bounded by construction; compaction is the reflection step of the generative-agent design.

* **Bounded inputs.** Only the top 8 memories enter a prompt (`MEMORY_TOP_K`, recency × importance × relevance), only the top 4–6 passages (`default_top_k`), the policy summary and the round context are short, the notes are capped at 30 000 characters.
* **Compaction.** Memories that matter are summarised into reflections once the accumulated importance passes a threshold (`maybe_reflect`, `REFLECTION_THRESHOLD`), as in Park et al. 2023; the raw stream grows, the prompt does not.
* **Measured context use.** Resident-turn prompts grow with the rounds but stay small: **2 139 → 2 503 → 2 706 tokens** over rounds 1–3 (25 residents, E27); mean 1.25 k, maximum 2.9 k tokens = **1.1 % of the 262 144-token window**. Composition of one prompt (characters): instructions + example 34 %, persona 29 %, passages 12 %, round + neighbours 8 %, memories + plan 1.4 %.
* **The one place the window is used deliberately** is the chat with a mid-sized document (up to 100 000 characters ≈ 37 k tokens ≈ 14 % of the window).

**Justification.** A compaction layer on top of this (summarising the conversation, evicting passages) would add calls and failure modes to solve a problem that does not occur at 1 % usage. We would need it for runs of many rounds (the original UI default was 75): the prompt grew 17 % from round 1 to 2 and 8 % from 2 to 3; the top-8 cap bounds it, but we measured only 3 rounds.
The new metrics panel shows the context use of every run so the day it matters is visible.

## 6. Have we validated our RAG against standard practice?

**Short answer.** Yes, now, on a real booklet and against the usual baselines (E30, `research/exp30_rag_baselines.py`), and it changed one decision.

Gold set: the 14 questions with a gold fact in the real 48-page Federal Council booklet (E17), German; metrics recall@k, MRR@10, nDCG@10; 480-character chunks (the shipped size). The relevant chunk is any chunk containing the gold phrase.

| retriever | recall@4 | recall@6 | recall@8 | MRR@10 | nDCG@10 |
| --- | --- | --- | --- | --- | --- |
| **BM25 as shipped** (accent folding, 6-character stems, ballot question pinned) | 0.79 | 0.86 | 0.86 | 0.29 | 0.47 |
| BM25 without the pinned chunk | 0.86 | 0.86 | 0.93 | 0.82 | 0.86 |
| dense, multilingual-e5-large | 1.00 | 1.00 | 1.00 | 0.89 | 0.90 |
| **hybrid: BM25 + e5-large, reciprocal rank fusion** | **1.00** | **1.00** | **1.00** | **0.91** | **0.93** |
| dense / hybrid, paraphrase-multilingual-MiniLM | 0.71 / 0.86 | 0.79 / 0.93 | 0.79 / 0.93 | 0.56 / 0.76 | 0.63 / 0.79 |

* **BM25 is a sound baseline here** (recall@6 = 12/14, the same as the end-to-end QA of E17), but the industry default for a multilingual corpus, **hybrid with a dense model, is better on every metric** (+14 points of recall@4, MRR 0.91 vs 0.82). A small paraphrase model is worse than BM25: the choice of embedding model matters.
* **The ballot-question pin costs retrieval slots** on a real booklet: it takes rank 1 (MRR 0.29 is that artefact: all passages reach the prompt, order does not matter to the model) and 1–2 of the 4–6 slots. At the shipped k = 6 recall is equal (12/14 with and without), so we left it; the parameter `max_pins` exists.
* **Chunk size:** 480 vs 960 characters is a wash for BM25 and hybrid; 1 500 characters hurts the dense model (recall@4 0.86). We kept 480.
* **Beyond retrieval** (E17, E26, E28): grounded QA correct 12/14, abstention on the three unanswerable questions 3/3, citation labels valid 17/17, and the chat's whole-document option (13/14).
* **Limits of this validation:** n = 14 questions, one document, German only (a French booklet could not be downloaded), a gold phrase can be cut by a chunk boundary (it favours bigger chunks), no cross-encoder re-ranker and no query rewriting (no model for them on the endpoints we can use). Differences of one question (7 points) are not significant.

**Decision.** Hybrid retrieval is implemented as an **option** (`EMBEDDING_MODEL=intfloat/multilingual-e5-large`, `pip install fastembed`; `graph/dense.py`), **off by default**: neither inference endpoint offers embeddings (404/403), the model is a 2.2 GB local download, and the app must run air-gapped. Where an embedding model is available we recommend turning it on.

## 7. Subagents, and tool-result pagination and truncation

**Short answer.** Each resident *is* an isolated agent; there is no model-driven tool loop, so there are no tool results to paginate, and every result set is bounded anyway.

* **Agents.** A resident turn is its own LLM context (persona, its memories, its passages) run in parallel and merged as events: no shared transcript, so personas cannot bleed into each other and a failed resident does not fail the round (`return_exceptions=True`). The "swarm" graph (an orchestrator picks initiators, reactors respond) is
  implemented and measured: **+27 % wall time and no quality gain** (E3d), so it is off by default. We did not build hierarchical sub-agents (an LLM planner delegating to workers): the work is not decomposable beyond "one call per resident", and every extra hop is another 3–15 s on the critical path.
* **Tools.** The loop uses none, deliberately: parallel tool calls are not supported (one call per request, 11/11 on both models, same on CSCS, E1/E20) and thinking models refuse tools (HTTP 400). Retrieval, the calculator and the checks are ordinary code run by the app, not tools chosen by the model; the model does not decide when to look something up, which is what keeps the citations verifiable.
* **Pagination / truncation.** A "page" is fixed and small: 4–6 passages of ≤ 480 characters; the UI shows 240-character snippets; the non-chunked chat fallback cuts the policy text at 800 characters; the report samples a bounded number of events. Nothing returns an unbounded list. Pagination would matter for an agent that asks for "more results"; ours does not.

## 8. Token counting and metrics in the frontend

**Short answer.** Implemented on 7 Oct, counted from the endpoint's own `usage` field, shown in the UI.

* **Where:** `graph/metrics.py` records every call (prompt, completion and cached tokens, latency, model) from the single place all JSON calls pass (`graph.llm._ainvoke`), the streamed chat and the thinking call; a ContextVar attributes calls to the run that made them (tests prove two concurrent runs never mix).
* **Surface:** the `round` message carries the snapshot, a final `metrics` event follows the report, `GET /simulate/{id}/metrics` returns it, `GET /metrics` the whole process. The frontend shows a collapsible **"Run metrics"** panel: tokens in/out, share cached, mean prompt, **context use (max) as a share of the 262k window**, mean / p95 latency,
  decode speed, requests-in-flight limit, 429 / 5xx retries, downgrades, and the model and endpoint host.
* **Why `usage` and not a tokenizer:** Apertus has its own tokenizer, an estimate would be a guess, and the endpoint's number is what is billed or limited. We need no pre-flight estimate (1 % context use); the one size guard, `CHAT_STUFF_MAX_CHARS` = 100 000 characters, is a character budget (measured ratio: 280 000 characters ≈ 105 000 tokens, E12/E22).
* **Seen in a live run** (25 residents, 2 rounds, CSCS): 143 calls, 168 k tokens in, 51 k out, 16 % cached, mean latency 6.6 s, p95 14.4 s, in-flight limit grown to 21–32, 0 retries; on the hackathon gateway the same kind of run showed mean latency 36 s and decode at 12 tokens/s per request (the gateway was busy).

## 9. Interchangeability of the two endpoints

See [`ENDPOINTS.md`](ENDPOINTS.md): one build, three environment variables, model-id mapping, adaptive concurrency, both directions tested live.
