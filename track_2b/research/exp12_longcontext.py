"""E12: long-context recall on Swiss civic text (DE/FR), Apertus 1.5 8B/70B.

The pitch says: "262k tokens lets us stuff a booklet section when retrieval is ambiguous"
and "stuffing both full booklets washes out the persona". Neither was measured.
Haystack = distinct official vote titles (DE or FR) from Swissvotes; needle = one Linden sentence.
Question must be answered from the needle (118 -> 124 %). 3 depths x 5 lengths x 2 langs x 2 models.
"""
import asyncio
import csv
import json
import re

from common import M70, M8, RESULTS, Gateway
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "swissvotes_titles_full.csv"
rows = list(csv.DictReader(open(DATA, encoding="utf-8-sig"), delimiter=";"))

NEEDLE = {"de": "Hinweis aus der Gemeinde Linden: Der Steuerfuss der Gemeinde Linden steigt von 118 % auf 124 % der einfachen Steuer.",
          "fr": "Note de la commune de Linden : le taux d'imposition de la commune de Linden passe de 118 % à 124 % de l'impôt simple."}
Q = {"de": "Auf welchen Prozentsatz steigt der Steuerfuss der Gemeinde Linden und von welchem Prozentsatz aus? Antworte kurz mit den beiden Zahlen.",
     "fr": "À quel pourcentage le taux d'imposition de la commune de Linden passe-t-il, et à partir de quel pourcentage ? Réponds brièvement avec les deux chiffres."}


def haystack(lang, n_chars):
    col = "titel_off_d" if lang == "de" else "titel_off_f"
    # cycle through titles with a changing prefix so the text never repeats verbatim
    out, i = [], 0
    while sum(len(x) + 1 for x in out) < n_chars:
        r = rows[i % len(rows)]
        out.append(f"({i + 1}) {r['datum']}: {r[col]} [{r['stichwort']}]")
        i += 1
    return "\n".join(out)[:n_chars]


async def main():
    gw = Gateway("e12_longcontext", concurrency=2)
    jobs, keys = [], []
    for model in (M70, M8):
        for lang in ("de", "fr"):
            for chars in (6_000, 24_000, 60_000, 140_000, 280_000):  # ~ 2k .. 80k tokens; > 72-81k chars the distinct titles are cycled (noted in the paper)
                for depth in (0.1, 0.5, 0.9):
                    hay = haystack(lang, chars)
                    pos = int(len(hay) * depth)
                    pos = hay.rfind("\n", 0, pos) + 1
                    text = hay[:pos] + NEEDLE[lang] + "\n" + hay[pos:]
                    p = f"{text}\n\n---\n{Q[lang]}"
                    jobs.append(gw.chat(p, model=model, max_tokens=60, tag=f"{model}|{lang}|{chars}|{depth}"))
                    keys.append((model, lang, chars, depth))
    recs = await asyncio.gather(*jobs)
    await gw.close()
    out = []
    for (model, lang, chars, depth), rec in zip(keys, recs):
        a = rec["resp"]["content"]
        ok = bool(re.search(r"\b124\b", a)) and bool(re.search(r"\b118\b", a))
        out.append({"model": model, "lang": lang, "chars": chars, "depth": depth, "ok": ok, "answer": a[:120],
                    "prompt_tokens": (rec["resp"]["usage"] or {}).get("prompt_tokens"), "lat": rec.get("latency_s"),
                    "failed": rec.get("api_failed", False)})
    (RESULTS / "e12_longcontext.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'model':18s} lang  prompt_tok   depth .1  .5  .9   latency(s)")
    for model in (M70, M8):
        for lang in ("de", "fr"):
            for chars in (6_000, 24_000, 60_000, 140_000, 280_000):
                r = [x for x in out if x["model"] == model and x["lang"] == lang and x["chars"] == chars]
                print(f"{model:18s} {lang}  {r[0]['prompt_tokens']!s:>9s}   {' '.join('OK ' if x['ok'] else 'xx ' for x in sorted(r, key=lambda x: x['depth']))}  {sum(x['lat'] or 0 for x in r) / len(r):6.1f}")


if __name__ == "__main__":
    asyncio.run(main())
