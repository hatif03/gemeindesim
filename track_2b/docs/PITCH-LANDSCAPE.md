# GemeindeSim: the landscape (who did something like this, with which model, and what happened)

Companion to [`PITCH.md`](PITCH.md). It answers: where were simulations like this used, where were they used in research, which LLMs were used for similar work and why, what failed, and what is
the Swiss situation. Everything here was looked up on **8 Oct 2026**; nothing is from memory.

**Tags.** **[V]** = we opened the page or paper and read it. **[S]** = search-result text only, treat as unconfirmed. **[vendor]** = the company's own claim, no independent audit. **[ours]** = our measurement
(experiment id in [`research/LAB-NOTEBOOK.md`](research/LAB-NOTEBOOK.md)). A web tool summarised some pages, so figures are "as reported by the source", not audited by us.

## 1. The five findings that matter for the pitch

1. **Simulation before the real thing is normal in policy**, in traffic, tax, pandemics, housing and energy. What is new is simulating *readers of a text*. [V]
2. **We found no government that runs a simulated town to pre-test a ballot text.** The closest real case is Singapore GovTech's *Echo* (11 Sep 2026): AI personas react to a draft announcement before it is released, with the stated rule
   "hypotheses, not conclusions". It is early and still being validated against real focus groups. [V]
3. **Pre-testing official wording with real people is established practice abroad** (UK Electoral Commission, 2012 and 2015; Oregon and Sion citizen panels) but costs weeks and money, so it is done for a few high-profile questions only. [V]/[S]
4. **Swiss texts do go wrong, and it matters**: a federal vote was annulled in 2019 because the booklet said 80,000 couples were affected when the number was 454,000; a parliamentary audit in 2023 found the four-eyes check is not always done by people with the right expertise;
   43 % of voters could not say what a 2018 vote was about. [V]
5. **The research on LLM respondents is mixed, and the honest reading is "good at comparing, bad at forecasting".** Models track the direction and rank of effects (r ≈ 0.85 on 70 survey experiments) but are wrong in level (Pew: 11–13 points average error),
   flatten variance, and differ more between models than between prompts. That is exactly the case for a *what-if pre-test with fixed open weights*, not a vote predictor. [V]

## 2. Simulation as normal practice in policy (non-LLM)

| system | who, since | what it simulates | what happened | tag |
| --- | --- | --- | --- | --- |
| [MATSim](https://matsim.org/gallery/zurich/) | ETH Zurich IVT, about 2004 | traffic: 181,484 agents in a 10 % Zurich sample, built from census data, checked against about 160 counting stations | open agent-based model; Swiss baseline of about 6 million agents [S]. We found no proof that a federal office uses it for official forecasts, so we do not claim that | [V] |
| [EUROMOD](https://euromod-web.jrc.ec.europa.eu/overview/what-is-euromod) | EU Joint Research Centre, 1996 | tax-benefit microsimulation for all member states | used for redistribution, work incentives and stress tests; open source since Dec 2020 | [V] |
| [Modelling for EU Policy Support](https://publications.jrc.ec.europa.eu/repository/handle/JRC131798) | JRC, 2023 | review of 118 Commission impact assessments (2019 to 2022) | models play an "increasing role" in impact assessments | [V] |
| [Imperial CovidSim, Report 9](https://en.wikipedia.org/wiki/CovidSim) | Imperial College, 16 Mar 2020 | pandemic spread under policies | described as "a critical factor" in the UK's change of policy; also attacked as a "buggy mess"; outputs varied by up to 300 % across 940 parameters; Codecheck reproduced it within mostly under 5 % | [V] |
| [Bank of England SWP 619](https://www.bankofengland.co.uk/-/media/boe/files/working-paper/2016/macroprudential-policy-in-an-agent-based-model-of-the-uk-housing-market.pdf) | BoE staff, Oct 2016 | agent-based UK housing market: effect of a loan-to-income limit | research support, carries a "not Bank policy" disclaimer | [V] |
| ECB ABM4Policy workshop | ECB, 2025 | agent-based models for policy | institutional interest, no decision claimed | [S] |
| AMIRIS (DLR), EMLab-Generation (TU Delft) | 2008 on | electricity-market design | used to assess market design and policy | [S] |
| Swiss COVID agent-based models | 2020 | one models all 8.57 million residents | no verified link to the federal task force's decisions | [S] |
| Exercise Cygnus | UK, Oct 2016 | pandemic rehearsal, over 1,000 organisations, three days | exposed shortages of PPE and critical-care beds; the report was not published and recommendations were weakly acted on | [V] |
| Swiss strategic leadership exercises (SVU 2014 and later) | Federal Chancellery, every four years | "pandemic and power shortage", 26 cantons | 16 recommendations | [S] |
| [UK Red Teaming Handbook](https://www.gov.uk/government/news/new-red-teaming-handbook-published) | MoD DCDC, 30 Jun 2021 | a method to challenge plans and assumptions | guidance for civilian use too | [V] |
| Behavioural Insights Team | UK Cabinet Office, 2010 | not a simulation: randomised pre-tests of letters and messages (more than 400 trials) | the tax-letter trial randomised about 100,000 taxpayers (NBER w20007) | [V] |

**What we take from it.** (a) Rehearsal pays only if the findings are acted on (Cygnus). (b) A simulation survives scrutiny only with open code, a sensitivity analysis and a stated uncertainty (CovidSim). GemeindeSim's open code, repeated runs
with ranges, and "no outcome" report follow from that. (c) It is a *support*, not a decision (Bank of England disclaimer).

## 3. Pre-testing official texts with people (what the simulation would be a cheap first pass for)

| case | what was done | result | tag |
| --- | --- | --- | --- |
| [Scottish referendum question, 2012](https://www.ipsos.com/en-uk/referendum-scottish-independence-question-testing) | UK Electoral Commission with Ipsos: 203 depth interviews and 10 focus groups (62 people), 17 Nov to 15 Dec 2012 | "Do you agree…" was seen as leaning to Yes; the commission recommended "Should Scotland be an independent country?" | [V] |
| EU referendum question, 2015 | Electoral Commission testing | a Yes/No question carried perceived bias and some people did not know whether the UK was a member; "Remain / Leave" was recommended and the government changed the wording | [S] |
| Oregon Citizens' Initiative Review, from 2010 | about two dozen voters, four days, write a one-page statement for the voters' pamphlet | voter awareness 43 % (2010) to 54 % (2014); 60 to 75 % rate it at least somewhat useful | [V] |
| [Sion (VS) pilot, Nov 2019](https://participedia.net/case/6439) | 20 citizens drawn from 205 respondents, four days, CHF 500 each, on a national housing initiative | all 20 felt able to vote with confidence by day four (37 % unsure at the start); Sion turnout 67.1 % against 50.28 % in Valais | [V] |
| Federal Chancellery booklet redesign, 2017 | a focus survey of German- and French-speaking voters on the new layout; Federal Council approved 8 Dec 2017 | rated better; redesign cost CHF 80,000; 88 % of voters used the booklet before the Sept 2017 votes | [V] |
| Zurich voting texts in Leichte Sprache, 2025 | Pro Infirmis translates, people with disabilities review; canton from the 28 Sep 2025 vote; FHNW evaluation published 12 Feb 2026 | exists; we did not read the findings | [V] landing page only |
| Citizen juries and focus groups, cost | UK citizens' jury quoted at £15,000 to £200,000 with 4 to 5 months of planning; a focus group £1,500 to £11,000 | weak sourcing, wide ranges | [S] |
| Cognitive pre-testing of survey questions | two rounds of 42 and 25 interviews for a US housing survey | problems recur in the field; but one field study found 67 % of flagged items answered adequately anyway, so pre-tests over-flag | [S] |

**The gap, stated carefully.** In the Swiss federal booklet we found a layout test, editorial and legal review and, since 2023, a recommended four-eyes check, and **no documented pre-test of whether the text is misread** (GPK-N report, 21 Nov 2023 [V]).
We did not look inside the Bundeskanzlei or any canton, so the safe wording is "none we found". A citizen panel is the gold standard and is not replaced: the simulation is the cheap, repeatable filter *before* the panel, and its output is a list of
hypotheses for the panel to check, the same stance Singapore's Echo takes.

## 4. Why Swiss official texts need a second reader (evidence)

| fact | number and source | tag |
| --- | --- | --- |
| a booklet error annulled a federal vote | 2016 *Heiratsstrafe* vote annulled by the Federal Supreme Court on 10 Apr 2019, the first federal annulment: the booklet said about 80,000 couples were affected, the real number was 454,000; the initiative had been rejected with 50.8 % No ([Blick](https://www.blick.ch/politik/bundesgericht-erklaert-abstimmung-ueber-heiratsstrafe-fuer-ungueltig-wie-lange-kann-sich-die-cvp-freuen-id15266130.html)) | [V] |
| the review process misses errors | GPK-N report of 21 Nov 2023: after booklet errors in 2018 the commission demanded clarifications; the PVK found the four-eyes check "not always done by people with the needed expertise"; the booklet is trusted "although not always easy to understand" ([report](https://www.parlament.ch/centers/documents/de/Bericht%20GPK-N%20vom%2021.11.2023%20D.pdf)) | [V] |
| many voters cannot say what is at stake | 43 % of 1,513 respondents had trouble identifying what the Nov 2018 "Swiss law first" vote was about (VOTO via [swissinfo](https://swissinfo.ch/eng/voto-analysis_-swiss-law-first--initiative-challenged-many-voters/44675792)); in 1979, 15 % of No-voters on the nuclear initiative wrongly thought they were voting against building plants (Menzi 2021, secondary citation) | [V] |
| the booklet moves votes | a study by Oliver Strijbis found booklet content shifts voters by more than 15 points, strongest among centrists; **commissioned by a campaign-communication body, so treat as indicative** ([swissinfo](https://swissinfo.ch/eng/swiss-politics/its-often-the-voting-booklet-that-decides-yes-or-no/87490263)) | [V] |
| simplification is legally delicate | the Federal Chancellery opposes heavily simplified versions because "highly simplified, inaccurate official statements would quickly be regarded as impermissible government influence"; about 800,000 adults struggle with simple texts (a figure the press says is old) ([SRF](https://www.srf.ch/news/abstimmungen-15-mai-2022/einfachere-sprache-ist-das-abstimmungsbuechlein-fuer-viele-zu-komplex)) | [V] |
| legal standard applies to towns too | Art. 34 para. 2 of the Federal Constitution; BGer 1P.377/2003 (a municipal case) requires "objective and sufficiently complete" explanations; annulment only if irregularities are substantial and could have influenced the result ([judgment](https://servat.unibe.ch/dfr/bger/2003/031104_1P-377-2003.html)) | [V] |
| most municipalities decide on a written text | 2,110 political municipalities on 1 Jan 2026; only about 20 % have a parliament, the rest an assembly (SRF; Gemeindemonitoring 2017); the share that votes only at the ballot box was not found | [V] |
| the assembly is small, the text is what people read | Sursee March 2019: about 600 people, just under 8 % of eligible voters; Glarus 2008 to 2019 on average 4.1 to 5.8 % [S]; Aargau 2013 to 2016: 0.8 % to 44.7 %, over half of the assemblies had fewer than six public comments ([SRF](https://www.srf.ch/news/grosse-studie-im-aargau-gemeindeversammlungen-sind-besser-als-ihr-ruf)) | [V] |
| Swiss voters accept AI with oversight | gfs.bern for the Federal Chancellery (2025): 80 % accept AI for translation, only 44 % for automatic answers to citizens; acceptance depends on human oversight, transparency and data protection ([Netzwoche](https://www.netzwoche.ch/news/2025-05-21/ki-in-der-behoerdenkommunikation-ist-okay-aber-nicht-bedingungslos)) | [V] |
| ballot language is hard everywhere | US 2025 statewide measures averaged Flesch-Kincaid grade 21, a record; initiatives 26 ([Ballotpedia](https://news.ballotpedia.org/2025/10/23/this-years-statewide-ballot-measures-were-written-at-the-highest-reading-level-since-2017/)); harder language goes with more roll-off (Reilly and Richey 2011) [S]. We found no Swiss readability index study of the booklet | [V]/[S] |

## 5. Research on LLM simulations of people: what was found, with which model, and why

### 5.1 Positive and foundational

| work | model | finding | relevance to us | tag |
| --- | --- | --- | --- | --- |
| Social Simulacra, Park et al., UIST 2022 ([arXiv 2208.04024](https://arxiv.org/abs/2208.04024)) | not stated in the abstract | an LLM generates thousands of community members and their interactions so designers can test a design before it is launched | **the original "populated prototype" idea; our use case** | [V] |
| Generative Agents, Park et al., 2023 ([2304.03442](https://arxiv.org/abs/2304.03442)) | not stated in the abstract | memory, reflection and planning give believable individual and emergent social behaviour | our resident loop | [V] |
| 1,052-person study, Park et al., 2024 ([2411.10109](https://arxiv.org/abs/2411.10109)) | not verified | agents grounded in interviews match survey answers at 85 % of participants' own two-week test-retest consistency; less bias across groups than demographic-only prompts | grounding beats demographics; the 85 % is relative to retest, not a hit rate | [V] abstract |
| Ashokkumar, Hewitt, Ghezae, Willer, *Nature* 656, 2026 | GPT-4 | 70 preregistered US survey experiments (476 effects): simulated and real effects correlate at r = 0.85, 0.90 on unpublished studies; effect sizes are systematically overestimated | **best precedent for pre-testing messages: right direction and rank, wrong magnitude** | [V] page, numbers [S] |
| Barnett, Kieslich, Diakopoulos, AIES 2024 ([2405.09679](https://arxiv.org/abs/2405.09679)) | GPT-4 | generated scenarios evaluate the perceived effects of an EU AI Act article; transparency helps against labour harms, less for social cohesion | text in, impacts out: the shape of our report | [V] |
| Rountree and Gastil, *Journal of Deliberative Democracy*, 2026 ([article](https://delibdemjournal.org/article/id/1625/)) | not model-specific | practitioners should simulate hypothetical policy discussions among diverse personas as a **complement** to human deliberation, with concerns about bias, privacy and transparency | the framing we use | [V] |
| Chen, PoliSim@CHI 2026 ([2608.07496](https://arxiv.org/abs/2608.07496)) | not model-specific | policy simulation should be exploratory, not question-answer, because ground truth is unknowable in advance | supports what-if over prediction | [V] |
| Argyle et al., "Out of One, Many" ([2209.06899](https://arxiv.org/abs/2209.06899)) | GPT-3 (175B, via API) | GPT-3 conditioned on demographics shows "algorithmic fidelity" for subgroup response distributions | silicon samples; the later work qualifies it | [V] |
| Törnberg et al., 2023 ([2310.05984](https://arxiv.org/abs/2310.05984)) | not stated | a "bridging" news-feed algorithm produced more constructive conversation in simulation | simulation used to compare designs, not forecast | [V] |
| Chuang et al., 2023 ([2311.09618](https://arxiv.org/abs/2311.09618)) | not stated | LLM agents drift toward factual consensus; induced confirmation bias produces polarised, fragmented opinions | why we compute opinion movement in code | [V] |
| Habermas Machine, Tessler et al., *Science* 2024 | fine-tuned in-house model (DeepMind) | AI-written group statements preferred over human mediators' 56 % of the time, groups less divided (5,734 UK participants) | AI-mediated deliberation is credible; no fact-checking, no public release planned | [V] via MIT Technology Review |
| Gudiño-Rosero et al., 2024 ([2405.03452](https://arxiv.org/abs/2405.03452)) | off-the-shelf, fine-tuned; names not stated | beat party-line assumptions on Brazil 2022 policy preferences; an LLM-augmented sample estimates aggregates better than the sample alone | LLMs as an aid to a real sample | [V] abstract |
| Kreutner et al., EACL 2026 ([2506.11798](https://arxiv.org/abs/2506.11798)) | not stated | persona prompts reproduce European Parliament votes at weighted F1 about 0.79 | our reading: predicting known actors with known positions is easier than predicting the public | [V] |

### 5.2 Voting, Switzerland and Germany

| work | model | finding | tag |
| --- | --- | --- | --- |
| **Barmettler 2026**, "Progressive in Principle, Centrist in Practice" ([2606.00048](https://arxiv.org/abs/2606.00048)) | 66 LLMs on Smartvote; 9 flagship models on 48 federal referenda | models lean left on the abstract questionnaire but act as centrist, status-quo "cautious civil servants" on real referenda; cross-language consistency from 50 % to 98 %; two models vote No on 83 to 94 % regardless; open vs closed predicts nothing (p = 0.87); Apertus was not in the list we read. **Single-author preprint, not peer reviewed as far as we know, title changed between versions** | [V] |
| Reveilhac, *Swiss Political Science Review* 2025 ([doi](https://onlinelibrary.wiley.com/doi/10.1111/spsr.12650)) | GPT-3.5 and GPT-4 | votes on 4 Swiss ballot items varied with model version and language (FR vs DE) | [S] |
| Yang et al. (ETH Zurich), AIES 2024 ([2402.01766](https://arxiv.org/abs/2402.01766)) | GPT-4, LLaMA-2 | on 24 Zurich projects, LLMs gave less diverse outcomes than 180 people, were order-sensitive and WEIRD-biased | [V] |
| Bachmann et al. (UZH), *PLoS One* 2025 ([2503.09311](https://arxiv.org/abs/2503.09311)) | GPT-4 | answered Smartvote as party members; closer to the party mean than the average real candidate | [V] |
| Stammbach et al. (ETH, EPFL), EMNLP 2024 ([2406.14155](https://arxiv.org/abs/2406.14155)) | fine-tuned model | about 100k Swiss candidate comments from smartvote gave more balanced viewpoints than ChatGPT | [V] |
| **Egli et al. (UZH), 2023** ([2306.08999](https://arxiv.org/abs/2306.08999)) | fine-tuned M-BERT | **stance detection on the Sep 2022 Swiss booklets in DE, FR, IT: some issues heavily favoured, others balanced, largely consistent across languages; the authors say it has implications for the editorial process of future booklets** | [V] |
| von der Heyde et al., 2025 ([2407.08563](https://arxiv.org/abs/2407.08563)) | GPT-3.5 | failed to predict German vote choice; biased toward Greens and Left | [V] abstract |
| von der Heyde et al., "United in Diversity?" ([2409.09045](https://arxiv.org/abs/2409.09045v1)) | GPT-4-Turbo | 26,000 voters, EU election 2024: prediction "largely fails", unequal across countries and languages | [V] abstract |
| Ma et al., ACL 2025 ([2412.13169](https://arxiv.org/abs/2412.13169v1)) | Llama-2-13B, Gemma-7B, Mixtral-8x7B | left-leaning bias, AfD supporters worst matched; Llama best; Gemma dropped after a 42 % COVID hallucination rate | [V] |
| Gong, Sanders, Schneier, 2026 ([2603.20229](https://arxiv.org/abs/2603.20229)) | not stated | asking the model for the response *distribution* directly beats simulating individuals, and is cheaper | [V] |
| Swiss-Bench SBP-002, Uenal, Mar 2026 ([2603.23646](https://arxiv.org/html/2603.23646v1)) | many | 395 Swiss regulatory tasks in DE/FR/IT: the top model reached 38.2 %, none is reliable without retrieval | [V] |

**Reading.** Every Swiss study found that the *model*, the *language* and the *information condition* change the answer. GemeindeSim answers that with a fixed open model and version, DE and FR runs of the same booklet, retrieval with validated citations (hybrid recall@4 1.00 vs 0.79 [ours, E30]), and ranges over repeated runs [ours].

### 5.3 Negative and cautionary results (cite these first, they make the framing credible)

| work | finding | what we do about it | tag |
| --- | --- | --- | --- |
| Bisbee et al., *Political Analysis* 2024 | means match ANES but variance is too low; 48 % of regression coefficients differ; wording-sensitive; the same prompt drifted over three months | code owns stance with noise; we report ranges; versions pinned | [V] |
| Wang, Morgenstern, Dickerson, *Nature Machine Intelligence* 2024 | LLMs misportray and flatten identity groups | residents are fictional, no claim about real groups | [V] |
| Park, Schoenegger, Zhu 2024 | GPT-3.5 replicated 37.5 % of Many Labs 2 findings; near-zero variation on nuanced questions | persona diversity set by code, not by the model | [V] |
| Santurkar et al. 2023 | substantial misalignment with US demographic groups, persists after steering | not a poll | [V] |
| Agnew et al., CHI 2024 | replacing participants with AI undermines representation and inclusion | complement, never replacement; the report says so | [V] |
| Pew, 30 Sep 2026 ([page](https://www.pewresearch.org/data-labs/2026/09/30/how-synthetic-polling-results-change-based-on-the-ai-model.md)) | digital twins of real panelists: average error 11.4 points (Claude Opus 4.6) and 13.3 (GPT-5.1); models disagree with each other about the shape of public opinion; 47 % of synthetic questions had an option nobody picked, against 0 % in human surveys; Pew has "no current or future plans" to use AI-generated results | pin an open model; do not forecast | [V] |
| Makerfield by-election test, Salford and UCL, 19 Jun 2026 ([page](https://www.salford.ac.uk/news/most-ai-models-predicted-a-reform-win-in-makerfield-the-voters-delivered-a-labour-landslide)) | six LLMs, 42,265 synthetic voters: four called Reform, Labour won with 54.8 %; the Reform estimate spread 38.5 % to 80.5 % across models; "Which model you ask matters more than how you ask it" | same | [V] |
| Verasight synthetic sampling report | best model error 4 points on toplines, about 8 on subgroups, about 20 % individual misclassification; newer models lagged GPT-4o-mini | same | [V] |
| "Plausible but Not Valid", Lukauskas 2026 ([2608.14606](https://arxiv.org/abs/2608.14606)) | 37 models give plausible but not valid data; a Gaussian-copula baseline beats every LLM | we claim no validity as a respondent | [V] |
| Larooij and Törnberg 2025 ([2504.03274](https://arxiv.org/abs/2504.03274)) | LLM agent-based models do not answer the old criticisms of agent-based modelling and may worsen validation | measured defects published (yes-bias, deference) | [V] |
| Ye et al. 2026 ([2605.18890](https://arxiv.org/abs/2605.18890)) | small design perturbations shift outcomes by up to 76 points | robustness runs before any claim | [V] |
| Flechtner, AIES 2026 ([2608.10186](https://arxiv.org/abs/2608.10186)); Yao et al. 2025 ([2509.23055](https://arxiv.org/abs/2509.23055)) | LLM deliberation: lower perspective diversity, fails to replicate human consensus patterns; sycophancy collapses debate into premature consensus | opinion dynamics computed in code, not left to model politeness | [V] |
| Luo et al. 2026 ([2604.07838](https://arxiv.org/abs/2604.07838)) | preconditions for policy simulation: no neutral treatment of marginalised groups, no simulating populations without their participation, accountability | fictional town, human review, no vote advice | [V] |
| Jang et al. 2026 ([2609.07573](https://arxiv.org/abs/2609.07573)) | census-grounded Korean personas surface arguments on both sides but do not reproduce population opinion patterns | arguments, not shares | [V] |
| Nate Silver, 11 Apr 2026; AAPOR proposed ethics update | "AI polls are fake polls"; AI-generated data are "not research participants" and must be labelled | we label every output as simulated | [V] secondary / [S] |
| AlgorithmWatch and AI Forensics, 2023 Swiss election audit | Bing Chat answered candidate questions about specific cantons correctly in 1 of 10 cases and invented false stories | no voter-advice mode; every claim cited | [S] |

## 6. Real deployments and products (and how much to believe them)

### 6.1 Government and public sector

| case | what it does | status and caveat | tag |
| --- | --- | --- | --- |
| **[Singapore GovTech Echo](https://www.tech.gov.sg/technews/using-ai-to-test-government-messages/)**, 11 Sep 2026 | AI personas, built from past focus-group transcripts, react to draft government announcements before release | early testing, still validated against real focus groups; "personas generate hypotheses, not conclusions"; sharpen focus groups, do not replace them | [V] |
| [UK i.AI Consult](https://www.gov.uk/government/news/government-built-humphrey-ai-tool-reviews-responses-to-consultation-for-first-time-in-bid-to-save-millions), May 2025 | analysed 2,000+ responses to the Scottish cosmetic-procedures consultation: F1 0.76, near-identical theme rankings to experts | analyses real responses, does not simulate people; weak at overlooked themes; the "75,000 days saved" is a projection | [V] |
| Taiwan MODA Alignment Assemblies, 2023 and 2024 | 447 representative participants drawn by SMS, AI facilitating only | no confirmed legislative outcome | [V] |
| Bowling Green, KY, "What Could BG Be?", 2025 | 7,890 residents (about 10 % of the city), 3,940 ideas clustered with Jigsaw Sensemaker (Gemini) | self-selected participants (older, homeowners, educated) | [V] |
| EU JRC FABLES, Oct 2023 | step-by-step guide to LLM emotional-agent populations for policy scenarios | conceptual, not deployed | [V] |
| Swiss Parliament PIA, approved 4 Sep 2026 | AI assistant for Parliament; operated and stored only by Swisscom in Switzerland; open-weight models of choice; pilot of about one year, at most CHF 150,000 | **a Swiss institution already picked Swiss-hosted open-weight models**; documents only, no simulation | [V] |
| Canton Fribourg chatbot, beta 17 Mar 2026 | built on Mistral AI by Liip, hosted by Infomaniak in Switzerland, with source links; planned for municipalities | a French model, not Apertus | [V] |
| BFH and City of Bern chatbot proof of concept, 2024 to 2025 | Llama-3.3-70B with retrieval over 296 documents (3,932 pages), on city servers: faithfulness 0.92, relevancy 0.92, recall 0.73 | the Swiss municipal pattern: local open model plus retrieval | [V] |
| City of Zurich council, 3 Jun 2026 | adopted an AI research tool (90 to 18) but rejected generative AI, citing hallucinations and energy | a visible Swiss sceptic position | [V] |
| UC Berkeley CivicSim, 2026 | synthetic personas by region; total variation distance 0.101 against Pew | student prototype, no government users | [V] |
| smartinfo, BFH with HSLU, Année Politique Suisse, easyvote, Politools, Jan 2026 to Dec 2028 ([project](https://www.bfh.ch/de/forschung/forschungsprojekte/2026-405-463-889/)) | "smartvote for referendums": explainable and generative AI to help voters form an opinion | a user-facing explainer, not a text pre-tester: **the most likely partner or neighbour to name** | [V] |
| OST "Fact Attack 2026" (Hack Apertus Track 2A) | checks whether voting booklets entail, are neutral to or contradict a claim, with page citations; about 60 booklets, 1,495 annotated pairs | tests claims against the booklet, not the booklet itself: complementary | [V] |

### 6.2 Companies (all [vendor] unless noted: read as market signal, not evidence of accuracy)

| company | what | money and customers | claims to treat with care |
| --- | --- | --- | --- |
| Aaru (New York, 2024) | agents from census data simulate voters and consumers | Series A above $50M, headline valuation $1B ([TechCrunch](https://techcrunch.com/2025/12/05/ai-synthetic-research-startup-aaru-raised-a-series-a-at-a-1b-headline-valuation)); Accenture, EY, IPG, campaigns | "within 371 votes" (NY primary 2024) and "within 2,000" (NYC) are the company's own single-event claims; no audit |
| Simile (2026, founded by the Generative Agents authors) | agents grounded in interviews | $100M Series A, Index Ventures; CVS, Telstra, Gallup partnership | the "85 to 99 %" is the company's; the 85 % in the paper is relative to retest consistency |
| Electric Twin (London, 2023) | synthetic audiences | $14M including a $10M round led by Atomico; lists public-sector decisions as a planned use | an LSE study it funded and co-led found synthetic answers inside the range of seven human panels, **not independent** |
| Artificial Societies (YC W25), Ipsos PersonaBot (Jul 2024), Qualtrics Edge Audiences, Toluna, YouGov (Yabble), Savanta | personas and synthetic panels for market research | Qualtrics claims "12x better accuracy than general LLMs" | no independent validation seen |
| Talk to the City, Polis, Remesh | AI-assisted listening and clustering, not simulated people | Taiwan, Tokyo election, UN; Polis in Taiwan, Singapore, Finland [S] | no causal evidence for outcomes (for example the Libya ceasefire) |

## 7. Which LLMs were used for similar work, and why

| model family | used for | why, as stated or evident | tag |
| --- | --- | --- | --- |
| GPT-3 | silicon samples (Argyle) | scale, API access | [V] |
| GPT-3.5, GPT-4, GPT-4-Turbo | vote prediction (von der Heyde), Swiss votes (Reveilhac), Smartvote (Bachmann), survey experiments (Ashokkumar), policy scenarios (Barnett) | the default and best available at the time; results biased or inaccurate for elections | [V]/[S] |
| Claude Opus 4.6, GPT-5.1 | synthetic polling (Pew) | frontier closed models; **the choice of model alone changed the answer** | [V] |
| Llama-2, Gemma, Mixtral | German opinions (Ma) | open weights, instruction-tuned; no rationale stated | [V] |
| Llama-3-8B (vLLM) | OASIS, up to one million agents | open and cheap, served locally; GPT-4o-mini used only as evaluator | [V] |
| Llama-3 via Ollama | Y Social | consumer hardware, reproducibility, local deployment | [V] |
| Mistral-7B | opinion dynamics grounded in real Twitter networks (Berjawi) | small and local | [V] |
| glm-4-9b, Llama-3.1-8B, Qwen3-8B | GPLab policy simulation (JASSS 2026) | small open models | [V] |
| Llama, Qwen, Aya | multilingual political views | open, for reproducibility; closed models excluded | [V] |
| any OpenAI-compatible model | AgentSociety (over 10,000 agents, 5 million interactions) | model-agnostic by design | [V] |
| Mistral (open weights) | French and German public administration, 2026 to 2030 | European, open weights, sovereign hosting | [V]/[S] |
| **Apertus** | Swiss public-sector and multilingual uses; SEA-LION adaptation; Swisscom hosting; MeditronFO medical framework at EPFL | open and auditable, Swiss data-protection and copyright design, Swiss languages, CSCS hosting | [V] swissinfo |

**Pattern.** Closed frontier models dominate the *measurement* papers (they were what was available, and the measurement is the point). **Large agent simulations use small open models** because cost, local serving and reproducibility decide.
**Governments choose open or national models for sovereignty**: the privatim resolution (24 Nov 2025) says Swiss public bodies may use international SaaS for sensitive data only if they hold the keys; the Federal Council's March 2026 digital strategy aims
to reduce dependence on single US providers [V] secondary; France and Germany announced a sovereign AI for public administration with Mistral and SAP (18 Nov 2025) [V]. Counter-examples exist: Estonia partnered with OpenAI and Anthropic for schools [S], and the
Swiss federal administration still rolled out Microsoft 365 to about 54,000 workplaces (documents labelled sensitive stay out of the cloud) [V], so we do not call Swiss sovereignty a settled policy.

### 7.1 National and sovereign models around Apertus

| model | country | languages and size | note | tag |
| --- | --- | --- | --- | --- |
| EuroLLM | EU | 24 EU languages; 22B, 9B, 1.7B | fully open, MareNostrum 5 | [V] |
| OpenEuroLLM | EU | 24 EU languages | about 20 organisations, EUR 37.4M for models | [S] |
| Teuken-7B | Germany | 24 EU languages | Apache 2.0, data kept in-house | [S] |
| Salamandra | Spain | Spanish, Catalan, Galician, Basque | co-official languages compulsory in administration, a parallel to Swiss multilingualism | [S] |
| Velvet, Minerva | Italy | Italian | trained on Leonardo | [S] |
| Poro, Viking | Finland | Finnish, Nordic | trained on LUMI | [S] |
| SEA-LION | Singapore | 11 Southeast Asian languages | Apertus has been adapted for it | [S] |
| GPT-NL | Netherlands | Dutch | EUR 13.5M, "transparent, fair and verifiable" | [S] |
| Aleph Alpha | Germany | German | deployed by Baden-Württemberg 2024, then pivoted to a platform; **a cautionary tale for sovereign models** | [S] |

### 7.2 Apertus: strengths and limits, stated plainly

| strength | source | tag |
| --- | --- | --- |
| fully open: Apache 2.0, 8B and 70B, 15T tokens, over 1,000 languages (the paper says 1,800+), about 40 % non-English | [paper](https://arxiv.org/abs/2509.14233), ETH press release | [V] |
| built for Swiss law and the EU AI Act: robots.txt opt-outs respected retroactively, PII and toxicity filtering, Goldfish objective against memorisation | paper | [V] |
| aligned with a Swiss AI Charter (neutrality, consensus, federalism, multilingualism), details from secondary summaries | paper | [V] abstract / [S] |
| Apertus 1.5 (24 Jul 2026): 262,144-token context, optional thinking mode, better tool use | [CSCS](https://www.cscs.ch/science/computer-science-hpc/2026/apertus-15-building-the-next-generation-of-open-ai-infrastructure) | [V] |
| adoption: over 4 million downloads, 70+ external deployments, 100+ derivatives; Ticino migration office uses it for translation per swissinfo (a vendor page says the canton uses it for official documents, **not confirmed**) | [swissinfo](https://www.swissinfo.ch/eng/swiss-ai/one-year-on-has-swiss-ai-model-apertus-lived-up-to-the-hype/91984276) | [V] |
| better than Llama-3.3-70B on German-to-Romansh translation | The Decoder | [V] |

| limit | source | tag |
| --- | --- | --- |
| "well behind similarly sized open-weight models" in coding, maths and reasoning; agentic capability lags; Apertus 1.5 weak on faithfulness (Liip) | swissinfo | [V] |
| scores below Llama-3.3-70B, Qwen2.5-72B and OLMo-2-32B on complex reasoning | The Decoder | [V] |
| Swiss German weaker than a small fine-tuned model: 48.61 vs 76.92 on Swiss-German-to-German translation | [Lightly](https://lightly.ai/blog/swiss-german-llms) | [V] |
| reproduces human stereotypes much like ChatGPT (a journalist's test, not a controlled study) | swissinfo | [V] |
| **our measurements**: yes-bias 14 to 15 of 15 residents; about 34 points too yes on 54 real federal votes; deference to the Federal Council line (8B: 98 %); one tool call per request; T = 0 not reproducible | `docs/research/` [ours] | [ours] |
| we found **no independent study of Apertus on politics or on voting texts** | searches, 8 Oct 2026 | none found |

The pitch sentence this supports: **Apertus is the sovereign and auditable choice, not the strongest model, and our design (the model voices, code owns stance, arithmetic and sources) is what makes a weaker, open model usable here.**

### 7.3 Does the language of the prompt fix cultural bias? Unsettled

| study | finding | tag |
| --- | --- | --- |
| AlKhamissi et al. (EPFL, Princeton, CMU) ([2402.13231](https://arxiv.org/html/2402.13231v2)) | models align better with a culture when prompted in its dominant language | [S] |
| Tao et al., *PNAS Nexus* 2024 | OpenAI models resemble English-speaking and Protestant European values; cultural prompting improves 71 to 81 % of countries | [S] |
| Durmus et al. (Anthropic), GlobalOpinionQA ([2306.16388](https://arxiv.org/abs/2306.16388)) | country prompts shift outputs, sometimes into stereotypes; **translating questions did not reliably align answers with native speakers** | [V] |
| "Multilingual Political Views of LLMs" ([2507.22623](https://arxiv.org/html/2507.22623v2)) | seven open models, 14 languages: English gives the most libertarian-left outputs, some languages drift to centrist or authoritarian-right | [V] |

We therefore **test German and French separately and do not assume the translation is equivalent** (native-speaker review is still pending, see the submission checklist).

## 8. Who in Switzerland does what: the map and the gap

| actor | what it does | does it pre-test a text? | tag |
| --- | --- | --- | --- |
| Federal Chancellery (BK) | writes the booklet; binding editorial guidelines with checklists, explainer videos for every vote; Art. 10a BPR: completeness, objectivity, transparency, proportionality | internal editorial, legal and four-eyes review; a layout test in 2017; no documented text pre-test found | [V] |
| GPK-N and PVK | parliamentary oversight, 2023 report | audit, not a test | [V] |
| Swissvotes (Uni Bern) | all federal votes since 1848; descriptions, campaign material, recommendations | no | [V] |
| smartvote (Politools) | candidate matching; about 20 % of voters use it | no | [V] |
| easyvote | digests official materials in simple language for young adults; neutrality committee | downstream of publication | [S] |
| VOX and VOTO | post-vote surveys (VOTO about 1,500 voters, financed by the BK) | after the vote only | [S] |
| demokratis.ch | consultations platform (Vernehmlassungen) | no, not votes | [V] |
| OpenParlData.ch | parliament data, online since 9 Feb 2026, federal, 26 cantons and over 50 cities | no | [V] |
| ZDA Aarau | studies of municipal assemblies and VOTO | no | [S] |
| Swiss Municipalities Association (SGV) | digitalisation surveys: 621 municipalities (2025) and 639 (2026) answered; 62 % prefer to tackle digitalisation with partners; 69 % lack clear information on the e-ID | a channel to municipalities, not a tester | [V] |
| UZH (Egli et al.) | stance detection on booklets, 2023 | **measures neutrality after publication**, the closest prior art | [V] |
| BFH smartinfo | explainable AI for referenda, 2026 to 2028 | an explainer for voters | [V] |
| OST Fact Attack | claims against booklets | tests claims, not the text | [V] |

**Conclusion we can defend.** Of the actors we found, none pre-tests the wording of an official text with simulated readers before publication; the nearest pieces are neutrality measurement after publication (UZH), voter explainers (smartinfo, easyvote) and claim checking (OST).
Whether a canton or the Chancellery does something internal that is not public, we cannot see.

### 8.1 Swiss digital and AI policy that frames the pitch

| item | what it says | tag |
| --- | --- | --- |
| Federal Council on AI, 12 Feb 2025 | Council of Europe AI convention plus mostly sector-specific changes; a consultation draft due by end of 2026; no AI-specific law today | [V] |
| Federal AI implementation plan, 12 Dec 2025 | CNAI contact point moves to the Chancellery on 1 Feb 2026; internal GenAI system and AI marketplace planned | [V] |
| revDSG, in force 1 Sep 2023 | applies to private persons and federal bodies; cantons and municipalities follow cantonal data-protection law. A simulator with **no personal data** avoids most of it | [S] |
| privatim resolution, 24 Nov 2025 | public bodies may use international SaaS for sensitive data only if they encrypt it themselves and the provider has no key; not legally binding; the CLOUD Act is the concern | [V] |
| E-voting | Lucerne approved 24 Jun 2026; about 181,000 voters (3.24 %) authorised on 27 Sep 2026; a March 2026 incident in Basel-Stadt left 2,048 votes uncounted | [V] |
| Federal vote dates | 27 Sep 2026, 29 Nov 2026 | [V] |
| Hack Apertus | online 1 to 16 Oct 2026; Liebefeld finals 19 Oct 2026; Grand Finals 14 May 2027 in St. Gallen | [V] |

## 9. What this means for GemeindeSim (design decisions that follow from the evidence)

| evidence | decision | status |
| --- | --- | --- |
| Echo, Rountree and Gastil, Chen: simulation as hypotheses and complement | the report lists *what residents misread and why*, never an outcome or a vote recommendation | built |
| Pew, Makerfield, Barmettler: the model matters more than the prompt; open vs closed does not predict | one pinned open model and version; run on both endpoints (gateway and CSCS) with the same results | built, [ours E20 to E31] |
| Bisbee, Park et al., Wang: flat variance, drift, flattened groups | stance computed in code with a seeded spread; fictional residents; ranges over repeated runs | built |
| Ashokkumar: direction right, magnitude wrong | compare conditions (text A vs text B, household with vs without a measure), do not read the level | built |
| Barmettler, Reveilhac, von der Heyde: language and information condition change answers | DE and FR runs; the official text is the information; validated citations [P#] | built; native-speaker review pending |
| GPK-N, Heiratsstrafe: numbers are where booklets fail | numeral gate (no invented figure passes), household calculator in code | built |
| Aleph Alpha, privatim: sovereign model risk and deployment constraints | one build on the hackathon gateway and the CSCS API; on-prem path documented but **not measured locally** | partly |
| gfs.bern: acceptance depends on oversight, transparency and data protection | every statement tied to a passage; no personal data; output is for a human editor | built |
| Menzi: people feel they understood without understanding | the "who misreads and why" view is the product, not a single score | designed |
| Sion and Oregon: panels work and are expensive | position as the filter *before* a panel; offer the panel questions as output | roadmap |

## 10. What we can say, and what we must not

**May say (with the source in this file):**

* Simulation before the real thing is routine in policy; reading a text with simulated people is the new step, and one government (Singapore, Echo) is testing exactly that and frames it as hypotheses.
* In Switzerland a booklet error annulled a federal vote (2019), and a 2023 audit found the four-eyes check is not always done by the right people.
* The research says LLM respondents rank effects well and get levels wrong, and that the model chosen changes the result more than the prompt, so a fixed open model is the defensible base.
* We found no one in Switzerland who pre-tests an official text with simulated readers.
* Apertus is the sovereign, auditable choice; Swiss institutions (Parliament's PIA with Swisscom, Bern, Fribourg) already pick Swiss-hosted or open models for public work.

**Must not say:**

| claim | why not |
| --- | --- |
| "Aaru predicted elections within 371 or 2,000 votes" (unless attributed to the company) | single self-reported events, no audit |
| "Simile is 85 to 99 % accurate", or the $200M Series B at $2B | the 85 % is relative to retest consistency; the Series B came from a low-credibility source |
| "synthetic audiences match real research" | Qualtrics, Toluna, Ipsos, Electric Twin claims are vendor-only; the LSE study was funded and co-led by Electric Twin |
| "Downing Street uses synthetic voters" | one reported experiment, relayed through an opinion piece |
| "AI mediation or Remesh brought about a ceasefire or a policy" | no causal evidence |
| "governments pilot simulated citizens to test official texts" | the only verified one is Singapore Echo, early-stage |
| "Swiss authorities pilot AI for the booklet" | SRF (2023): no; the Vice-Chancellor called it difficult and said it must be handled very carefully |
| "Ticino uses Apertus for official translation" | one vendor page; swissinfo names the migration office only |
| "Apertus beats other open models" | it does not on reasoning, coding or faithfulness; it leads on openness, compliance and Romansh |
| "it predicts the vote", "calibrated stance weights", "tested on-prem", "native-reviewed German and French" | not true; see `SUBMISSION-CHECKLIST.md` |
| Barmettler's results as settled | single-author preprint, title changed, not peer reviewed as far as we know |
| the Strijbis 15-point booklet effect as neutral evidence | commissioned by a campaign-communication body |
| the 800,000 low-literacy figure as current | the press says it is about 15 years old |
| the 2013 "20 % have a parliament" as a 2026 figure | the 2013 count was 475 of 2,352; SRF repeats "20 %", we found no newer count |

## 11. Not found (so we say so)

* No Swiss readability index (Flesch or Hohenheim) study of the federal booklet; no Swiss study of reader pre-testing of the booklet text beyond the 2017 layout survey.
* No independent study of Apertus on politics or voting texts; no confirmation that Barmettler or the SwissText MP paper used Apertus.
* No verified national share of municipalities that decide by ballot box only; no national association of municipal clerks with a verified size.
* The model behind the 1,052-person study and the Generative Agents paper (not stated in the abstracts we read).
* No LLM-resident pre-test of a ballot or municipal text by any public body other than Singapore's Echo.
