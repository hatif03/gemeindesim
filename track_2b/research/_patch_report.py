"""One-off: rewrite report/report.html (no repository paths in the text, similar applications up front, references at the end)."""
import re
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "report" / "report.html"
s = P.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert old in s, old[:70]
    s = s.replace(old, new, count)


def between(a, b, new):
    """Replace everything from the start of marker a up to (not including) marker b."""
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]


# ---- meta
between('<div class="meta">', "</div>", '<div class="meta">Hack Apertus 2026 · Track 2B (own project) · Team <b>1ne</b> · 5–15 October 2026 · code: github.com/hatif03/gemeindesim (public) · judged endpoint: CSCS inference API · every number comes from logged experiments in the public repository; sources are listed in section 7')
rep('<div class="meta">Hack Apertus 2026', '<div class="meta">Hack Apertus 2026')

# ---- section 1: problem + similar applications
between("<p><b>Problem.</b>", "<p><b>What we built.</b>",
'''<p><b>Problem.</b> Swiss voters decide on written text, and the text can be wrong or misread. In 2019 the Federal Supreme Court annulled the 2016 <i>Heiratsstrafe</i> vote because the booklet said about 80,000 couples were affected when 454,000 were [50]; a 2023 parliamentary audit found the booklet's four-eyes check is not always done by people with the right expertise [51]; 43&nbsp;% of 1,513 respondents could not say what the November 2018 vote was about [52]. In many of the 2,110 municipalities the assembly sees 4&ndash;8&nbsp;% of eligible voters, so the written proposal is what most people read [58]. We found no actor that pre-tests the wording of an official text with simulated readers before it is published.</p>
<p><b>Similar applications, and what they are used for.</b> Simulated people and AI-assisted listening are used in research and, increasingly, in government and market research; the reference numbers point to section 7.</p>
<table>
<tr><th style="width:23%">Application</th><th style="width:40%">What it is used for</th><th>What is known about it</th></tr>
<tr><td>Singapore GovTech <i>Echo</i>, Sept 2026 [44]</td><td>AI personas, built from past focus-group transcripts, react to a draft government announcement before it is released</td><td>the closest government case; early testing, still validated against real focus groups; &ldquo;personas generate hypotheses, not conclusions&rdquo;</td></tr>
<tr><td>Social Simulacra, Stanford, 2022 [2]</td><td>an LLM generates thousands of community members so designers can test a community design before launch</td><td>the origin of the &ldquo;populated prototype&rdquo; idea we follow</td></tr>
<tr><td>Generative agents and the 1,052-person study, Stanford, 2023 and 2024 [1, 3]</td><td>agents with memory, reflection and interview-grounded personas simulate individuals and small societies</td><td>match survey answers at 85&nbsp;% of participants' own two-week consistency; the authors' spin-off sells it (company claims only)</td></tr>
<tr><td>Predicting experiment results, <i>Nature</i> 2026 [13]</td><td>GPT-4 simulates 70 US survey experiments to pre-test messages</td><td>direction and rank right (r = 0.85), effect sizes systematically too large: good for comparing, not for levels</td></tr>
<tr><td>AI-mediated deliberation: Habermas Machine, DeepMind 2024 [28]; Consult, UK government 2025 [45]</td><td>write group statements that people prefer 56&nbsp;% of the time; sort 2,000+ consultation answers (F1 0.76)</td><td>they work on real people's words, not simulated ones; no public deployment of the first</td></tr>
<tr><td>Synthetic respondents in market research: Aaru, Electric Twin, Ipsos, Qualtrics [46]</td><td>persona panels to test ads, products and campaign messages</td><td>accuracy figures are the vendors' own; the independent test (Pew 2026 [40]) found 11&ndash;13 points average error</td></tr>
<tr><td>Human pre-testing of ballot wording: UK Electoral Commission 2012 and 2015 [47]; citizen panels in Oregon and Sion (VS) [48]</td><td>203 interviews and 10 focus groups changed the wording of the Scottish referendum question; panels write the voter-pamphlet statement</td><td>the gold standard GemeindeSim is a cheap first pass for: it costs weeks and thousands of francs per question</td></tr>
</table>
''')

rep("more than 20,000 logged calls and trials in 91 logs, 32 experiment scripts, 48 instrumented simulations.", "more than 20,000 logged calls and trials, 32 experiment scripts, 48 instrumented simulations.")

# ---- stack paragraph without file names
between("<p><b>Stack.</b>", '<h3>Use of Apertus</h3>',
'''<p><b>Stack.</b> Two Docker services. A FastAPI + LangGraph backend holds the standard and a two-phase (initiator/reactor) round graph; sentence-level chunking with BM25 retrieval (per-chunk language, the ballot question pinned) and an optional dense hybrid; an async model client with an adaptive concurrency limiter, retries and sentence-level streaming; a grounded 1:1 chat; token accounting; the report writer with its guardrails; a Socket.IO stream; and a multi-seed spread run. A Next.js + Phaser frontend shows the map, the event feed with citation chips, the stance poll, the influence graph, the report, a run-metrics panel and a recorder/loader for saved runs. The corpus is read-only; the only outbound call is the OpenAI-compatible <code>LLM_BASE_URL</code>. No personal data is used: residents are generated at run time (code draws name, role, income band, leaning and language; the model writes the persona text).</p>
''')

# ---- use of apertus table -> shorter
between('<h3>Use of Apertus</h3>', '<p><b>Deployability.</b>',
'''<h3>Use of Apertus</h3>
<p>Policy parsing, personas, pro/con arguments, resident turns, impact judgement and the report: the 70B (the 8B also works) in <code>json_object</code> mode, thinking off, one language per completion, with an <i>instruction-placeholder</i> example in the resident's language (49/49 first-attempt valid, 0&nbsp;% parroting; a filled example is parroted, 8B 53&nbsp;%; strict <code>json_schema</code> breaks the 8B). DE&harr;FR translation of lines is a separate call; the 1:1 chat is streamed per sentence. Retrieval, numbers, stance and dynamics are plain code: no tool calls (parallel calls fail 11/11; thinking plus JSON silently skips the reasoning).</p>
''')

rep("(<code>research/probe_endpoint.py</code> runs the same capability table against any endpoint)", "(a probe script in the repository runs the same capability table against any endpoint)")

# ---- section 3 header
rep("<h2>3. Experiments (every call logged; scripts in <code>research/exp*.py</code>, raw logs in <code>research/results/</code>)</h2>", "<h2>3. Experiments (every call is logged; the scripts and raw logs are in the repository)</h2>")
rep("pytest, 69 tests, two runs, --durations", "69 offline tests, two runs, timed")
rep("One test (test_e2e.py::test_full_pipeline, 45 s) calls the live gateway, so the suite is not offline.", "One end-to-end test (45 s) calls the live gateway, so the suite is not offline.")

# ---- demo run heading
rep("<h3>The demo run (recorded from the running app on CSCS, <code>docs/replays/</code>)</h3>", "<h3>The demo run (recorded from the running app on CSCS)</h3>")

# ---- progress table -> compact
between("<h3>Progress</h3>", "<h3>Limitations (what we do not claim)</h3>",
'''<h3>Progress</h3>
<p><b>5 Oct:</b> audit of the inherited code (citations 0/159, outcomes asserted), instrumented baseline (E3), probes E1&ndash;E12, the yes-bias (E11) and the failed fixes (E11b, E11c), then the <b>v2 design</b> (code-owned stance, validated citations, numeral gate, speech binding E14&ndash;E16), the real booklet (E17), compare-conditions (E19), a repaired clean-clone build (E18) and a corrected measurement error (C1). <b>6 Oct:</b> second endpoint, CSCS (E20&ndash;E28); chat wired and grounded. <b>7 Oct:</b> the mentor's engineering questions (E29&ndash;E32); defaults switched to CSCS, which the judges use. <b>8 Oct:</b> literature and deployment survey, the demo run recorded from the running app. <b>13 Oct:</b> a fresh clone of the public repository built with Docker; recording the demo found a deployment bug (two server workers, so a run and its Socket.IO session could land on different workers and about every other run failed with &ldquo;Simulation not found&rdquo;): fixed with one worker and verified; ready-to-paste scenarios added; this report, the footage and the voice-over.</p>
''')

# ---- limitations review pack
rep("German/French register: a native-speaker review pack exists (<code>docs/review/</code>); we do not claim native review until corrections are applied.", "German/French register: a native-speaker review pack is prepared; we do not claim native review until its corrections are applied.")

# ---- reproducibility
between("<h3>Reproducibility (what a judge runs)</h3>", "<h3>Next steps</h3>",
'''<h3>Reproducibility (what a judge runs)</h3>
<p>Clone the public repository, set three environment variables (<code>LLM_BASE_URL</code>, <code>LLM_NAME</code>, <code>LLM_API_KEY</code>; the defaults are the CSCS endpoint and <code>swiss-ai/Apertus-v1.5-70B</code>) and run <code>make run</code> (without <code>make</code>: <code>docker compose up --build</code> in the project directory). The app opens at <code>http://localhost:3000</code> (a second port is <code>UI_ALT_PORT</code>; change it if 8080 is taken). <b>LOAD</b> replays the recorded demo run included in the repository without calling the model; <b>PLAY</b> opens the editor, where a text is pasted and a run started. The repository README lists <b>ready-to-paste scenarios</b> (German, French and English: a fire-station vote with a tax change, a swimming-pool credit, parking fees, a budget, a bike-lane trial, and a deliberately ambiguous text) with what to look for in each. Offline tests: 146, run with <code>uv run pytest</code> in the backend. Every experiment is a script with raw call logs, and a lab notebook records every decision including the failed attempts.</p>
''')

# ---- next steps stays; license and references -> section 7
between("<h3>License and references</h3>", "</body>",
'''<h2>7. References</h2>
<div class="refs"><b>License.</b> CC-BY-4.0 (all Hack Apertus projects are open-sourced); code Apache-2.0. Vendor and press items are marked as such in section 1.
<ol start="1">
%REFS%
</ol></div>
''')

refs = [
 ("g", "Generative agents and social simulation"),
 ("Park, O'Brien, Cai, Morris, Liang, Bernstein (2023). Generative Agents: Interactive Simulacra of Human Behavior.", "arxiv.org/abs/2304.03442"),
 ("Park, Popowski, Cai, Morris, Liang, Bernstein (2022). Social Simulacra: Creating Populated Prototypes for Social Computing Systems. UIST.", "arxiv.org/abs/2208.04024"),
 ("Park, Zou, et al. (2024). Generative Agent Simulations of 1,000 People.", "arxiv.org/abs/2411.10109"),
 ("Yang et al. (2024). OASIS: Open Agent Social Interaction Simulations with One Million Agents.", "arxiv.org/abs/2411.11581"),
 ("Piao et al. (2025). AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents.", "arxiv.org/abs/2502.08691"),
 ("Rossetti et al. (2024). Y Social: an LLM-powered Social Media Digital Twin.", "arxiv.org/abs/2408.00818"),
 ("Anthis et al. (2025). LLM Social Simulations Are a Promising Research Method. ICML.", "arxiv.org/abs/2504.02234"),
 ("g", "Opinion dynamics"),
 ("Deffuant, Neau, Amblard, Weisbuch (2000). Mixing beliefs among interacting agents. Advances in Complex Systems 3.", "doi.org/10.1142/S0219525900000078"),
 ("Peralta, Kertész, Iñiguez (2022). Opinion dynamics in social networks: from models to data.", "arxiv.org/abs/2201.01322"),
 ("Chuang et al. (2023). Simulating Opinion Dynamics with Networks of LLM-based Agents.", "arxiv.org/abs/2311.09618"),
 ("Törnberg, Valeeva, Uitermark, Bail (2023). Simulating Social Media Using LLMs to Evaluate Alternative News Feed Algorithms.", "arxiv.org/abs/2310.05984"),
 ("g", "LLM respondents, voting and survey experiments"),
 ("Argyle et al. (2022). Out of One, Many: Using Language Models to Simulate Human Samples. Political Analysis.", "arxiv.org/abs/2209.06899"),
 ("Ashokkumar, Hewitt, Ghezae, Willer (2026). Large language models can predict the results of social science experiments. Nature 656.", "ai4pb.stanford.edu/projects/predicting-results-of-social-science-experiments-using-large-language-models"),
 ("Bisbee, Clinton, Dorff, Kenkel, Larson (2024). Synthetic Replacements for Human Survey Data? The Perils of Large Language Models. Political Analysis 32(4).", "cambridge.org/core/product/B92267DC26195C7F36E63EA04A47D2FE"),
 ("Barmettler (2026). Progressive in Principle, Centrist in Practice: LLM Political Bias Is Instrument-Dependent (48 Swiss federal referenda, four languages).", "arxiv.org/abs/2606.00048"),
 ("Reveilhac (2025). ChatGPT as a voting application in direct democracy. Swiss Political Science Review.", "doi.org/10.1111/spsr.12650"),
 ("Yang, Dailisan, Korecki, Hausladen, Helbing (2024). LLM Voting: Human Choices and AI Collective Decision Making. AIES.", "arxiv.org/abs/2402.01766"),
 ("Bachmann, van der Weijden, Heitz, Sarasua, Bernstein (2025). Adaptive political surveys and GPT-4. PLoS One.", "arxiv.org/abs/2503.09311"),
 ("Stammbach, Widmer, Cho, Gulcehre, Ash (2024). Aligning Large Language Models with Diverse Political Viewpoints. EMNLP.", "arxiv.org/abs/2406.14155"),
 ("Egli, Mamié, Dolev, Müller (2023). Voting Booklet Bias: Stance Detection in Swiss Federal Communication.", "arxiv.org/abs/2306.08999"),
 ("von der Heyde, Haensch, Wenz (2025). Vox Populi, Vox AI? Using Language Models to Estimate German Public Opinion; and (2024) United in Diversity? Contextual Biases in LLM-Based Predictions of the 2024 European Parliament Elections.", "arxiv.org/abs/2407.08563, arxiv.org/abs/2409.09045"),
 ("Ma et al. (2025). Algorithmic Fidelity of Large Language Models in Generating Synthetic German Public Opinions. ACL.", "arxiv.org/abs/2412.13169"),
 ("Gudiño-Rosero, Grandi, Hidalgo (2024). Large Language Models (LLMs) as Agents for Augmented Democracy.", "arxiv.org/abs/2405.03452"),
 ("Kreutner, Lutz, Strohmaier (2026). Persona-driven Simulation of Voting Behavior in the European Parliament with LLMs. EACL.", "arxiv.org/abs/2506.11798"),
 ("Gong, Sanders, Schneier (2026). Characterizing the ability of LLMs to recapitulate Americans' distributional responses to public opinion polling questions.", "arxiv.org/abs/2603.20229"),
 ("g", "Policy simulation and deliberation"),
 ("Barnett, Kieslich, Diakopoulos (2024). Simulating Policy Impacts: A Generative Scenario Writing Method to Evaluate the Perceived Effects of Regulation. AIES.", "arxiv.org/abs/2405.09679"),
 ("Rountree, Gastil (2026). The Case for Using Generative AI to Run Deliberation Simulations. Journal of Deliberative Democracy.", "delibdemjournal.org/article/id/1625"),
 ("Tessler et al. (2024). AI can help humans find common ground in democratic deliberation (Habermas Machine). Science 386; coverage: MIT Technology Review.", "technologyreview.com/2024/10/17/1105810"),
 ("Chen (2026). Human-Simulation Interaction: From Prediction to Exploration in LLM Agent Simulations for Policy. PoliSim@CHI.", "arxiv.org/abs/2608.07496"),
 ("European Commission Joint Research Centre (2023). FABLES: LLM-driven agent populations for policy scenarios.", "publications.jrc.ec.europa.eu/repository/handle/JRC135070"),
 ("g", "Critiques and limits"),
 ("Wang, Morgenstern, Dickerson (2024). Large language models that replace human participants can harmfully misportray and flatten identity groups. Nature Machine Intelligence.", "arxiv.org/abs/2402.01908"),
 ("Park, Schoenegger, Zhu (2024). Diminished Diversity-of-Thought in a Standard Large Language Model.", "arxiv.org/abs/2302.07267"),
 ("Santurkar et al. (2023). Whose Opinions Do Language Models Reflect?", "arxiv.org/abs/2303.17548"),
 ("Agnew et al. (2024). The Illusion of Artificial Inclusion. CHI.", "arxiv.org/abs/2401.08572"),
 ("Larooij, Törnberg (2025). Do Large Language Models Solve the Problems of Agent-Based Modeling? A Critical Review of Generative Social Simulations.", "arxiv.org/abs/2504.03274"),
 ("Ye, Cao, Chen, Ferrara (2026). Stop Drawing Scientific Claims from LLM Social Simulations Without Robustness Audits.", "arxiv.org/abs/2605.18890"),
 ("Lukauskas, Šarkauskaitė (2026). Plausible but Not Valid: A Psychometric Audit of LLMs as Synthetic Survey Respondents.", "arxiv.org/abs/2608.14606"),
 ("Flechtner (2026). The Deliberative Deficit. AIES; Yao et al. (2025). Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate.", "arxiv.org/abs/2608.10186, arxiv.org/abs/2509.23055"),
 ("Luo, Arora, Guirado (2026). We Need Strong Preconditions For Using Simulations In Policy; Jang et al. (2026). From Simulated Citizens to Simulated Deliberation.", "arxiv.org/abs/2604.07838, arxiv.org/abs/2609.07573"),
 ("Pew Research Center (30 Sept 2026). How synthetic polling results change based on the AI model.", "pewresearch.org/data-labs/2026/09/30/how-synthetic-polling-results-change-based-on-the-ai-model"),
 ("University of Salford and UCL (2026). Most AI models predicted a Reform win in Makerfield; the voters delivered a Labour landslide.", "salford.ac.uk/news/most-ai-models-predicted-a-reform-win-in-makerfield-the-voters-delivered-a-labour-landslide"),
 ("Durmus et al. (2023). Towards Measuring the Representation of Subjective Global Opinions in Language Models; AlKhamissi et al. (2024). Investigating Cultural Alignment of Large Language Models.", "arxiv.org/abs/2306.16388, arxiv.org/abs/2402.13231"),
 ("Hu, Collier (2024). Quantifying the Persona Effect in LLM Simulations; Atil et al. (2024). Non-Determinism of \"Deterministic\" LLM Settings.", "arxiv.org/abs/2402.10811, arxiv.org/abs/2408.04667"),
 ("g", "Deployments and practice"),
 ("Singapore GovTech (11 Sept 2026). Using AI to test government messages (Echo).", "tech.gov.sg/technews/using-ai-to-test-government-messages"),
 ("UK Government, i.AI (2025). Government-built Humphrey AI tool reviews responses to consultation for the first time (Consult).", "gov.uk/government/news/government-built-humphrey-ai-tool-reviews-responses-to-consultation-for-first-time-in-bid-to-save-millions"),
 ("Market-research vendors (company claims, not independent): Aaru (TechCrunch, 5 Dec 2025), Electric Twin (tech.eu, 12 Feb 2026), Simile, Ipsos PersonaBot, Qualtrics.", "techcrunch.com/2025/12/05/ai-synthetic-research-startup-aaru-raised-a-series-a-at-a-1b-headline-valuation"),
 ("Ipsos for the UK Electoral Commission (2012). Scottish independence referendum question testing.", "ipsos.com/en-uk/referendum-scottish-independence-question-testing"),
 ("Citizens' Initiative Review (Oregon, from 2010) and the Sion (VS) pilot on a federal initiative (Nov 2019).", "participedia.net/case/6439"),
 ("MIT Technology Review (2025). A small US city experiments with AI to find out what residents want (Bowling Green, KY).", "technologyreview.com/2025/04/15/1115125"),
 ("g", "Swiss context"),
 ("Federal Supreme Court (10 Apr 2019): annulment of the 2016 Heiratsstrafe vote (Blick).", "blick.ch/politik/bundesgericht-erklaert-abstimmung-ueber-heiratsstrafe-fuer-ungueltig-wie-lange-kann-sich-die-cvp-freuen-id15266130.html"),
 ("Geschäftsprüfungskommission des Nationalrats (21 Nov 2023). Report on authority communication before votes.", "parlament.ch/centers/documents/de/Bericht%20GPK-N%20vom%2021.11.2023%20D.pdf"),
 ("swissinfo. VOTO analysis of the 25 Nov 2018 \"Swiss law first\" vote.", "swissinfo.ch/eng/voto-analysis_-swiss-law-first--initiative-challenged-many-voters/44675792"),
 ("Federal Supreme Court, 1P.377/2003 (4 Nov 2003): objective and complete explanations in a municipal vote.", "servat.unibe.ch/dfr/bger/2003/031104_1P-377-2003.html"),
 ("swissinfo (2024). It's often the voting booklet that decides yes or no (Strijbis study, commissioned by a campaign-communication body).", "swissinfo.ch/eng/swiss-politics/its-often-the-voting-booklet-that-decides-yes-or-no/87490263"),
 ("SRF (2022). Einfachere Sprache: Ist das Abstimmungsbüchlein für viele zu komplex?", "srf.ch/news/abstimmungen-15-mai-2022/einfachere-sprache-ist-das-abstimmungsbuechlein-fuer-viele-zu-komplex"),
 ("gfs.bern for the Federal Chancellery (2025), via Netzwoche. KI in der Behördenkommunikation.", "netzwoche.ch/news/2025-05-21/ki-in-der-behoerdenkommunikation-ist-okay-aber-nicht-bedingungslos"),
 ("Menzi (2021). Swiss Yearbook of Administrative Sciences 12(1): many voters do not understand voting proposals.", "doi.org/10.5334/ssas.157"),
 ("SRF (2019). Aargau study of municipal assemblies; SRF on assembly attendance and the share of municipalities with a parliament.", "srf.ch/news/grosse-studie-im-aargau-gemeindeversammlungen-sind-besser-als-ihr-ruf"),
 ("Bern University of Applied Sciences: smartinfo (2026-2028); OST: Fact Attack 2026 (Hack Apertus track 2A); Swissvotes, University of Bern.", "bfh.ch/de/forschung/forschungsprojekte/2026-405-463-889, github.com/JJukic/Apertus-Team-Fact-Attack-2026, swissvotes.ch"),
 ("Federal Chancellery (28 Sept 2025). Erläuterungen des Bundesrates (the real booklet used in the evaluation).", "bk.admin.ch"),
 ("g", "Apertus, retrieval and methods"),
 ("Apertus: Swiss AI Initiative (2025). Apertus technical report; ETH Zurich press release; CSCS (2026), Apertus 1.5.", "arxiv.org/abs/2509.14233, cscs.ch/science/computer-science-hpc/2026/apertus-15-building-the-next-generation-of-open-ai-infrastructure"),
 ("Robertson, Zaragoza (2009). The Probabilistic Relevance Framework: BM25 and Beyond.", "doi.org/10.1561/1500000019"),
 ("Wang et al. (2024). Multilingual E5 Text Embeddings: A Technical Report.", "arxiv.org/abs/2402.05672"),
 ("Cormack, Clarke, Büttcher (2009). Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. SIGIR.", "doi.org/10.1145/1571941.1572114"),
 ("Gao et al. (2023). Enabling Large Language Models to Generate Text with Citations.", "arxiv.org/abs/2305.14627"),
]
# numbering must match the [n] used in the text: group headings are not numbered
html = []
n = 0
for item in refs:
    if item[0] == "g":
        html.append(f'<li class="grp">{item[1]}</li>')
        continue
    n += 1
    links = ", ".join(f'<a href="https://{u.strip()}">{u.strip()}</a>' for u in item[1].split(","))
    html.append(f"<li>{item[0]} {links}</li>")
print("references:", n)
s = s.replace("%REFS%", "\n".join(html))

# css for references
rep("  .pb { break-before: page; }", "  .pb { break-before: page; }\n  .refs { font-size: 6.2pt; line-height: 1.22; columns: 2; column-gap: 12px; }\n  .refs ol { margin: 2px 0 0 0; padding-left: 15px; }\n  .refs li { margin: 0 0 1px; break-inside: avoid; }\n  .refs li.grp { list-style: none; font-weight: bold; margin: 3px 0 1px -15px; font-size: 6.6pt; }\n  .refs a { color: #1b4f8a; text-decoration: none; word-break: break-all; }")

P.write_text(s, encoding="utf-8")
print("ok")
