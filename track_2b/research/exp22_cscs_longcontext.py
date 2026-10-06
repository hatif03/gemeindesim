"""E22: long-context recall on the CSCS inference API up to the advertised 262k tokens (E12 stopped at ≈105k on the hackathon gateway).

Same haystack as E12 (distinct official vote titles, cycled beyond ≈ 80k characters, DE or FR) with two question types:
 - single: one Linden sentence (118 → 124 %) at depth 10 / 50 / 90 %
 - multi : three Linden sentences (rate, credit, classrooms) at depth 20 / 50 / 80 %; all three figures must be in the answer
Sizes 140k, 280k, 400k, 520k, 620k characters ≈ 52k … 235k tokens. 70B and 8B, DE and FR. Raw calls: research/results/cscs/e22_longcontext.jsonl.

    . research/cscs_env.sh && uv run --project src/backend python research/exp22_cscs_longcontext.py
"""
import asyncio
import csv
import json
import re
from pathlib import Path

from common import M70, M8, RESULTS, Gateway

DATA = Path(__file__).resolve().parent / "data" / "swissvotes_titles_full.csv"
rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig"), delimiter=";"))
N1 = {"de": "Hinweis aus der Gemeinde Linden: Der Steuerfuss der Gemeinde Linden steigt von 118 % auf 124 % der einfachen Steuer.",
      "fr": "Note de la commune de Linden : le taux d'imposition de la commune de Linden passe de 118 % à 124 % de l'impôt simple."}
N2 = {"de": "Hinweis aus der Gemeinde Linden: Der Kredit für das Schulhaus Linden-Dorf beträgt 4.8 Millionen CHF.",
      "fr": "Note de la commune de Linden : le crédit pour l'école de Linden-Dorf s'élève à 4,8 millions de CHF."}
N3 = {"de": "Hinweis aus der Gemeinde Linden: Das neue Schulhaus enthält 8 Klassenzimmer und eine Turnhalle.",
      "fr": "Note de la commune de Linden : la nouvelle école compte 8 salles de classe et une salle de gymnastique."}
Q1 = {"de": "Auf welchen Prozentsatz steigt der Steuerfuss der Gemeinde Linden und von welchem Prozentsatz aus? Antworte kurz mit den beiden Zahlen.",
      "fr": "À quel pourcentage le taux d'imposition de la commune de Linden passe-t-il, et à partir de quel pourcentage ? Réponds brièvement avec les deux chiffres."}
Q3 = {"de": "Nenne die drei Zahlen der Gemeinde Linden: neuer Steuerfuss in Prozent, Kredit in Millionen CHF, Anzahl Klassenzimmer. Antworte nur mit den drei Zahlen.",
      "fr": "Donne les trois chiffres de la commune de Linden : nouveau taux d'imposition en pourcent, crédit en millions de CHF, nombre de salles de classe. Réponds seulement avec les trois chiffres."}
import os
SIZES = [int(x) for x in os.environ.get("E22_SIZES", "140000,280000,400000,520000,620000").split(",")]
DEPTHS = [float(x) for x in os.environ.get("E22_DEPTHS", "0.1,0.5,0.9").split(",")]
LANGS = os.environ.get("E22_LANGS", "de,fr").split(",")
MULTI = os.environ.get("E22_MULTI", "1") == "1"


def haystack(lang, n_chars):
    col = "titel_off_d" if lang == "de" else "titel_off_f"
    out, i = [], 0
    while sum(len(x) + 1 for x in out) < n_chars:
        r = rows[i % len(rows)]
        out.append(f"({i + 1}) {r['datum']}: {r[col]} [{r['stichwort']}]")
        i += 1
    return "\n".join(out)[:n_chars]


def insert(hay, needles_at):
    """needles_at: [(depth, sentence)] ascending depth; inserts at line boundaries."""
    text, offset = hay, 0
    for depth, sent in sorted(needles_at):
        pos = text.rfind("\n", 0, int(len(hay) * depth) + offset) + 1
        text = text[:pos] + sent + "\n" + text[pos:]
        offset += len(sent) + 1
    return text


async def main():
    gw = Gateway("e22_longcontext", concurrency=2)
    jobs, keys = [], []
    for model in (M70, M8):
        for lang in LANGS:
            for chars in SIZES:
                hay = haystack(lang, chars)
                for depth in DEPTHS:
                    p = f"{insert(hay, [(depth, N1[lang])])}\n\n---\n{Q1[lang]}"
                    jobs.append(gw.chat(p, model=model, max_tokens=60, tag=f"single|{model}|{lang}|{chars}|{depth}"))
                    keys.append(("single", model, lang, chars, depth))
                p = f"{insert(hay, [(0.2, N1[lang]), (0.5, N2[lang]), (0.8, N3[lang])])}\n\n---\n{Q3[lang]}"
                jobs.append(gw.chat(p, model=model, max_tokens=60, tag=f"multi|{model}|{lang}|{chars}"))
                keys.append(("multi", model, lang, chars, None))
    recs = await asyncio.gather(*jobs)
    await gw.close()
    out = []
    for (kind, model, lang, chars, depth), rec in zip(keys, recs):
        a = rec["resp"]["content"]
        if kind == "single":
            ok = bool(re.search(r"\b124\b", a)) and bool(re.search(r"\b118\b", a))
        else:
            ok = bool(re.search(r"\b124\b", a)) and bool(re.search(r"\b4[.,]8\b", a)) and bool(re.search(r"\b8\b", re.sub(r"4[.,]8", "", a)))
        out.append({"kind": kind, "model": model, "lang": lang, "chars": chars, "depth": depth, "ok": ok, "answer": a[:140],
                    "prompt_tokens": (rec["resp"]["usage"] or {}).get("prompt_tokens"), "lat": rec.get("latency_s"),
                    "http": rec.get("http"), "failed": rec.get("api_failed", False)})
    (RESULTS / "e22_longcontext.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("kind    model                       lang  chars    prompt_tok  ok     mean latency (s)")
    for kind in ("single", "multi") if MULTI else ("single",):
        for model in (M70, M8):
            for lang in LANGS:
                for chars in SIZES:
                    r = [x for x in out if x["kind"] == kind and x["model"] == model and x["lang"] == lang and x["chars"] == chars]
                    print(f"{kind:7s} {model:27s} {lang}  {chars:7d}  {r[0]['prompt_tokens']!s:>9s}  {sum(x['ok'] for x in r)}/{len(r)}  "
                          f"{sum(x['lat'] or 0 for x in r) / len(r):6.1f}  http {sorted({x['http'] for x in r})}")


if __name__ == "__main__":
    asyncio.run(main())
