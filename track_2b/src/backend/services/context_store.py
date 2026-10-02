from __future__ import annotations

import uuid
from typing import Any

_sources: dict[str, dict[str, Any]] = {}


def create_source_record(
    *,
    kind: str,
    filename: str,
    label: str,
    preview_text: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
    content_text: str = "",
) -> dict[str, Any]:
    source_id = f"src_{uuid.uuid4().hex[:12]}"
    record = {
        "id": source_id,
        "kind": kind,
        "filename": filename,
        "label": label,
        "status": "ready",
        "preview_text": preview_text,
        "summary": summary,
        "metadata": metadata or {},
        "content_text": content_text,
    }
    _sources[source_id] = record
    return record


def get_source(source_id: str) -> dict[str, Any] | None:
    return _sources.get(source_id)


def get_sources(source_ids: list[str]) -> list[dict[str, Any]]:
    return [src for source_id in source_ids if (src := _sources.get(source_id)) is not None]


def clear_sources() -> None:
    _sources.clear()
