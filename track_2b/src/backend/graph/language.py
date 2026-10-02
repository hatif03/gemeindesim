"""Language glossaries, fallbacks, translation hop, numeral grounding."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

_NUM = re.compile(r"\d+(?:[.,]\d+)?")

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

LANG_LABEL = {"de": "German", "fr": "French", "en": "English"}


def glossary_for(lang: str) -> str:
    return GLOSSARY.get(lang, GLOSSARY["en"])


def fallback_utterance(lang: str) -> str:
    return FALLBACK_UTTERANCE.get(lang, FALLBACK_UTTERANCE["en"])


def numerals(text: str) -> set[str]:
    return set(_NUM.findall(text or ""))


def ungrounded_numerals(utterance: str, pack: str) -> set[str]:
    return numerals(utterance) - numerals(pack)


def strip_ungrounded_numerals(utterance: str, pack: str) -> str:
    extra = ungrounded_numerals(utterance, pack)
    if not extra:
        return utterance
    out = utterance
    for n in sorted(extra, key=len, reverse=True):
        out = out.replace(n, "[n]")
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
        return translated or text
    except Exception as exc:
        logger.warning("translation hop failed: %s", exc)
        return text


def assign_langs(count: int, setting: str) -> list[str]:
    if setting != "ch":
        return ["en"] * count
    langs: list[str] = []
    for i in range(count):
        langs.append("de" if i % 2 == 0 else "fr")
    # Prefer a balanced mix when count is odd (one extra de).
    return langs
