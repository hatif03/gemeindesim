"""E17: retrieval and grounded QA on a REAL booklet (Federal Council explanations, 28 Sept 2025, German, 48 pages).

The Linden sample (1.6 k characters) cannot stress retrieval. This booklet is ~83 k characters (≈ 170 chunks), 50x larger.
Part A  directed retrieval recall@4 for 14 questions with gold evidence in the text: v1 retriever vs v2 retriever.
Part B  what a resident sees: fact coverage of the 4 passages for 15 resident-style queries (v1 query vs v2 query).
Part C  grounded QA with the 70B on the retrieved passages: accuracy, correct abstention on 3 unanswerable questions,
        citation validity, v1 vs v2 passages.
Usage: python research/exp17_real_booklet.py   (needs research/data/booklets/erlaeuterungen_2025-09-28_de.txt; see download_booklet.py)
"""
import asyncio
import json
import re
import statistics as st
from pathlib import Path

import corpus_v1
from common import M70, RESULTS, Gateway
from graph import corpus as corpus_v2

TEXT = (Path(__file__).resolve().parent / "data" / "booklets" / "erlaeuterungen_2025-09-28_de.txt").read_text(encoding="utf-8")
QA = [  # (question, gold regex that the evidence/answer must match)
    ("Wie hoch schätzt der Bundesrat die Kosten für Entwicklung und Betrieb der E-ID für die Jahre 2023 bis 2028?", r"180\s+Millionen"),
    ("Ist die Nutzung der E-ID freiwillig und kostenlos?", r"freiwillig\s+und\s+kostenlos"),
    ("Warum kommt das E-ID-Gesetz zur Abstimmung?", r"Referendum\s+ergriffen"),
    ("Warum haben die Stimmberechtigten die erste E-ID-Vorlage im Jahr 2021 abgelehnt?", r"private[nr]?\s+Unternehmen"),
    ("Wer gibt die E-ID gemäss dem neuen Gesetz heraus?", r"Bund\s+die\s+E-ID\s+herausgibt"),
    ("Was kritisieren die Referendumskomitees an der E-ID?", r"nicht\s+sicher"),
    ("Auf wie viel schätzt der Bundesrat die Mindereinnahmen insgesamt, wenn der Eigenmietwert wegfällt?", r"1,8\s+Milliarden"),
    ("Wie viel der Mindereinnahmen entfällt auf Zweitliegenschaften?", r"260\s+Millionen"),
    ("Was passiert mit der Besteuerung des Eigenmietwerts, wenn die besondere Liegenschaftssteuer abgelehnt wird?", r"bleibt\s+die\s+Besteuerung\s+des\s+Eigenmietwerts\s+bestehen"),
    ("Können Schuldzinsen nach der Reform noch abgezogen werden?", r"nur\s+noch\s+abgezogen\s+werden,\s+wenn\s+jemand\s+über\s+vermietete"),
    ("Was ist der Ersterwerberabzug?", r"Ersterwerberabzug"),
    ("Wie hoch war die Hypothekarverschuldung im Jahr 2023?", r"1000\s+Milliarden"),
    ("Welche Abzüge fallen nach der Reform weg, die mit Energie und Umwelt zu tun haben?", r"Energiespar-\s+und\s+Umweltschutzmassnahmen\s+weg"),
    ("An welchem Datum findet die Volksabstimmung statt?", r"28\.\s+September\s+2025"),
]
UNANSWERABLE = ["Wie hoch ist der Steuerfuss der Stadt Bern?", "Wie viele Personen haben die E-ID bisher bestellt?",
                "Welche Partei hat im Kanton Zug die höchste Wählerstärke?"]
EN_SUMMARY = ("A new policy affecting Public administration, Housing and Digital services has been announced.\nKey expected impacts:\n"
              "  - Tax treatment of home ownership changes\n  - A digital identity is introduced\nControversy level: medium")
PERSONAS = [  # resident-style context: profession + a bio line (as the app builds the v2 query)
    ("Mieterin, Mechanikerin in einer kleinen Werkstatt", "Lebt in einer Mietwohnung und kommt finanziell knapp über die Runden."),
    ("Landwirtin, Bio-Hof mit Direktvermarktung", "Führt den Familienbetrieb und hat eine Hypothek auf dem Hof."),
    ("Lehrerin an der Sekundarschule", "Kauft nächstes Jahr mit ihrem Mann erstmals eine Wohnung."),
    ("Rentner, ehemaliger Bauleiter", "Wohnt im eigenen Haus, Hypothek abbezahlt, kleines Ferienhaus im Tessin."),
    ("Gemeindeangestellter, Leiter Bauamt", "Beschäftigt sich beruflich mit Liegenschaftssteuern und Baubewilligungen."),
    ("Ladenbesitzerin an der Dorfstrasse", "Hat ein Geschäftslokal gemietet und eine kleine Zweitwohnung in den Bergen."),
    ("Informatiker bei einer Bank", "Nutzt digitale Dienste täglich und macht sich Sorgen um Datenschutz."),
    ("Studentin, wohnt in einer WG", "Wählt zum ersten Mal und interessiert sich für digitale Verwaltung."),
    ("Handwerker, selbständiger Sanitärinstallateur", "Besitzt ein Haus mit Hypothek und renoviert regelmässig energetisch."),
    ("Pensionierte Lehrerin", "Besitzt eine Eigentumswohnung und beobachtet die Zinsentwicklung."),
    ("Treuhänder", "Berät Kunden bei der Steuererklärung, auch zu Schuldzinsen und Liegenschaftsunterhalt."),
    ("Bauer im Nebenerwerb", "Hat zwei Liegenschaften und einen Pachtbetrieb."),
    ("Krankenpflegerin im Schichtdienst", "Mietet eine Wohnung und braucht amtliche Dokumente online."),
    ("Gemeinderätin", "Interessiert sich für die Steuerausfälle der Gemeinde durch Reformen."),
    ("Taxifahrer", "Wohnt zur Miete und hat kein eigenes Haus."),
]


def v1_pack(query, k=4):
    ch = corpus_v1.chunk_policy_document("--- Author notes / pasted text ---\n" + TEXT)
    return corpus_v1.retrieve_passages(ch, query, top_k=k, lang="de")


def v2_pack(query, k=4):
    return corpus_v2.retrieve_passages(CH2, query, top_k=k, lang="de")


CH2 = corpus_v2.chunk_policy_document("--- Author notes / pasted text ---\n" + TEXT)
CH1 = corpus_v1.chunk_policy_document("--- Author notes / pasted text ---\n" + TEXT)


def hit(passages, gold):
    return any(re.search(gold, " ".join(p["text"].split()), re.I) for p in passages)


def hit_joined(passages, gold):  # gold may straddle a chunk cut (v1 cuts mid-word); join neighbours only if consecutive
    return hit(passages, gold)


async def main():
    print(f"booklet chars {len(TEXT)}  v1 chunks {len(CH1)}  v2 chunks {len(CH2)}")
    # ---- Part A: directed recall@4
    rA = {"v1": 0, "v2": 0}
    for q, g in QA:
        rA["v1"] += hit(v1_pack(q), g)
        rA["v2"] += hit(v2_pack(q), g)
    print(f"A directed retrieval recall@4 (n={len(QA)}):  v1 {rA['v1']}/{len(QA)}   v2 {rA['v2']}/{len(QA)}")
    # ---- Part B: resident view
    names = "Anna Berger Léa Rochat Hans Weber"
    cov = {"v1": [], "v2": []}
    for prof, bio in PERSONAS:
        q1 = f"{EN_SUMMARY} {names} Last round saw 12 total actions across town. {prof}"
        q2 = f"{prof} {bio} {names}"
        cov["v1"].append(sum(hit(v1_pack(q1), g) for _, g in QA) / len(QA))
        cov["v2"].append(sum(hit(v2_pack(q2), g) for _, g in QA) / len(QA))
    print(f"B resident view: share of the {len(QA)} key facts inside the 4 passages (mean over {len(PERSONAS)} residents):  "
          f"v1 {st.mean(cov['v1']):.2f}   v2 {st.mean(cov['v2']):.2f}   (a resident sees 4 of ~{len(CH2)} chunks)")
    # ---- Part C: grounded QA
    gw = Gateway("e17_booklet", concurrency=3)

    def prompt(q, passages):
        pack = "\n\n".join(f"[P{i}] {' '.join(p['text'].split())}" for i, p in enumerate(passages, 1))
        return (f"Beantworte die Frage ausschliesslich anhand dieser Passagen aus den Erläuterungen des Bundesrates.\n\n{pack}\n\nFrage: {q}\n"
                'Wenn die Antwort nicht in den Passagen steht, antworte mit "NICHT IM TEXT". '
                'Antworte nur mit JSON: {"answer": "<kurze Antwort>", "sources": ["P1"]}')

    async def ask(q, passages):
        rec = await gw.chat(prompt(q, passages), model=M70, max_tokens=200, json_mode=True, tag="qa")
        c = rec["resp"]["content"]
        a = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', c)
        s = re.findall(r"P(\d+)", (re.search(r'"sources"\s*:\s*\[(.*?)\]', c, re.S) or [None, ""])[1])
        return (a.group(1) if a else c), [int(x) for x in s]

    rows = []
    for ver, packer in (("v1", v1_pack), ("v2", v2_pack)):
        jobs = [(q, g, packer(q)) for q, g in QA] + [(q, None, packer(q)) for q in UNANSWERABLE]
        res = await asyncio.gather(*[ask(q, ps) for q, g, ps in jobs])
        for (q, g, ps), (ans, src) in zip(jobs, res):
            abst = "NICHT IM TEXT" in ans.upper()
            ok_cite = all(1 <= i <= len(ps) for i in src) and (bool(src) or abst)
            rows.append({"ver": ver, "q": q, "answerable": g is not None, "answer": ans, "sources": src, "abstained": abst,
                         "retrieved_gold": hit(ps, g) if g else None,
                         "correct": (bool(re.search(g, " ".join(ans.split()), re.I)) if g else abst), "valid_citation": ok_cite,
                         "cited_passage_has_gold": (any(hit([ps[i - 1]], g) for i in src if 1 <= i <= len(ps)) if g else None)})
    await gw.close()
    (RESULTS / "e17_real_booklet.json").write_text(json.dumps({"A": rA, "B": {k: st.mean(v) for k, v in cov.items()}, "C": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    for ver in ("v1", "v2"):
        r = [x for x in rows if x["ver"] == ver]
        ans = [x for x in r if x["answerable"]]
        un = [x for x in r if not x["answerable"]]
        print(f"C {ver}: answerable correct {sum(x['correct'] for x in ans)}/{len(ans)} (gold retrieved {sum(bool(x['retrieved_gold']) for x in ans)}/{len(ans)}, "
              f"wrongly abstained {sum(x['abstained'] for x in ans)}); unanswerable abstained {sum(x['correct'] for x in un)}/{len(un)}; "
              f"valid citation {sum(x['valid_citation'] for x in r)}/{len(r)}; cited passage contains the evidence {sum(bool(x['cited_passage_has_gold']) for x in ans)}/{len(ans)}")


if __name__ == "__main__":
    asyncio.run(main())
