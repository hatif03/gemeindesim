"""E11c: is the unanimous 'yes' of E11 a property of the model, or of a one-sided corpus?

Same 15 residents, same elicitation as E11, two corpora: the original council-only text and a balanced
variant that adds the referendum committee's counter-arguments (as real Swiss booklets do).
Persona conditions: full persona and no persona. T=0 plus two T=0.7 draws for the full persona.
Usage: python research/exp11c_balanced_corpus.py base70_s1 base70_s2 base70_s3
"""
import asyncio
import json
import math
import re
import sys
from collections import Counter

from common import M70, RESULTS, Gateway, read_sample

CORP = {
    "original": {"de": read_sample("steuerfuss_linden_de.txt"), "fr": read_sample("steuerfuss_linden_fr.txt")},
    "balanced": {"de": read_sample("steuerfuss_linden_balanced_de.txt"), "fr": read_sample("steuerfuss_linden_balanced_fr.txt")},
}
LEAN = lambda x: ("stark progressiv" if x <= -0.6 else "eher progressiv" if x <= -0.2 else "moderat/zentristisch" if x <= 0.2 else "eher konservativ" if x <= 0.6 else "stark konservativ")


def prompt(n, corpus, persona):
    lang = n["lang"] if n["lang"] in ("de", "fr") else "de"
    head = ""
    if persona:
        head = (f"Du bist {n['name']}, {n['profession']} in Linden. Einkommen: {n['income_level']}.\n{n.get('bio','')}\n"
                f"Überzeugungen: {', '.join(n.get('beliefs', []))}\nPolitische Haltung: {LEAN(n.get('political_leaning', 0))}.\n")
        if lang == "fr":
            head = (f"Tu es {n['name']}, {n['profession']} à Linden. Revenu : {n['income_level']}.\n{n.get('bio','')}\n"
                    f"Convictions : {', '.join(n.get('beliefs', []))}\n")
    text = CORP[corpus][lang]
    if lang == "fr":
        return (f"{head}\nTu habites à Linden et tu votes sur l'objet suivant.\n{text}\n"
                'Comment votes-tu ? Réponds uniquement en JSON : {"stance": "yes" | "no" | "undecided", "certainty": 0.0-1.0, "reason": "une phrase"}')
    return (f"{head}\nDu wohnst in Linden und stimmst über die folgende Vorlage ab.\n{text}\n"
            'Wie stimmst du? Antworte nur mit JSON: {"stance": "yes" | "no" | "undecided", "certainty": 0.0-1.0, "reason": "ein Satz"}')


def entropy(c):
    t = sum(c.values())
    return -sum(v / t * math.log2(v / t) for v in c.values() if v) if t else 0.0


async def main(tags):
    gw = Gateway("e11c_balanced", concurrency=3)
    npcs = []
    for t in tags:
        npcs += [dict(n, src=t) for n in json.loads((RESULTS / "sims" / f"{t}.json").read_text(encoding="utf-8"))["npcs0"]]

    async def one(n, corpus, persona, temp, k):
        rec = await gw.chat(prompt(n, corpus, persona), model=M70, temperature=temp, max_tokens=150, json_mode=True,
                            tag=f"{n['src']}|{n['id']}|{corpus}|{persona}|{k}")
        m = re.search(r'"stance"\s*:\s*"(yes|no|undecided)"', rec["resp"]["content"])
        return {"src": n["src"], "id": n["id"], "role": n["role"], "income": n["income_level"], "lang": n["lang"], "corpus": corpus,
                "persona": persona, "k": k, "stance": m.group(1) if m else None, "reason": rec["resp"]["content"][-160:]}

    jobs = [one(n, c, p, 0.0, 0) for n in npcs for c in CORP for p in (True, False)]
    jobs += [one(n, c, True, 0.7, k) for n in npcs for c in CORP for k in (1, 2)]
    res = await asyncio.gather(*jobs)
    await gw.close()
    (RESULTS / "e11c_balanced.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for corpus in CORP:
        for persona in (True, False):
            r = [x for x in res if x["corpus"] == corpus and x["persona"] == persona and x["k"] == 0]
            c = Counter(x["stance"] for x in r)
            print(f"{corpus:9s} persona={persona!s:5} n={len(r)} {dict(c)} entropy={entropy(c):.2f} bits")
        r = [x for x in res if x["corpus"] == corpus and x["persona"] and x["k"] > 0]
        print(f"{corpus:9s} persona=True T=0.7 draws: {dict(Counter(x['stance'] for x in r))}")
    for corpus in CORP:
        for cond in ("income", "lang"):
            print(corpus, "by", cond, {v: dict(Counter(x['stance'] for x in res if x['corpus'] == corpus and x['persona'] and x['k'] == 0 and x[cond] == v)) for v in sorted({x[cond] for x in res})})


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
