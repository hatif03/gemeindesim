# GemeindeSim: the pitch

*Why this project should exist, why on Apertus, why Switzerland, and what it changes for the people who write, read and vote on official voting material. Every factual claim is tagged by where it comes from: **[ours]** measured in this repository (experiment ids in
[`research/LAB-NOTEBOOK.md`](research/LAB-NOTEBOOK.md)), **[V]** a source opened and read, **[S]** seen in a search result only (verify before quoting on stage), **[context]** common knowledge we did not look up. Section 14 lists the sources.*

---

## 0. The pitch on one page

**One line.** *Before a Swiss Gemeinde prints its voting booklet, it can watch a small, synthetic town read it: where it lands, who is confused, which numbers nobody can find, and what changes if the text changes. Sources cited, no vote advice, running on Swiss open weights.*

**The problem.** Switzerland asks its citizens to decide on tax rates, school credits and federal laws, again and again, on the strength of an official text that is written once, by a small team, in several languages, and is read by people whose stakes differ completely (a tenant, a shop owner, a retiree, a municipal employee).
Nobody can pre-test that text on a diverse electorate before it is printed: a real panel is slow and expensive, and a generic chatbot answers one question at a time and invents figures. **Official texts are known to be hard to read** [S: studies of Swiss voting materials report language levels around CEFR C1/C2; the press asks whether the booklet is too complex].

**The solution.** GemeindeSim creates a bilingual (German/French) fictional town from the vote text. Residents with different roles, incomes and languages talk to each other and quote the text; every quoted sentence links to the passage it came from; every figure comes from the text or a calculator; a stance poll shows how the town splits and how it moves; the report describes who is affected and why, and never says how to vote or who will win.
You can run the same vote five times and see the *range*, change the text and compare, or ask a resident a question.

**Why a simulation, not a chatbot.** Heterogeneity (different residents read the same sentence differently), interaction (opinions move when people talk), and *what-if comparison* (the same seeds under two texts) are what a pre-test needs; a single assistant has none of them. The literature supports using such simulations **comparatively and for pilots, not as forecasts** [V], which is exactly how we position it.

**Why Apertus.** Swiss, fully open (weights, data, recipes), compliant with Swiss and EU rules, hosted in Switzerland, strong in German/French (our test: 112 of 112 utterances in the right language), a 262k-token context that holds a whole booklet, Apache-2.0 weights (the 8B card adds an acceptable-use gate) so a Gemeinde can run it itself, and a model charter built around neutrality, consensus, federalism and multilingualism [V/S]. A foreign API is the wrong default for a draft that is not yet public.

**Why it is credible.** We tested the model instead of trusting it: it says "yes" to everything (15 of 15 residents, ≈ 34 points too favourable on 54 real federal votes), so **the stance is computed in code and the model only voices it**; we fixed what was broken in our own earlier pitch (0 of 159 citations were real, reports invented outcomes); and every result replicates on a second endpoint. We publish the limits.

**The ask.** A pilot Gemeinde (one real booklet, before publication), a native-speaker reviewer for German and French, and Apertus-team answers to six open questions (Part 5 of [`INNOVATIONS.md`](INNOVATIONS.md)).

---

## 1. The problem: official material is written once and read by very different people

* **Volume and level.** Swiss voters decide at three levels (Confederation, canton, Gemeinde), on several voting days a year [context]; our Swissvotes benchmark alone holds 54 federal votes from March 2021 to September 2026 [ours: E8]. There are **2 121 Gemeinden** (status March 2025) [S: BFS figure quoted by swissinfo], and most Gemeinde budgets, tax rates (*Steuerfuss*) and credits are decided locally [context].
* **The text is the product.** The Federal Council must inform completely, objectively, transparently and proportionately, present the main positions of the parliamentary debate, and **may not recommend against Parliament's position**; objectivity forbids misleading about purpose or scope, withholding relevant facts, or misreporting the opponents' arguments (Art. 10a BPR) [V/S: fedlex text via search]. The same expectation carries to cantons and Gemeinden. The legal standard is clear; **whether a text meets it for real readers is rarely tested before it goes out**.
* **Readability is a documented problem.** A study published in 2021 reported that analysed voting information was consistently written at CEFR C1/C2; another found that feeling one had understood a proposal raised support, while actually understanding it did not [S: Yearbook of Swiss Administrative Sciences 2021; Translation Spaces]. Swiss media ask whether the booklet is too complex for many [S: SRF 2022].
* **The audiences do not share a stake.** The same sentence "the Steuerfuss rises from 118 % to 124 %" means 144 CHF a year to one household and 432 CHF to another [ours: calculator, E7]. A single "average opinion" hides that.
* **Existing help does not pre-test.** *smartvote* matches voters with candidates, *easyvote* produces neutral explainer leaflets for young voters (largely volunteer work), *Swissvotes* archives every vote [S]. These inform readers *after* the text exists. Nothing lets the author watch the text land on a diverse town *before* publication.

## 2. What GemeindeSim is, and is not

| it is | it is not |
| --- | --- |
| a **what-if explainer and pre-test** of an official text on a fictional, role-based town | a vote predictor: ≈ 34 points too favourable on 54 real votes, so we do not claim forecasts [ours: E8] |
| **closed corpus**: residents quote only retrieved passages (shown as chips) and computed figures | a chatbot with opinions: the model never decides a stance [ours: E3, E11] |
| a **report** of who is affected and why, in the residents' language | advice: no vote recommendation (0/30), no asserted outcome (0/30) [ours: E9b] |
| **open and self-hostable** (Apache-2.0, `LLM_BASE_URL` points anywhere) | a SaaS: it runs where the text is allowed to be |
| honest about limits: see [`research/04-pitch-audit.md`](research/04-pitch-audit.md) | a replacement for a human panel or for legal review |

**Who uses it, and for what.**

| user | task | what they get |
| --- | --- | --- |
| Gemeindeschreiberin / Gemeinderat drafting the Botschaft | pre-test before printing | which passages are never cited, which figure questions have no answer in the text, where tenants and owners diverge, what changes with and without the committee's counter-arguments |
| Cantonal chancellery / language services | multilingual parity check | the same text run in German and French; the prompt language alone moved the stance by ≈ 19 points and the majority by 14–17 % of votes in our test, a signal of translation drift to look at [ours: E8] |
| Civic education (Staatskunde, easyvote-style projects) | classroom | students question a resident, see the cited passage, replay a saved run |
| Civic tech and journalism | explainers | "where does this text land", with sources |
| Researchers | a reproducible Swiss testbed | the harness, the 54-vote benchmark, every call logged |

## 3. Is there precedent? Simulations of people are useful, with conditions

**Where simulated populations have been shown useful**

| work | what it shows | how we use it |
| --- | --- | --- |
| **Social Simulacra**, Park et al., UIST 2022 [V: abstract] | LLM-populated prototypes let designers see how a system behaves with many users *before* any real user; participants often could not tell simulated from real community behaviour, and designers iterated on their designs with it | the closest conceptual twin: a **populated prototype of an official text** |
| **Generative Agents**, Park et al., UIST 2023 [V] | memory, reflection and retrieval give believable individual and emergent behaviour | our resident loop |
| **1 052-person simulation**, Park et al. 2024 [V] | agents grounded in interviews reached 83–86 % of participants' own test–retest consistency and beat demographic-only personas by 12 points | rich grounding beats thin personas: why role, income and a life story, and why the next step is statistics-based personas |
| **Silicon samples**, Argyle et al., Political Analysis 2023 [V] | persona-conditioned models show fine-grained, demographically correlated response patterns | the optimistic case for persona conditioning |
| **LLMs predicting survey experiments**, Hewitt et al., Nature 2026 [V, caveat] | on 70 pre-registered US survey experiments, simulated responses predicted treatment effects about as well as pooled human forecasts, with a tendency to overestimate | supports **comparing conditions** (text A vs B, with vs without a recommendation), not absolute vote shares |
| **The Habermas Machine**, Tessler et al., Science 2024 [S] | an LLM mediator helped groups (> 5 000 UK participants) find common ground; its statements were preferred over human mediators' | LLMs are credible *civic instruments*; ours informs the author, not the voter's choice |
| **AgentSociety**, **OASIS**, **S3** [V] | large-scale open platforms (10 000+ agents; polarisation, herd effects, information spreading) | shows the method is established; they target social media, none targets a closed official text with citations |
| Pilot use of LLM simulations, Anthis et al., ICML 2025 [V] | simulations are usable for pilot and exploratory studies with iterative evaluation | our stated scope |

**Where it fails, and what we did about it** (we cite the critics because a judge will)

| critique | source | our answer |
| --- | --- | --- |
| LLM survey respondents have unrealistically low variance and flip effect directions | Bisbee et al. 2024 [V] | we measure spread across seeds and report ranges, not a mean [ours: E3d, E27b] |
| identity-keyed personas misportray and flatten groups | Wang et al., Nature MI 2025 [V] | residents are role- and issue-based fictional archetypes; the report says so |
| LLM predictions of European elections "largely fail" | von der Heyde et al. 2024 [V] | we do not predict |
| the only Swiss referendum study: model "politics" depends on the measuring instrument; cross-language inconsistency | Barmettler 2026 [V] | we run per language and report cross-language agreement [ours: E8] |
| LLM-only opinion dynamics collapse toward consensus | Chuang et al. 2024 [V] | **opinion state is computed in code**, the model only voices it [ours: E3, E15] |
| validation of generative social simulation is mostly "believability" | Larooij and Törnberg 2025 [V] | we validate against 54 real votes, a real booklet, and two endpoints, and publish the negative result |

**Our own tests of the same risk.** Asked directly, Apertus said yes for 14–15 of 15 residents whatever the persona; the persona simulation correlates only weakly with real votes (Spearman 0.25–0.38, 70B) and the Federal Council's line *alone* (0.63) is as good as any model condition [ours: E8, E11, E24]. That is why the product is a **comparative pre-test**.

## 4. Why Apertus (and why not just any model)

| reason | evidence | note |
| --- | --- | --- |
| **Sovereignty for a draft that is not yet public.** A Gemeinde's draft Botschaft is an internal document; a foreign API is the wrong default | Swiss data-protection officers (privatim, 24 Nov 2025) declared the use of a large SaaS office suite for specially protected data and official-secret material inadmissible in most cases [S]; this suggests the direction of travel for authorities: Swiss-hosted or on-premise | our app's only outbound call is `LLM_BASE_URL`: CSCS today, on-prem vLLM later (configured; local run not yet measured) |
| **Fully open and Swiss** | EPFL, ETH Zurich and CSCS released Apertus in September 2025: open weights, data and recipes, trained on the Alps supercomputer in Lugano, compliance with Swiss and EU rules, robots.txt opt-outs respected [S/V] | auditability matters for a civic tool; judges and Gemeinden can inspect the model, not just the product |
| **The languages we need** | Apertus 1.0: 15 T tokens, > 1 800 languages, ≈ 40 % non-English; post-training includes Swiss-German and Romansh instruction data [V]. Our test: **112 of 112** utterances in the resident's language, fluent DE↔FR translation | Italian and Romansh are the next step [not tested] |
| **Neutrality built into the model's charter** | the Swiss AI Charter (11 articles: neutrality, consensus-building, federalism, multilingualism) is used in alignment [V]; our guardrail tests: 0/30 explicit vote advice | the charter fits Art. 10a-style duties; we still add code guardrails because the model asserted invented outcomes in most default reports |
| **A context that holds the whole booklet** | Apertus 1.5: 262 144 tokens [V]; our tests: needle recall to 233 k tokens on both endpoints; a whole 25 k-token booklet answers 13/14 questions vs 11/14 with retrieval [ours: E22, E26] | a real, cheap feature for civic documents |
| **Sizes a municipality can host** | 8B and 70B, Apache-2.0 with an acceptable-use gate on the 8B card [V]; the 8B is 2.3× faster than the 70B and keeps most behaviours [ours] | on-prem for the 8B is realistic; the 70B needs larger hardware |
| **A public benefit loop** | little user-written documentation exists; our measured field guide (one tool call per request, thinking vs JSON, non-reproducible `temperature 0`, rate limits, the yes-bias) is published for the next builder | [`INNOVATIONS.md`](INNOVATIONS.md) |

**Honest limits of the Apertus case.** It has the yes-bias, weak Swiss facts (12/15 on our questions; it misdefines *Steuerfuss* and gets 4 000 × 6 % wrong), strong deference to an official recommendation (8B: 98 %), and `temperature 0` is not reproducible.
We do not say it is the most capable model; we say it is the right *fit* (open, Swiss, multilingual, hostable, charter-aligned) and that **the design makes the weaknesses harmless**: facts come from the corpus and a calculator, the stance from code, the guardrails from code.

## 5. Why the Swiss narrative is not decoration

1. **Direct democracy multiplies the problem.** More decisions, at three levels, each with its own text. A tool that makes each text testable scales with the number of votes, not with the number of experts.
2. **Federalism and multilingualism are structural.** The same measure is published in several languages; the *Röstigraben* is a known pattern. A DE/FR parity check is a Swiss need, not a feature of a generic simulator.
3. **Gemeindeautonomie and the Milizsystem.** Tax rates and credits are decided locally by volunteer authorities with small administrations [context]; they cannot commission a panel for each Botschaft. A free, self-hostable pre-test fits that reality.
4. **Neutrality is law and culture.** Art. 10a BPR on the federal level; the Apertus charter in the model; "no vote advice" in the product. The same constraint shapes all three, so the product's refusal to recommend is not a limitation but the legitimacy.
5. **A national AI infrastructure exists and wants real use cases.** Apertus and CSCS were built as public infrastructure; a municipal use case that runs on them end to end (model, hosting, language) is the kind of proof the Swiss AI Initiative needs [context].
6. **The ecosystem is already there to plug into.** Swissvotes (archive and benchmark), smartvote and easyvote (reader-side tools), the Federal Chancellery's booklets (the corpus), Gemeinde Botschaften (the target). GemeindeSim sits *upstream* of them, at the author.

## 6. How it helps, concretely (with the numbers we can show)

| need | what GemeindeSim does | evidence |
| --- | --- | --- |
| "Will people find the figure that matters?" | residents ask for it and the report lists what the text never answers; abstention when it is not in the text | grounded QA 12/14, 3/3 correct abstentions on a real 48-page booklet; chat declines unknown facts 5/5 [ours: E17, E25] |
| "Does every number in our text check out?" | the numeral gate removes figures that are not in the text; the calculator computes household cost | 4 000 × 6 % the model gets wrong, the calculator right [ours: E6, E7] |
| "Who is affected differently?" | role, income band and a computed household cost drive each resident's stance | stance poll with spread across runs (share *for* 0.00–0.80) [ours: E3d] |
| "What if we add the counter-arguments?" | same seeds under two texts | adding the committee's counter-arguments lowered the mean stance in 3 of 3 paired seeds [ours: E19, n = 3, 8B] |
| "Is the French the same as the German?" | run both languages, compare | prompt language moved the stance ≈ 19 points (70B) [ours: E8] |
| "Can citizens ask the town?" | grounded 1:1 chat with cited passages | 0 invented figures, 0/5 vote recommendations, first text after 1.5 s [ours: E25, E32] |
| "Can we afford it?" | one 5-resident, 3-round run ≈ 61 s and ≈ 70 000 tokens on the 70B (≈ 23 s on the 8B); 25 residents ≈ 90–105 s | [ours: E27, E29, E31]; hosting cost depends on where it runs; CSCS access and self-hosting are both possible |

**Scale and cost story (Track criterion 3).** Residents run in parallel; the app adapts its request rate to the endpoint (4 in flight on a strict gateway, up to 32 on CSCS) and the wall time is set by the dependent chain of calls, not by Python (2.2 % of the wall time) [ours: E29]. A small town is the right unit: five to 25 residents, three rounds.

## 7. Why now

* Apertus 1.5 (July 2026) brought a 262 k context and Apache-2.0 weights [V]; the CSCS inference API makes a Swiss-hosted endpoint usable today [ours: E20–E28].
* Authorities are being told where not to send sensitive material (privatim, November 2025) [S]; a self-hostable Swiss model is the alternative they need.
* The evidence base for LLM simulation matured and became more honest in 2024–2026: positive for pilots and comparisons, negative for forecasts [V], which lets us make a narrow, defensible claim.

## 8. Differentiation

| alternative | what it lacks for this job | GemeindeSim |
| --- | --- | --- |
| a general chatbot with the booklet | one opinion at a time, no population, no spread, invents figures, foreign hosting | population, spread, computed figures, cited chips, Swiss hosting |
| smartvote, easyvote, Swissvotes | reader-side or archive; do not test a draft | author-side pre-test |
| a focus group or panel | weeks and thousands of francs per text; not repeatable | minutes, repeatable, run five times for the range |
| classical agent-based models | no language: cannot read a text | residents read, quote and argue |
| large LLM social-simulation platforms | social-media scale, English, no closed-corpus citations, no Swiss languages | closed corpus, DE/FR, validated citations, Swiss stack |
| doing nothing | status quo: texts at C1/C2 and untested [S] | a first, cheap test |

## 9. Risks, ethics, and what we do about them

| risk | what we do |
| --- | --- |
| **Manipulation**: simulated agents can be used to design persuasion (coordinated agents shift beliefs within a few rounds, He et al. 2026 [V]) | synthetic residents only; the report never recommends or predicts; outputs labelled as simulation; no real-person profiles; a "no real-campaign use" line is on the list for the organisers (see [`MENTOR-BRIEF.md`](MENTOR-BRIEF.md) topic 7) |
| **Flattening real groups** | role-based archetypes, not identity categories; the report states that residents are fictional |
| **False confidence** | what-if framing; the spread across runs is shown; stance weights are marked uncalibrated; the yes-bias and the real-vote result are published |
| **Privacy** | no real personal data; self-hostable; the endpoint documents that prompts are not recorded (CSCS) [S] |
| **Model drift and hosting changes** | pinned model id logged with every run; metrics panel shows model and endpoint; the app runs on two endpoints |
| **Language quality** | 100 % language fidelity measured; native-speaker review pack of 49 items is ready and **not yet returned**; Swiss spelling enforced in code |
| **Overclaiming** | claims table: may / may not ([`SUBMISSION-CHECKLIST.md`](SUBMISSION-CHECKLIST.md)); the original pitch was audited claim by claim ([`research/04-pitch-audit.md`](research/04-pitch-audit.md)) |

## 10. Roadmap (after the hackathon)

| when | step | what it proves |
| --- | --- | --- |
| first 30 days | one **pilot Gemeinde**: run a real Botschaft before publication, hand the author the list "never cited / unanswered / diverging roles"; native-speaker review of DE and FR | does it find real problems that authors accept? |
| 90 days | **calibrate** the stance prior on municipal results (the Swissvotes and cantonal archives, VOX survey data); add statistics-based personas (BFS marginals); an Italian booklet; the French booklet | does the spread tighten and do the weights survive a held-out vote? |
| 6 months | **on-prem** reference deployment (8B on one GPU, 70B on two) with the probe run on the target; the hybrid retrieval option with a local embedding model (+14 points of recall@4 in our test) | the sovereign claim, measured |
| 12 months | a library of **tested Botschaften** and a shared, open benchmark; partnership with a Gemeindeverband, a cantonal chancellery or a civic-tech group | a Swiss open standard for pre-testing official text |

## 11. The 60-second and 2-minute versions

**60 seconds (spoken).**
"In Switzerland a Gemeinde asks its citizens to vote on a tax rate or a school credit, on the strength of a booklet that was written once, by a few people, in two languages, and is read by a tenant, a shop owner and a retiree who each see something different. Nobody tests that text on a diverse town before it is printed.
GemeindeSim does. It builds a small, fictional, German- and French-speaking town from the text. The residents talk; every sentence they quote is linked to the passage it came from; every figure comes from the text or a calculator. You see how the town splits, run it five times to see the range, change the text and compare. It never says how to vote or who will win.
We built it on Apertus because it is Swiss, open, hostable in a Gemeinde and strong in German and French. And we tested it: Apertus says yes to everything, so we compute each resident's stance in code and let the model only give it a voice. That is the difference between a demo and something an authority could use."

**2 minutes (structure).** 0:00 the problem in one example (118 % → 124 %: 144 CHF for one household, 432 for another); 0:20 the town on screen, a resident quoting a passage with its chip; 0:40 the stance poll and the "run five times" spread; 0:55 the what-if (counter-arguments added, the poll moves); 1:10 the chat (a resident declines a fact that is not in the text); 1:25 why Apertus and why code owns the stance (15 of 15 yes; 0 of 159 citations in the first version); 1:45 the ask. Shot list: [`DEMO-SCRIPT.md`](DEMO-SCRIPT.md).

**Slide order for a deck.** 1 problem; 2 who is affected differently; 3 what it does (screenshot); 4 why a simulation (precedents); 5 why Apertus; 6 why Switzerland; 7 evidence (the before/after chart, the two-endpoint chart); 8 limits we published; 9 roadmap and pilot; 10 the ask. Figures: `docs/figures/`.

**Taglines.** *"Test the text before the town does."* · *"A rehearsal for a vote, not a forecast."* · *"Swiss open weights, Swiss open democracy."*

## 12. Hard questions, and honest answers

| question | answer |
| --- | --- |
| Does it predict votes? | No. ≈ 34 points too favourable on 54 real votes; the Federal Council line alone is as good as any model condition. It is a pre-test and a comparer |
| If the model says yes to everything, why trust any result? | Because the stance is not the model's: it is computed from ideology, judged impact and a calculated household cost; the model gives it a voice (speech matches the code stance 0.85–0.91). The weights are knobs we say are uncalibrated, and the pilot calibrates them |
| Why not GPT or Claude? | They may be stronger on facts. A draft Botschaft is not public and the authorities' own data-protection officers are steering away from foreign SaaS for sensitive material; Apertus is open, Swiss, multilingual, hostable, and our design removes the dependence on its facts |
| Who would actually use it? | A Gemeindeschreiberin before printing a Botschaft; a cantonal language service; a civics class. The pilot tests whether authors accept what it finds |
| Isn't a fictional town just a toy? | Social Simulacra and Habermas-style tools show LLM populations are useful as prototypes and mediators when scoped; our difference is that every claim is traceable to a passage and every number to a source |
| Could it be used to manipulate voters? | It could be misused like any persuasion-testing tool. It produces no recommendations or predictions, uses no real profiles, labels output as simulation, and we ask the organisers for an explicit no-campaign-use line |
| Is the German and French good enough? | Language fidelity is 100 % in our tests; register has not been reviewed by a native speaker yet (the pack is ready) |
| Does it run on sovereign infrastructure? | It runs on the CSCS API (a Swiss national infrastructure) and on the hackathon gateway with the same build; a local or air-gapped run is configured and not yet measured: we say so |
| What is new? | A measured field guide to Apertus in an agent loop; a design where code owns state and the model voices it; validated citations and a number gate; a grounded chat with checks before streaming; a congestion-aware limiter. What is only standard is listed in [`INNOVATIONS.md`](INNOVATIONS.md) |
| What did you get wrong? | Our first pitch claimed citations that did not exist (0 of 159), a calculator that did not exist, and reports without invented outcomes; we measured, fixed and published the audit |

## 13. Fit with the Track 2B criteria (0–5 each)

| criterion | our case | where to look |
| --- | --- | --- |
| Purposeful use of AI: simulation and citations, not generic chat | a populated pre-test with validated citation chips; the model voices, code owns state | `MENTOR-BRIEF.md` §3, `INNOVATIONS.md` |
| Technical rigour: schema gate, eval harness, probe-backed limits | 146 offline tests; more than 30 experiments with raw call logs; limits measured on two endpoints; corrections logged | `research/LAB-NOTEBOOK.md`, `ENGINEERING-QA.md` |
| Value, cost and scalability | 61 s and ≈ 70 k tokens for a 5-resident run; adaptive concurrency; 2 121 Gemeinden is the addressable base; no per-seat cost | §6, `ENDPOINTS.md` |
| Sovereign deployability | CSCS API and gateway with one build; `LLM_BASE_URL` for on-prem; probe script for any endpoint; honest status (local run not measured) | `technical_report.md` §2, `ENDPOINTS.md` |
| Implementation feasibility | `make run`, Docker, three env vars, verified from a clean clone and through the UI | `SUBMISSION-CHECKLIST.md` |

## 14. Sources

**Opened and read [V]** (the verified literature review lists the rest: [`research/01-literature-review.md`](research/01-literature-review.md)): Park et al. 2023, arXiv:2304.03442; Park et al. 2024, arXiv:2411.10109; Argyle et al., Political Analysis 31(3), arXiv:2209.06899; Hewitt et al., Nature 2026; Bisbee et al., Political Analysis 32(4); Wang et al., Nature Machine Intelligence 2025, arXiv:2402.01908;
von der Heyde et al. 2024, arXiv:2409.09045; Barmettler 2026, arXiv:2606.00048; Chuang et al. 2024, arXiv:2311.09618; Larooij and Törnberg 2025, arXiv:2504.03274; Anthis et al., ICML 2025, arXiv:2504.02234; He et al. 2026, arXiv:2605.19915; Piao et al. 2025 (AgentSociety), arXiv:2502.08691; Yang et al. (OASIS), arXiv:2411.11581; Gao et al. (S3), arXiv:2307.14984;
Apertus technical report arXiv:2509.14233 and the Apertus 1.5 pages. **Social Simulacra:** Park et al., UIST 2022, arXiv:2208.04024 (abstract read in search results).

**Seen in search results only [S], verify before quoting on stage:** Tessler et al., Science 386 (2024), "AI can help humans find common ground in democratic deliberation" (the Habermas Machine; > 5 000 UK participants); 2 121 Gemeinden, status 7 March 2025
(<https://www.swissinfo.ch/eng/swiss-politics/cantons-and-municipalities/29289028>); Art. 10a BPR (<https://www.droit-bilingue.ch/de-en/1/16/161.1-10a-15.html>, <https://onlinekommentar.ch/de/kommentare/bpr10a>); readability of voting materials (Yearbook of Swiss Administrative Sciences, Nov 2021; Translation Spaces, "The challenge of multilingual plain language";
SRF, 2022, <https://www.srf.ch/news/abstimmungen-15-mai-2022/einfachere-sprache-ist-das-abstimmungsbuechlein-fuer-viele-zu-komplex>); easyvote, smartvote and Swissvotes descriptions (cantonal and SRF pages in the search results); the privatim resolution of 24 November 2025 on cloud services for specially protected data
(as summarised by cantonal government documents, for example <https://rrb.so.ch/beschlussnummer/2026_752/download/984a613a0f5641028160efbc772f3be3/>); the Apertus release by EPFL, ETH Zurich and CSCS, September 2025 (<https://ai.epfl.ch/apertus-a-fully-open-transparent-multilingual-language-model>, <https://apertus.ai/en/blog/swiss-ai-apertus-models-release/>).

**[context]** claims (voting several times a year, Gemeinde autonomy over tax rates, small municipal administrations, Apertus as national infrastructure) are general knowledge we did not look up; have a source ready or soften them on stage.
