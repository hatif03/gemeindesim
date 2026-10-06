from __future__ import annotations

import json
import logging
import re
from collections import Counter
from typing import Any

from graph.language import LANG_LABEL, NO_VOTE_LINE, swissify
from config import LLM_VOICE_NAME
from graph.llm import get_llm, invoke_llm_structured
from graph.prompts import ECONOMIC_REPORT_PROMPT
from models.schemas import (
    BarChartData,
    BarChartEntry,
    ChartSlice,
    EconomicReportNarrative,
    EconomicReportResponse,
    PieChartData,
    ReportImpact,
    ReportStat,
)

logger = logging.getLogger(__name__)

LAYOFF_RE = re.compile(
    r"layoff|fired|let\s+go|cut.*jobs|furlough|entlass|kündig|stellenabbau|licenci|suppression d.emplois",
    re.IGNORECASE,
)
CLOSURE_RE = re.compile(
    r"clos(e|ing|ed)|shut.*down|going out of business|bankrupt|schliess|geschlossen|aufgeben|konkurs|"
    r"ferm(e|er|eture|ée|é)\b|faillite",
    re.IGNORECASE,
)
# Vote advice and *asserted outcomes* are both removed at sentence level (the old regex
# substitution left ", ." fragments and did not cover outcomes at all: research E9).
_VOTE_ADVICE = re.compile(
    r"(?i)(vote\s+(yes|no)|should vote|stimm\w*\s+(sie\s+)?(mit\s+)?(ja|nein)|empfehl\w+|recommande[rz]?\s+de\s+voter|"
    r"votez\s+(oui|non)|je (vous )?conseille|ich (rate|empfehle)|sollten?\s+(sie\s+)?(ja|nein|zustimmen|ablehnen)|doit voter|"
    r"conseille de (voter|rejeter|accepter))"
)
# An asserted result: an outcome word in a sentence that is not conditional ("würde", "if approved").
_OUTCOME_WORD = re.compile(
    r"(?i)\b(angenommen|abgelehnt|bewilligt\w*|genehmigt\w*|verabschiedet|verhinderte|"
    r"accepté\w*|rejeté\w*|adopté\w*|approuvé\w*|approved|rejected|adopted|passed|passes|pass)\b"
)
_CONDITIONAL = re.compile(
    r"(?i)\b(würde\w*|wenn|falls|bei annahme|im falle|könnte\w*|would|could|if|should it|serait|pourrait|si|en cas)\b"
)
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
MOOD_ORDER = [
    "angry",
    "anxious",
    "worried",
    "skeptical",
    "neutral",
    "determined",
    "hopeful",
    "excited",
]
STRAIN_MOODS = {"angry", "anxious", "worried", "skeptical"}
POSITIVE_MOODS = {"hopeful", "excited", "determined"}


def _strip_vote_advice(text: str) -> str:
    """Drop whole sentences that advise a vote or assert the vote's result."""
    sentences = _SENT_SPLIT.split(" ".join((text or "").split()))
    return " ".join(x for x in sentences if not (_VOTE_ADVICE.search(x) or _asserts_outcome(x)))


def _asserts_outcome(sentence: str) -> bool:
    return bool(_OUTCOME_WORD.search(sentence)) and not _CONDITIONAL.search(sentence)


def _title_case_mood(mood: str) -> str:
    return mood.replace("_", " ").title()


def _truncate(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3].rstrip()}..."


def _percentage(part: int, whole: int) -> str:
    if whole <= 0:
        return "0%"
    return f"{round((part / whole) * 100)}%"


def _dominant_mood(mood_counts: Counter[str]) -> tuple[str, int]:
    if not mood_counts:
        return "neutral", 0
    return max(
        mood_counts.items(),
        key=lambda item: (item[1], -MOOD_ORDER.index(item[0]) if item[0] in MOOD_ORDER else 0),
    )


def _sorted_mood_items(mood_counts: Counter[str]) -> list[tuple[str, int]]:
    return sorted(
        mood_counts.items(),
        key=lambda item: (-item[1], MOOD_ORDER.index(item[0]) if item[0] in MOOD_ORDER else len(MOOD_ORDER)),
    )


def _build_key_stats(
    *,
    num_npcs: int,
    completed_rounds: int,
    mood_counts: Counter[str],
    price_change_count: int,
    protest_count: int,
    layoff_mentions: int,
    closure_mentions: int,
) -> list[ReportStat]:
    dominant_mood, dominant_count = _dominant_mood(mood_counts)
    strain_count = sum(count for mood, count in mood_counts.items() if mood in STRAIN_MOODS)
    positive_count = sum(count for mood, count in mood_counts.items() if mood in POSITIVE_MOODS)

    return [
        ReportStat(label="Rounds Simulated", value=str(completed_rounds), trend="flat"),
        ReportStat(label="Residents Tracked", value=str(num_npcs), trend="flat"),
        ReportStat(
            label="Dominant Mood",
            value=f"{_title_case_mood(dominant_mood)} ({_percentage(dominant_count, num_npcs)})",
            trend="mixed",
        ),
        ReportStat(
            label="Residents Under Strain",
            value=_percentage(strain_count, num_npcs),
            trend="up" if strain_count else "flat",
        ),
        ReportStat(
            label="Residents Feeling Positive",
            value=_percentage(positive_count, num_npcs),
            trend="up" if positive_count else "flat",
        ),
        ReportStat(
            label="Price Change Events",
            value=str(price_change_count),
            trend="up" if price_change_count else "flat",
        ),
        ReportStat(
            label="Protests Logged",
            value=str(protest_count),
            trend="up" if protest_count else "flat",
        ),
        ReportStat(
            label="Layoff / Closure Signals",
            value=str(layoff_mentions + closure_mentions),
            trend="up" if (layoff_mentions + closure_mentions) else "flat",
        ),
    ]


def _build_pie_chart(mood_counts: Counter[str]) -> PieChartData:
    slices = [
        ChartSlice(label=_title_case_mood(mood), value=count)
        for mood, count in _sorted_mood_items(mood_counts)
        if count > 0
    ]
    if not slices:
        slices = [ChartSlice(label="Neutral", value=0)]
    return PieChartData(title="Final Town Sentiment", slices=slices)


def _build_bar_chart(
    *,
    price_change_count: int,
    protest_count: int,
    mood_shift_count: int,
    layoff_mentions: int,
    closure_mentions: int,
) -> BarChartData:
    bars = [
        BarChartEntry(label="Price Changes", value=price_change_count),
        BarChartEntry(label="Protests", value=protest_count),
        BarChartEntry(label="Mood Shifts", value=mood_shift_count),
        BarChartEntry(label="Layoff Signals", value=layoff_mentions),
        BarChartEntry(label="Closure Signals", value=closure_mentions),
    ]
    bars = sorted(bars, key=lambda bar: (-bar.value, bar.label))[:4]
    if all(bar.value == 0 for bar in bars):
        bars = [BarChartEntry(label="No Major Shock Signals", value=0)]
    return BarChartData(title="Pressure Signals During The Run", bars=bars)


def _fallback_narrative(
    *,
    completed_rounds: int,
    entities: list[dict[str, Any]],
    mood_counts: Counter[str],
    notable_events: list[str],
    num_npcs: int,
    protest_count: int,
    price_change_count: int,
    layoff_mentions: int,
    closure_mentions: int,
) -> EconomicReportNarrative:
    dominant_mood, dominant_count = _dominant_mood(mood_counts)
    impacts = entities[0].get("economic_impacts", []) if entities else []
    top_impacts: list[ReportImpact] = []

    for impact in impacts[:3]:
        desc = impact if isinstance(impact, str) else impact.get("description", "Economic ripple")
        top_impacts.append(
            ReportImpact(
                title=_truncate(desc, 48),
                description=desc or "Simulation highlighted a meaningful downstream effect.",
                direction="mixed" if isinstance(impact, str) else impact.get("direction", "mixed"),
                severity="medium" if isinstance(impact, str) else impact.get("magnitude", "medium"),
            )
        )

    if protest_count or layoff_mentions or closure_mentions:
        top_impacts.append(
            ReportImpact(
                title="Social strain surfaced in public",
                description=(
                    f"The run logged {protest_count} protest events and "
                    f"{layoff_mentions + closure_mentions} layoff or closure signals, showing that "
                    "economic stress spilled into visible public reaction."
                ),
                direction="negative",
                severity="high" if (protest_count + layoff_mentions + closure_mentions) >= 4 else "medium",
            )
        )

    if price_change_count:
        top_impacts.append(
            ReportImpact(
                title="Prices adjusted across town",
                description=(
                    f"Businesses reacted with {price_change_count} price change events, suggesting the policy "
                    "quickly affected household purchasing pressure."
                ),
                direction="mixed",
                severity="medium",
            )
        )

    if not top_impacts:
        top_impacts.append(
            ReportImpact(
                title="Mixed local fallout",
                description="The simulation showed a blend of economic opportunity and pressure, with uneven effects across residents.",
                direction="mixed",
                severity="medium",
            )
        )

    summary = (
        f"After {completed_rounds} rounds with {num_npcs} residents, the town ended in a mostly "
        f"{dominant_mood} mood, with {_percentage(dominant_count, num_npcs)} of residents in that camp. "
        f"The run logged {price_change_count} price change events and {protest_count} protests, indicating that "
        "economic ripple effects were visible in both household budgets and public reaction."
    )
    livelihood_impact = (
        "Residents' day-to-day lives were shaped by how quickly the policy translated into prices, job security, "
        "and business confidence. The strongest livelihood effects appeared where economic pressure became concrete "
        "enough to trigger cost adjustments, layoff fears, or collective protest."
    )

    return EconomicReportNarrative(
        headline=f"Town Ends The Simulation Feeling {_title_case_mood(dominant_mood)}",
        summary=summary,
        livelihood_impact=livelihood_impact,
        top_impacts=top_impacts[:4],
        notable_events=notable_events[:4],
    )


async def generate_economic_report(
    *,
    policy_text: str,
    objective: str,
    entities: list[dict[str, Any]],
    source_summaries: list[str],
    indicator_snapshots: list[dict[str, Any]],
    final_npcs: list[dict[str, Any]],
    events: list[dict[str, Any]],
    completed_rounds: int,
    max_rounds: int,
    situation_kind: str = "policy",
    stance_summary: dict[str, Any] | None = None,
    lang: str | None = None,
) -> EconomicReportResponse:
    if lang is None:  # report in the residents' majority language (ties -> German for Swiss text)
        counts = Counter(str(n.get("lang", "en")) for n in final_npcs)
        lang = max(counts, key=lambda k: (counts[k], k == "de")) if counts else "en"
    mood_counts = Counter(str(npc.get("mood", "neutral")).lower() for npc in final_npcs)
    event_counts = Counter(str(event.get("event_type", "")) for event in events)
    layoff_mentions = sum(1 for event in events if LAYOFF_RE.search(str(event.get("message", ""))))
    closure_mentions = sum(1 for event in events if CLOSURE_RE.search(str(event.get("message", ""))))
    protest_count = event_counts.get("protest", 0)
    price_change_count = event_counts.get("price_change", 0)
    mood_shift_count = event_counts.get("mood_shift", 0)
    num_npcs = len(final_npcs)

    top_event_messages = [
        _truncate(str(event.get("message", "")))
        for event in events
        if event.get("event_type") in {"price_change", "protest", "mood_shift"}
        or LAYOFF_RE.search(str(event.get("message", "")))
        or CLOSURE_RE.search(str(event.get("message", "")))
    ][:6]
    if not top_event_messages:
        top_event_messages = [_truncate(str(event.get("message", ""))) for event in events[:4] if event.get("message")]

    aggregate_summary = {
        "completed_rounds": completed_rounds,
        "max_rounds": max_rounds,
        "num_npcs": num_npcs,
        "dominant_mood": _dominant_mood(mood_counts)[0],
        "mood_counts": dict(_sorted_mood_items(mood_counts)),
        "event_counts": dict(event_counts),
        "layoff_mentions": layoff_mentions,
        "closure_mentions": closure_mentions,
        "source_summaries": source_summaries[:4],
        "indicator_snapshots": indicator_snapshots[:6],
    }

    policy_summary = json.dumps(
        {
            "objective": objective or "general economic and social impact",
            "entities": entities[:1],
            "policy_excerpt": _truncate(policy_text, 800),
        },
        indent=2,
    )
    trend_context = json.dumps(
        {
            "source_summaries": source_summaries[:4],
            "indicator_snapshots": indicator_snapshots[:6],
        },
        indent=2,
    )
    event_samples = "\n".join(f"- {message}" for message in top_event_messages) or "- No standout events were captured."

    fallback = _fallback_narrative(
        completed_rounds=completed_rounds,
        entities=entities,
        mood_counts=mood_counts,
        notable_events=top_event_messages,
        num_npcs=num_npcs,
        protest_count=protest_count,
        price_change_count=price_change_count,
        layoff_mentions=layoff_mentions,
        closure_mentions=closure_mentions,
    )

    prompt = ECONOMIC_REPORT_PROMPT.format(
        report_language=LANG_LABEL.get(lang, "English"),
        stance_summary=json.dumps(stance_summary, ensure_ascii=False) if stance_summary else "not available",
        objective=objective or "general economic and social impact",
        policy_summary=policy_summary,
        aggregate_summary=json.dumps(aggregate_summary, indent=2),
        trend_context=trend_context,
        event_samples=event_samples,
    )

    try:
        narrative = await invoke_llm_structured(
            prompt,
            EconomicReportNarrative,
            max_tokens=6000,
            llm=get_llm(max_tokens=6000, model=LLM_VOICE_NAME or None),
        )
    except Exception:
        logger.exception("economic_report: structured output failed, using fallback narrative")
        narrative = fallback

    entity_kind = entities[0].get("kind") if entities else None
    if entity_kind in ("vote", "budget"):
        kind = entity_kind
    else:
        kind = situation_kind or "policy"
    headline = swissify(_strip_vote_advice(narrative.headline), lang)
    summary = swissify(_strip_vote_advice(narrative.summary), lang)
    livelihood = swissify(_strip_vote_advice(narrative.livelihood_impact), lang)
    if kind == "vote":
        line = NO_VOTE_LINE.get(lang, NO_VOTE_LINE["en"])
        if line.strip() not in summary:
            summary = (summary.rstrip(".") + "." + line).strip()

    return EconomicReportResponse(
        headline=headline,
        summary=summary,
        livelihood_impact=livelihood,
        top_impacts=[i.model_copy(update={"title": swissify(i.title, lang), "description": swissify(i.description, lang)}) for i in narrative.top_impacts[:4]],
        key_stats=_build_key_stats(
            num_npcs=num_npcs,
            completed_rounds=completed_rounds,
            mood_counts=mood_counts,
            price_change_count=price_change_count,
            protest_count=protest_count,
            layoff_mentions=layoff_mentions,
            closure_mentions=closure_mentions,
        ),
        pie_chart=_build_pie_chart(mood_counts),
        bar_chart=_build_bar_chart(
            price_change_count=price_change_count,
            protest_count=protest_count,
            mood_shift_count=mood_shift_count,
            layoff_mentions=layoff_mentions,
            closure_mentions=closure_mentions,
        ),
        notable_events=[swissify(x, lang) for x in narrative.notable_events[:4]],
        stance_summary=stance_summary,
    )
