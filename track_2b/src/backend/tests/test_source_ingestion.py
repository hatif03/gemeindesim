from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.schemas import PolicyInput
from routers import extract as extract_router
from routers import simulate as simulate_router
from services.context_store import clear_sources


async def _fake_extract_pdf(_: bytes) -> str:
    return "Federal industrial policy with tariff relief and tax credits for domestic production."


class DummyUploadFile:
    def __init__(self, filename: str, data: bytes) -> None:
        self.filename = filename
        self._data = data

    async def read(self) -> bytes:
        return self._data


class TestSourceIngestion:
    def setup_method(self) -> None:
        clear_sources()
        simulate_router.simulations.clear()

    @pytest.mark.asyncio
    async def test_uploads_primary_pdf_source(self, monkeypatch) -> None:
        monkeypatch.setattr(extract_router, "_extract_pdf", _fake_extract_pdf)

        source = await extract_router.upload_context_source(
            file=DummyUploadFile("policy.pdf", b"%PDF-1.4 fake"),  # type: ignore[arg-type]
            label="Primary Policy PDF",
        )

        assert source.kind == "pdf"
        assert source.filename == "policy.pdf"
        assert source.label == "Primary Policy PDF"
        assert source.id.startswith("src_")
        assert "Federal industrial policy" in source.summary

    @pytest.mark.asyncio
    async def test_start_simulation_accepts_pdf_source(self, monkeypatch) -> None:
        monkeypatch.setattr(extract_router, "_extract_pdf", _fake_extract_pdf)

        pdf_source = await extract_router.upload_context_source(
            file=DummyUploadFile("policy.pdf", b"%PDF-1.4 fake"),  # type: ignore[arg-type]
            label="Primary Policy PDF",
        )

        response = await simulate_router.start_simulation(
            PolicyInput(
                primary_policy_source_id=pdf_source.id,
                notes_text="Focus on inflation and wages.",
                num_rounds=10,
                num_npcs=20,
                objective="Measure pressure on consumer prices.",
                map_id="ccity",
            )
        )

        assert response["simulation_id"]

    @pytest.mark.asyncio
    async def test_rejects_non_pdf_upload(self) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await extract_router.upload_context_source(
                file=DummyUploadFile("memo.md", b"# Tariffs\nSome policy text."),  # type: ignore[arg-type]
                label="Policy memo",
            )

        assert exc_info.value.status_code == 415

    def test_rejects_simulation_without_pdf_source(self) -> None:
        with pytest.raises(ValidationError, match="policy source upload"):
            PolicyInput(
                primary_policy_source_id=None,
                num_rounds=3,
                num_npcs=5,
            )
