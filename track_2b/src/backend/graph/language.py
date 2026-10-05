"""Language glossaries, fallbacks, translation hop, numeral grounding, Swiss orthography."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# A number with optional Swiss/French thousands separators ('  ’  nbsp, thin nbsp, space)
# and optional decimal part. "80'000" -> one token, "4,8" -> one token.
_NUM = re.compile(r"\d{1,3}(?:['’\u202f\u00a0 ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")
_LIST_INDEX = re.compile(r"(?m)^\s*\d{1,2}[.)]\s")  # "1. " numbering in booklets is not a figure
_FIGURE_UNIT = re.compile(
    r"^\s*(%|‰|chf|fr\.|franken|francs?|millionen|million|mio|prozent|pour\s*cent|punkte|points?|rappen|centimes)",
    re.IGNORECASE,
)

GLOSSARY = {
    "de": (
        "Vorlage, Abstimmungsfrage, Erläuterungen, Stimmvolk, Steuerfuss, "
        "Gemeinderat, Rechnung, Budget, Gemeinde, CHF"
    ),
    "fr": (
        "objet, question votée, explications, souverain, taux d'imposition, "
        "conseil communal, comptes, budget, commune, CHF"
    ),
    "en": "policy, town, budget, tax rate, livelihoods, CHF or USD as in the source",
}

TOWN = {"ch": "Linden", "us": "Millfield"}

FALLBACK_UTTERANCE = {
    "de": "Ich will die amtliche Erklärung noch einmal lesen, bevor ich mich festlege.",
    "fr": "Je veux relire l'explication officielle avant de me prononcer.",
    "en": "I want to read the official explanation again before I decide.",
}

NO_VOTE_LINE = {
    "de": " Dieser Bericht gibt keine Abstimmungsempfehlung ab.",
    "fr": " Ce rapport ne recommande pas comment voter.",
    "en": " This report does not recommend how anyone should vote.",
}

LANG_LABEL = {"de": "German", "fr": "French", "en": "English"}


def glossary_for(lang: str) -> str:
    return GLOSSARY.get(lang, GLOSSARY["en"])


def fallback_utterance(lang: str) -> str:
    return FALLBACK_UTTERANCE.get(lang, FALLBACK_UTTERANCE["en"])


def swissify(text: str, lang: str = "de") -> str:
    """Swiss Standard German does not use ß (Apertus' own system prompt says so)."""
    return text.replace("ß", "ss") if lang == "de" and text else text


def swissify_persona(npc: dict[str, Any]) -> dict[str, Any]:
    """Swiss orthography for every free-text persona field of a German-speaking resident."""
    if npc.get("lang") != "de":
        return npc
    for k in ("bio", "persona", "life_story", "expert_reflection", "profession", "category"):
        if isinstance(npc.get(k), str):
            npc[k] = swissify(npc[k])
    for k in ("beliefs", "controversial_ideas", "interested_topics"):
        if isinstance(npc.get(k), list):
            npc[k] = [swissify(x) if isinstance(x, str) else x for x in npc[k]]
    return npc


# ---------------------------------------------------------------------------
# Numeral grounding
# ---------------------------------------------------------------------------

def _canon(token: str) -> str:
    """'80'000' -> '80000', '4,8' -> '4.8', '6.0' -> '6'."""
    t = re.sub(r"['’\u202f\u00a0 ]", "", token).replace(",", ".")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t


_MILLION = re.compile(r"^\s*(millionen|million|mio)", re.IGNORECASE)


def _figures(text: str) -> list[tuple[int, int, str, set[float], str]]:
    """(start, end, canon, comparable values, tail) for each number; '4,8 Millionen' also
    compares as 4'800'000, so both notations ground each other."""
    text = text or ""
    masked = _LIST_INDEX.sub(lambda m: " " * len(m.group(0)), text)  # keep offsets
    out = []
    for m in _NUM.finditer(masked):
        c = _canon(m.group(0))
        v = float(c)
        tail = text[m.end(): m.end() + 14]
        vals = {v, v * 1e6} if _MILLION.match(tail) else {v}
        out.append((m.start(), m.end(), c, vals, tail))
    return out


def numerals(text: str) -> set[str]:
    return {c for _, _, c, _, _ in _figures(text)}


def _needs_grounding(canon: str, tail: str) -> bool:
    """Bare small integers ('2 Personen') are counting words; figures are not."""
    v = float(canon)
    return v > 12 or "." in canon or bool(_FIGURE_UNIT.match(tail)) or bool(_MILLION.match(tail))


def _near(v: float, pool: set[float]) -> bool:
    return any(abs(v - p) <= 1e-6 * max(1.0, abs(p)) for p in pool)


def _classify(utterance: str, pack: str) -> list[tuple[int, int, str, bool]]:
    """(start, end, canon, grounded) for every figure in the utterance that needs grounding."""
    pack_vals: set[float] = set()
    for _, _, _, vals, _ in _figures(pack):
        pack_vals |= vals
    res = []
    for s, e, c, vals, tail in _figures(utterance):
        if not _needs_grounding(c, tail):
            continue
        res.append((s, e, c, any(_near(v, pack_vals) for v in vals)))
    return res


def has_figures(utterance: str, pack: str) -> bool:
    """Does the utterance state any figure (grounded or not) that would need a source?"""
    return bool(_classify(utterance, pack))


def ungrounded_numerals(utterance: str, pack: str) -> set[str]:
    return {c for _, _, c, ok in _classify(utterance, pack) if not ok}


def strip_ungrounded_numerals(utterance: str, pack: str) -> str:
    """Replace only the offending figure spans (never substrings of other numbers).

    ponytail: correct derived arithmetic (240/12 = 20) is still flagged. A one-step
    "derived from two pack figures" allowance was tried (E6) and made the gate worse:
    ~25 pack figures reach almost every small number. Upgrade path: a real calculator tool."""
    out = utterance or ""
    for s, e, _, ok in sorted(_classify(out, pack), reverse=True):
        if not ok:
            out = out[:s] + "[n]" + out[e:]
    return out


async def translate_utterance(
    text: str,
    target_lang: str,
    llm: ChatOpenAI,
) -> str:
    """Separate Apertus call: one language only. Copy numerals exactly."""
    if not (text or "").strip():
        return text
    from graph.llm import invoke_llm_json

    label = LANG_LABEL.get(target_lang, target_lang)
    prompt = (
        f"Translate the utterance into {label} only. Copy every numeral exactly. "
        "Do not add facts. Output ONLY JSON:\n"
        '{"text": "..."}\n\n'
        f"Utterance:\n{text}"
    )
    try:
        data = await invoke_llm_json(prompt, llm=llm, max_tokens=512)
        translated = str(data.get("text", "")).strip()
        return swissify(translated or text, target_lang)
    except Exception as exc:
        logger.warning("translation hop failed: %s", exc)
        return text


def assign_langs(count: int, setting: str) -> list[str]:
    if setting != "ch":
        return ["en"] * count
    return ["de" if i % 2 == 0 else "fr" for i in range(count)]
