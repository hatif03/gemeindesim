"""Explicit, code-owned stance on the question.

Why (docs/research, E3/E11, literature): without a stance variable the simulation had nothing to
measure about the Vorlage, `political_leaning` was a random left-right number unrelated to it, and
the report had to invent an outcome. And when Apertus is asked directly for a stance it says "yes"
for every resident, whatever the persona (E11: 15/15, also with no persona at all).

So the split is: Apertus judges *impact on this household* and writes the best argument for and
against, in the resident's language; the stance itself is computed in code from impact, the
measure's ideological valence and the resident's leaning. Afterwards only the Python opinion
dynamics move it (Chuang et al. 2024: LLM-only opinion updates drift to consensus).
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
from collections import Counter
from typing import Any

from graph.calculator import household_amount
from graph.corpus import chunk_policy_document, format_passages, retrieve_passages
from graph.llm import invoke_llm_structured
from graph.utils import clamp
from models.schemas import ImpactResponse

logger = logging.getLogger(__name__)

# Knobs, not calibrated constants:
#   stance = valence*leaning (ideology) + 0.5*impact (LLM-judged benefit) - 0.6*burden (computed cost) + noise.
# E8/E11/E11c: asked directly, Apertus says "yes" for (almost) every resident, so the sign cannot come
# from the model; the cost term is deterministic (calculator), the impact term is the model's judgement.
W_IDEOLOGY, W_IMPACT, W_BURDEN, NOISE_SD = 1.0, 0.5, 0.6, 0.15
BURDEN_SCALE_CHF = 500.0  # extra yearly tax at which the burden term saturates
_IMPACT = {"benefit": 1.0, "mixed": 0.0, "none": 0.0, "harm": -1.0}

_PROMPT = {
    "de": (
        "Du bist {name}, {profession} in {town}. Einkommen: {income}.\n{bio}\nÜberzeugungen: {beliefs}\n\n"
        "Amtliche Passagen zur Abstimmung (nur diese Zahlen sind verbindlich):\n{pack}\n\n"
        "Wie wirkt sich die Vorlage auf deinen Haushalt oder Betrieb aus? impact: \"benefit\" (Vorteil), "
        "\"harm\" (Nachteil), \"mixed\" (beides) oder \"none\" (keine Wirkung). "
        "support_reason: das stärkste Argument FÜR die Vorlage aus deiner Lage (ein Satz, Deutsch). "
        "oppose_reason: das stärkste Argument DAGEGEN aus deiner Lage (ein Satz, Deutsch)."
    ),
    "fr": (
        "Tu es {name}, {profession} à {town}. Revenu : {income}.\n{bio}\nConvictions : {beliefs}\n\n"
        "Passages officiels sur l'objet (seuls ces chiffres font foi) :\n{pack}\n\n"
        "Quel effet l'objet a-t-il sur ton ménage ou ton entreprise ? impact : \"benefit\" (avantage), "
        "\"harm\" (désavantage), \"mixed\" (les deux) ou \"none\" (aucun). "
        "support_reason : le meilleur argument POUR l'objet depuis ta situation (une phrase, français). "
        "oppose_reason : le meilleur argument CONTRE depuis ta situation (une phrase, français)."
    ),
    "en": (
        "You are {name}, {profession} in {town}. Income: {income}.\n{bio}\nBeliefs: {beliefs}\n\n"
        "Official passages about the measure (only these figures are binding):\n{pack}\n\n"
        "How does the measure affect your household or business? impact: \"benefit\", \"harm\", \"mixed\" "
        "or \"none\". support_reason: the strongest argument FOR the measure from your situation (one "
        "sentence). oppose_reason: the strongest argument AGAINST it from your situation (one sentence)."
    ),
}


def stance_label(x: float) -> str:
    return "for" if x > 0.15 else "against" if x < -0.15 else "undecided"


def stance_line(npc: dict[str, Any]) -> str:
    x = float(npc.get("stance", 0.0))
    reason = (npc.get("stance_reason") or "").strip()
    base = f"{stance_label(x)} ({x:+.2f}; -1 = firmly against, +1 = firmly for)"
    return f"{base}. Your reason: {reason}" if reason else base


_HOW = {
    "for": "you SUPPORT the measure and make the case for it in every line "
           "(you may acknowledge a concern, but you never argue against it)",
    "against": "you OPPOSE the measure and make the case against it in every line",
    "undecided": "you are torn and say so openly, weighing both sides",
}


def stance_binding(npc: dict[str, Any]) -> str:
    """Last paragraph of the resident prompt that ties SPEECH to the code-owned stance.

    Research E14/E15: the stance line alone controlled speech only for opponents (residents held 'for'
    sounded for just 17-42 % of the time); a binding reminder at the END of the prompt raised agreement
    from ~50 % to ~84 % on both sizes with no loss of event diversity. Undecided residents did not improve."""
    x = float(npc.get("stance", 0.0))
    label = stance_label(x)
    reason = (npc.get("stance_reason") or "").strip()
    carry = f" The argument you carry: {reason}" if reason else ""
    return f"REMINDER before you answer: Your position on the question: {label} ({x:+.2f}). In everything you say, {_HOW[label]}.{carry}"


def stance_prior(
    valence: float, leaning: float, impact: str, burden: float = 0.0, rng: random.Random | None = None
) -> float:
    """Initial stance in [-1, 1] from ideology alignment, judged impact, computed burden and noise."""
    noise = (rng or random).gauss(0.0, NOISE_SD)
    s = W_IDEOLOGY * valence * leaning + W_IMPACT * _IMPACT.get(impact, 0.0) - W_BURDEN * burden + noise
    return round(clamp(s, -1.0, 1.0), 3)


async def elicit_impact(npc: dict[str, Any], chunks: list[dict[str, Any]], town: str, llm: Any) -> ImpactResponse:
    lang = npc.get("lang", "en") if npc.get("lang") in _PROMPT else "en"
    query = f"{npc.get('profession', '')} {npc.get('bio', '')[:300]} {' '.join(npc.get('beliefs', []))}"
    pack = format_passages(retrieve_passages(chunks, query, top_k=3, lang=lang))
    prompt = _PROMPT[lang].format(
        name=npc.get("name", ""), profession=npc.get("profession", ""), town=town,
        income=npc.get("income_level", "medium"), bio=npc.get("bio", ""),
        beliefs="; ".join(npc.get("beliefs", [])), pack=pack,
    )
    try:
        return await invoke_llm_structured(prompt, ImpactResponse, max_tokens=400, llm=llm)
    except Exception as exc:  # a failed elicitation must not stop the town
        logger.warning("impact elicitation failed for %s: %s", npc.get("id"), exc)
        return ImpactResponse(impact="mixed", support_reason="", oppose_reason="")


async def elicit_stances(
    npcs: list[dict[str, Any]], policy_text: str, town: str, llm: Any, valence: float = 0.0
) -> None:
    """Fill ``stance`` / ``stance_reason`` / ``impact`` on every npc dict (concurrent, bounded)."""
    chunks = chunk_policy_document(policy_text)
    corpus = "\n".join(c.get("text", "") for c in chunks)
    impacts = await asyncio.gather(*[elicit_impact(n, chunks, town, llm) for n in npcs])
    for n, r in zip(npcs, impacts):
        amount = household_amount(corpus, n.get("income_level", "medium"))
        burden = min(1.0, amount / BURDEN_SCALE_CHF) if amount is not None else 0.0
        s = stance_prior(valence, float(n.get("political_leaning", 0.0)), r.impact, burden)
        n["stance"] = s
        n["impact"] = r.impact
        if s > 0.15:
            n["stance_reason"] = r.support_reason.strip()
        elif s < -0.15:
            n["stance_reason"] = r.oppose_reason.strip()
        else:
            n["stance_reason"] = f"{r.support_reason.strip()} / {r.oppose_reason.strip()}".strip(" /")


def stance_summary(npcs: list[dict[str, Any]]) -> dict[str, Any]:
    """Tally used by the dashboard, the report prompt and the paper's homogenisation metrics."""
    xs = [float(n.get("stance", 0.0)) for n in npcs]
    n = len(xs) or 1
    labels = Counter(stance_label(x) for x in xs)
    mean = sum(xs) / n
    probs = [c / n for c in labels.values() if c]
    return {
        "for": labels.get("for", 0), "against": labels.get("against", 0), "undecided": labels.get("undecided", 0),
        "mean": round(mean, 3),
        "spread": round(math.sqrt(sum((x - mean) ** 2 for x in xs) / n), 3),
        "entropy_bits": round(-sum(p * math.log2(p) for p in probs), 3),
        "n": len(xs),
    }
