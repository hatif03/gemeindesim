# Field notes from building on Apertus 1.5: what we measured, what we invented, what is only standard practice

*Source material for a blog post. Project: GemeindeSim, a Swiss municipal-vote simulator (a small town of German- and French-speaking LLM residents) built for Hack Apertus 2026, Track 2B.
Repository: <https://github.com/hatif03/gemeindesim> (Apache-2.0). Everything below was measured on the two hosted Apertus v1.5 endpoints (the hackathon gateway and the CSCS inference API) between
5 and 7 October 2026; every call is logged in `track_2b/research/results/`, every claim has an experiment id (E#) in `track_2b/docs/research/LAB-NOTEBOOK.md`. Apertus has very little user-written documentation
yet, so the first part is written as a practical field guide for the next person.*

**How to read the labels.** *Measured* = first-hand observation we could repeat, with n stated. *New to us* = we could not find it described elsewhere (we did a literature pass, ≈ 55 papers, `docs/research/01-literature-review.md`, but absence of evidence is not novelty).
*Adapted* = a published idea applied in a new setting. *Standard* = ordinary good practice, listed so nobody mistakes it for an invention. n is small almost everywhere (5–54 items, 3–5 seeds); none of it is a significance-tested result.

---

## Part 1. Field guide: how Apertus v1.5 behaves in an agent loop (measured)

| # | finding | evidence | label |
| --- | --- | --- | --- |
| 1 | **One tool call per request.** Asked for two cities in one request, both sizes return one `tool_calls` entry; `tool_choice="required"` and `parallel_tool_calls=true` change nothing. When explicitly told to "return two function calls", the **70B writes two pseudo-calls as plain text and returns no `tool_calls` at all** (11/11 on the hackathon gateway, 5/5 on CSCS); the 8B returns one | E1, E20: n = 11 / 5 per cell | measured |
| 2 | **`thinking` and JSON do not combine in one call**, except on one model. `chat_template_kwargs: {enable_thinking: true}` on the plain model puts the reasoning in `content` as `<\|inner_prefix\|>…<\|inner_suffix\|>` with the `reasoning` field null; adding `response_format=json_object` makes the reasoning disappear and a trap puzzle (bat and ball) is answered wrongly in 15 tokens | E1, E20: 16/16 | measured |
| 3 | **Separate `-thinking` models exist on CSCS, and only the 8B has a reasoning parser**: the 8B-thinking fills `reasoning`, keeps `content` clean and *keeps its reasoning under `json_object`* (5/5 right); the 70B-thinking still leaves the span in `content`. Thinking models reject tools (HTTP 400, documented) and do not change the yes-bias | E20, E24 | measured |
| 4 | **`temperature 0` is not reproducible on real prompts**, and `seed` does not fix it. A short probe misleads (the CSCS 8B returned 1 distinct output of 5); on our 2–3 k-token resident prompts, three repeats gave 2.5–2.75 distinct outputs on both endpoints and both sizes, with or without `seed` | E1, E23: 24 prompts × 3 | measured |
| 5 | **Rate limits come in three shapes.** The hackathon gateway answered 429 above 4–5 requests in flight on 5 Oct, and on 6–7 Oct, when busy, it *queued* instead (32 in flight: every request at 7.5 tokens/s instead of 30, no error); CSCS answered 2 496 requests up to 96 in flight with no 429 but returns **504 "upstream request timeout"** when long jobs overlap. A client needs: retry on 429 and 5xx, and a limiter that reacts to latency, not only to errors | E10, E21, E29/E31 | measured |
| 6 | **Latency is generation.** On a 70B call, output tokens explain 81 % of the latency (≈ 60 tokens/s), prompt processing ≈ 12 %; Python itself was 2.2 % of the wall time of a run (5 % on the 8B). The wall time of a multi-agent step is the longest *dependent chain* of calls, not the CPU and not the concurrency | E29: 464 calls | measured |
| 7 | **Long context works to 233 k tokens on both endpoints** (single needle: 8B 30/30, 70B 26/30 with digit corruption such as "16 %" for "124 %" in the German haystack above 150 k tokens). A three-fact question: 70B 9/10, 8B **5/10** (it returns the old tax rate or repeats one figure). Latency at 233 k: ≈ 30–45 s on CSCS, 98 s on the busy gateway | E12, E22 | measured |
| 8 | **Prefix caching is real and, on CSCS, visible**: `usage.prompt_tokens_details.cached_tokens` reported 94 % of a shared 24.5 k-token prompt served from cache (a whole booklet in the prompt then costs 1.5 s per call). The gateway does not report the field | E26 | measured |
| 9 | **Strict structured output is deployment-dependent.** `response_format: json_schema` (and `structured_outputs`) is enforced on both endpoints, but on the CSCS 8B 13 of 24 outputs degenerated into valid JSON followed by endless whitespace until `max_tokens`; the same request was 24/24 on the gateway. The old `guided_json` / `guided_choice` parameters are silently ignored (`structured_outputs` is the name that works on these deployments). `json_object` + an example in the prompt was 72/72 valid on both | E20, E23 | measured |
| 10 | **A strong "yes" default on civic questions, a property of the weights.** Asked how a resident votes, both sizes say yes for 14–15 of 15 residents with a full persona and 15/15 with none, with a balanced booklet and with thinking models. On 54 real Swiss federal votes the simulated electorate is ≈ 34 points too "yes" and persona detail adds almost nothing (Spearman 0.25–0.38 for the 70B, ≈ 0 for the 8B) | E8, E11, E24 (replicated on two deployments to ±0.01) | measured |
| 11 | **Deference to an official recommendation.** Shown the Federal Council's line, the 8B follows it on 98 % of votes (42 % without), the 70B 83 % (62 %); the 8B's apparent forecasting skill (Spearman 0.67) is that deference. The recommendation alone (Spearman 0.63, direction 0.75) is as good as any model condition | E8 | measured |
| 12 | **The stance a model "has" depends on how you ask.** Asked for one word, the 8B puts 25 % of its probability mass on "no" for residents it answers "yes" in JSON with a reason; logprobs (available on both endpoints) show it, argmax hides it | E24 | measured |
| 13 | **Swiss civic knowledge is weak and arithmetic unreliable**: both sizes define *Steuerfuss* as a rate on income (it is a multiplier on the simple tax) and get 4 000 × 6 % wrong (280 and 360, correct 240); 12/15 (70B), 9/15 (8B) on 15 questions | E7 | measured |
| 14 | **German and French fidelity is excellent**: 112 of 112 utterances in the resident's language, a separate translation call reads fluently; *Swiss* orthography is not: the 70B emitted ≈ 6 *ß* per run (Swiss Standard German has none) | E3, E7 | measured |
| 15 | **A filled example in the prompt gets parroted; a placeholder gets echoed.** For a JSON turn: a shipped placeholder instance (`"..."`, `0`) gave `to_x = 0` echoes in 82–96 % of 70B turns and one event per turn on the 8B; a realistic filled example was copied (16 % of 70B turns, 53 % of 8B turns); an example with `<instruction>` fields and three events gave 100 % valid JSON, 0 % parroting, 0 echo | E2b: 49 real prompts × 2 sizes × 4 variants | measured |

## Part 2. Techniques we developed (the part that may be new)

| # | technique and what it is | evidence | label | where |
| --- | --- | --- | --- | --- |
| A | **"The model voices; code owns the state."** The resident's stance is computed in code from ideology × the question's valence, the model's *judged impact* on the household and a **calculated household cost**; the model never reports a stance. Opinion dynamics (Deffuant bounded confidence) are applied in code | speech–stance agreement 0.5 → 0.91 on the same seeds; the model alone agrees with the code stance only 0.64 (E3, E13, E14) | adapted (Park 2023, Deffuant, Chuang 2024) to a civic vote, with an explicit stance variable | `graph/nodes/stance.py` |
| B | **A last-paragraph "speech binding".** The stance line alone controls the dialogue only for opponents (residents *for* sounded for 17–42 %); a one-paragraph reminder as the **last** paragraph of the prompt, tying what is said to the stance, lifted agreement from ≈ 0.5 to 0.8–0.91 on both sizes without losing event diversity | E14, E15, E15b | new to us | `stance_binding` |
| C | **Making an *undecided* resident sound undecided.** "You are torn" makes residents sound like opponents; a two-sided instruction (one concrete reason for, one against, never only costs) raised "mixed" lines 0.47 → 0.67 but 62–67 % of turns *copied the supplied argument*; adding "do not repeat the sentences word for word" gave 0.72–0.74 mixed with 5 % copying | E16, E16b | new to us | `stance_binding` |
| D | **The numeral gate.** Every number a resident says must appear in the retrieved passages or come from the calculator; otherwise it is replaced. Edge cases 10/12; a "derived arithmetic" variant was *worse* (7/12) and was removed | E6 | new to us (simple, effective) | `graph/language.py` |
| E | **Validated citations.** The model cites passage labels (`[P1]…`) of *its own* retrieved pack; labels that are not in that pack are dropped. The original app's ids were decorative: **0 of 159 cited ids existed**; now 99–100 % valid and shown to the user as chips with the quoted passage | E3 | adapted | `run_round.py`, UI `EventFeed` |
| F | **A deterministic household calculator** fed into the prompt and the grounding pack, because the model gets the booklet's own worked example wrong (240 CHF) | E7 | standard idea, necessary here | `graph/calculator.py` |
| G | **Report guardrails.** Sentence-level removal of vote advice and of asserted outcomes ("the measure passed") in German, French and English: before, ≥ 12 of 30 reports invented an outcome; after, 0/30 | E9, E9b | new to us | `services/economic_report.py` |
| H | **A grounded 1:1 chat** with three rules found by reading live answers: *answer first, then let the stance colour it* (the round's "in every line…" binding made undecided residents answer every question with their position); *strip all bracketed text after reading the valid citation labels*; *label the calculator figure as the resident's own household*. Result: 0 invented figures, unknown facts declined 5/5, 0/5 vote recommendations | E25 | new to us | `graph/chat.py` |
| I | **Whole text first, cached.** For documents of 6 000–100 000 characters the complete text is the *first* part of every chat prompt (identical across residents, so the prefix cache serves it); labelled passages stay for citations. A question retrieval missed 5/5 times was answered 5/5 | E26, E28 | adapted (long-context + caching) | `chat.py` |
| J | **Guardrails before streaming.** The chat answer is sent sentence by sentence, but each sentence passes the number gate, bracket removal and Swiss spelling *before* it is sent, so the user never sees text the checks would have changed; first text after 1.5 s instead of 2.4 s | E32 | new to us | `stream_npc_chat_reply` |
| K | **A congestion-aware adaptive limiter for LLM calls.** Slow start (double on a clean streak), halve on 429 / 5xx, remember the ceiling that worked, and step back one level only when a *rise* of the limit makes every answer more than 2× slower per token (a gateway that queues instead of answering 429), while ignoring slowness that other users cause. One setting (`auto`) works on an endpoint that says 429 at 5 and on one that allows 96 | E31 | adapted (AIMD / slow start / Vegas-style latency rule) | `graph.llm.Limiter` |
| L | **One build, two endpoints.** Model ids differ (`apertus-v1.5-70b` vs `swiss-ai/Apertus-v1.5-70B`); a resolver maps either style to the one the endpoint serves and derives the matching 8B fallback; tested live in both directions | E31 | standard engineering, undocumented for Apertus | `config.resolve_model` | 
| M | **A what-if comparer, not a predictor.** The same seeds are run under different texts (with/without an official recommendation, with/without the committee's counter-arguments); a "yes" and a "no" recommendation move the stance equally little (the code stance does not read it), adding the counter-arguments lowers it in all three seeds. A 5-run spread in the app shows the *range* of the poll, because one run is an anecdote (share *for* at the end ranged 0.00–0.80 across five seeds) | E19, E3d, E27b | adapted | `routers/ensemble.py` |
| N | **Silicon electorate vs real votes.** A reusable check of an LLM electorate against 54 federal votes (Swissvotes, Univ. Bern) with the right baselines (always-No, the Federal Council line alone) | E8 | adapted; the baselines are the useful part | `research/exp08_*` |

## Part 3. Method: how we kept ourselves honest (transferable)

* **Log every call in full** (request + response, no credentials) so any number can be re-derived; keep negative results (a contaminated first throughput run, a number-gate variant that was worse, an automatic grader that undercounted 7/14 vs 11/14 by hand).
* **A metric is a claim: read its false positives.** Our self-introduction regex ran case-insensitively and flagged "Ich bin noch unentschieden" as an introduction; the correction (C1) is in the notebook, the numbers recomputed.
* **Same-day control on the other endpoint before attributing a difference.** Three "CSCS advantages" we first wrote (strict `json_schema`, `seed`, the 262 k window) were also true of the gateway; the control corrected them before they reached a document.
* **Replicate on a second deployment**: the real-vote result and the v2 fixes reproduced to ±0.01 Spearman and with the same citation validity, so they are properties of the weights and the design, not of one gateway.
* **Measure the thing a mentor asks about instead of arguing it**: "is Python slow?" became a CPU-time measurement (2.2 %), "do we use caching?" became a regression of latency on prompt vs output tokens.
* **Hand-grade the small set** that matters (14 booklet questions), and say that n = 14 means differences of one question are noise.

## Part 4. Standard practice (so it is not mistaken for novelty)

JSON mode with Pydantic validation and a repair call; BM25 retrieval, sentence-packed chunks, reciprocal rank fusion (our hybrid option); Park et al.'s memory / reflection / plan loop; Deffuant bounded confidence and Baumann controversy drift; asyncio with a semaphore; Socket.IO for streaming events;
prefix caching; Docker compose; a closed corpus with abstention ("not in the text").

## Part 5. Open questions for the Apertus team

1. Why is the reasoning span left in `content` (and `reasoning` null) on the plain model and on the 70B-thinking, but parsed on the 8B-thinking? Is a parser setting planned for all?
2. Is "one tool call per request, two pseudo-calls as text on the 70B" the intended behaviour of the chat template, or a parser limit?
3. Is the strong *yes* default on civic proposals a known effect of alignment data? Would a system-role or a logit-level mitigation be preferred to computing the stance outside the model?
4. Can strict `json_schema` be made reliable on the 8B (it degenerates into whitespace on one deployment)?
5. What is the expected behaviour of `seed` and `temperature 0` under tensor-parallel batching? We could not make a long prompt reproducible.
6. Are the Swiss-orthography (no *ß*) and *Steuerfuss*-style knowledge gaps something a fine-tune or a glossary in the system prompt is expected to close?

## Part 6. Blog outline (suggested)

1. **"One tool call per request: what to expect from Apertus 1.5 in an agent loop"**: findings 1–5 with the throughput chart and the two-endpoint table (Part 1). The most reusable post.
2. **"The model voices, code owns the state"**: why we moved the stance out of the model (the 15/15 yes, the 0.5 → 0.91 speech binding, the undecided-resident story), with the before/after chart (techniques A–C).
3. **"Grounding a civic assistant: citations, numbers and 'not in the text'"**: D, E, F, G, H, I, and the 0-of-159-citations confession.
4. **"Is Python slow? We measured"**: finding 6 and the critical-path picture; how to read a multi-agent wall time; the limiter (K, L).
5. **"A simulation is a what-if, not a forecast"**: the 54 real votes, the 98 % deference, M and N.
Charts already in the repo: `docs/figures/` (pipeline, stance formula, speech-matches-stance, yes-bias, real-votes signal, throughput, fixes, endpoints), `docs/research/ensemble_final_70.png`.

## Part 7. Where to look

| need | path |
| --- | --- |
| complete project explanation | `track_2b/docs/MENTOR-BRIEF.md` (also `.pdf`) |
| every experiment, failure and correction | `track_2b/docs/research/LAB-NOTEBOOK.md` |
| consolidated results, pitch audit, paper draft | `docs/research/03-results.md`, `04-pitch-audit.md`, `05-paper-draft.md` |
| two endpoints compared, and the plan | `docs/research/07-cscs-vs-livemap.md`, `08-cscs-plan.md`, `docs/ENDPOINTS.md` |
| engineering questions (async, streaming, caching, RAG, tokens) | `docs/ENGINEERING-QA.md` |
| reproduce | `track_2b/research/` (`probe_endpoint.py` measures any endpoint), `research/README` in the notebook |

*Not claimed:* that GemeindeSim predicts votes; that it was tested on a local or air-gapped deployment; that the stance weights are calibrated; that the German and French were reviewed by a native speaker (the review pack is ready, not yet returned).
