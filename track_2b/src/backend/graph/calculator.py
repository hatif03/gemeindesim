"""Deterministic household-impact calculator (the "calculator" the docs always promised).

Research E7: Apertus 1.5 gets the corpus' own arithmetic wrong (4'000 CHF x 6 % -> 280 on the
70B, 360 / 72 on the 8B; correct 240) and defines "Steuerfuss" incorrectly without the corpus.
So the figure a resident quotes about their own household is computed here and handed to the
model as a fact (and added to the numeral-grounding pack).

Scope (ponytail): one pattern, the Swiss Steuerfuss vote ("118 % -> 124 %" plus a worked example
"80'000 CHF ... 240 CHF mehr"). Other situations return None and the resident simply has no
personal figure. Add patterns, not a framework, when a second booklet needs one.
"""

from __future__ import annotations

import re

_NUM = r"(\d[\d'’\u202f\u00a0 ]*\d|\d)(?:[.,](\d+))?"
_RATE_CHANGE = re.compile(rf"(\d{{2,3}}(?:[.,]\d+)?)\s*%\s*(?:auf|à|to)\s*(\d{{2,3}}(?:[.,]\d+)?)\s*%")
_EXAMPLE = re.compile(
    rf"(?:Einkommen|revenu imposable)[^.]{{0,40}}?{_NUM}\s*CHF[^.]{{0,60}}?{_NUM}\s*CHF\s*(?:mehr|de plus)",
    re.IGNORECASE,
)
# Illustrative scaling of the booklet's worked example (taxable income 80'000 CHF) to income bands.
# Assumption, not data: tax is treated as proportional to income. Stated to the resident as an estimate.
INCOME_FACTOR = {"low": 0.6, "medium": 1.0, "high": 1.8}

_LINE = {
    "de": "Berechnete Zahl für deinen Haushalt (Schätzung, hochgerechnet vom Beispiel in der Vorlage): "
          "etwa {amount} CHF mehr Steuern pro Jahr bei Annahme.",
    "fr": "Chiffre calculé pour ton ménage (estimation à partir de l'exemple de l'objet) : "
          "environ {amount} CHF d'impôt en plus par an en cas d'acceptation.",
    "en": "Computed figure for your household (estimate scaled from the worked example): "
          "about {amount} CHF more tax per year if accepted.",
}


def _f(whole: str, frac: str | None) -> float:
    return float(re.sub(r"['’\u202f\u00a0 ]", "", whole) + ("." + frac if frac else ""))


def household_amount(policy_text: str, income_level: str) -> int | None:
    """Extra yearly tax in CHF for this income band, or None if the text has no worked example."""
    rate = _RATE_CHANGE.search(policy_text or "")
    ex = _EXAMPLE.search(policy_text or "")
    if not rate or not ex:
        return None
    old, new = (float(x.replace(",", ".")) for x in rate.groups())
    if new == old:
        return None
    return round(_f(ex.group(3), ex.group(4)) * INCOME_FACTOR.get(income_level, 1.0))


def household_line(policy_text: str, income_level: str, lang: str) -> str | None:
    """One sentence with the resident's extra yearly tax, or None if the text has no such example."""
    amount = household_amount(policy_text, income_level)
    if amount is None:
        return None
    return _LINE.get(lang, _LINE["en"]).format(amount=f"{amount:,}".replace(",", "'"))
