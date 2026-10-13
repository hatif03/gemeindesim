"""One-off: tighten report/report.html to six pages."""
import re
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "report" / "report.html"
s = P.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new, 1)


def between(a, b, new):
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]


# base typography a little tighter
rep("body { font: 8.9pt/1.33", "body { font: 8.6pt/1.3")
rep("table { border-collapse: collapse; width: 100%; margin: 3px 0 5px; font-size: 7.6pt; }\n  table.ex { font-size: 7.1pt; } table.ex th, table.ex td { padding: 1px 3px; }",
    "table { border-collapse: collapse; width: 100%; margin: 3px 0 4px; font-size: 7.3pt; }\n  table.ex { font-size: 6.5pt; line-height: 1.2; } table.ex th, table.ex td { padding: 0.5px 3px; }")
rep("h2 { font-size: 11pt; margin: 9px 0 3px;", "h2 { font-size: 10.5pt; margin: 7px 0 2px;")

# figure sizes
rep('alt="pipeline" style="width:68%"', 'alt="pipeline" style="width:60%"')
rep('alt="endpoints" style="width:56%"', 'alt="endpoints" style="width:50%"')
rep('alt="time budget" style="width:60%"', 'alt="time budget" style="width:54%"')
rep('alt="demo run" style="width:74%"', 'alt="demo run" style="width:66%"')
rep('alt="app screens" style="width:100%"', 'alt="app screens" style="width:92%"')
rep(".row2 img { width: 86%; }", ".row2 img { width: 80%; }")

# experiments table: narrower id/question/setup so the result column is wide
rep('<tr><th style="width:5%">ID</th><th style="width:22%">Question</th><th style="width:19%">Setup</th><th>Result</th></tr>',
    '<tr><th style="width:4%">ID</th><th style="width:19%">Question</th><th style="width:16%">Setup</th><th>Result</th></tr>')

# drop the speech-binding figure; keep the fixes figure next to the table text
between('<div class="row2"><div style="flex:0.85"><img src="../docs/figures/fig07-fixes.png"', "<table>\n<tr><th>Defect</th>",
        '<div class="fig"><img src="../docs/figures/fig07-fixes.png" alt="fixes" style="width:46%"><span class="cap">Fig. 5. Before / after (3 baseline vs 5 final 70B runs, same seeds).</span></div>\n')

# defect table: drop three minor rows
for key in ("Ballot question in the resident's prompt", "Numeral gate, 12 edge cases", "Influence log reaching the UI"):
    i = s.index(f"<tr><td>{key}")
    j = s.index("</tr>", i) + 6
    s = s[:i] + s[j:]

# RAG table -> sentence
between("<p><b>RAG against the usual baselines", "<h3>The demo run",
        '<p><b>RAG against the usual baselines (E30; 14 gold questions, 209 chunks of the real booklet).</b> recall@4 / MRR@10: our BM25 0.79 / 0.29; dense multilingual-e5-large 1.00 / 0.89; <b>hybrid BM25 + e5-large (reciprocal rank fusion) 1.00 / 0.91</b>; a small paraphrase model 0.71 / 0.56 (worse than BM25). n = 14 on one German document: one-question differences are noise. The hybrid is an option, off by default because it needs a 2.2 GB local model that an air-gapped deployment would have to ship.</p>\n')

# mentor bullets: shorter
between("<ul>\n<li><b>Python / async / context.</b>", "<p><b>RAG against", '''<ul>
<li><b>Python, async, context.</b> The wall time is the longest chain of dependent calls (persona, impact, reflection, turn, translation) at &asymp;60 tokens/s; every call is async; resident prompts use at most 1.1&nbsp;% of the 262 k window, so no compaction is needed; 17&ndash;25&nbsp;% of prompt tokens were cached on CSCS (moving the instruction block to the front would save &asymp;0.3 s of a 5.5 s call but moves the speech-binding paragraph: not done).</li>
<li><b>Streaming, tokens, subagents.</b> The chat streams sentence by sentence after the number gate and citation check (first text 1.5 s, whole answer 2.4 s, 0 invented figures); JSON turns and the report are not streamed (they must be complete to be validated). Tokens are counted from the endpoint's <code>usage</code> and shown in a run-metrics panel (in/out/cached, latency p50/p95, context use, retries, in-flight limit). Each resident is an isolated context run in parallel; there is no tool loop.</li>
</ul>
''')

# endpoints paragraph shorter
between("<p><b>CSCS (E20", "<h3>Mentor questions", '''<p><b>CSCS (E20&ndash;E28).</b> Capability matrix, throughput, long context, determinism, structured output, stance on four models, retrieve-first vs whole-booklet, the final code on 5 seeds &times; 2 sizes, and the grounded chat live. All v2 fixes replicate (valid citations 1.00, no asserted outcome, speech matches the code stance 0.85&ndash;0.88), and so do the Swiss-knowledge and real-vote results. Unchanged: the yes-bias (E24), one tool call, non-reproducible <code>T=0</code>. With the complete booklet in the chat prompt (6,000&ndash;100,000 characters) the real revenue question is answered 5/5 instead of 0/5. <b>One build, both endpoints (E31):</b> ids are mapped and the limiter adapts (three iterations): 25 residents &times; 2 rounds took 89&ndash;97 s on CSCS and 654 s on the busy gateway.</p>
''')

# limitations and fixes: small trims
rep("; LLM classifiers (79&ndash;91&nbsp;% mutual agreement) score the speech tests", "")

P.write_text(s, encoding="utf-8")
print("ok")
