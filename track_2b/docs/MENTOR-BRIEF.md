# GemeindeSim — mentor-meeting brief

Hack Apertus, Track 2B. State as of **5 Oct 2026**, branch `submission/v2` (HEAD `999fd96`). Every number below comes from the logs in
`track_2b/research/results/` and is tabulated in [`research/03-results.md`](research/03-results.md); the story including failures is in
[`research/LAB-NOTEBOOK.md`](research/LAB-NOTEBOOK.md).

"What mentors would recommend" below is **our informed expectation, not something a mentor has said.** Treat it as a hypothesis to test in the meeting.

---

## 0. If you only have 20 minutes

**One-sentence pitch.** A small Swiss town of Apertus-voiced residents reads a municipal vote text (German/French), argues about it with citations to
the text, and reports how the town's stance moved. The model supplies the voice; code owns each resident's stance, the household arithmetic and the
sources, because Apertus alone says "yes" to everything.

**Spend the time on these four** (only a mentor can answer them; the rest we can settle ourselves):

| # | Ask | Why a mentor | Your question 1–9 |
| --- | --- | --- | --- |
| A | Which vLLM version, reasoning parser and tool parser does the gateway run, and does a local `vllm serve` of Apertus behave the same? (reasoning spans land in `content`, `reasoning` is null, no parallel tool calls, 4 in flight, T=0 not reproducible) | Only the people running the gateway know | 1, 2, 3 |
| B | Is code-owned stance + LLM voice a defensible design, or should the dynamics live in the LLM? How would you calibrate the weights? | It is the central design decision | 6 |
| C | For a sovereign/local story: is 8B for the loop + 70B for the shown voice and report a sensible split? What hardware does a municipality realistically have? | Deployment realism; we have no GPU | 8 |
| D | Is the yes-bias (15/15 "yes", ~35 pp too yes on 54 real votes) expected for Apertus, and is there a known mitigation? | Model-training knowledge | new |

**Settle ourselves, do not spend mentor time:** (4) APO vs hand-tuned example — hand sweep is enough for a hackathon; (5) retrieval vs stuffing — one cheap
experiment answers it (section 4); (9) one language per completion — it works (100 % fidelity), just state it.
**Clarify first:** (7) what exactly the "charter line" is — see section 4.

---

## 1. Catch-up: what happened, in order

1. **Starting point (original repo).** A Park-et-al.-style generative-agent town on LangGraph + FastAPI/Socket.IO + Next.js/Phaser. Residents had memory,
   mood, plans; an LLM decided what each resident did every round. The pitch claimed grounding in the vote text, a household calculator, and realistic
   disagreement.
2. **Static audit first** (`02-codebase-audit.md`), hypotheses written *before* testing. Then ~19 experiments (E1–E19) on the hosted gateway, every call
   logged in full.
3. **What we found broken in our own app** (not model issues):
   * Citations: **0 of 159** cited ids existed. Retrieval put the ballot question in the prompt for only 4/15 residents; the language filter was a no-op.
   * The calculator the docs promised did not exist; the model got 4 000 × 6 % wrong (said 280 / 360, correct 240).
   * A silent town polarised on its own (|leaning| 0.51 → 0.69 in 15 rounds with **zero** conversations): the drift ran for everyone.
   * The report said the vote "passed" in at least 12/30 samples, mixed German and English, and gave no advice (good) but invented outcomes (bad).
   * `influence_events` was silently dropped by LangGraph state in all runs. Default concurrency 6 > the gateway's 4; 429s silently swapped to the 8B.
4. **What we found about Apertus** (section 3 table): no parallel tool calls, thinking and JSON are mutually exclusive on this gateway, T=0 is not reproducible,
   strong DE/FR fidelity, needle recall 60/60 to ≈105k tokens, weak Swiss facts, authority deference, and above all a **yes-bias**.
5. **The design response** (section 2): move stance, arithmetic and sources into code; bind speech to stance with one prompt paragraph; ground and validate.
6. **Result on identical seeds** (70B, baseline → final): valid citations 0 → 100 %; ballot question in prompt 13 → 100 %; reports asserting "passed" 2/3 → 0/5; speech
   matches the stance 0.46–0.55 → **0.91** (8B 0.87); influence outcomes logged 0 → 77; 70B wall time 334 → 126 s (**not attributable to our code**, endpoint load varies up to 8×).
7. **Undecided residents** were the hard case: a two-sided prompt raised "mixed" lines 0.47 → 0.74 (70B) but made models copy the supplied argument; "do not repeat word for word" cut copying to 5 %. 8B stays weak (0.54).
8. **Real-world checks.** 54 real Swiss federal votes: persona detail adds little, the Federal Council position alone (direction 0.75, Spearman 0.63) beats every LLM condition
   (0.25–0.38). A real 48-page booklet (28 Sept 2025, German): recall@4 11/14, grounded QA 12/14, 3/3 correct abstentions. French edition not tested.
9. **Submission work.** Fixed a clean-checkout Docker build (the original `make run` failed), compose defaults, a silent HTTP 422 for texts > 4 000 characters
   (cap now 30 000), a 6-page-limit PDF report (3 pages), judge briefing, demo script, native-speaker review pack (49 items), 120 offline tests.
   Pushed to `hatif03/gemeindesim`, public; the default branch `main` was stale and has just been fast-forwarded locally (push pending).

**Honest framing:** this is not a vote predictor and not a proven sovereign deployment. It is a what-if explainer plus a measured map of where Apertus works and where code must take over.

---

## 2. How the app works now

```
vote text (DE/FR) ──► parse policy (LLM: summary, impact, ideological valence of the question)
                 └──► chunk + index (BM25, per-chunk language, ballot-question chunks pinned)
residents (LLM-generated personas, Swiss roles/names, DE/FR)
   └─► STANCE (code):  valence·leaning + 0.5·judged impact − 0.6·computed household burden (+noise)
          └ household burden = calculator on the booklet's worked example, scaled by income band 0.6 / 1.0 / 1.8
every round, for each resident (≤ 4 requests in flight):
   1. retrieve passages in the resident's language → pack with labels [P1]… + personal CHF figure
   2. prompt = persona + memories + pack + "your position: for/against/undecided" + LAST-PARAGRAPH binding of speech to stance
   3. ONE completion, JSON mode, thinking off, `<instruction>` placeholder example → events (chat, mood, move, price, protest)
   4. code checks: citations must exist in the pack · numbers not in the pack are stripped (numeral gate) · Swiss spelling (no ß)
   5. dynamics (code): Deffuant bounded-confidence on stance for residents who actually talked; keep / compromise / adopt
end ──► report (LLM, in the residents' language): no outcome asserted, no vote advice, stance shift summary, localized disclaimer
UI ──► stance poll panel · event feed with citation chips (passage text on click) · resident profile (stance + reason) · report
```

**Division of labour (the pitch in one line): the model voices; code owns stance, arithmetic, sources.**

| Owned by the model | Owned by code |
| --- | --- |
| Persona text, dialogue, mood wording, the report prose, impact judgement ("benefit/burden") | Stance value and poll, household CHF, retrieval and citation validity, number gate, spelling, opinion update rule, report guardrails |

**Known gaps you should know before someone asks:**
* **The 1:1 chat with a resident is not covered by v2.** `graph/chat.py` retrieves memories only; it uses no stance, no retrieval of the vote text (policy summary cut to 800 characters),
  no numeral gate and no Swiss-spelling pass. A resident chatted with directly can therefore say "yes" and quote numbers freely. (I confirmed this by reading the file; it is a small fix — say so if asked.)
* Stance weights (1.0 / 0.5 / 0.6, noise 0.15) and the persona proportions are assumptions, not calibrated.
* Dynamics move little in 3 rounds: the poll is unchanged in 4 of 5 final 70B runs; spread across seeds is large (share *for* 0.00–0.80).
* The model alone agrees with the code stance only 0.64 (7 of 10 code-*against* residents turn "undecided"/"yes" if the model answers by itself) — that is the reason for code ownership and also the thing a critic will poke.
* `price_pressure` is always 0; `invoke_llm_think` is dead code; the numeral gate misses derived arithmetic ("240/12 = 20").
* German/French have not been reviewed by a native speaker yet (pack ready, 49 items).

---

## 3. Measured limits of Apertus 1.5 on the hosted gateway

Gateway: `vllm-0.23.1rc1…-tp2`, `apertus-v1.5-70b` / `-8b`, 5 Oct 2026. Properties of *this deployment*, not necessarily of the model.

| area | finding (n) |
| --- | --- |
| Tool calls | one per request; asked for two → 70B (11/11) writes two pseudo-calls as **text** with no `tool_calls`; 8B emits one |
| Thinking | span appears in `content` as `<|inner_prefix|>…`, `reasoning` field is null (8/8); we strip it in code |
| Thinking + JSON | `response_format=json_object` makes the reasoning vanish (16/16); bat-and-ball answered 0.10 in 15 tokens. Thinking alone: 70B 6/8 right (2 truncated at 900 tok), 8B 8/8 at 266 tok |
| Determinism | T=0, same long prompt ×5: 70B 3 distinct outputs, 8B 5 |
| Concurrency | clean up to 4 in flight; 5 → 4/10 succeed (429). Aggregate: 70B 40 → 156 tok/s (1 → 4 in flight), 8B 158 → 555 |
| Structured output | filled examples get parroted (70B 16 %, 8B 53 %); a placeholder gives 1 event/turn on the 8B; the `<instruction>` 3-event example fixes both (valid 100 %, 0 % parroted) |
| Language | 100 % of 112 utterances in the resident's language; DE↔FR translation fluent |
| Swiss knowledge | 12/15 (70B), 9/15 (8B); *Steuerfuss* misdefined; ß appears in Swiss German (6.3 per run baseline) |
| Long context | 60/60 single-needle recall to ≈105k tokens; latency 70B 31–36 s at 100k vs 1.5–8 s ≤ 22k. **Not tested:** multi-fact, persona dilution, > 105k (the 262k claim) |
| Bias | asked directly, 15/15 "yes" for every persona, with no persona, with a balanced corpus; 54 real votes ≈ 35 pp too yes (70B DE 83 %); language of prompt moves it ≈ 19 pp |
| Authority | 8B follows the Federal Council line 98 % when shown (42 % without); 70B 83 % |

---

## 4. Your nine questions, updated with the evidence

For each: where we are → our lean → what to ask → what mentors would likely say (expectation).

### 1. `json` / `think` / `tool_one` as the production recipe vs json+thinking on the gateway
* **Now:** production = `json` (thinking off, `json_object`, one example). `think` exists but is unused; `tool_one` is unused in the loop.
* **Evidence:** thinking + `json_object` suppresses reasoning (16/16), so the only way to get reasoning *and* a schema is two calls; answer quality with a short JSON turn did not need reasoning because the hard part (stance) is code.
* **Lean:** keep `json` for resident turns; use thinking (separate call, no `json_object`) only where reasoning pays — impact judgement and the report.
* **Ask:** is there a supported way on the gateway to get reasoning *and* constrained output in one call (reasoning parser + guided decoding), or is two calls the norm?
* **Likely:** "Two calls is fine; don't fight the server, but ask us to enable a reasoning parser."

### 2. No parallel `tool_calls` — model, vLLM or gateway?
* **Evidence:** 11/11 on both models; 70B asked for two writes pseudo-calls as text, the 8B emits one; `tool_choice=required` also gives one. Template vs parser vs gateway not separable from outside.
* **Lean:** assume model/template; we do not rely on tools in the loop.
* **Ask:** which tool parser is enabled? Can we run the same probe against a local vLLM? (`research/probe_endpoint.py` is ready; I have no GPU.) If a mentor can run it for 5 minutes, that decides it.
* **Likely:** "Probably the chat template/parser; Apertus wasn't trained for parallel calls. Sequential calls are fine."

### 3. Thinking spans remaining in `content`
* **Evidence:** 8/8 on both models: `<|inner_prefix|>` in `content`, `reasoning` null. `strip_think_tags` removes them; a truncated/unclosed span would leak (2 of 8 70B calls hit the 900-token limit).
* **Lean:** a gateway configuration issue (no reasoning parser for Apertus' tokens); keep the strip as a safety net.
* **Ask:** can the gateway be told Apertus' reasoning delimiters? Is the span format stable across 1.5 → later versions?
* **Likely:** "Config on the vLLM side; strip defensively."

### 4. Example-instance prompting vs a real APO loop
* **Evidence:** a hand sweep of four example styles × 2 models × 49 real prompts: placeholder → low diversity and `to_x=0` echo; filled example → parroting (0.16 / 0.53); `<instruction>` 3-event → valid 100 %, parroting 0 %, echo 0. The example controls event *types* (70B `move` 13 → 1 with a two-event example).
* **Lean:** the sweep was enough; APO adds overfit risk on 49 prompts and burns the 4-in-flight budget. If we do one: held-out prompts, objective = validity + type diversity + parroting + (new) speech-matches-stance.
* **Ask (optional):** any APO setup (DSPy/GEPA-style) that works cheaply with a tiny gateway quota?
* **Likely:** "Good enough for the hackathon; mention it as future work, keep a held-out set."

### 5. Retrieve-first vs stuffing the 262k context
* **Evidence:** retrieval is the *bottleneck* on the real booklet (recall@4 11/14; the model answers right whenever the evidence is retrieved and abstains otherwise). Long-context needle recall is 60/60 to 105k, but latency grows 70B 1.5–8 s (≤ 22k) → 31–36 s (100k), and every resident calls every round at 4 in flight. The real booklet is ≈ 83k characters, so **stuffing it whole is feasible for one booklet**, but untested end-to-end.
* **Lean:** keep retrieve-first because it gives validated citations and passage chips; add a "whole booklet in context" condition and compare.
* **We can settle this ourselves** with one experiment on E17 (14 questions × stuffed vs retrieved, 70B and 8B). Do it before the meeting if there is time (~30 calls).
* **Ask:** has anyone measured Apertus beyond 100k with instructions plus persona (not a needle)?
* **Likely:** "Hybrid: retrieval for citations, long context as fallback; test degradation past 100k."

### 6. Opinion dynamics in equations vs in the LLM
* **Evidence for code:** asked directly, the model is "yes" for everyone; unconstrained drift polarised a silent town; model-alone agreement with the code stance is 0.64. Binding speech to code stance lifts the dialogue match 0.5 → 0.9 with no loss in validity or event mix.
* **Evidence against / risk:** weights are assumptions; dynamics barely move in 3 rounds; the code stance itself is only as good as the persona and the one valence number the LLM provides.
* **Lean:** keep (voice from the model, state from code); add calibration as the explicit next step.
* **Ask:** how would you calibrate — municipal results (Gemeinde-level Swissvotes data), survey (VOX), or just publish sensitivity? Is a persuasion model (LLM scores an argument, equation applies it) the right middle?
* **Likely:** "Defensible, and it is the right call given the bias; be explicit that it is not calibrated; show sensitivity to the weights."

### 7. "Charter line" if a resident is an activist — *please confirm what you meant*
I read this as: **where does the project's own boundary sit when a persona is an activist** (an advocate resident pushing others; persuasion text that could be reused to manipulate real voters).
* **Now:** the report removes vote advice and asserted outcomes (0/30 asserted, 0/30 advice), says the vote has not happened and carries a localized disclaimer; stance is not a prediction; Swissvotes is used under its terms.
* **Open:** activist personas amplify persuasion and the 8B follows authority cues 98 %; we have no rule that stops someone using the dialogue as a messaging test bench.
* **Ask:** is there a hackathon/Apertus charter line (e.g. no targeting of real persons or real campaigns, only synthetic residents, label output as simulation)? Where should we state it — report and UI banner?
* **Likely:** "State a no-real-campaign-use / synthetic-only line and label outputs as simulation; don't over-engineer."

### 8. 8B locally vs 70B for the shown voice
* **Evidence:** 8B is ≈ 4× faster (555 vs 156 tok/s aggregate at 4 in flight); final stance–speech match 0.87/0.85 vs 0.91/0.88; undecided lines 0.54 vs 0.73; Swiss facts 9/15 vs 12/15; never emits `move`; schema 0.88 → 1.00 after re-scoring; strongest authority deference. 70B (tp2) needs two large GPUs; 8B fits one.
* **Untested:** the hybrid itself (8B loop + 70B for report/chat voice) and any local run at all.
* **Lean:** 8B for the loop, 70B for what the user reads (report, 1:1 chat), selectable by env var.
* **Ask:** realistic municipal hardware; vLLM flags for 8B; whether quantized 70B behaves like the hosted one.
* **Likely:** "Hybrid is sensible; test quantized local and report the delta honestly."

### 9. One completion, one language
* **Evidence:** 100 % of 112 utterances in the resident's language, translation hop fluent, no code-switching; cost = one extra call when a UI language differs.
* **Lean:** keep; the open risk is quality, not fidelity — native-speaker review pending.
* **Ask (short):** whether Apertus is expected to hold Swiss-German/Italian equally.
* **Likely:** "Good; add Italian only if you have a reviewer."

---

## 5. Questions we did not have before (rank by value)

1. **Yes-bias**: is it from alignment data? Would a calibration (logit bias, a "devil's advocate" system role) be preferred to code-owned stance? (Measured: persona detail adds almost nothing.)
2. **Local-vs-gateway parity**: why 4 in flight; is T=0 non-determinism from tensor-parallel batching? Does a single-GPU local vLLM give reproducible output?
3. **Validation story**: Federal Council position alone beats every LLM condition (0.75 / 0.63 vs ≤ 0.38). Is "explain and compare conditions" a legitimate research contribution rather than prediction?
4. **Persona data**: synthetic electorate from BFS/census marginals vs LLM-generated personas (homogeneous).
5. **Swiss orthography/dialect**: ß leakage fixed in code; is there an Apertus tokenizer/fine-tune angle?
6. **Sovereignty wording** in the report: how strongly may we claim air-gapped deployability when we measured only the hosted gateway?
7. **Eval metric hygiene**: our self-introduction regex metric ran case-insensitively and was wrong (correction C1 in the notebook). Is there a standard civic-simulation evaluation we should cite?

---

## 6. Questions they may ask you (and honest answers)

| they ask | answer |
| --- | --- |
| Does it predict votes? | No. 54 real votes: ≈ 35 pp too yes; Federal Council alone is better. We say so. |
| Why not let the LLM decide the stance? | It says yes to everyone (15/15); direct elicitation had no spread. |
| Are the weights calibrated? | No. They are knobs; sensitivity and calibration are the next step. |
| Did you test local/sovereign deployment? | No GPU. `LLM_BASE_URL` swap and a portable probe exist; limits are those of the hosted gateway. |
| Is the German/French right? | Not native-reviewed yet; 100 % language fidelity measured, register not. |
| Why is it faster? | We cannot attribute it; the endpoint load varied up to 8×. |
| What does the 1:1 chat do? | Memories only — see known gaps. Not yet grounded or stance-bound. |
| What did you get wrong? | Self-introduction metric (regex case), a first run contaminated by two jobs sharing one key, a numeral variant that made things worse (removed), the regex grader that undercounted — all logged. |

## 7. What to bring / take away

* Bring: stance panel screenshot (`docs/screenshots/06`, `07`), the §3 table, `ensemble_final_70.md` (spread across seeds), `research/probe_endpoint.py`.
* Ask them to: run the probe on a local vLLM (or tell you the gateway flags), name the persuasion/charter wording, recommend a calibration data source.
* Afterwards update `research/06-next-steps.md`.

## 8. Still open before 15 Oct (submit by the 15th, deadline 16 Oct 12:00 CEST)

Push `main`; record the ≤ 2-min video (`DEMO-SCRIPT.md`); native-speaker review (`docs/review/`); rename the PDF with the team name; submit the form; optional: ground the 1:1 chat, stuffed-booklet experiment, local probe.
