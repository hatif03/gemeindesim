"""Build the native-speaker review pack (docs/review/) from the v2.2 runs.

Sampling is seeded, so the pack is reproducible. Output: NATIVE-SPEAKER-REVIEW.md (read + fill in) and
review-sheet.csv (one row per item, same ids, for spreadsheet use).
Usage: python research/make_review_pack.py
"""
import csv
import json
import random
from pathlib import Path

from common import ROOT, RESULTS, read_sample
from graph.language import FALLBACK_UTTERANCE, GLOSSARY, NO_VOTE_LINE

OUT = ROOT / "docs" / "review"
OUT.mkdir(parents=True, exist_ok=True)
rnd = random.Random(7)
RUNS = {"70B": ["v22_70_s1", "v22_70_s2", "v22_70_s3"], "8B": ["v22_8_s1", "v22_8_s2"]}

lines = []
for model, tags in RUNS.items():
    for t in tags:
        d = json.loads((RESULTS / "sims" / f"{t}.json").read_text(encoding="utf-8"))
        npcs = {n["id"]: n for n in d["npcs0"]}
        for r in d["rounds"]:
            for e in r["events"]:
                txt = (e["data"].get("dialogue") or e["message"] or "").strip()
                n = npcs[e["npc_id"]]
                if e["event_type"] in ("chat", "mood_shift") and len(txt) > 40 and n["lang"] in ("de", "fr"):
                    lines.append({"model": model, "run": t, "lang": n["lang"], "role": n["role"], "profession": n["profession"],
                                  "type": e["event_type"], "text": txt})
picked = []
for lang, k70, k8 in (("de", 14, 6), ("fr", 14, 6)):
    for model, k in (("70B", k70), ("8B", k8)):
        pool = [x for x in lines if x["lang"] == lang and x["model"] == model]
        rnd.shuffle(pool)
        picked += pool[:k]
rows = []  # (id, kind, lang, context, text)
for i, x in enumerate(picked, 1):
    rows.append((f"L{i:02d}", "resident line", x["lang"], f"{x['model']} · {x['role']} · {x['profession']} · {x['type']}", x["text"]))
d = json.loads((RESULTS / "sims" / "v22_70_s1.json").read_text(encoding="utf-8"))
rep = d["report"]
rows.append(("R01", "report headline", "de", "70B report, German", rep["headline"]))
rows.append(("R02", "report summary", "de", "70B report, German", rep["summary"]))
rows.append(("R03", "report livelihood", "de", "70B report, German", rep["livelihood_impact"]))
for i, (lang, text) in enumerate(FALLBACK_UTTERANCE.items(), 1):
    if lang in ("de", "fr"):
        rows.append((f"F{i:02d}", "fallback line", lang, "shown when the model fails twice", text))
for lang, text in NO_VOTE_LINE.items():
    if lang in ("de", "fr"):
        rows.append((f"N-{lang}", "report disclaimer", lang, "appended to every vote report", text.strip()))
for lang, text in GLOSSARY.items():
    if lang in ("de", "fr"):
        rows.append((f"G-{lang}", "glossary (terms the residents are told to prefer)", lang, "prompt glossary", text))

md = ["# Native-speaker review: GemeindeSim German and French", "",
      "Thank you. The authors are **not** native speakers of German or French; the sample booklet, the glossary and the",
      "residents' lines were produced with machine assistance. This pack asks you to judge what a Swiss reader would see.",
      "", "## What to do (about 45 minutes)", "",
      "1. Read the **synthetic booklet** (section A) as if it were a municipal *Abstimmungsbüchlein* / *brochure de vote*.",
      "2. Rate each numbered item (sections B and C) on the five criteria below, 1 (bad) to 5 (native-natural).",
      "3. Write the corrected wording wherever you would change something. Mark *Germanisms* (Hochdeutsch/Germany vocabulary",
      "   in a Swiss text, e.g. *Abitur* for *Matura*) and *Gallicisms* / France-French (e.g. *nonante* vs *quatre-vingt-dix*).",
      "4. Return the filled `review-sheet.csv` (or this file). Items keep the same ids.", "",
      "### Criteria", "",
      "| code | question |", "| --- | --- |",
      "| REG | Is the register right for this person and situation (neighbour talking, official text, report)? |",
      "| TERM | Are the official terms right (Vorlage, Steuerfuss, Gemeinderat / objet, taux d'imposition, conseil communal …)? |",
      "| CH | Does it sound Swiss (vocabulary, *ss* instead of *ß*, number format 80'000, CHF) rather than German/French-French? |",
      "| NAT | Would a person really say or write it this way (not stiff, not translated)? |",
      "| ERR | Any outright error (grammar, wrong word, wrong meaning)? Quote it. |", "",
      "## A. The synthetic booklet text", "", "### Deutsch", "", "```", read_sample("steuerfuss_linden_de.txt").strip(), "```", "",
      "### Français", "", "```", read_sample("steuerfuss_linden_fr.txt").strip(), "```", "",
      "## B. Fixed phrases, glossary and report", "",
      "| id | what | lang | context | text | REG | TERM | CH | NAT | ERR / correction |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
md += [f"| {i} | {k} | {l} | {c} | {t.replace('|', '/').replace(chr(10), ' ')} |  |  |  |  |  |" for i, k, l, c, t in rows if i[0] in "RFNG"]
md += ["", "## C. Residents' lines (generated; seeded sample, 14 from the 70B and 6 from the 8B per language)", "",
       "| id | lang | context | text | REG | TERM | CH | NAT | ERR / correction |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
md += [f"| {i} | {l} | {c} | {t.replace('|', '/').replace(chr(10), ' ')} |  |  |  |  |  |" for i, k, l, c, t in rows if i[0] == "L"]
md += ["", "## D. Free comments", "", "Anything systematically wrong (a word the model always uses, a tone that is off, missing Swiss terms):", ""]
(OUT / "NATIVE-SPEAKER-REVIEW.md").write_text("\n".join(md), encoding="utf-8")
with (OUT / "review-sheet.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "kind", "lang", "context", "text", "REG", "TERM", "CH", "NAT", "ERR", "correction"])
    for r in rows:
        w.writerow([*r, "", "", "", "", "", ""])
print(f"{len(rows)} items -> {OUT}")
