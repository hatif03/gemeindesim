"""Eval fixtures: schema, nearby-id, closed moods (no live LLM)."""

from __future__ import annotations

import pytest
from models.schemas import NPCEvent, NPCRoundResponse

_MOODS = ("angry", "anxious", "worried", "neutral", "hopeful", "excited")
_TYPES = ("chat", "move", "protest", "price_change", "mood_shift")


def _fixture(i: int) -> dict:
    kind = _TYPES[i % len(_TYPES)]
    mood = _MOODS[i % len(_MOODS)]
    nearby = "npc_02"
    ev: dict = {
        "event_type": kind,
        "message": f"fixture {i} in character",
        "new_mood": mood,
        "used_source_ids": ["policy#0"] if i % 2 == 0 else [],
        "grounded": i % 2 == 0,
    }
    if kind == "chat":
        ev["target_npc_id"] = nearby
        ev["dialogue"] = "Wir haben die 4.8 Millionen im Text gelesen."
    if kind == "move":
        ev["to_x"] = i % 20
        ev["to_y"] = i % 15
    return {"events": [ev], "perception": f"round perception {i}"}


def test_twenty_round_fixtures_validate():
    ok = 0
    for i in range(20):
        parsed = NPCRoundResponse.model_validate(_fixture(i))
        assert parsed.events
        ev = parsed.events[0]
        if ev.event_type == "chat":
            assert ev.target_npc_id == "npc_02"
        if ev.new_mood:
            assert ev.new_mood in _MOODS
        ok += 1
    assert ok == 20


def test_single_event_dict_normalizes():
    parsed = NPCRoundResponse.model_validate(
        {"event_type": "protest", "message": "on the square"}
    )
    assert len(parsed.events) == 1
    assert parsed.events[0].event_type == "protest"


def test_linden_sample_mentions_steuerfuss():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3] / "data" / "steuerfuss_linden_de.txt"
    text = root.read_text(encoding="utf-8")
    assert "Steuerfuss" in text
    assert "4.8" in text


def test_linden_fr_sample_and_millfield_en():
    from pathlib import Path

    data = Path(__file__).resolve().parents[3] / "data"
    fr = (data / "steuerfuss_linden_fr.txt").read_text(encoding="utf-8")
    en = (data / "tariff_millfield_en.txt").read_text(encoding="utf-8")
    assert "taux" in fr.lower() or "impôt" in fr.lower() or "impot" in fr.lower()
    assert "Millfield" in en or "tariff" in en.lower()


def test_fallback_event_is_in_language():
    from graph.language import fallback_utterance

    de = fallback_utterance("de")
    fr = fallback_utterance("fr")
    assert "Erklärung" in de or "amtliche" in de
    assert "explication" in fr.lower()
    for lang in ("de", "fr", "en"):
        ev = NPCEvent(event_type="mood_shift", message=fallback_utterance(lang), new_mood="neutral")
        assert ev.event_type == "mood_shift"


def test_report_prompt_forbids_vote_advice():
    from graph.prompts import ECONOMIC_REPORT_PROMPT

    assert "Do not recommend how anyone should vote" in ECONOMIC_REPORT_PROMPT


def test_vote_kind_detected_on_linden():
    from pathlib import Path

    from graph.corpus import detect_situation_kind

    text = (Path(__file__).resolve().parents[3] / "data" / "steuerfuss_linden_de.txt").read_text(
        encoding="utf-8"
    )
    assert detect_situation_kind(text, "policy") == "vote"


def test_assign_langs_bilingual_for_swiss():
    from graph.language import assign_langs

    langs = assign_langs(5, "ch")
    assert langs.count("de") >= 2
    assert langs.count("fr") >= 2
    assert assign_langs(3, "us") == ["en", "en", "en"]


def test_thinking_markers_stripped_from_user_text():
    from graph.llm import strip_reasoning_spans

    visible = strip_reasoning_spans("<|inner_prefix|>hidden<|inner_suffix|>Hallo Linden.")
    assert "<|inner_prefix|>" not in visible
    assert "Hallo Linden." in visible


@pytest.mark.asyncio
async def test_vote_report_strips_advice_and_adds_disclaimer(monkeypatch):
    from models.schemas import EconomicReportNarrative
    from services.economic_report import generate_economic_report

    async def mock_invoke(prompt, response_model, max_tokens=None, **kwargs):
        return EconomicReportNarrative(
            headline="Vote yes now",
            summary="You should vote yes on the Vorlage.",
            livelihood_impact="jobs",
            top_impacts=[],
            notable_events=["n"],
        )

    monkeypatch.setattr("services.economic_report.invoke_llm_structured", mock_invoke)
    report = await generate_economic_report(
        policy_text="Vorlage",
        objective="",
        entities=[{"kind": "vote"}],
        source_summaries=[],
        indicator_snapshots=[],
        final_npcs=[{"mood": "neutral"}],
        events=[],
        completed_rounds=1,
        max_rounds=3,
        situation_kind="policy",
    )
    assert "does not recommend how anyone should vote" in report.summary.lower()
    assert "vote yes" not in report.headline.lower()
