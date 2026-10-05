"""E6 (offline): behaviour of graph.language numeral grounding on edge cases.
Each case: (description, utterance, expected_to_be_flagged_by_a_correct_gate)."""
import json
from common import RESULTS, read_sample
from graph.language import strip_ungrounded_numerals, ungrounded_numerals

pack = read_sample("steuerfuss_linden_de.txt") + read_sample("steuerfuss_linden_fr.txt")
cases = [
 ("grounded integer", "Der Steuerfuss steigt auf 124 %.", False),
 ("Swiss thousands sep", "Bei 80'000 CHF Einkommen sind es 240 CHF.", False),
 ("decimal comma in DE text (std DE)", "Der Kredit beträgt 4,8 Millionen.", False),
 ("typographic apostrophe thousands", "Sparauftrag von 400’000 CHF.", False),
 ("narrow nbsp thousands (fr)", "économies de 400 000 CHF", False),
 ("correct derived: 240/12=20 per month", "Das sind 20 CHF pro Monat.", False),
 ("correct derived: 124-118=6", "Das sind 6 Punkte mehr.", False),
 ("hallucinated percent", "Die Steuern steigen um 15 %.", True),
 ("hallucinated amount", "Die Gemeinde spart 2 Millionen CHF.", True),
 ("substring collision (4 in 124)", "Ich zahle 4 Franken mehr, bei 124 %.", True),
 ("year grounded", "Seit 2019 unverändert.", False),
 ("spelled-out number", "Sechzig Prozent der Haushalte sind betroffen.", True),
]
rows = []
for d, u, should in cases:
    extra = sorted(ungrounded_numerals(u, pack))
    out = strip_ungrounded_numerals(u, pack)
    rows.append({"case": d, "utterance": u, "flagged": bool(extra), "should_flag": should,
                 "ungrounded": extra, "output": out, "correct": bool(extra) == should})
    print(f"{'OK ' if rows[-1]['correct'] else 'BAD'} | {d:38s} | flagged={bool(extra)!s:5} | {out}")
print("correct:", sum(r['correct'] for r in rows), "/", len(rows))
(RESULTS / "e06_numeral_gate.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
