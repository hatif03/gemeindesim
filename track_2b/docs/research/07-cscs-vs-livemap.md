# 07 — Two endpoints compared: the hackathon gateway (livemap) and the CSCS inference API

Measured on 5–6 October 2026 with the same scripts, the same prompts and, where it mattered, the same seeds. Raw calls: `research/results/` (livemap, 5 Oct),
`research/results/livemap_2026-10-06/` (same-day control) and `research/results/cscs/`. Chronological record with every failure and correction:
`LAB-NOTEBOOK.md`, entries E20-E28 (findings F60–F7x). Nothing here says one is "better" in general: it says what each one does to *this* app.

**Endpoints.** *livemap*: `https://hackapertus.livemap.sh/v1`, ids `apertus-v1.5-70b` / `-8b`, vLLM 0.23.1rc1 (tp2), the endpoint the hackathon template and the judges use.
*CSCS*: `https://api.inference.cscs.ch/v1` (Swiss National Supercomputing Centre; "Envoy AI Gateway" in front of vLLM 0.23.1rc1), ids `swiss-ai/Apertus-v1.5-70B` / `-8B` / `-70B-thinking` / `-8B-thinking`.
The CSCS documentation states that it does not record prompts or responses and that data does not leave the infrastructure it controls (a statement of the provider; we did not verify it).

## 1. At a glance

| dimension | livemap | CSCS | consequence for GemeindeSim |
| --- | --- | --- | --- |
| Requests in flight | **≈ 4–5** (at 6 in flight only 40-50 % of requests answered, the rest 429) | **no limit found up to 96** (0 non-200 in 2 496 requests) | `LLM_CONCURRENCY` 4 → 16 or more; spread runs and big towns become practical |
| 70B throughput | 160 tok/s at 4 in flight (ceiling ≈ 200) | 247 at 4, 962 at 16, 1 737 at 32, 4 359 at 96 | ≈ 11× at 32, 27× at 96 |
| 70B single-call latency (short prompt) | 6.0 s today, 10–11 s on 5 Oct | 3.8 s (2.2 s for a 2.4 k-token prompt with cache) | |
| Models | 70B, 8B | 70B, 8B, **70B-thinking, 8B-thinking** (other families: 403) | separate thinking models |
| Reasoning in one call with JSON | no (thinking + `json_object` skips it) | **8B-thinking yes** (field filled, content clean); 70B-thinking no | the "think-then-format in one call" option exists for the 8B only |
| Reasoning span in `content` | yes (`reasoning` null) | 70B-thinking yes; 8B-thinking no (parser) | keep stripping spans |
| Parallel tool calls | no | no | unchanged: no tools in the loop |
| Strict structured output (`json_schema`, `structured_outputs`) | works, 24/24 valid on the real prompts | works on the 70B (23/24), **fails on the 8B (11/24: endless whitespace)** | do not adopt `json_schema` on CSCS |
| `temperature 0` on real 2–3 k-token prompts | 2.75 distinct of 3, 1/24 identical | 2.71 distinct of 3, 1/24 identical | **no difference: not reproducible on either** |
| `seed` | no effect on real prompts | no effect on real prompts | log runs, report ranges |
| Context | needle recall to 233k tokens works (70B 3/3, 8B 3/3 single needle, n = 1 per cell); 70B 98 s at 233k | needle recall to **233k** (8B 30/30, 70B 26/30); 70B 29-46 s at 140-233k | whole booklets fit on both; CSCS is 2-3x faster |
| Prefix cache | not reported | **reported: 94 % of a shared 24.5k-token prefix cached** | stuffing a booklet is as cheap as retrieval |
| Failure mode under load | HTTP 429 (retry-able) | HTTP 504 "upstream request timeout" when long jobs overlap, esp. 8B-thinking | retry 5xx on the same model (added) |
| Logprobs, `n`, `stop`, streaming, system role | work | work | logprobs usable for evaluation |
| Embeddings | 404 | 404 (Apertus), 403 (others) | not available on either |
| Who can use it | every hackathon participant and the judges | **this key only**; only the four Apertus v1.5 models | the submission must keep working on livemap |

## 2. What did *not* change (important for the paper)

* **The yes-bias is in the weights.** 14 of 15 "yes" with a persona and 15 of 15 without, on all four CSCS models including the thinking ones, as on livemap (E24, E11).
* **No parallel tool calls**, 70B writes pseudo-calls as text, `enable_thinking` puts a span in `content`, thinking + `json_object` skips reasoning: all identical (E20).
* **Real-prompt non-determinism**: both endpoints, both sizes, with or without `seed` (E23).
* **Weak Swiss facts** and **authority deference**: properties of the weights; not re-measured as they cannot depend on the deployment (same checkpoint ids assumed; we did not verify the checkpoints are byte-identical).
* **Answer format changes the stance** (one word vs JSON with a reason: the 8B puts 25 % of its mass on "no" in the first) — a modelling fact, not an endpoint one.

## 3. What did change

### 3.1 Speed: the same simulation, the same code, the same seeds (E27, 5 seeds per size)

| metric | livemap 70B | CSCS 70B | livemap 8B | CSCS 8B |
| --- | --- | --- | --- | --- |
| simulation wall time, 5 residents, 3 rounds | 126 s (120-132) | **61 s (59-63)** | 28 s (27-29) | 23 s (22-24) |
| mean call latency | 9.4 s | 5.4 s | 2.2 s | 2.2 s |
| LLM calls | 46 | 44 | 41 | 40 |
| events | 33.0 | 33.2 | 31.6 | 31.4 |

The 70B is 2.1x faster end to end; the 8B (never the bottleneck) 1.2x. A **25-resident town** (3 rounds, 70B, 16 in flight) took 105 s, 200 calls, 163 events on CSCS. The same-day control (25 residents, 2 rounds, `LLM_CONCURRENCY=auto`, E31): **CSCS 89–97 s, livemap 654 s** (the gateway was busy: 28 s mean call latency and 12 tokens/s per request; the same run with the first, additive limiter, which stayed at 4 in flight, took 656 s).

### 3.2 Quality: the v2 fixes replicate on a second deployment

| metric (same definitions as `03-results.md` section 7) | livemap 70B | CSCS 70B | livemap 8B | CSCS 8B |
| --- | --- | --- | --- | --- |
| cited ids that exist in the pack | 1.00 | 1.00 | 1.00 | 1.00 |
| events with at least one valid citation | 0.57 | 0.55 | 0.48 | 0.49 |
| ballot question in the resident prompt | 1.00 | 1.00 | 1.00 | 1.00 |
| utterances in the resident's language | 1.00 | 1.00 | 1.00 | 1.00 |
| chats starting with a self-introduction / sz in Swiss text | 0.00 / 0 | 0.00 / 0 | 0.00 / 0 | 0.00 / 0 |
| reports that mix languages / assert the measure passed | 0/5 / 0/5 | 0/5 / 0/5 | 0/5 / 0/5 | 0/5 / 0/5 |
| speech matches the code stance (classifier 70B / 8B) | 0.91 / 0.88 (n = 146) | 0.85 / 0.87 (n = 137) | 0.87 / 0.85 (n = 150) | 0.88 / 0.86 (n = 150) |

Same seeds fix the random attributes only: the personas' text, the judged impact and therefore the initial stance poll differ between endpoints (for example seed 1: 0/2/3 on livemap,
0/4/1 on CSCS), which is the spread across runs that `ensemble_final_70.md` already showed. Nothing in the table is a difference beyond that noise.

### 3.3 New things this endpoint made possible (and what they found)

* **The grounded 1:1 chat, tested live (E25, 25 answers per run, 5 residents x 5 scripted questions).** First run: 0 errors, but undecided residents answered every question with their position and
  residents misattributed the calculator figure to the person asking; after an answer-first chat binding, an own-household label and bracket stripping: facts answered with the booklet's figure,
  unknown facts declined ("not in the text") 5/5, no vote recommendation (0/5; residents say how *they* vote), reply translated into the user's language 5/5.
* **The real booklet through the whole app (E28).** PDF upload, 5 residents, 2 rounds and the chat took 95 s. Retrieval alone left the chat unable to answer "how large are the lost revenues"
  (0/5, honest "not in the text"); with the complete text first in the prompt (24.5k tokens, mostly cached) 5/5 answered 1.8 billion CHF. Cost: those answers cite no passage label.
* **Spread of the stance poll, in the app** (`POST /ensemble`, button "Run 5x: show the spread"): tested live with three parallel runs (5 residents, 2 rounds): 62 s on CSCS, so five 3-round runs take roughly 2-3 minutes; at 4 in flight the same would take about 8 minutes (estimate). It returned the range of the poll (share for 0.40-1.00 across the three runs).
* **Stuffing versus retrieval** (E26): 13/14 vs 11/14 for the 70B, same latency class thanks to the prefix cache.
* **Replications** (same scripts, other deployment): Swiss knowledge 11/15 (70B), 9/15 (8B) vs 12/15 and 9/15 (E7); yes-bias on four models (E24); real votes (E8, section 5 below).


## 4. Reading the comparison honestly

* Same-day livemap controls corrected three things we would otherwise have attributed to CSCS: strict `json_schema`, `seed` and `logprobs` all work on livemap too (our first reading of E20 on CSCS alone suggested a difference).
* The CSCS 8B-thinking deployment looked "broken" (504) until we changed the request shape: it is the combination of long generations and several requests in flight, not the model.
* One key, one day, a service shared with other users: latency and 504 behaviour will move. The throughput numbers are lower bounds for a quiet service and not a promise.
* We did not measure a local deployment (no GPU): neither endpoint is evidence about on-prem behaviour.

## 5. Replications (same scripts, other deployment)

| result | livemap (5 Oct) | CSCS (6 Oct) |
| --- | --- | --- |
| Swiss knowledge, 15 questions (E7) | 70B 12/15, 8B 9/15 | 70B 11/15, 8B 9/15 (same failing questions) |
| real votes, Spearman with the real yes-share, personas, DE / FR (E8, 54 votes, 3 672 calls) | 70B 0.25 / 0.38, 8B -0.02 / 0.02 | 70B 0.25 / 0.37, 8B -0.02 / 0.03 |
| persona-less with the Federal Council line, DE / FR | 70B 0.47 / 0.54, 8B 0.67 / 0.56 | 70B 0.47 / 0.54, 8B 0.67 / 0.56 |
| Federal Council position alone | 0.63 | 0.63 (no model) |
| recalibrated MAE on the 15 votes of 2025-26 | 70B 12.4-12.5 pp, 8B with the line 8.2-10.2 pp | 70B 12.4-12.6 pp, 8B with the line 8.2-10.2 pp |
| yes-bias, 15 residents with a persona / without (E11, E24) | 15 / 15 yes | 14 / 15 yes with, 15 / 15 without, on four models |

The silicon-electorate result and the yes-bias are properties of the weights, not of one deployment.
