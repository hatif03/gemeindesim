"""End-to-end test: upload real PDF → run full graph pipeline."""
from __future__ import annotations

import pathlib

import pytest

from graph.builder import build_graph
from services.context_store import clear_sources, create_source_record

_PDF = pathlib.Path(__file__).parent / "data" / "tariff_capital_policy.pdf"


def _read_pdf_text() -> str:
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(_PDF.read_bytes()))
    pages = [p.extract_text() or "" for p in reader.pages]
    return "\n\n".join(p.strip() for p in pages if p.strip())


@pytest.fixture(autouse=True)
def clean_store():
    clear_sources()
    yield
    clear_sources()


@pytest.mark.asyncio
async def test_full_pipeline():
    """Upload real PDF, run 1 round with 3 NPCs — must not raise."""
    text = _read_pdf_text()
    assert text, "PDF produced no text"

    record = create_source_record(
        kind="pdf",
        filename="tariff_capital_policy.pdf",
        label="Test Policy",
        preview_text=text[:500],
        summary=text[:300],
        metadata={},
        content_text=text,
    )
    source_id = record["id"]

    events_received: list = []

    async def on_events(events: list) -> None:
        events_received.extend(events)

    async def on_npc_added(npc: dict) -> None:
        pass

    graph = build_graph()
    state = {
        "policy_text": "",
        "notes_text": "",
        "trend_summary": "",
        "context_summary": "",
        "indicator_snapshots": [],
        "source_summaries": [],
        "policy_sources": [source_id],
        "trend_sources": [],
        "objective": "measure economic impact on workers",
        "max_rounds": 1,
        "num_npcs": 3,
        "map_id": "ccity",
        "entities": [],
        "npcs": [],
        "relationships": [],
        "events": [],
        "current_round": 0,
        "economic_indicators": {},
        "memory_streams": {},
        "npc_stream_callback": on_events,
        "npc_added_callback": on_npc_added,
    }

    final_state: dict = {}
    async for chunk in graph.astream(state):
        for key, update in chunk.items():
            final_state.update(update)

    # Basic assertions
    assert final_state.get("npcs"), "No NPCs generated"
    assert len(final_state["npcs"]) == 3
    assert final_state.get("entities"), "Policy parsing produced no entities"
    assert final_state.get("current_round", 0) >= 1, "No rounds ran"
