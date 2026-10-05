# Where an open Swiss LLM stops being enough: measuring Apertus 1.5 inside a bilingual generative-agent town

*Draft, 5 October 2026. Team GemeindeSim, Hack Apertus Track 2B. Raw data, code and the chronological
notebook are in `track_2b/research/` and `track_2b/docs/research/`; every number below is traceable to
a logged run.*

## Abstract

We built GemeindeSim, a town of generative agents that read a Swiss municipal vote in German and French
and talk about it on a map, on top of Apertus 1.5 (8B and 70B), the first fully open Swiss LLM. Instead of
only demonstrating it we used it as a test bench for the model. Across 18 experiments (≈ 5 000 stand-alone logged
gateway calls plus 15 instrumented simulations) we measured what an agent loop needs from the model and where the
model, and our own code, fail. **Model limits:** native parallel tool calls fail (11/11 trials per model);
"thinking" and JSON mode cannot be combined (a thinking request with `json_object` silently skips the
reasoning and answers wrongly); `temperature 0` is not reproducible (5 identical prompts gave 3 and 5
distinct outputs); the gateway tolerates only 4 requests in flight; both sizes define the central Swiss
tax term wrongly and fail a one-step percentage; language fidelity in German and French is excellent
(112/112 events). **Population validity:** asked directly, every simulated resident votes *yes* regardless of
persona (15/15, also with no persona and with a balanced corpus); on 54 real federal votes the simulated
electorate is 34–37 points too favourable, persona detail adds little, and the 8B follows an official
recommendation 98 % of the time. **Engineering:** the pipeline contained defects independent of the model
(0 % valid citations, a polarisation artefact, a non-existent "calculator", dropped influence events,
invented vote outcomes in reports). A design principle — *the model voices, the code owns stance, numbers
and sources* — and targeted fixes removed them (citations 0 → 99 %, invented outcomes 12/30 → 0/30,
unanimity → visible disagreement) and, once the stance was bound to the prompt's last paragraph, residents' speech matched their stance in 0.80 of lines (70B) instead of ≈ 0.5. We release the harness.

## 1. Introduction

Agent-based simulation with large language models promises to let a municipality, a canton office or a
civic-tech group "run" a text — a vote, a budget — before it is put to residents, and see who is affected and
how they might talk about it. The idea is not new (Park et al., 2023), and its validity is contested: LLM
survey respondents flatten groups and misportray them (Bisbee et al., 2024; Wang et al., 2025), LLM
opinion dynamics drift toward consensus (Chuang et al., 2024), and prediction of European elections "largely
fails" (von der Heyde et al., 2024). For Switzerland there is direct evidence that LLM voting on referendums
depends on language and on how information is given (Barmettler, 2026), but none of it covers Apertus.

Apertus is open in weights, data and process, multilingual, and aimed at being deployable on Swiss
infrastructure. A civic simulator built on it is a natural use case — and a demanding one: it needs many
structured calls per round, two official languages, figures that must come from a document, and restraint
about politics. We therefore asked three questions:

* **RQ1** What are the capabilities and limits of Apertus 1.5 in such an agent loop, quantitatively?
* **RQ2** Does a population of Apertus residents behave like a population, and like Swiss voters?
* **RQ3** Which failures are not the model's fault (retrieval, grounding, dynamics, reporting), and how much do fixes buy?

**Contributions.** (1) A reproducible table of Apertus-1.5 behaviours that matter for agent loops (§5.1).
(2) Evidence on 54 real Swiss federal votes (2021–2026) that persona-conditioned Apertus electorates are
strongly acquiescent, barely informative beyond an authority cue, and language-sensitive (§5.2). (3) A
division of labour — *the model voices, the code owns stance, arithmetic and sources* — with measurements of
what happens without it (§3, §5.3). (4) An audit-driven baseline-versus-fix comparison on identical seeds
(§5.4). (5) Open code and logs of every call.

## 2. Related work (selected; full review in `01-literature-review.md`)

*Generative agents.* Park et al. (2023, arXiv:2304.03442) introduced memory-retrieve-reflect-plan agents; Park
et al. (2024, arXiv:2411.10109) grounded 1 052 agents in interviews and evaluated against ground truth, which is
the standard we could only partly meet. *Silicon samples and their limits.* Argyle et al. (2023,
arXiv:2209.06899), Santurkar et al. (2023, arXiv:2303.17548), Bisbee et al. (2024), Wang et al. (2025).
*Opinion dynamics.* Peralta et al. (2022, arXiv:2201.01322) survey bounded-confidence and related models that we
implement in code; Chuang et al. (2024, arXiv:2311.09618) show LLM-only dynamics converge toward truth/
consensus. *Persona effects and robustness.* Hu & Collier (2024, arXiv:2402.10811): personas explain little
variance; Ye et al. (2026, arXiv:2605.18890): small perturbations move results by tens of points; population
collapse is documented by Ozkan (2026, arXiv:2607.18310) and Xiao et al. (2026, arXiv:2604.24698).
*Reproducibility.* Atil et al. (2024, arXiv:2408.04667): "deterministic" LLM settings are not. *Structured output.*
Tam et al. (2024, arXiv:2408.02442): format constraints can hurt reasoning; Gao et al. (2023, arXiv:2305.14627):
about half of cited outputs are incompletely supported even for strong models. *Swiss voting.* Barmettler
(2026, arXiv:2606.00048): 48 federal votes, nine frontier models, DE/FR/IT/RM, centrist behaviour on concrete
votes and large cross-language differences; Apertus is not among the models.

## 3. System

**GemeindeSim v1** (commit `0bb53b2`) is a FastAPI/LangGraph backend with a Phaser frontend. Nodes: read the
policy; parse it into sectors/stakeholders/impacts; create residents (role, income, a random left-right
`political_leaning`, a persona written by the model); then per round every resident retrieves memories and
passages, reflects, plans and emits 1–3 events (`chat`, `move`, `protest`, `mood_shift`, `price_change`). Opinion
updates (Deffuant bounded confidence, Baumann drift, keep/compromise/adopt from Chacoma & Zanette via
Peralta et al.) run in Python. A report is written at the end. All model calls use JSON mode, thinking off, a
placeholder example instance, a Pydantic validator, a repair call, and a deterministic fallback.

**GemeindeSim v2** (this work) keeps the architecture and changes what the audit and experiments
justified:

1. *Stance owned by code.* Each resident has `stance ∈ [−1, 1]` computed once as
   `valence × leaning + 0.5 × impact − 0.6 × burden + noise`, where *valence* (which side the measure favours) comes from
   the policy analysis, *impact* from a model judgement about the household, and *burden* from a deterministic
   calculator (new; reads the booklet's worked example and scales it by income band). Apertus writes the best
   argument for and against in the resident's language; the code chooses which one the resident holds. Bounded-confidence updates act on the stance,
   drift applies only to residents who conversed, and `policy_approval` for a vote is the stance poll.
2. *Grounding that can be checked.* Sentence-aware chunks tagged per language, BM25 with accent folding and
   light stemming, the ballot-question chunk always included, a query in the resident's language, citation
   labels (`P1…`) validated against that resident's pack, a numeral gate with normalised numbers.
3. *Report discipline.* The report prompt states that the vote has not happened and fixes the output language;
   the stance poll is supplied by code; a sentence-level sanitiser removes advice and asserted outcomes.
4. *Model-interface hygiene.* A null-tolerant event schema; an instruction-placeholder example per language;
   back-off on 429 instead of a silent switch to the 8B; Swiss orthography (ß → ss) in code.

## 4. Method

**Instrumentation.** A headless runner drives the unmodified LangGraph graph and logs every prompt,
response, token count and latency (`research/run_sim.py`); a gateway client logs full requests/responses
for the stand-alone experiments (`research/common.py`). Metrics are programmatic (regular expressions,
stop-word language detection, schema validation); no LLM judge is used.

**Experiments** (ids as in the notebook). E0 test-suite timing. E1 tool/thinking/determinism probe. E2/E2b
structured-output conditions on 49 logged resident prompts. E3 baseline vs v2.1: 5 residents × 3 rounds, three
70B and two 8B seeds each. E4 opinion-dynamics artefact (offline). E5 retrieval coverage (offline). E6 numeral-gate
edge cases (offline). E7 Swiss civic knowledge (15 questions). E8 54 real federal votes (3 672 calls). E9/E9b
report behaviour under six user objectives. E10 throughput and rate limit. E11/E11b/E11c stance elicitation and
corpus balance. E12 long-context recall. E13 stance fidelity. Experiments shared one API key and were run
sequentially; one early run contaminated by two concurrent jobs was discarded and is recorded as such.

**Caveats of the design.** n is small (3 and 2 simulations per group; 15 residents in the population tests;
15 held-out votes). We report ranges, not significance tests. Temperature 0 is not deterministic (§5.1), so
single runs are anecdotes. Persona marginals in E8 and the stance-prior weights are assumptions. The authors
are not native German or French speakers.

## 5. Results

### 5.1 Capabilities and limits of Apertus 1.5 (RQ1)

*Tool calling.* A single forced or free tool call works (11/11 each size). Two cities in one request yielded one
call (22/22), `tool_choice="required"` did not change that, and on an explicit "return two function calls" the
70B returned **no** `tool_calls` and two pseudo-calls as text (11/11), the 8B one call. A round loop therefore
cannot fan out through one completion; ours fans out over many completions.
*Thinking.* Reasoning appears inside `content` between `<|inner_prefix|>` and `<|inner_suffix|>`, `reasoning`
is null (16/16). Combined with `response_format=json_object` the model emits no reasoning (16/16) and the 70B
answers the bat-and-ball puzzle 0.10 in 15 tokens (correct: 0.05); with thinking alone it is right in 6/8
(two cut at 900 tokens) and the 8B in 8/8. Tools plus thinking is *accepted* without error (one call, no visible
reasoning). "Think, then format" must be two calls.
*Reproducibility.* Five identical long prompts at `T=0` gave 3 (70B) and 5 (8B) distinct outputs.
*Rate limit.* At 5, 6 and 8 requests in flight only 4–5 succeeded (6–12 HTTP 429); at 4 all did. Latency per
request does not depend on concurrency (70B ≈ 10–11 s, ≈ 40 tokens/s per stream; 8B ≈ 2 s, ≈ 158 tokens/s),
so throughput is linear up to 4 (156 and 555 tokens/s) and then capped by the limiter.
*Structured output.* On 49 real resident prompts strict JSON parsing succeeded in 100 % of cases in every
example condition, with or without `response_format`; the old placeholder-example gate failed 14 % of 70B
first attempts because the model returned `null` for string fields. The example is the behaviour policy: a
two-event filled example made both sizes emit two events per turn (8B from 1.0) but the 8B copied 53 % of its
dialogue and the 70B's `move` events fell from 13 to 1; instruction placeholders (`<what you do, one sentence>`)
gave 0 % copying and, with a `move` slot, kept moves on the 70B (6) and raised 8B events from 1.0 to 1.8 per
turn. The 8B never emits `move`.
*Language.* All 112 utterances were in the resident's language (DE/FR) and the DE↔FR translation hop read fluent.
*Swiss facts.* 70B 12/15, 8B 9/15 on Swiss civic questions. Both define *Steuerfuss* as a rate on income; both
fail 4 000 CHF × 6 % (280, 360, 72; correct 240). Both abstain correctly when a premise is missing. The 70B
writes ß at 2.6 per 1 000 characters of German.

### 5.2 Population validity (RQ2)

*Direct stance.* All 15 residents (five roles, three income bands, two languages, leaning from −0.9 to +0.9)
answered *yes* with ≈ 0.8 certainty, identically under four persona ablations including none, and stably across
draws. A balanced corpus with the minority committee's arguments added left 14/15 (27 of 29 at `T=0.7`): the
bias is a model property. Judged impact was "benefit" for 14/15. The model can state both arguments well; it
cannot be the source of the sign.
*Real votes.* With only the ballot title, the 70B electorate says yes in 83 % (German prompt) / 65 % (French) of
cases against a real mean of 46.5 % (24 of 54 votes accepted). Direction accuracy equals the always-No baseline
(0.56) for German personas and reaches 0.69 for French; Spearman with the real yes-share is 0.25/0.38 (70B) and
≈ 0 (8B). Adding a left-right self-placement removes the signal (−0.03/0.10). The Federal Council's position alone
scores 0.75 and 0.63, and no LLM condition beats it: shown the recommendation, the 8B follows it on 98 % of votes
(70B 83 %) and its apparent skill (Spearman 0.67) is that deference. German and French prompts differ by 19
points in yes-rate and flip the majority on 14–17 % of votes; the simulated DE–FR gap is unrelated to the real
Röstigraben (r = +0.17). After a bias correction fitted on ≤ 2024 and tested on 15 votes from 2025–26, the 70B
error is 12.4 pp versus 14.1 pp for predicting the mean. The tool is not a vote predictor.
*Fidelity of the code-owned stance.* Re-asked directly with their own memories, the model agreed with the
code stance for 40 % of residents and turned three of four opponents into "yes" (E13): left to itself it
erases dissent.

*Stated versus expressed position.* Classifying 238 chat and mood lines for the position the speaker expresses showed that
dialogue does not tilt toward yes but toward worry about cost (v2.1 70B: 9–16 % for, 54–61 % against; the baseline already
leaned that way), and that the stance line in the prompt controlled speech only for opponents: residents the code holds *for*
sounded for 17–42 % of the time (E14). A reminder placed as the last paragraph of the prompt, naming the position and the
chosen argument, raised the agreement between speech and code stance from 0.46–0.55 to 0.80 on the 70B and from 0.50–0.52
to 0.73–0.76 on the 8B in the real loop (E15b; 5 runs, 59–80 lines), with no change in schema validity, event mix, citations
or lexical diversity. Residents held *undecided* did not improve (0.53 → 0.58 on the 70B): the model voices cost worry,
not ambivalence.

### 5.3 Defects independent of the model (RQ3)

*Polarisation artefact.* The Baumann term was applied to every resident every round: with zero conversations
mean |leaning| rose from 0.51 to 0.69 (0.72 at high controversy) in 15 rounds and 35–39 % of residents ended beyond
0.9. *Retrieval.* The shipped sample is 1.6 k characters per language, so four passages were half the corpus; even
so the ballot question reached the prompt in 4 of 15 cases, because the query was an English model summary
against a German/French corpus, and a language filter was inert (every chunk tagged `de`). *Citations.* 0 of 159
cited ids existed in the corpus, and `grounded` was true whenever no unknown number appeared. *Numerals.* The gate
passed 8 of 12 edge cases (list numbering grounds the digits 1–5; a substring replace corrupts `124`); a variant
that allowed one-step derived arithmetic made it worse (7/12) because 25 figures reach almost every small number.
*Reports.* With the original prompt 12 of 30 reports (a lower bound) asserted that the measure had passed — also
when the user asked for advice or a result — and language flipped between German and English; explicit vote
advice never occurred (0/30). *Plumbing.* The influence log was silently dropped by the graph (an undeclared state
key), a "calculator" promised in four documents did not exist, and a rate-limit error switched the model to the
8B without a trace.

### 5.4 Baseline versus v2.1 on identical seeds

| | 70B baseline | 70B v2.1 | 8B baseline | 8B v2.1 |
| --- | --- | --- | --- | --- |
| events per run | 27 | 33 | 15 | 30 |
| cited ids that exist | 0.00 | 0.99 | 0.00 | 1.00 |
| ballot question in the resident prompt | 0.13 | 1.00 | 0.30 | 1.00 |
| chats opening with a self-introduction | 0.29 | 0.02 | 0.20 | 0.00 |
| report asserts a result | 2/3 | 0/3 | 0/2 | 0/2 |
| report mixes languages | 3/3 | 0/3 | 2/2 | 0/2 |
| initial stance for/against/undecided | none | 1/3/1; 3/0/2; 2/2/1 | none | 1/2/2; 3/0/2 |
| influence outcomes logged | 0 | 49 | 0 | 39 |

The report prompt change alone took asserted outcomes from 12/30 to 0/30 (E9b). The 70B's wall time fell from
219–235 s to 120–127 s at equal token volume, but the runs were hours apart on a shared endpoint whose latency
varied up to 8× between runs; we do not attribute it to the code. The 8B is about four times faster than the
70B in both versions.

### 5.5 Long context (E12)

A single Linden sentence (118 % → 124 %) was inserted at 10 %, 50 % and 90 % depth into DE or FR haystacks of Swiss
official vote titles and keywords, from ≈ 2 k to ≈ 105 k prompt tokens (the distinct titles are cycled beyond
≈ 72–81 k characters), and the model was asked for the two figures. **Both sizes found the needle in 60/60 cases**
(70B and 8B, German and French, five lengths, three depths). Latency at ≈ 105 k tokens was ≈ 36 s (70B) and ≈ 9 s
(8B), i.e. roughly three times the cost of a 20 k-token prompt. This is the easy version of the question (one fact,
direct question, distinctive content): it shows that *recall* of stuffed text is not the limit up to ≈ 100 k tokens. It does
not test whether stuffing dilutes a persona or degrades multi-fact reasoning, which the pitch also claims and which
remains untested.

## 6. Discussion

**What Apertus is good at here.** Writing in role in two official languages without drifting; arguing both sides
of a measure when asked; abstaining when a premise is missing; following a structured format with very high
reliability once the example and schema are right; refusing to give voting advice even when asked. These match the
project's charter-driven alignment and are real strengths for a civic tool.

**What it should not be asked to do.** Be the source of a stance, of a number, or of a Swiss fact. Its default
disposition on a civic proposal is *yes*, its sensitivity to an authority cue is near-total at 8B, its prompt
language shifts the answer, and it errs on elementary Swiss tax vocabulary and arithmetic. The correct reading is
not that the model is "biased" in a way prompting can remove (a balanced corpus did not) but that the loop must
keep the quantities that decide outcomes in code, where they can be inspected, ablated and recalibrated.

**Implications for design.** (i) The model voices, the code owns. (ii) An example in the prompt is a policy: choose
its content on purpose. (iii) Treat a run as a sample: `T=0` is not determinism, so show distributions. (iv)
Compare conditions, not absolute shares: with / without the council's recommendation, with / without the
committee text, German vs French. (v) A closed corpus is justified empirically, but only if retrieval, citations and
the numeral gate are *tested*, which they were not.

**Sovereign deployment.** Every gateway behaviour above (single tool call, thinking in `content`, four in flight) belongs to
the hosted deployment; the same probe table must be re-measured on a local vLLM before claiming parity.

## 7. Threats to validity

* Small n: 3 and 2 simulations per group, 15 residents, 15 held-out votes; ranges, no significance tests.
* One endpoint, one day; latency drifts; a hosted gateway may change under us.
* The Linden text is synthetic and short; real booklets will stress retrieval differently.
* Heuristic metrics (stop-word language ID, regex outcome/advice detectors) can mis-score; where we checked
  (E9) detectors under-counted.
* The stance-prior weights and E8 persona marginals are assumptions.
* The stance prior is a modelling choice that *produces* disagreement; it is not evidence that real residents
  would disagree in that proportion.
* Authors are not native speakers: register and idiom were not human-reviewed.

## 8. Reproducibility

All scripts in `track_2b/research/`, all raw calls in `research/results/*.jsonl`, the per-run simulation state in
`research/results/sims/`. `make run` starts the application; `uv run --project src/backend pytest` runs the 114
offline tests (46 pin a finding from this paper). The Swissvotes extract used in E8 comes from Swissvotes
(University of Bern), trimmed to the needed columns.

## 9. Conclusion

Apertus 1.5 is a strong *speaker* and an unreliable *decider*. A civic simulation built on it works when the
model is confined to what it does well and the application owns the rest, and it fails in measurable ways when it
is not. The limits we measured — one tool call per completion, thinking incompatible with JSON, non-reproducible
`T=0`, a yes-biased and authority-deferential electorate, wrong elementary Swiss facts — are cheap to measure and
worth publishing; the harness that measures them is part of this submission.

## References (verified in `01-literature-review.md`)

Argyle et al. 2023, arXiv:2209.06899 · Atil et al. 2024, arXiv:2408.04667 · Barmettler 2026, arXiv:2606.00048 ·
Bisbee et al. 2024, Political Analysis 32(4) · Chuang et al. 2024, arXiv:2311.09618 · Gao et al. 2023,
arXiv:2305.14627 · Hu & Collier 2024, arXiv:2402.10811 · Ozkan 2026, arXiv:2607.18310 · Park et al. 2023,
arXiv:2304.03442 · Park et al. 2024, arXiv:2411.10109 · Peralta et al. 2022, arXiv:2201.01322 · Santurkar et al.
2023, arXiv:2303.17548 · Tam et al. 2024, arXiv:2408.02442 · von der Heyde et al. 2024, arXiv:2409.09045 · Wang
et al. 2025 (see review §1.6) · Xiao et al. 2026, arXiv:2604.24698 · Ye et al. 2026, arXiv:2605.18890 · Swissvotes,
University of Bern (data).
