"""Apertus gate: reasoning-span strip, numerals, corpus retrieve, fallbacks."""

from __future__ import annotations

from graph.corpus import chunk_text, detect_lang, detect_setting, retrieve_passages
from graph.language import fallback_utterance, strip_ungrounded_numerals, ungrounded_numerals
from graph.llm import strip_reasoning_spans
from models.schemas import NPCEvent, NPCRoundResponse


def test_strip_apertus_inner_spans():
    raw = "<|inner_prefix|>secret math<|inner_suffix|>The ball costs 0.05 CHF."
    assert "<|inner_prefix|>" not in strip_reasoning_spans(raw)
    assert "0.05 CHF" in strip_reasoning_spans(raw)


def test_strip_truncated_thinking():
    raw = "<|inner_prefix|>unfinished deliberation"
    assert "<|inner_prefix|>" not in strip_reasoning_spans(raw)


def test_detect_swiss_setting():
    assert detect_setting("Der Steuerfuss der Gemeinde Linden steigt.") == "ch"
    assert detect_setting("Raise the steel tariff in Millfield.") == "us"


def test_detect_lang():
    assert detect_lang("Wollen Sie den Steuerfuss erhöhen?") == "de"
    assert detect_lang("Acceptez-vous le taux d'imposition?") == "fr"
    assert detect_lang("The mill will recall overtime shifts.") == "en"


def test_numeral_grounding():
    pack = "Steuerfuss 124 % and 4.8 Millionen CHF"
    dirty = "The tax rate jumps to 40% and costs 9 million."
    extra = ungrounded_numerals(dirty, pack)
    assert extra
    cleaned = strip_ungrounded_numerals(dirty, pack)
    assert "40" not in cleaned
    assert "[n]" in cleaned


def test_fallback_languages():
    assert "Erklärung" in fallback_utterance("de")
    assert "explication" in fallback_utterance("fr").lower()
    assert "official" in fallback_utterance("en").lower()


def test_retrieve_prefers_overlap():
    chunks = chunk_text(
        "The mill tariff is 25 percent. Household prices may rise. "
        "Construction quotes already mention steel beams.",
        "policy",
        "en",
    )
    hits = retrieve_passages(chunks, "steel tariff mill", top_k=2)
    assert hits
    assert any("tariff" in h["text"].lower() or "steel" in h["text"].lower() for h in hits)


def test_five_event_types_still_valid():
    for kind in ("chat", "move", "protest", "price_change", "mood_shift"):
        ev = NPCEvent(event_type=kind, message="ok", new_mood="hopeful")
        assert ev.event_type == kind


def test_unknown_mood_maps_to_neutral():
    ev = NPCEvent(event_type="mood_shift", message="hmm", new_mood="considerate")
    assert ev.new_mood == "neutral"


def test_round_response_accepts_one_to_three_events():
    payload = {
        "events": [
            {"event_type": "chat", "message": "hello", "dialogue": "hello", "target_npc_id": "npc_02"},
            {"event_type": "move", "message": "to the square", "to_x": 3, "to_y": 4},
        ],
        "perception": "neighbors nearby",
    }
    parsed = NPCRoundResponse.model_validate(payload)
    assert len(parsed.events) == 2
