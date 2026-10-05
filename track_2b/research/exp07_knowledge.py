"""E7: Swiss civic knowledge + Swiss orthography of Apertus 1.5 (8B/70B), DE/FR.

Why: the app deliberately keeps facts in the corpus because 'factual recall is mid-pack'
(docs). That claim was never measured on the Swiss civic facts the residents rely on.
Rubric = regex on gold facts (we know the gold; checked by hand afterwards, see notebook).
"""
import asyncio
import json
import re

from common import M70, M8, RESULTS, Gateway

Q = [  # (id, lang, question, must_match_all, must_not_match, gold note)
 ("steuerfuss_def", "de", "Was bedeutet der Begriff «Steuerfuss» in einer Schweizer Gemeinde? Antworte in 2 Sätzen.",
  [r"einfach\w* (Staats)?steuer|Steuereinheit|Grundsteuer|Multiplik|Faktor|Vielfach"], [], "Steuerfuss = Prozentsatz/Multiplikator auf die einfache (Staats-)Steuer"),
 ("steuerfuss_def_fr", "fr", "Que signifie le « taux d'imposition » (quotité) communal en Suisse ? Réponds en 2 phrases.",
  [r"imp[oô]t (cantonal )?simple|coefficient|multipli|quotit|centimes|base"], [], "multiplicateur appliqué à l'impôt de base/simple"),
 ("doppelmehr", "de", "Was braucht es für die Annahme einer eidgenössischen Volksinitiative? Antworte in einem Satz.",
  [r"(Volk|Stimm)\w*.*(Kanton|Stände)|Ständemehr|doppelte"], [], "Volks- und Ständemehr"),
 ("unterschriften_init", "de", "Wie viele Unterschriften braucht eine eidgenössische Volksinitiative und in welcher Frist? Nur die Zahlen.",
  [r"100\W?000", r"18 Monat"], [], "100'000 in 18 Monaten"),
 ("unterschriften_ref", "de", "Wie viele Unterschriften braucht ein fakultatives Referendum gegen ein Bundesgesetz und in welcher Frist?",
  [r"50\W?000", r"100 Tage"], [], "50'000 in 100 Tagen"),
 ("unterschriften_ref_fr", "fr", "Combien de signatures faut-il pour un référendum facultatif fédéral et dans quel délai ?",
  [r"50\W?000", r"100 jours"], [], "50 000 en 100 jours"),
 ("gemeindeversammlung", "de", "Wie unterscheiden sich Gemeindeversammlung und Gemeindeparlament in der Schweiz? Antworte in 2 Sätzen.",
  [r"Versammlung.*(alle|Stimmberechtigt|direkt)|(alle|Stimmberechtigt).*Versammlung", r"Parlament.*(gewählt|Vertreter)|(gewählt|Vertreter).*Parlament"], [], "GV: alle Stimmberechtigten; Parlament: gewählte Vertretung"),
 ("sprachregion_ju", "de", "In welcher Sprachregion liegt der Kanton Jura? Ein Wort.", [r"franz|Romandie|Westschweiz"], [], "französisch"),
 ("roestigraben", "de", "Was ist der «Röstigraben»? Ein Satz.", [r"(Deutsch|Franz).*(Franz|Deutsch)|Sprachgrenze|Westschweiz|Romandie"], [], "Kluft Deutschschweiz/Romandie"),
 ("bundesrat_n", "de", "Wie viele Mitglieder hat der Schweizer Bundesrat? Nur die Zahl.", [r"\b7\b|sieben"], [], "7"),
 ("rechnung_240", "de", "Der Steuerfuss einer Gemeinde steigt von 118 % auf 124 % der einfachen Steuer. Die einfache Steuer einer Person beträgt 4'000 CHF. Wie viel zahlt sie mehr pro Jahr? Nur die Zahl in CHF.",
  [r"\b240\b"], [], "4000 * 0.06 = 240"),
 ("rechnung_240_fr", "fr", "Le taux d'imposition passe de 118 % à 124 % de l'impôt simple. L'impôt simple d'une personne est de 4'000 CHF. Combien paie-t-elle de plus par an ? Seulement le chiffre en CHF.",
  [r"\b240\b"], [], "240"),
 ("rechnung_monat", "de", "Eine Steuererhöhung kostet eine Person 240 CHF pro Jahr. Wie viel pro Monat? Nur die Zahl.", [r"\b20\b"], [], "20"),
 ("budget_defizit", "de", "Eine Gemeinde hat ein Defizit von 1.2 Millionen CHF und schlägt eine Steuererhöhung vor, die 6 Prozentpunkte beträgt. Kann ich aus diesen zwei Angaben berechnen, ob die Erhöhung das Defizit deckt? Antworte mit Ja oder Nein und begründe in einem Satz.",
  [r"\bNein\b"], [], "Nein: Steuerertrag der Gemeinde fehlt (einfache Steuer total)"),
 ("hallu_nonexist", "de", "Was steht in Artikel 47 des Steuergesetzes der fiktiven Gemeinde Linden? Wenn du es nicht weisst, sage das.", [r"nicht|kein|fiktiv|weiss|weiß|keine Information|keinen Zugriff"], [], "should abstain"),
]
ORTHO = ["Schreibe 3 Sätze über die Reparatur der Strasse vor dem Schulhaus. Schweizer Rechtschreibung.",
         "Schreibe 3 Sätze darüber, dass die Gemeinde die Steuern erhöhen will und der Bürger sich darüber ärgert.",
         "Schreibe 3 Sätze über Maßnahmen zur Entlastung der Haushalte und über grosse Ausgaben der Gemeinde.",
         "Ein Ladenbesitzer an der Dorfstrasse spricht mit der Nachbarin über die Abstimmung. Schreibe seinen Dialog in 3 Sätzen auf Deutsch."]


async def main():
    gw = Gateway("e07_knowledge", concurrency=3)
    res = []

    async def q(model, item):
        qid, lang, text, must, mustnot, gold = item
        rec = await gw.chat(text, model=model, max_tokens=250, tag=f"{qid}|{model}")
        c = rec["resp"]["content"]
        ok = all(re.search(p, c, re.I | re.S) for p in must) and not any(re.search(p, c, re.I) for p in mustnot)
        return {"id": qid, "model": model, "ok": ok, "gold": gold, "answer": c.strip()[:300]}

    async def o(model, text, i):
        out = []
        for rep in range(3):
            rec = await gw.chat(text, model=model, temperature=0.7, max_tokens=250, tag=f"ortho|{model}|{i}")
            out.append(rec["resp"]["content"])
        return {"model": model, "prompt": text, "eszett": sum(t.count("ß") for t in out), "chars": sum(len(t) for t in out), "texts": out}

    res = await asyncio.gather(*[q(m, it) for m in (M70, M8) for it in Q])
    ortho = await asyncio.gather(*[o(m, t, i) for m in (M70, M8) for i, t in enumerate(ORTHO)])
    await gw.close()
    (RESULTS / "e07_knowledge.json").write_text(json.dumps({"qa": res, "ortho": ortho}, ensure_ascii=False, indent=1), encoding="utf-8")
    for m in (M70, M8):
        r = [x for x in res if x["model"] == m]
        print(m, f"{sum(x['ok'] for x in r)}/{len(r)} pass;", "fails:", [x["id"] for x in r if not x["ok"]])
        oo = [x for x in ortho if x["model"] == m]
        print("   ß per 1000 chars:", round(1000 * sum(x["eszett"] for x in oo) / sum(x["chars"] for x in oo), 2),
              "ß total", sum(x["eszett"] for x in oo))


if __name__ == "__main__":
    asyncio.run(main())
