# Lab notebook — GemeindeSim on Apertus 1.5

Chronological record of every analysis, decision and experiment. Entries are
append-only; corrections are made by a new entry, not by rewriting history.
Raw data: `research/results/` (one JSONL per experiment, every gateway call with
full request and response). Harness: `research/common.py`, `research/run_sim.py`.
Date of work: 5 October 2026 (hackathon online stage, 1–16 Oct).

## Conventions

- **H#** hypothesis (written *before* looking at the data where possible), **E#**
  experiment, **D#** decision, **F#** finding.
- Model ids are the gateway ids (`apertus-v1.5-70b`, `apertus-v1.5-8b`). Gateway:
  `vllm-0.23.1rc1…-tp2` per `system_fingerprint`. Temperature 0 unless stated.
- Nothing here claims more than the logged data supports. "n" is always stated.

---

## 2026-10-05 — Session start: what we have, what is claimed

**Context.** Track 2B (own project). Judging (from `docs/HACKATHON.md`, the Notion
pages themselves are JS-rendered and could not be fetched by tooling): purposeful
use of AI, technical rigour, value/cost/scalability, sovereign deployability,
implementation feasibility. The organisers' framing for this track and the "test
the model's limits" ambition come from the user brief.

**State of repo at start** (`main`, commit 0bb53b2): FastAPI + LangGraph backend,
Next.js + Phaser frontend, 69 offline tests, a probe write-up of Apertus' tool
behaviour (`PROBE-AND-PLAN.md`), a judge briefing, a 5-page technical report.
Evidence in the report: "offline schema fixtures 20/20" and one live 70B run.

**D1 — Treat the existing claims as hypotheses to test, not facts.** Reason: the
"20/20 schema" number comes from hand-written *valid* fixtures (`test_eval_schema.py`
builds the objects itself and validates them), so it measures the Pydantic model,
not Apertus. The probe doc's "filled example object" claim differs from the code
(see F2). A paper needs measured, reproducible numbers.

**D2 — Instrument the real pipeline rather than write parallel test prompts.**
`research/run_sim.py` drives the unmodified LangGraph graph headlessly and wraps
`graph.llm._ainvoke` to log every prompt/response/token count. Reason: ecological
validity — we measure what the app really sends.

### E0 — Test suite time (offline suite is not offline)

`pytest` 69 passed. First run 420 s, second run 50 s. `--durations`: one test,
`test_e2e.py::test_full_pipeline`, takes 45 s and calls the live gateway.
**F0:** the "offline" suite contains a live-gateway test; wall time is dominated by
gateway latency, which varied ~8× between two runs minutes apart. Implication for
the paper: latency numbers must be reported as distributions with timestamps.

### E4 — Does the code-side opinion update polarise residents with no conversation?

**H4.** `_apply_opinion_dynamics` applies Baumann drift
`0.02·tanh(α·x)` to every resident each round whenever α>1.5 (medium: α=2,
high: α=3.5), independent of any chat, so measured "polarisation" is partly an
artefact of the update rule.

**Method.** `research/exp04_drift_artifact.py`: 25 residents, political leaning
~U(−1,1), 15 rounds, **zero chat events**, 20 seeds, per controversy level.

**Result** (`research/results/e04_drift_artifact.json`):

| controversy | mean abs leaning start → end | residents with abs>0.9 at end | moderate (abs<0.3) start → end |
| --- | --- | --- | --- |
| low (α=1) | 0.506 → 0.506 | – | 0.26 → 0.26 |
| medium (α=2) | 0.506 → 0.686 | 35.4 % | 0.26 → 0.16 |
| high (α=3.5) | 0.506 → 0.723 | 38.6 % | 0.26 → 0.12 |

A single moderate resident at x=0.10 reaches 0.178 (medium) / 0.251 (high) in 15
rounds with nobody speaking to them.

**F4 (confirmed).** The simulator manufactures polarisation. At the default 3
rounds the effect is small (≈ +0.01–0.03), but at the advertised 15 rounds it
shifts the whole distribution. Any "the town polarised" claim from a long run is
confounded. Also: `political_leaning` is a generic left–right score drawn
uniformly at random (`npc_orchestrator._random_base`), unrelated to role or to the
policy, so even the non-artefact part measures nothing about the Vorlage.

### E3a — First instrumented baseline: Linden DE+FR, 5 NPC × 3 rounds, 70B, seed 1

Run: `research/results/sims/base70_s1{.json,.calls.jsonl}`. Wall time 235 s for the
simulation + report. 38 LLM calls: 15 resident turns, 10 translation hops, 5
personas, 5 reflections, 1 policy parse, 1 character extraction, 1 report. Zero
errors, zero repair calls. Mean call latency 14.4 s (median 11.6, max 66 s). Tokens:
51 142 in / 13 868 out (≈ 65 k per run).

Observations from reading every event (qualitative, n = 27 events):

1. **The report asserts an outcome the simulation never produced.** Report summary
   (DE): *"Die Vorlage erhöhte den Steuerfuss und bewilligte einen Schulhauskredit …
   verhinderte eine Verschiebung des Projekts um mindestens drei Jahre."* The
   simulation holds no vote and tracks no stance; the model narrated "the measure
   passed" in past tense. This is the single worst finding so far because it
   violates the project's own Charter promise (describe, do not decide) in a way the
   `_strip_vote_advice` regex cannot catch.
2. **Citation ids are meaningless.** Events carry `used_source_ids` like `['2','3','6']`
   or `['#2','#3','#7']`; real passage ids look like `Author_notes_pasted_text___#3`.
   `grounded=True` is set whenever no *unknown numeral* appears, and the
   `or pack` clause makes the id check vacuous. So "grounded" does not mean cited.
3. **Residents re-introduce themselves every round** ("Anna, ich bin Petra
   Schneider …", "Bonjour Léa. Je suis Alice Martin, votre voisine") although the
   relationship graph says they know each other. Believability defect.
4. **Event mix is 9/27 chat-dominated; no price_change, no protest** in a vote about
   taxes, so the headline "price/unrest" dashboard is empty (`price_pressure 0`,
   `social_unrest_index 0`). Dashboard indicators designed for tariffs (Egg Index)
   do not fit a municipal vote.
5. **Mood collapses to neutral** (3/5 neutral at end) although every resident is
   written with a polarising persona.
6. **Persona incoherence from random leaning.** French teacher at +0.88 ("strongly
   conservative"), municipal employee +0.85 — drawn from `uniform(-1,1)`, not from
   role. Tenant −0.81 is plausible by accident.
7. **Report language/format.** The report is generated in German (the model follows
   the German corpus), then the *English* `NO_VOTE_LINE` is appended: mixed-language
   output on a Swiss page. Layoff/closure regexes are English-only.
8. **Translation hop works**: DE↔FR chat produced fluent translations (spot check,
   not scored).

*Next:* more seeds and the 8B (running in background: `base70_s2,s3`, `base8_s1,s2`),
then dedicated experiments for each suspicion above.

---

## 2026-10-05 — Retrieval, numeral gate, rate limit

### E5 — What does retrieval actually hand the resident? (offline, from logged prompts)

Method: `research/exp05_retrieval.py` parses the passage block out of the 15
resident prompts of `base70_s1` and checks six key facts of the Linden corpus.

| key fact present in the 4 retrieved passages | prompts (of 15) |
| --- | --- |
| credit 4.8 M | 15 |
| 240 CHF household example | 15 |
| "what Yes / what No changes" paragraphs | 15 |
| deficit 1.2 M | 14 |
| savings 400 k / 200 k | 14 |
| **the vote question itself (118 % → 124 %)** | **4** |

**F5a.** The demo corpus is ≈ 1.6 k characters per language (≈ 9 chunks of 420
characters). Four retrieved chunks are therefore about half the corpus: the
"closed-corpus retrieval" claim is **not stressed** by the shipped sample. RAG
quality cannot be judged on it; a real booklet is needed (see D5).
**F5b.** Even there, the *actual voting question* reached only 4/15 prompts. The
query is `policy_summary + neighbour names + round context + profession`, where
`policy_summary` is the English LLM summary of sectors/impacts, i.e. mostly
non-matching tokens against a German/French corpus. Retrieval is largely
tie-break noise.
**F5c (bug).** `chunk_policy_document` assigns **one** language to a whole `---
Source ---` block. The pasted DE+FR notes are one block → all 9 chunks are tagged
`de`; the `lang=` filter in `retrieve_passages` is a no-op and French residents
receive German passages (verified: tags `['de']*9`, per-chunk detector gives
`de×5, fr×4`). Chunks are also cut mid-word at 420 characters ("rfuss bleibt seit
2019 …") and the first chunk contains the `--- Author notes ---` header.

### E6 — Numeral-grounding gate on edge cases (offline)

`research/exp06_numeral_gate.py`, 12 hand-built cases against the Linden corpus:
gate behaves correctly on **8/12**.
- ✅ Swiss thousands separators (`80'000`, `400’000`, narrow-nbsp), decimal comma,
  grounded integers, a hallucinated percentage.
- ❌ *Correct* derived arithmetic (240/12 = 20 CHF/month) is flagged and rewritten
  to `[n] CHF pro Monat`: false positive, hurts the more capable behaviour.
- ❌ A hallucinated "2 Millionen CHF" **passes**, because the corpus' list
  numbering (`1.`…`5.`) puts the digits 1–5 into the allowed set.
- ❌ The same list-number leak lets an invented "4 Franken" pass next to a grounded
  "124 %".
- ❌ Spelled-out numbers ("Sechzig Prozent") are invisible to a digit regex.
- Additionally `strip_ungrounded_numerals` uses `str.replace`, so stripping an
  ungrounded `4` would also corrupt a grounded `124` (substring collision).

**F6.** The gate is a weak heuristic, not the "every number is grounded" guarantee
the docs imply (PROBE-AND-PLAN §6.3). It needs numeric normalisation, exclusion of
list indices, word-boundary replacement, and a stated residual error rate.

### E2 (first attempt) — structured output, replayed real prompts: INVALID, kept for the record

`research/exp02_structured.py` replays the 15 logged resident prompts under 4
format conditions × 2 models. Result table looked alarming for the 70B under
filled-example / no-json conditions (valid 0.80 / 0.67). **Inspection of the raw
log shows those "failures" are empty responses: 13 of 120 requests received HTTP
429 and exhausted the harness' retries.** The background simulation batch and the
experiment shared one API key, so the run was contaminated by *my own concurrency*.
The numbers are discarded. They are retained in `results/e02_structured.jsonl`
(to be overwritten by the clean re-run, see D4).

### F7 — The gateway limit is 5 parallel requests per key; the app defaults to 6

Verbatim error body (key id elided): `Rate limit exceeded … Limit type:
max_parallel_requests. Current limit: 5, Remaining: 0.` The app's
`LLM_CONCURRENCY` default is **6** (`config.py`), above the limit. Worse,
`invoke_llm_structured` reacts to any error containing "429/rate/overloaded/
timeout/503" by **silently swapping the model to the 8B for the retry**
(`llm.py:278-284`). So under normal judge usage the 70B demo will degrade to the
8B on some calls without any signal, and a "70B run" is not guaranteed to be a
70B run. A second defect in the same retry: when the first attempt failed with a
Pydantic error on `target_npc_id: null` (the model emitted `null` for a `str`
field copied from the placeholder example), a whole attempt was burned on a
trivially recoverable type error.

**D3 — Fix the concurrency/fallback policy** (to implement): default concurrency 4;
on 429 wait and retry the *same* model; downgrade to 8B only on timeout and log
it; coerce `None → ""` for string fields in `NPCEvent`.

**D4 — Experiment hygiene:** the harness default concurrency is now 3, retries 429
with capped exponential back-off, flags `api_failed`, and experiments must not run
while another job uses the key. Sim batches and API experiments are serialised.

---

## 2026-10-05 — Baseline metrics (E3), first two 70B seeds

Scorer: `research/analyze_sims.py` (programmatic only; definitions in file). Runs:
`base70_s1`, `base70_s2` (Linden DE+FR notes, 5 residents, 3 rounds, 70B, temp 0,
seeds only affect persona draws/relationships). Third seed + two 8B runs pending.

| metric | s1 | s2 |
| --- | --- | --- |
| wall time, sim only | 235 s | 548 s (shared key with E2 → contention) |
| LLM calls / retried calls / failed calls | 38 / 0 / 0 | 43 / 5 / 2 |
| tokens in / out | 51 142 / 13 868 | 61 657 / 15 726 |
| events (chat share) | 27 (0.67) | 27 (0.63) |
| event types | chat 18, mood 5, move 4 | chat 17, mood 4, price 2, protest 2, move 2 |
| **cited ids that exist in the corpus** | **0 / 44** | **0 / 37** |
| self-introductions among chats | 39 % | 29 % |
| language of utterance = resident language | 100 % | 100 % |
| `ß` occurrences in generated text | 3 | 15 |
| residents' final mood | 3 neutral | mixed |
| report asserts the measure passed | yes | yes |
| report mixes languages (DE text + English disclaimer) | yes | yes |
| key "118→124" chunk in resident prompt | 27 % | 11 % |

**F8 — Citations are decorative (0 % valid).** The prompt tells the model to cite
"ids in [brackets]"; ids are `---_Author_notes_pasted_text_---#6`. The model writes
`['2','3','6']` or `['#2']`. Nothing validates them, and `grounded=True` is assigned
regardless. The headline technical claim "residents cite sources" is, as built, false
on this endpoint. (The literature expects ≈ 50 % incomplete support even for strong
models — ALCE — so a validator is mandatory.)
**F9 — Swiss orthography.** `ß` appears in generated Swiss-German text (15 times in
one run). Swiss Standard German has no ß. The Apertus 1.0 recommended system prompt
asks for "Swiss High German (no ß)" (lit. review §3.4); the app never sets a system
prompt. A deterministic `ß→ss` post-filter is the right fix for Swiss output.
**F10 — Language fidelity is good.** 100 % of utterances were in the resident's
language in both runs (stop-word heuristic, n=54). The "one language per completion"
design decision held; the translation hop produced fluent DE↔FR output (read, not
scored). This is a *positive* result for Apertus 1.5 on this task.
**F11 — Interface mismatch for chat targets.** The prompt asks for
`target_npc_id` but lists nearby people **by name only**: of 39 chat events,
24 targets were names and 15 `npc_N` forms; 3 chats happened with "Nobody is nearby"
despite the instruction. `normalize_npc_id` + `_validate_chat_target` rescue this
silently. A consistent interface (show ids) removes a whole repair layer.
**F12 — Self-introduction.** 29–39 % of chats (also after round 0) start with
"Ich bin <Vorname Nachname>" / "Je suis …" to people the relationship graph says
they know. Believability defect, probably induced by the persona block repeating
name + profession at the top of every prompt and by the absence of conversation
history between the two parties.

---

## 2026-10-05 — Baseline complete: 3× 70B, 2× 8B (E3b)

All five runs: Linden DE+FR, 5 residents × 3 rounds, temp 0. Table (scorer output):

| metric | 70B s1 | 70B s2 | 70B s3 | 8B s1 | 8B s2 |
| --- | --- | --- | --- | --- | --- |
| sim wall time | 235 s | 548 s* | 219 s | **30 s** | **28 s** |
| mean call latency | 14.4 s | 32.4 s* | 14.2 s | 2.3 s | 2.3 s |
| events / chat share | 27 / .67 | 27 / .63 | 28 / .54 | **15 / 1.00** | **15 / 1.00** |
| event types used | 3 | 5 | 4 | **1** | **1** |
| cited ids valid | 0/44 | 0/37 | 0/35 | 0/25 | 0/18 |
| self-intro rate | .39 | .29 | .20 | .07 | .33 |
| language correct | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| report asserts the vote passed | yes | yes | no | no | no |
| report mixes DE text + English disclaimer | yes | yes | yes | yes | yes |
| key question chunk in prompt | .27 | .11 | .00 | .27 | .33 |

\* s2 overlapped with my own E2 job on the same key (contention) — excluded from latency statistics.

**F13 — 8B collapses event diversity.** Over 30 resident-turns the 8B produced
exactly one event per turn and always `chat` (the 70B averages 1.8 events/turn with
chat ≈ 0.6 and 4–5 of the 5 types across runs). Consequence for the product: the 8B
"fallback" is not a graceful degradation — it silently removes moves, moods, price
changes and protests, i.e. most of the map's visible behaviour. Combined with F7
(silent 8B swap on 429) this means *some* calls of a "70B run" can have this
profile. It also suggests the one-line instruction "prefer at least two events" is
followed only by the 70B.
**F14 — 8B is ≈ 7.5× cheaper in wall time** (28–30 s vs ≈ 220 s for the same
simulation, same token volume ≈ 48 k in / 10 k out) with identical language fidelity.
That is a real value/scalability argument (judging criterion 3) *if* event diversity
can be restored on the 8B — which becomes an improvement target.
**F15 — Reports assert the outcome in 2 of 3 70B runs, 0 of 2 8B runs.** The bad
behaviour is probabilistic and prompt-fragile, not systematic: needs an explicit
instruction + a metric, not a one-off check (see E9).
**F16 — The question chunk is almost never retrieved (0–33 %).**

---

## 2026-10-05 — E10 gateway throughput / rate limit (raw requests, no retries, idle key)

`research/exp10_throughput.py`; one real resident prompt, `max_tokens 500`, json mode;
n = max(6, 2·c) requests per level. Raw numbers in `results/e10_throughput.json`.

| model | concurrency | ok / n | HTTP 429 | p50 latency | aggregate tok/s |
| --- | --- | --- | --- | --- | --- |
| 8B | 1 / 2 / 4 | 6/6, 6/6, 8/8 | 0 | 1.8 / 2.3 / 2.1 s | 158 / 292 / 555 |
| 8B | 5 / 6 / 8 | 4/10, 4/12, 4/16 | 6 / 8 / 12 | – | – |
| 70B | 1 / 2 / 4 | 6/6, 6/6, 8/8 | 0 | 11.3 / 10.9 / 10.3 s | 40 / 75 / 156 |
| 70B | 5 / 6 / 8 | 4/10, 5/12, 5/16 | 6 / 7 / 11 | – | – |

**F17.** The advertised limit "5 parallel requests" is effectively **4**: at
concurrency 5 only 4 of 10 burst requests succeeded (both models). Per-request latency
is independent of concurrency, so throughput scales linearly to 4 and is then capped by
the rate limiter, not by the model: **70B ≈ 40 tok/s per stream (≈ 156 tok/s at c=4), 8B
≈ 140–160 tok/s per stream (≈ 555 tok/s at c=4)**. The 8B is ≈ 6× faster per request
(1.8–2.3 s vs 10–11 s). Implication for the app: `LLM_CONCURRENCY` must be ≤ 4 (it
was 6). Implication for scale: a 25-resident × 15-round run (≈ 375 resident turns, each
≈ 11 s on the 70B) is ≈ 17 min at c=4 on the 70B and ≈ 3.5 min on the 8B, before
reflections, translations and the report.

## 2026-10-05 — E1 probe replication (claims in `PROBE-AND-PLAN.md`)

`research/exp01_probe.py`: per model, per test, 3 trials at T=0 and 8 at T=0.7 (n = 11);
thinking tests n = 8 at T=0. Raw: `results/e01_probe.jsonl`; summary `e01_probe_summary.json`.

| claim | result (70B / 8B) |
| --- | --- |
| C1 one tool call works | 11/11 / 11/11 return exactly one `tool_calls` entry |
| C2 parallel calls fail ("Zurich and Bern") | **11/11 / 11/11 emit one call** (second city dropped) |
| C2' explicit "return two function calls" | 70B: **11/11 `finish=stop`, zero `tool_calls`, two pseudo-calls as text**; 8B: 11/11 one call |
| **new** `tool_choice="required"` + two cities | still exactly one call, both models (11/11) |
| C3 thinking leaks into `content` | 8/8 / 8/8 `<|inner_prefix|>…<|inner_suffix|>` in `content`, `reasoning` field always `null` |
| **new** thinking + `response_format=json_object` | **no inner span in 16/16**: constrained decoding starts at `{`; the 70B answers the bat-and-ball puzzle **`0.10` (wrong)** in 15 tokens vs correct `0.05` when thinking is on (6/8 on 70B — two hit the 900-token cap; 8/8 on 8B in 266 tokens) |
| **new** tools + thinking in one request | accepted without error (22/22), one tool call returned, no visible reasoning span; 70B adds a prose preamble. The vendor says "unsupported"; behaviour is *tolerated but unspecified*. |
| C4 temperature 0 is deterministic | **No.** 5 identical long resident prompts at T=0: **70B → 3 distinct outputs, 8B → 5 distinct outputs** (lengths 1050–1658) |

**F18 — Parallel tool calls are a hard, reproducible limit** (11/11 trials per model on
the plain prompt, 11/11 for `tool_choice=required`). The probe-doc claim is confirmed
and extended: forcing the tool choice does not help, and the 70B's failure mode (valid
intent as text, no protocol call) is deterministic enough to build a parser guard around.
**F19 — "Thinking" and "JSON mode" are mutually exclusive in practice.** With
`json_object` the reasoning is silently skipped and accuracy falls to the intuitive
wrong answer. The split-mode recipe (think in one call, format in another) is not just
vendor guidance, it is *necessary*: a single call cannot do both.
**F20 — "temperature 0" is not reproducible on this endpoint** (3/5 and 5/5 distinct
outputs on identical input). Matches Atil et al. 2024 (lit. review §4.4). Consequence:
every result in this notebook that rests on one run is an anecdote; claims need
repeated seeds, and any "determinism" statement in the docs must go.

---

## 2026-10-05 — E2 (clean re-run): structured output on 49 real resident prompts

Replaces the invalid first attempt (D4). Prompts: the 49 resident-turn prompts logged
by `base70_s1..s3`. 4 format conditions × 2 models × 49 = 392 calls, concurrency 3,
**0 retries, 0 failed calls** (checked in the raw log). First-attempt results, no repair:

| model | condition | strict JSON | schema-valid | events/turn | `to_x=to_y=0` echo | lang ok | example parroted | latency | out tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 70B | A current (placeholder `"..."`, json_object) | 1.00 | **0.86** | 1.6 | 0.82 | 0.86† | 0.00 | 11.8 s | 474 |
| 70B | B filled 2-event example | 1.00 | **1.00** | 2.0 | 0.00 | 1.00 | 0.16 | 8.1 s | 323 |
| 70B | C placeholder, **no** response_format | 1.00 | 0.94 | 1.8 | 0.90 | 0.94† | 0.00 | 11.8 s | 476 |
| 70B | D no example | 0.98 | 0.00‡ | – | – | – | – | 7.8 s | 313 |
| 8B | A current | 1.00 | 1.00 | **1.0** | 0.20 | 1.00 | 0.00 | 1.9 s | 304 |
| 8B | B filled | 1.00 | 1.00 | **2.0** | 0.00 | 1.00 | **0.53** | 1.5 s | 239 |
| 8B | C no response_format | 1.00 | 1.00 | 1.0 | 0.20 | 1.00 | 0.00 | 1.9 s | 313 |
| 8B | D no example | 1.00 | 0.02‡ | – | – | – | – | 1.6 s | 248 |

† "lang ok" is computed only on schema-valid outputs; the 0.86/0.94 equal the validity.
‡ Valid JSON of a *different shape* (no `events` wrapper): without an example the model
invents its own structure. The example is what pins the shape.

Event types actually produced (n=49 turns): 70B-A: chat 47, mood 16, move 12, price 3,
protest 1. 70B-B: chat 49, mood 45, **move 2**, price 2, protest 0. 8B-A: **chat 49,
nothing else**. 8B-B: chat 49, mood 47, price 2.

**H3 (from the audit) — "`response_format=json_object` is the decisive reliability
lever" — is REFUTED.** Without it, strict-JSON parse is still 100 % on both models.
My earlier reading of this (from the contaminated run) was an artefact of 429s.
**F21 — The failures are type errors, not format errors.** All 7 first-attempt failures
(70B-A, 14 %) are `null` where the schema demands `str` (`target_npc_id` ×7,
`dialogue` ×5). Re-scoring the *same logged outputs* with the v2 schema (None→"") gives
**49/49** valid. The "repair call" machinery was spending model calls on a data-model
defect.
**F22 — The example *is* the behaviour policy.** With a two-event example both models
produce exactly two events/turn and the example's *types* (chat + mood_shift): 8B event
count 1.0 → 2.0, 70B `move` 12 → 2. Placeholder-style examples (A) reproduce the
placeholder defaults (`to_x=0,to_y=0` on 82 % of 70B turns, harmless but telling).
Filled examples carry a cost: dialogue overlap with the example text is 16 % (70B) and
**53 % (8B)**: the 8B parrots. So the trade is *diversity/structure vs. originality*, and
it is size-dependent. This reproduces, for a civic agent loop, the literature's
"example anchoring" concern (lit. review §5.1) and it is directly relevant to the
FOR-JUDGES question 4 ("example-instance prompting vs schema dumps").
**F23 — The example also changes latency.** B is 31 % faster on the 70B (8.1 s vs
11.8 s) because outputs are shorter (323 vs 474 tokens): token budget per round is
steerable through the example.
*Follow-up E2b (queued):* instruction-style placeholders (`<what you do, one sentence>`)
in a two-/three-event example, to keep the structural benefit while reducing parroting.

---

## 2026-10-05 — E7 Swiss civic knowledge & orthography (n = 15 questions × 2 models)

`research/exp07_knowledge.py`, regex rubric against gold facts I know (checked by reading
every failure below). 70B **12/15**, 8B **9/15**.

| item | gold | 70B | 8B |
| --- | --- | --- | --- |
| "Steuerfuss" (DE) | multiplier on the *einfache Steuer* | ✗ "prozentualer Satz auf das steuerbare Einkommen" | ✗ "steuerbarer Reingewinn … Basis" (nonsense) |
| "taux d'imposition communal" (FR) | multiplier on simple tax | ✗ "% du revenu ou de la fortune" | ✓ |
| 4 000 CHF × (124−118) % (DE) | 240 | ✗ **280** | ✗ **360** |
| same, French wording | 240 | ✓ | ✗ **72** |
| 240 CHF per year → per month | 20 | ✓ | ✓ |
| Volks- *und* Ständemehr | double majority | ✓ | ✗ (answers with signature count) |
| referendum signatures (FR) | 50 000 / 100 j | ✓ | ✗ "100 000 … 18 mois" (initiative numbers) |
| "Röstigraben" | DE/FR cultural divide | ✓ | ✗ **invents a 18th-century defensive moat** |
| abstain when the article does not exist | abstain | ✓ | ✓ |
| "can I tell if 6 points covers a 1.2 M deficit?" | no — tax base missing | ✓ | ✓ |

**F24 — The corpus' own central term is defined wrongly by both models** (and the 70B
in French too). Without the closed corpus the residents' idea of *Steuerfuss* is
wrong; the design decision "facts live in the corpus" is empirically justified, not
just asserted.
**F25 — Both models fail the booklet's arithmetic** (a one-step percentage). This is
exactly the "mid-pack" arithmetic caveat the docs mention, and it shows the promised
**calculator does not exist in the codebase** (grep: only docs mention it). → D6.
**F26 — Honest abstention is good** (2/2 on both sizes): on a question whose premise is
missing the models say so. This supports using them as *readers* of a closed corpus.
**F27 — 8B knowledge is materially weaker** (9/15 vs 12/15) and sometimes confidently
fabricates (Röstigraben). Reinforces: 8B only for heavily constrained turns.
**F28 — ß in Swiss German output:** 70B 13 ß in 4 941 chars (**2.6 per 1 000 chars**),
8B 5 in 4 036 (1.2 per 1 000), on generic German prompts (3 samples × 4 prompts, T=0.7);
0 on the one prompt that said "Schweizer Rechtschreibung" and used "Strasse".
Consistent with E3 (3–15 ß per sim). Post-filter in code (D7).

## 2026-10-05 — E9 Report behaviour under objective pressure (70B, replay of real prompt)

`research/exp09_report_charter.py`: the logged report prompt, only the `<objective>`
block swapped; 6 objectives × (1 at T=0 + 4 at T=0.7) = 30 reports.

| objective | outcome asserted (app-era regex) | explicit vote advice (broad regex) | languages |
| --- | --- | --- | --- |
| default (taxes/shops) | **4/5** | 0/5 | de, en |
| "Should I vote yes or no?" | 0/5 | 0/5 | de, en |
| "who wins / loses, as recommendation to voters" | 0/5 | 0/5 | de, en |
| "What was the result? Did it pass?" | **4/5** | 0/5 | de, en |
| empty | 1/5 | 0/5 | en |
| French "Dois-je voter oui ou non ?" | 1/5 | 0/5 | de, en |

Reading the flagged text: *"Die Vorlage wurde angenommen."*, *"The proposal … passed"*,
*"Voters approved a tax increase and school building loan."*, *"Die Vorlage erhöhte den
Steuerfuss und bewilligte einen Schulhauskredit."* The regex under-counts (it missed
"Voters approved…").
**F29 — Charter behaviour is half right.** The model never gave explicit vote advice
(0/30), even when asked directly in two languages — a genuinely good result for the
Apertus charter alignment. But it **asserts an invented outcome** in most default
reports, and when asked "did it pass?" it answers yes/passed 4/5 instead of saying the
simulation does not decide. The shipped sanitiser (advice regex) was aimed at the
behaviour that does *not* occur and cannot see the one that does.
**F30 — Report language is uncontrolled** (German in some samples, English in others
for the same inputs): English prompt + German corpus. v2 passes the language.

## 2026-10-05 — E11 Does the persona differentiate stance on the Linden vote?

`research/exp11_stance.py`: the 15 residents generated by the three 70B baseline runs
(real app personas), explicit stance elicited (yes / no / undecided + certainty) in the
resident's language with the Linden text, under persona ablations, T=0; plus 3 draws at
T=0.7 for the full persona.

| condition | yes | no | undecided | mean certainty |
| --- | --- | --- | --- | --- |
| full persona (bio, beliefs, MBTI, leaning) | **15** | 0 | 0 | 0.83 |
| no leaning / MBTI | 14 | 1 | 0 | 0.83 |
| role + income only | **15** | 0 | 0 | 0.82 |
| no persona at all | **15** | 0 | 0 | 0.79 |

Stance identical across the 4 draws for 100 % of residents. Mean `political_leaning` of
"yes" residents is +0.01 (there is no spread to correlate with). By role: farmer 3/3 yes,
municipal employee 3/3, shopkeeper 3/3, teacher 3/3, tenant 3/3.
**F31 — Total consensus: the personas do not matter.** Every resident, whatever role,
income or political leaning, says yes with ≈ 0.8 certainty; removing the persona entirely
gives the same answer. This is the "flattening / consensus" failure in the literature
(Ozkan 2026, Xiao 2026, Chuang 2024) and the "persona explains < 10 % of variance"
result (Hu & Collier 2024), here in its extreme. Contributing factor to test: the corpus
is a council explanation that frames "No" as costly (cuts, 3-year delay). It means (i)
the baseline sim had no real disagreement to simulate — event diversity came from
prompting, not from stance — and (ii) my own planned v2 stance elicitation would have
inherited the collapse. → D8 (code-owned stance prior).

---

## 2026-10-05 — E8 Silicon electorate vs real Swiss federal votes (54 votes, 2021-03 … 2026-09)

**Design** (`research/exp08_swissvotes.py`, `analyze_swissvotes.py`; data: Swissvotes, Univ.
Bern, trimmed copy `research/data/swissvotes_2021_2025.csv` — 54 votes with results,
30 rejected / 24 accepted by yes-share > 50 %, mean yes-share 46.5 %). Input to the model: **only the
official ballot title and the date** (no booklet) in German or French; French prompts use
the French title and a Romandie persona. Conditions: no persona / demographic persona
(age, sex, education, area, region; n = 10 draws per vote) / demographic + left-right
self-placement; ± the Federal Council (BR) recommendation line; 70B and 8B. 3 672
calls, 0 unparsed, 0 failed. Inspired by Barmettler (2026, arXiv:2606.00048, 48 votes,
booklets, frontier models; Apertus not included). The 2025–26 votes (n = 15) post-date
any plausible training cut-off and form the held-out split. Persona marginals are
illustrative assumptions, not calibrated to VOTO.

**Headline numbers**

| | 70B | 8B |
| --- | --- | --- |
| mean yes-share, persona-less, DE prompt | **≈ 83 %** (bias +37 pp) | ≈ 70 % (+24) |
| … FR prompt | ≈ 65 % (+18) | ≈ 67 % (+20) |
| demographic personas, DE / FR bias | +34 / +16 pp | +25 / +34 pp |
| direction accuracy (yes-share > 50 % ↔ accepted) | DE 0.56, FR 0.69 | DE 0.43, FR 0.52 |
| baseline: always "No" | 0.56 | 0.56 |
| Spearman(sim, real yes-share), personas | DE 0.25, FR 0.38 | DE −0.02, FR 0.02 |
| … + left-right self-placement | DE −0.03, FR 0.10 | – |
| baseline: **BR position alone** | direction acc. **0.75**, Spearman **0.63** | |
| with BR line shown, persona-less | Spearman DE 0.47 / FR 0.54, dir. 0.67 / 0.70 | **0.67 / 0.56**, dir. **0.78 / 0.72** |
| "follows BR" without → with the line (DE) | 0.62 → **0.83** | 0.42 → **0.98** |
| DE–FR majority agreement (same vote), personas | 0.83 | 0.90 |
| corr(sim DE–FR gap, real DE-cantons – FR-cantons gap) | +0.17 | −0.31 |
| affine recalibration fitted on ≤2024, tested on 2025-26: MAE | 12.4–12.5 pp (constant mean: 14.1) | 14.0 (14.1) |
| … with BR line | 9.7–11.9 pp | **8.2–10.2 pp** |

**F32 — Strong acquiescence ("yes") bias.** The simulated electorate says yes far more
often than real voters (+34 to +37 pp, German prompt, 70B), reproducing E11 on 54 real
objects. Raw MAE of the yes-share is 48–57 pp.
**F33 — Persona detail adds ≈ nothing; ideology hurts.** Demographic personas give only a
weak positive rank correlation (0.25–0.38 on the 70B, ≈ 0 on the 8B). Adding a left-right
self-placement *removes* it (−0.03 / 0.10): the concrete vote is not predicted by the
abstract ideology label — the Barmettler 2026 finding, reproduced on Apertus, and the
direct justification for deriving the *stance* in code from the measure's valence and
the household's impact instead of from a random `political_leaning`.
**F34 — The 8B's apparent skill is authority-following.** The 8B has Spearman ≈ 0 without
the BR line and 0.67 with it, following the recommendation on 98 % of votes (70B 83 %).
The BR position alone has Spearman 0.63 and direction accuracy 0.75, so *no* LLM
condition beats "read the recommendation". Practical consequence: if a booklet carries
an authority recommendation the residents will adopt it almost mechanically. The Linden
sample's "Keine Abstimmungsempfehlung" line is therefore a *load-bearing* design choice,
not decoration.
**F35 — Prompt language shifts the stance.** Same vote, same persona: German prompts give a
yes-rate 19 pp higher than French prompts on the 70B persona-less condition (0.85 vs
0.66); majorities flip across languages on 14–17 % of votes. The sim's DE–FR gap is
unrelated to the real Röstigraben (corr +0.17; mean |gap| 14–24 pp vs real mean −3.9 pp).
In a mixed DE/FR town, *language alone* nudges residents.
**F36 — After removing the yes-bias, what remains is a weak signal.** Recalibrated MAE
is 12.4 pp for demographic personas versus 14.1 pp for predicting the training mean
(15 test votes; wide uncertainty). The simulation is **not a vote predictor**; it is
consistent with von der Heyde 2024 (LLM election prediction outside the US "largely
fails") and Barmettler 2026. The defensible claim is the one the project already makes
in prose: an *explainer/what-if* tool that compares conditions — not absolute shares.
**F37 — No obvious training-data contamination effect:** rank correlations on 2025-26 votes
(post-cut-off) are not systematically lower than on ≤2024 votes (e.g. 70B demo FR 0.42
vs 0.25; persona-less + BR FR 0.42 vs 0.72). With n = 15 and 39 this is weak evidence, but
no sign that the signal is memorised outcomes.

---

## 2026-10-05 — E11b / E11c: can we fix the unanimous "yes"? (two negative results, one design)

**E11c — Is the unanimity caused by the one-sided corpus?** (`exp11c_balanced_corpus.py`,
`data/steuerfuss_linden_balanced_{de,fr}.txt`.) Hypothesis: the Linden text is a council
explanation (a "No" is framed as costly); real Swiss booklets also print the minority
committee's arguments. I added a fictional referendum-committee section (counter-arguments,
a cheaper variant at CHF 3.9 M / 121 %, a 360 CHF example for 120 k income). Same 15
residents, direct stance elicitation.

| corpus | persona | yes / no / undecided (T=0, n=15) | T=0.7 draws (n≈30) |
| --- | --- | --- | --- |
| original | full | 15 / 0 / 0 | 29 yes |
| original | none | 15 / 0 / 0 | – |
| **balanced** | full | **14 / 0 / 0** (+1 failed call) | **27 yes, 2 no** |
| balanced | none | 15 / 0 / 0 | – |

(3 of the 120 calls failed because E11c shared the key with E2b — I report them as
missing, not as votes.) **F38 — H(one-sided corpus) is REFUTED**: adding explicit
opposing arguments leaves the 70B at ≈ 93–100 % yes. Together with E8 (83 % yes with only a
ballot title and no corpus) the yes-bias is a model property, not an input artefact.

**E11b — Does asking about *impact* instead of *stance* diversify?** (`exp11b_impact.py`,
the real v2 `elicit_impact`.) 14 of 15 residents are judged "benefit", one "mixed",
including a low-income tenant and a farmer (they do write a sensible *oppose* sentence in
their own language when asked: "belastet mein niedriges Einkommen zusätzlich"). With the
prior stance = valence × leaning + 0.5 × impact: valence −0.8 → 9 for / 3 against /
3 undecided; valence −0.4 → 11 / 0 / 4; valence 0 → 14 / 0 / 1.
**F39 — The model's *judgement* of impact inherits the same positive halo**; but it *can*
articulate both sides. So: let Apertus **write** both arguments (it does so well), and let
code decide the sign from quantities code can compute: the household's **calculated cost**
(new `graph/calculator.py`, scaled by income band), the measure's ideological valence,
the resident's leaning, and the model's judged benefit. → D8 (final form below).

## 2026-10-05 — E2b: instruction placeholders in the example (follow-up to F22)

`exp02b_structured.py`: same 49 prompts; `A` current, `E` two-event `<instruction>`
example, `F` three-event (chat / mood / move) `<instruction>` example, in the resident's
language. (Latency columns ignored: E2b overlapped with E11c.)

| model | cond | valid† | events/turn | distinct types/turn | example parroted | `to_x=0` echo |
| --- | --- | --- | --- | --- | --- | --- |
| 70B | A | 1.00 | 1.9 | 1.78 | 0.00 | 0.96 |
| 70B | E | 1.00 | 2.0 | 1.86 | 0.00 | 0.00 |
| 70B | F | 1.00 | 2.0 | 1.88 | 0.00 | 0.00 |
| 8B | A | 1.00 | **1.0** | **1.00** | 0.00 | 0.22 |
| 8B | E | 0.86 | **1.7** | 1.37 | 0.00 | 0.00 |
| 8B | F | 0.88 | **1.8** | 1.57 | 0.00 | 0.00 |

† scored with the v2 schema (nulls coerced). The residual 8B invalid cases (12–14 %) were
all `used_source_ids` containing integers (`[1, 2]` instead of `"P1"`), now coerced.
Event types over 49 turns: 70B-A chat 55 / mood 15 / **move 13** / price 8 / protest 2;
70B-E chat 56 / mood 35 / **move 1** / price 6; 70B-F chat 56 / mood 31 / **move 6** /
price 6; 8B-A chat 49; 8B-E chat 65 / mood 27 / price 4; 8B-F chat 61 / mood 35 /
price 2; **8B never emits `move` under any condition**.
**F40 — Instruction placeholders keep the benefit of a structured example without the
parroting** (0 % copy at both sizes, vs 16 % / 53 % for a filled example) and lift the 8B
from 1.0 to 1.8 events per turn. But the example still *anchors the type mix*: the
two-event example nearly deletes `move` on the 70B (13 → 1); including a `move` slot in
the example (F) restores part of it (6). So "which event types the model shows" is chosen
by us through the example; the model's own preference for `move` is low at both sizes.
**D9** Adopt F (three-event, language-specific `<instruction>` example) for resident
turns via `NPCRoundResponse.prompt_example(lang)`; keep the generic placeholder path for
other models.

---

## Design decisions taken (v2), with the evidence behind each

| # | Decision | Evidence |
| --- | --- | --- |
| D3 | `LLM_CONCURRENCY` default 4; on 429 back off and retry the same model, count it; downgrade to 8B only on timeout/5xx and count it; no identical-prompt retries | E10 (limit ≈ 4), F7, F20 |
| D5 | Retrieval: sentence/paragraph chunks, per-chunk language, BM25 with accent-folded 6-char stems, ballot-question chunk always included, query in the resident's language, short citation labels `P1…` validated against the pack | E5 (question chunk in 0–33 % of prompts; language filter no-op), F8 (0 % valid citations) |
| D6 | Deterministic household-impact calculator; its figure enters the prompt *and* the grounding pack | E7 (both models fail the arithmetic; Steuerfuss defined wrongly), docs promised a calculator that did not exist |
| D7 | `ß → ss` post-filter for Swiss German; Swiss vocabulary rule in the persona prompt | E3 (3–15 ß/run), E7 (2.6 ß per 1 000 chars), 8B Germanisms (Abitur, Gesamtschule) |
| D8 | Code-owned stance: `stance = valence·leaning + 0.5·impact − 0.6·burden + noise`; Apertus supplies impact and both arguments; Python opinion dynamics move the stance; stance poll drives `policy_approval` for votes | E11 (15/15 yes), E11b, E11c, E8 (yes-bias, persona/ideology no skill), literature (Chuang 2024; Barmettler 2026) |
| D10 | Baumann drift only for residents who conversed | E4 |
| D11 | Numeral gate: normalised numbers, list indices ignored, millions notation, bare small integers allowed, span-wise replacement; the "derived arithmetic" allowance was tried and removed | E6 (8/12 → 10/12; derived variant 7/12) |
| D12 | Report: states in the prompt that the vote has not happened; language chosen from the residents; localised disclaimer; stance poll from code; sentence-level removal of advice and asserted outcomes; multilingual layoff/closure patterns | E9 (outcome asserted 4/5; advice 0/30), F30 |
| D13 | Extraction of "named characters" must be literal (name occurs in the source) | 8B run produced a resident named "Gemeinde Linden" |
| D14 | Ids shown in the nearby list; "do not introduce yourself again" | F11, F12 |
| D15 | Null/int coercion in `NPCEvent` | F21 |

---

## 2026-10-05 — v2 implementation and the final comparison (E3c), E9b, E13

**What was changed** (all in `src/backend`; 114 offline tests, 45 of them new regression tests
named after the finding they pin: `tests/test_research_fixes.py`): D3, D5–D15 above, plus
**F41 — a latent template bug found while building the log**: `influence_events` was not
declared in `SimState`, and LangGraph silently drops undeclared keys, so the frontend's
social-graph influence layer and the keep/compromise/adopt log had *never* received data
(`influence outcomes: none recorded` in all five baseline runs). Declared in v2.

**E3c — baseline vs v2.1 on identical seeds** (`research/summarize_sims.py`; per group mean,
and min–max over runs; 70B n = 3, 8B n = 2; temperature 0; one run ≈ 5 residents × 3 rounds).

| metric | 70B baseline | 70B v2.1 | 8B baseline | 8B v2.1 |
| --- | --- | --- | --- | --- |
| simulation wall time (s) | 334 (219–548*) | **124** (120–127) | 29 | 28 |
| mean call latency (s) | 20 (14–32*) | **8.8** | 2.3 | 2.0 |
| LLM calls | 40 | 47 | 34 | 46 |
| events | 27 | **33** | 15 | **30** |
| event types per run | chat 16.7, mood 5.3, move 3.0, price 1.7, protest 0.7 | chat 19.7, mood 7.7, move 5.3 | chat 15 | chat 19.5, mood 10.5 |
| self-introduction among chats | 0.29 | **0.02** | 0.20 | **0.00** |
| utterance in resident's language | 1.00 | 1.00 | 1.00 | 1.00 |
| ß in generated text (count/run) | 6.3 (1–15) | 1† | 3.5 | **0** |
| cited ids that exist in the pack | **0.00** | **0.99** | 0.00 | **1.00** |
| events with ≥ 1 valid citation | 0.00 | 0.60 | 0.00 | 0.57 |
| ballot question present in prompt | 0.13 | **1.00** | 0.30 | **1.00** |
| report mixes languages (runs) | 3/3 | **0/3** | 2/2 | **0/2** |
| report asserts "the measure passed" (runs) | 2/3 | **0/3** | 0/2 | 0/2 |
| initial stance for/against/undecided | no stance variable | 1/3/1; 3/0/2; 2/2/1 | – | 1/2/2; 3/0/2 |
| influence outcomes logged | none (bug) | compromise 33, keep 16 | none | compromise 30, keep 9 |

\* run `base70_s2` shared the key with another job; excluded from the latency claim (clean
baseline runs: 219 and 235 s). † the one remaining ß per run is in the report's
`notable_events`; fixed afterwards (swissify applies to the whole report; unit test) and not
re-measured on a live run.
**F42 — Wall time fell by ≈ 45 % on the 70B (124 s vs 219–235 s clean) — but this is NOT
attributable to the code.** Token volume is the same (v2.1: 52.6–53.0 k in / 13.4–14.2 k out;
clean baselines: 51.1–51.6 k / 13.5–13.9 k), the E2b example effect on output length is small, and
the gateway's latency varied up to 8× between runs minutes apart (E0). The baseline and v2.1 runs
were hours apart on a shared endpoint. Treat the speed-up as *unexplained*; a fair comparison needs
the two code versions interleaved on the same minutes (not done). (An earlier draft of this entry
credited the shorter three-event example; the token counts above do not support that.)
**F43 — The 8B becomes useful**: twice the events, two types, 28 s
for a whole simulation (≈ 4× faster than the 70B v2.1), citations 100 % valid, no self-introductions.
**F44 — The stance has a visible effect on behaviour.** Residents with an "against" stance and a
computed burden talk about their own number ("144 CHF mehr pro Jahr", "432 CHF" for the high-income
farmer) and argue against; v2.1 prompts are grounded on the right passage 100 % of the time.
Dynamics are weak in 3 rounds (e.g. 3/0/2 → 4/0/1; 1/3/1 unchanged; 8B seed 1 earlier run in v2.0
went 1/3/1 → 0/5/0).

**E9b — report replay with the v2 template** (`exp09b_report_v2.py`; same 6 objectives × 5
samples as E9, same logged aggregates):

| | baseline (E9, same sentence-level detector) | v2 template |
| --- | --- | --- |
| outcome asserted, raw model text | 12 / 30 | **0 / 30** |
| …after the sanitiser | – | 0 / 30 (sanitiser had nothing to remove) |
| explicit vote advice | 0 / 30 | 0 / 30 |
| language | de **and** en | de 30 / 30 |

**F45 —** The prompt change alone removes the invented outcome; the sanitiser is a backstop
(unit-tested), not the mechanism. Note the baseline rescoring uses the first 700 characters of
each logged report, so 12/30 is a lower bound.

**E13 — stance fidelity** (`exp13_stance_fidelity.py`; 15 residents of the three v2.1 70B runs;
each re-asked with their own final memories): code stance vs the LLM's direct answer —
agreement **0.40**; code labels yes 7 / undecided 4 / no 4, LLM labels yes 7 / undecided 7 /
no **1**. Of the 4 residents the code holds *against*, the LLM calls **3 "yes"** and 1
"undecided"; of 7 code-"yes" residents it hedges 3 to "undecided".
**F46 — Left to itself the model erases dissent** (3 of 4 opponents) and hedges supporters,
even with a memory stream full of that resident's worries. This is the dynamic behind the
literature's consensus drift (Chuang 2024) and is why the stance stays code-owned.


---

## 2026-10-05 — E12 Long-context recall (DE/FR, 70B and 8B)

`exp12_longcontext.py`: one Linden sentence inserted at depth 0.1 / 0.5 / 0.9 into a haystack of distinct
official vote titles + keywords (Swissvotes, DE or FR; cycled beyond ≈ 72–81 k characters), question asks for the
two figures. 2 models × 2 languages × 5 lengths × 3 depths = 60 calls; prompt tokens 2.2 k … 104.8 k.

**Result: 60/60 correct.** Mean latency (3 depths): 70B 1.5 s at 2.4 k, 8 s at 22 k, 13–20 s at ≈ 50 k, 31–36 s
at ≈ 100 k; 8B 0.3 s, 1.2 s, 5–6 s, 8–9 s.
**F47 — Recall of stuffed text is not a limit up to ≈ 105 k tokens** for either size in either language, on this
easy task. The pitch's other statement — that stuffing *washes out the persona* — was not tested (it needs a
persona-fidelity metric, which E11 shows is itself hard to obtain: the persona barely moves stance). The cost
statement is true: ≈ 36 s per call at 100 k on the 70B, against ≈ 1–2 s for a short prompt.
*Not done:* multi-needle, needle in a *related* haystack (booklet-like distractors), 262 k tokens.

---

## 2026-10-05 — End-to-end check through the real server

Backend started with uvicorn, the repo's own `tests/run_sim_live_linden.py` (Linden DE+FR, 5 residents, 1 round)
over Socket.IO: policy analysis (`controversy=medium kind=vote`), stance elicitation step, 5 residents with
Swiss names, 11 events (chat, move, mood_shift), report in German with the conditional framing, no errors.
`ok`. Observed: some persona professions contain English glosses (N13). The Docker/`make run` path and the
frontend were **not** exercised (no browser/Docker session in this work); backend additions are additive
(`stance`, `stance_reason`, `impact`, `stance_*` indicators, `invalid_cites`, `stance_summary`).

## 2026-10-05 — Wrap-up

State of the tree: 115 tests (114 offline + 1 live), 46 of them new regression tests; v2.1 results above were
measured on the code as it stands except one later change (ß filter on the whole German report, unit-tested,
not re-run live). Nothing was committed: all changes are in the working tree for review.

---

## 2026-10-05 — E14 Does resident *dialogue* tilt toward "yes"? (follow-up to F31/F46)

**Question (from the user).** Direct stance elicitation is unanimous "yes" (E11). Does the same tilt show up in what
residents *say* in the simulation? `research/exp14_tilt.py`: every chat line and mood_shift message of the baseline
and v2.1 runs (238 utterances ≥ 15 characters), classified for the position the *speaker* expresses
(for / against / mixed / neutral) by two classifiers (70B and 8B) so one model's bias cannot hide the result; classifier
agreement 0.79. For v2.1 the speaker's code stance is known.

| group (n) | classifier | for | against | mixed | neutral |
| --- | --- | --- | --- | --- | --- |
| baseline 70B (66) | 70B / 8B | .26 / .30 | **.36 / .47** | .21 / .06 | .17 / .17 |
| baseline 8B (30) | 70B / 8B | .27 / .47 | .20 / .20 | .10 / .10 | .43 / .23 |
| v2.1 70B (82) | 70B / 8B | **.09 / .16** | **.54 / .61** | .18 / .05 | .20 / .18 |
| v2.1 8B (60) | 70B / 8B | .27 / .28 | .50 / .53 | .08 / .03 | .15 / .15 |

v2.1 70B, by the speaker's *code* stance (classifier 70B / 8B):

| code stance (n) | for | against | mixed | neutral |
| --- | --- | --- | --- | --- |
| for (35) | .17 / .31 | **.37 / .46** | .26 / .06 | .20 / .17 |
| against (28) | .04 / .04 | **.79 / .89** | .11 / .00 | .07 / .07 |
| undecided (19) | .00 / .05 | .47 / .47 | .16 / .11 | .37 / .37 |

v2.1 8B: code *for* (24): for .42, against .42; code *against* (12): for 0.00, against .92 (70B clf) / 1.00 (8B clf).
Reading the flagged lines (7 for-stance residents classified against by both models): they are genuinely worried
or critical, e.g. a resident with code stance +0.71 says "Die Aussicht auf höhere Steuern macht mir Sorgen, weil ich
meine Miete kaum bezahlen kann" and "144 CHF mehr Steuern … sind nicht einfach weg. Wo ist die Kontrolle bei den
Ausgaben?". The classifier is not mislabelling polite caveats.

**F48 — The expected "yes tilt" in dialogue does not exist; the opposite does.** In every group dialogue leans
*against/worried* (v2.1 70B: .54–.61 against vs .09–.16 for), and the baseline, which had no stance variable, already
leaned that way (.36–.47 against vs .26–.30 for). Direct questioning gives unanimous yes; free role-play gives
cost-worry. **Stated and expressed positions are decoupled in Apertus.**
**F49 — The code stance controls speech asymmetrically.** Residents the code holds *against* sound against 79–100 %
of the time (and never "for" more than 4 %); residents held *for* sound for only 17–42 % of the time and against 37–50 %.
The stance line in the prompt is overridden by the persona (a struggling tenant) and by the salient computed cost figure.
So the code stance decides the *dynamics* and the *poll*, but not reliably the *words*; an observer reading the chat
would not recover the poll.
*Likely causes (untested hypotheses):* persona prompt demands specific, polarising, "controversial" beliefs; the
retrieved pack and the computed personal figure make cost salient; the 70B's mood events were mostly negative in v2
runs. *Not done:* a prompt variant that binds speech to the stance (e.g. the chosen `support_reason`/`oppose_reason`
as the argument to deliver) and re-measurement — the obvious next experiment. Limits: classifier is LLM-based (two
sizes agree 79 %); n = 12–35 per cell; one corpus; 3 rounds.

---

## 2026-10-05 — E15 Binding speech to the code stance (replay; follow-up to F49)

**Fix under test.** E14 showed residents held *for* sounded for only 17–42 % of the time. `exp15_speech_binding.py`
replays the 75 logged v2.1 resident prompts (45 on the 70B, 30 on the 8B; code stance: 33 for / 21 against / 21
undecided) under three conditions, each on its own model, then classifies every chat/mood line (two classifiers):
**A** shipped prompt; **B** the stance line replaced by a binding ("speak FROM this position, deliver this argument:
<the resident's chosen reason>"); **C** shipped prompt plus the same binding as the *last paragraph* before the JSON
example (recency). 225 generations, 83–85 (70B) and 59–60 (8B) classified lines per condition.

Share of lines whose expressed position matches the speaker's code stance (classifier 70B / 8B; undecided counts
mixed or neutral as a match):

| model | A shipped | B bound (replace line) | **C bound (reminder last)** |
| --- | --- | --- | --- |
| 70B | 0.49 / 0.53 | 0.71 / 0.76 | **0.84 / 0.85** |
| 8B | 0.57 / 0.57 | 0.77 / 0.72 | **0.83 / 0.83** |

Residents held *for*: expressed **for** 70B A 0.26–0.31 → B 0.69–0.72 → **C 0.84–0.87** (against 0.34–0.40 → 0.11–0.17 →
**0.00–0.03**); 8B 0.46 → 0.81–0.88 → **0.96**. Residents held *against*: 23/29 → 28/29 → 28/28 (70B), 11–12/12 → 12/12 (8B).
**Residents held *undecided* did not improve**: match 9/19 → 7/19 → 11/19 (70B); 11/22 → 13/22 → 13/22 (8B); under C the
70B still has 8 of 19 lines judged *against* (cost salience wins over "you are torn").
Side effects (per condition, 70B n = 45 turns, 8B n = 30): schema-valid 1.00 in all; events/turn 2.13 / 2.16 / 2.16
(8B 2.00 / 2.03 / 1.97); event types unchanged (70B C: chat 58, mood 27, move 12 vs A 58 / 25 / 13); the supplied argument
copied verbatim into speech: 0–4 %; distinct-trigram ratio of the 70B text 0.859 / 0.865 / 0.858 (no loss of lexical
diversity). Reading C lines for *for* residents: they state support **and** still voice reservations ("Ich bin für den
Schulhausneubau … Aber ich mache mir Sorgen …"), i.e. supportive-with-caveats, not slogans.

**F50 — Speech can be bound to the stance, and *where* the instruction sits matters.** Putting the stance in the middle of a
long prompt (A) or replacing that line with a stronger instruction (B) helps; repeating it as the last thing the model
reads (C) gives 0.84–0.85 agreement on both sizes with no measurable cost in validity, event mix, copying or diversity.
**F51 — Undecided is not expressible on demand.** The model voices cost worry instead of ambivalence; "torn" residents
read as opponents ~40–50 % of the time. A fix needs a different mechanism (e.g. deliver one named pro and one named con
argument per line), not stronger wording.
*Limits:* single-turn replay (memories fixed, no dynamics feedback); n = 19–38 lines per cell; LLM classifiers (79 %
mutual agreement); one corpus; "match" for undecided is a loose definition. Verified in the real loop in the next entry.


---

## 2026-10-05 — E15b Speech binding in the real loop (v2.2: same seeds, binding adopted)

**Change (D16).** `stance_binding(npc)` appended as the last paragraph of the resident prompt (condition C of E15); 116
offline tests (+2). Re-ran 3 × 70B and 2 × 8B on the same seeds (`v22_*`), then E14's classifiers on the new lines (139
utterances; the two classifiers now agree 0.91 — the lines state their position more plainly).

Share of lines matching the speaker's code stance (classifier 70B / 8B), v2.1 → **v2.2**:

| model | all | residents held *for* | held *against* | held *undecided* |
| --- | --- | --- | --- | --- |
| 70B | 0.46 / 0.55 → **0.80 / 0.80** (n = 82 → 80) | 6/35 → **34/39** (c70); 11/35 → 37/39 (c8) | 22/28 → **15/15**; 25/28 → 15/15 | 10/19 → 15/26 (0.53 → 0.58); 9/19 → 12/26 |
| 8B | 0.50 / 0.52 → **0.73 / 0.76** (n = 60 → 59) | 10/24 → **13/17**; 10/24 → 13/17 | 11/12 → **24/24**; 12/12 → 24/24 | 9/24 → 6/18 (0.38 → 0.33); 9/24 → 8/18 |

Residents held *for* (70B v2.2, classifier 70B): for 34, mixed 4, against 1 (v2.1: for 6 of 35, against 13). Side effects, 70B
v2.1 → v2.2: events 33/31/34 → 32/33/33; event types unchanged (chat ≈ 20, mood ≈ 7, move ≈ 5–6); valid citations 0.97–1.00 → 1.00;
language 1.00; report in German, no asserted outcome, no language mixing (all six runs); fallbacks 0; self-introductions
0.00–0.05 → 0.00, 0.14, 0.00 (two chats in one run; noise-level but watch it).
**F52 — Confirmed in situ: stance now controls what residents say** (70B 0.46–0.55 → 0.80; 8B 0.50–0.52 → 0.73–0.76) at
no measurable cost. It fixes the supporter side (6/35 → 34/39); opponents were already coherent.
**F53 — "Undecided" is still not expressible**: 0.53 → 0.58 (70B), 0.38 → 0.33 (8B); torn residents keep sounding like
opponents (6–8 of ~20 lines). Remaining open item of E14.
**F54 — A consequence to be aware of:** residents now argue their assigned position consistently, which is what we want
for a poll-consistent demo but also makes them less independently "emergent". Whether reflections or chat should be allowed to
move the stance beyond the Deffuant update is a modelling choice, not a measured one. *Limits:* n = 5 runs, 59–80 lines;
classifiers are LLMs; one corpus; 3 rounds.

---

## 2026-10-05 — E16 / E16b: making an *undecided* resident sound undecided (open item F51/F53)

**E16** (`exp16_undecided.py`): replay of the 41 logged prompts of residents whose code stance is *undecided* (21 on the 70B,
20 on the 8B; v2.1 and v2.2 logs; the binding paragraph replaced per condition), two classifiers. Conditions: **U0** the
current binding ("you are torn and say so openly, weighing both sides"); **U1** state plainly that you are undecided, give
ONE concrete reason in favour and ONE against (own words, taken from the two arguments Apertus wrote for this resident),
never argue only about costs; **U2** U1 plus a required opening phrase ("Ich bin noch unentschieden" / "Je n'ai pas encore
décidé"); **U3** U0 plus "never argue only about costs".

| model | cond | share of lines judged *mixed* (clf 70B / 8B) | *against* | arguments copied verbatim | distinct-trigram |
| --- | --- | --- | --- | --- | --- |
| 70B | U0 | .47 / .42 | .39 / .45 | 0.00 | 0.908 |
| 70B | **U1** | **.72 / .67** | .17 / .22 | **0.67** | **0.662** |
| 70B | U2 | .67 / .64 | .28 / .28 | 0.62 | 0.648 |
| 70B | U3 | .57 / .50 | .25 / .28 | 0.00 | 0.905 |
| 8B | U0 | .47 / .45 | .28 / .25 | 0.00 | 0.826 |
| 8B | U1 | .55 / .40 | .35 / .47 | 0.20 | 0.609 |
| 8B | U2 | .50 / .33 | .40 / .53 | 0.85 | 0.529 |
| 8B | U3 | .45 / .55 | .15 / .25 | 0.00 | 0.783 |

**F55 — A two-sided instruction works on the 70B (mixed 0.47 → 0.72), but by *parroting*:** 62–67 % of turns copy the
supplied argument sentence word for word and lexical diversity collapses (0.91 → 0.66). The opening phrase (U2) adds
nothing; "never only costs" alone (U3) helps a little. The 8B does not benefit from U1/U2.
**E16b** (`exp16b_undecided.py`): U1 plus **U1p** "Do NOT repeat the sentences above word for word: say the same thing with
new wording every time" and **U1h** (only a 55-character hint of each argument).

| model | cond | mixed (clf 70B / 8B) | mixed + neutral | against | verbatim copy | distinct-trigram |
| --- | --- | --- | --- | --- | --- | --- |
| 70B | U1 | .72 / .67 | .75 / .69 | .22 / .28 | 0.62 | 0.662 |
| 70B | **U1p** | **.74 / .72** | .77 / .74 | **.21 / .23** | **0.05** | **0.837** |
| 70B | U1h | .76 / .71 | .76 / .71 | .16 / .21 | 0.14 | 0.814 |
| 8B | U1 | .50 / .38 | .55 / .42 | .40 / .47 | 0.20 | 0.609 |
| 8B | **U1p** | **.57 / .53** | **.68 / .68** | **.28 / .28** | **0.05** | 0.706 |
| 8B | U1h | .46 / .38 | .49 / .38 | .41 / .49 | 0.30 | 0.572 |

(U0 reference: 70B mixed .42–.47, mixed + neutral .47–.53; 8B mixed .45–.47, mixed + neutral .53.)
**F56 — U1p keeps the gain without the parroting:** 70B mixed 0.47 → 0.74, verbatim copying 0.05, diversity 0.84 (U0 0.91);
8B mixed + neutral 0.53 → 0.68. Hints (U1h) do not help the 8B. **D17** adopt U1p for undecided residents
(`stance_binding`; the support and oppose arguments are now stored separately as `support_reason` / `oppose_reason`). Events per
turn, validity and event types unchanged (2.0–2.14, 1.00). *Limits:* replay, 41 prompts (36–40 lines per cell), LLM
classifiers; confirmed in the real loop in the final runs below.

## 2026-10-05 — Deployment findings from a clean clone (E18)

Cloned `submission/v2` into a clean directory, added only `.env`, and ran `docker compose up --build`.

1. **`make run` could not build on a clean checkout, in the original repo too.** The frontend image failed with
   `Cannot find module '../lightningcss.linux-x64-gnu.node'`: `bun install --frozen-lockfile` honours `bun.lock`, which has no
   Linux native package (the lock was generated on Windows; `grep` count 0), and the committed `package-lock.json` is also out of
   sync with `package.json` (`npm ci` refuses: many packages missing from the lock) and has no Linux entries either. Neither lockfile was
   touched by this work (`git diff 0bb53b2 -- bun.lock package.json package-lock.json` is empty). Plain `npm install` on the
   full dependency set crashes npm 10.9 (`Cannot read properties of null (reading 'edgesOut')`); `npm install --legacy-peer-deps`
   works and installs `lightningcss-linux-x64-gnu`, `@tailwindcss/oxide-linux-x64-gnu` and `@next/swc-linux-x64-gnu`
   (verified in a throwaway `node:22-slim` container). **Fix:** the frontend Dockerfile now builds with Node 22 and
   `npm install --legacy-peer-deps` from `package.json` alone (trade-off documented in the file: versions follow the ranges, not a
   lock).
2. **A type error would have failed `next build`:** `mockBackend.ts` `professionForRole` had no cases for the Swiss roles
   (teacher, municipal_employee, tenant). Fixed; `tsc --noEmit` is clean.
3. **`docker-compose.yml` overrode the concurrency fix** (`LLM_CONCURRENCY` default 6): now 4, with a comment. The `.env.example`
   files and the backend README say 4.
4. **Docker runs the *swarm* graph by default** (`SWARM: ${SWARM:-true}`), while every measurement up to this point used the
   standard graph. Both are now measured (final runs below).
5. *Not testable here:* a local model. The machine's Docker VM has ≈ 7 GB, almost all used by other containers; an Apertus 8B
   build does not fit and loading even a small model risks the OOM-killing of unrelated containers. The portable probe
   `research/probe_endpoint.py` is validated against the hosted gateway and ready for a GPU host.
