# Running GemeindeSim on either inference endpoint

The mentors confirmed that the judges run the app against the **CSCS inference API**; we developed on the hackathon gateway ("livemap") and measured both (research
E20–E32, [`research/07-cscs-vs-livemap.md`](research/07-cscs-vs-livemap.md)). One build runs on both: three environment variables, nothing else.

## Judges: what to set

```bash
cp track_2b/.env.example track_2b/.env     # then edit the three lines
LLM_BASE_URL=https://api.inference.cscs.ch/v1
LLM_NAME=swiss-ai/Apertus-v1.5-70B
LLM_API_KEY=<your key>
make run                                    # http://localhost:3000
```

The defaults in `.env.example` and `docker-compose.yml` are already the CSCS values, so only the key has to be filled in. Everything else (model-id style, concurrency, fallback model) is handled by the app.

## What differs between the endpoints, and what the app does about it

| difference | livemap (`https://hackapertus.livemap.sh/v1`) | CSCS (`https://api.inference.cscs.ch/v1`) | in the app |
| --- | --- | --- | --- |
| model ids | `apertus-v1.5-70b`, `apertus-v1.5-8b` | `swiss-ai/Apertus-v1.5-70B`, `-8B`, `-70B-thinking`, `-8B-thinking` | `config.resolve_model` maps either style to the one the endpoint serves (Apertus v1.5 ids only; any other id, e.g. a local vLLM, is passed through unchanged) |
| fallback model (after a timeout / 5xx) | `apertus-v1.5-8b` | `swiss-ai/Apertus-v1.5-8B` | derived from `LLM_NAME` (`config.smaller_model`); never a different family; nothing smaller → no silent switch |
| requests in flight | 429 above ≈ 4–5 | no limit found up to 96 | `LLM_CONCURRENCY=auto`: slow start from 4, halve on 429 / 5xx, remember the ceiling, step back one level when a rise makes each answer more than 2× slower per token (a gateway that queues instead of answering 429); a number fixes it |
| overload answer | HTTP 429 (and queueing under load) | HTTP 504 "upstream request timeout" when long jobs overlap | 429 retried with back-off (≤ 6×), 502/503/504 retried twice on the same model, then the caller decides |
| token usage | `usage` has no cache field | `cached_tokens` reported | the metrics panel shows the cache share when it is reported (0 % means "not reported" on livemap) |
| thinking models | none (`enable_thinking` puts a span in `content`) | separate `-thinking` models | the loop uses the plain model with thinking off on both; spans are stripped defensively |
| strict `json_schema` | works | works on the 70B, **breaks on the 8B** (endless whitespace) | not used: `json_object` + an example in the prompt works on both (E23) |
| embeddings | 404 | 404 / 403 | hybrid retrieval is a local, optional model (`EMBEDDING_MODEL`), off by default |
| key scope | hackathon key | one key reaches only the four Apertus v1.5 models (other models: 403) | `LLM_NAME` must be one of them |
| streaming, `n`, `logprobs`, `stop`, system role, 262k context | work | work | chat streams sentence by sentence on both |

## Verified

| check | result |
| --- | --- |
| unit tests (`tests/test_metrics_and_endpoints.py`): id mapping both directions, fallback derivation, adaptive limiter (slow start, ceiling, floor, latency rule, external slowness) | pass |
| **CSCS URL + livemap-style id** `apertus-v1.5-70b`, `LLM_CONCURRENCY=auto`: simulation + 15 chat answers | model sent as `swiss-ai/Apertus-v1.5-70B`, 44 calls, 0 errors, limit grew 4 → 9 |
| **livemap URL + CSCS-style id** `swiss-ai/Apertus-v1.5-70B`, auto: simulation + 15 chat answers | model sent as `apertus-v1.5-70b`, 42 calls, 0 errors, limit grew 4 → 9 |
| 25 residents × 2 rounds, auto, **CSCS** | 89–97 s (the same run: 6.7–7.3× faster than livemap that afternoon), limit grew 4 → 32, 0 retries |
| 25 residents × 2 rounds, auto, **livemap** (busy that day: 28 s mean call latency, 12 tokens/s per request) | 654 s, limit grew 4 → 16, 1 × 429 handled, 0 errors (the first, additive limiter, which stayed at 4 in flight, took 656 s: on the busy gateway more requests in flight added latency, not throughput) |

## If something does not work

* `401`: the key does not belong to that base URL (a CSCS key on livemap or the other way round).
* `403 key not authorized for this model`: `LLM_NAME` is not one of the four models the key reaches.
* The backend logs its effective setting at start (`GemeindeSim ready — model=… base_url=…`) and `GET /metrics` returns the model, the endpoint host, tokens, cache share, retries and the current in-flight limit.
* Slow runs: look at the "Run metrics" panel (mean latency, decode speed in tokens/s per request, in-flight limit). Decode speed per request below ≈ 20 tokens/s on the 70B means the endpoint is busy, not that the app is slow
  (CSCS 57–64 tokens/s, livemap 30 on a quiet day and 8–15 when busy).
