"""E8: external validity — can Apertus residents reproduce real Swiss federal vote outcomes?

Data: Swissvotes (Univ. Bern), federal votes 2021-03 .. 2026-09 with known results
(downloaded to research/data/swissvotes_dataset.csv). Input to the model is ONLY the
official ballot title + date (+ optionally the Federal Council position). Design follows
Barmettler (2026, arXiv:2606.00048) in spirit (real votes, DE vs FR), but with the
ballot title instead of the full booklet.

Conditions (per vote): language {de, fr} x persona {none, demo, demo+ideology}
x model {70B, 8B}. Metrics computed in analyze_swissvotes.py.
Usage: python research/exp08_swissvotes.py [--limit N] [--n 10]
"""
import argparse
import asyncio
import csv
import json
import random
import re
from datetime import datetime
from pathlib import Path

from common import M70, M8, RESULTS, Gateway

DATA = Path(__file__).resolve().parent / "data" / "swissvotes_2021_2025.csv"
DE_CANTONS = "zh be lu ur sz ow nw gl zg so bs bl sh ar ai sg gr ag tg".split()
FR_CANTONS = "vd ne ge ju".split()


def load_votes(start="2021-03-01", end="2026-12-31"):
    rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig"), delimiter=";"))
    out = []
    for r in rows:
        d = datetime.strptime(r["datum"], "%d.%m.%Y")
        if not (start <= d.strftime("%Y-%m-%d") <= end) or not r["volkja-proz"]:
            continue
        def share(cs):
            xs = [float(r[f"{c}-japroz"]) for c in cs if r.get(f"{c}-japroz")]
            return sum(xs) / len(xs) if xs else None
        out.append({"anr": r["anr"], "date": d.strftime("%Y-%m-%d"), "de": r["titel_off_d"], "fr": r["titel_off_f"],
                    "short_de": r["titel_kurz_d"], "form": r["rechtsform"], "br_pos": r["br-pos"],
                    "yes": float(r["volkja-proz"]), "accepted": float(r["volkja-proz"]) > 50,
                    "yes_de": share(DE_CANTONS), "yes_fr": share(FR_CANTONS)})
    return out


AGE = [("18-34", 0.22), ("35-49", 0.23), ("50-64", 0.25), ("65+", 0.30)]
EDU = {"de": [("obligatorische Schule", .15), ("Berufslehre", .40), ("Hochschule", .45)],
       "fr": [("scolarité obligatoire", .15), ("apprentissage", .40), ("haute école", .45)]}
AREA = {"de": [("Stadt/Agglomeration", .65), ("ländlich", .35)], "fr": [("ville/agglomération", .65), ("rural", .35)]}
SEX = {"de": ["Frau", "Mann"], "fr": ["femme", "homme"]}
REGION = {"de": "Deutschschweiz", "fr": "Suisse romande"}


def pick(rnd, pairs):
    x, acc = rnd.random(), 0
    for v, p in pairs:
        acc += p
        if x <= acc:
            return v
    return pairs[-1][0]


def persona(rnd, lang, ideology):
    age, edu, area, sex = pick(rnd, AGE), pick(rnd, EDU[lang]), pick(rnd, AREA[lang]), rnd.choice(SEX[lang])
    s = (f"{sex}, {age} Jahre, {edu}, {area}, {REGION[lang]}" if lang == "de"
         else f"{sex}, {age} ans, {edu}, {area}, {REGION[lang]}")
    if ideology:
        mu = 4.6 if lang == "fr" else 5.0
        lr = max(0, min(10, round(rnd.gauss(mu, 2.2))))
        s += (f", politische Selbsteinstufung links-rechts {lr} (0 = links, 10 = rechts)" if lang == "de"
              else f", auto-positionnement gauche-droite {lr} (0 = gauche, 10 = droite)")
    return s


def prompt(v, lang, who, with_br):
    br = {"1": "ja", "2": "nein"}.get(v["br_pos"])
    brt = ""
    if with_br and br:
        brt = (f"\nEmpfehlung des Bundesrats: {br.upper()}." if lang == "de"
               else f"\nRecommandation du Conseil fédéral : {'OUI' if br == 'ja' else 'NON'}.")
    if lang == "de":
        who_s = f"Du bist eine stimmberechtigte Person in der Schweiz ({who})." if who else "Du bist eine stimmberechtigte Person in der Schweiz."
        return (f"{who_s}\nAm {v['date']} findet eine eidgenössische Volksabstimmung statt.\nVorlage: «{v['de']}»{brt}\n"
                'Wie stimmst du ab? Antworte nur mit JSON: {"stimme": "ja", "begruendung": "ein kurzer Satz"} '
                'oder {"stimme": "nein", "begruendung": "ein kurzer Satz"}')
    who_s = f"Vous êtes une personne ayant le droit de vote en Suisse ({who})." if who else "Vous êtes une personne ayant le droit de vote en Suisse."
    return (f"{who_s}\nLe {v['date']} a lieu une votation populaire fédérale.\nObjet : « {v['fr']} »{brt}\n"
            'Comment votez-vous ? Répondez uniquement en JSON : {"vote": "oui", "raison": "une courte phrase"} '
            'ou {"vote": "non", "raison": "une courte phrase"}')


def parse_vote(text):
    m = re.search(r'"(?:stimme|vote)"\s*:\s*"(ja|nein|oui|non)', text.lower())
    if not m:
        return None
    return 1 if m.group(1) in ("ja", "oui") else 0


async def main(limit, n):
    votes = load_votes()[: limit or None]
    print("votes", len(votes))
    gw = Gateway("e08_swissvotes", concurrency=4)
    jobs = []

    async def one(v, lang, cond, model, i, with_br=False):
        rnd = random.Random(f"{v['anr']}|{lang}|{cond}|{i}")
        who = None if cond == "none" else persona(rnd, lang, cond == "demo_ideology")
        rec = await gw.chat(prompt(v, lang, who, with_br), model=model, max_tokens=90, json_mode=True,
                            temperature=0.0, tag=f"{v['anr']}|{lang}|{cond}|{model}|{i}|br{int(with_br)}")
        return {"anr": v["anr"], "lang": lang, "cond": cond, "model": model, "i": i, "br": with_br,
                "vote": parse_vote(rec["resp"]["content"]), "raw": rec["resp"]["content"][:160],
                "failed": rec.get("api_failed", False)}

    for v in votes:
        for lang in ("de", "fr"):
            for model in (M70, M8):
                jobs.append(one(v, lang, "none", model, 0))
                jobs.append(one(v, lang, "none", model, 0, with_br=True))
                for i in range(n):
                    jobs.append(one(v, lang, "demo", model, i))
            for i in range(n):
                jobs.append(one(v, lang, "demo_ideology", M70, i))
    print("calls", len(jobs))
    res = await asyncio.gather(*jobs)
    await gw.close()
    (RESULTS / "e08_swissvotes_results.json").write_text(json.dumps({"votes": votes, "results": res}, ensure_ascii=False), encoding="utf-8")
    print("done; unparsed:", sum(r["vote"] is None for r in res), "api_failed:", sum(r["failed"] for r in res))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--n", type=int, default=10)
    a = ap.parse_args()
    asyncio.run(main(a.limit, a.n))
