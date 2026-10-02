"""File ingestion endpoints for policy narratives (PDF) and trend CSV sources."""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from fastapi import APIRouter, Form, HTTPException, UploadFile

from models.schemas import ContextSourceResponse
from services.context_store import create_source_record

logger = logging.getLogger(__name__)

router = APIRouter()


async def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(p.strip() for p in pages if p.strip())


def _safe_float(value: str | None) -> float | None:
    cleaned = (value or "").strip().replace(",", "").replace("$", "").replace("%", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_csv(data: bytes, source_id: str) -> tuple[str, dict[str, Any]]:
    text = data.decode("utf-8", errors="replace").strip()
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    columns = reader.fieldnames or []

    if not columns or not rows:
        raise HTTPException(status_code=422, detail="CSV file has no rows.")

    period_col = next(
        (col for col in columns if any(token in col.lower() for token in ("date", "time", "period", "quarter", "year", "month"))),
        columns[0],
    )

    numeric_columns: list[str] = []
    for col in columns:
        values = [_safe_float(row.get(col, "")) for row in rows]
        if any(v is not None for v in values):
            numeric_columns.append(col)

    indicators: list[dict[str, Any]] = []
    summary_lines = [f"{len(rows)} rows across columns: {', '.join(columns)}."]
    for col in numeric_columns[:5]:
        numeric_points: list[tuple[str | None, float]] = []
        for row in rows:
            value = _safe_float(row.get(col, ""))
            if value is None:
                continue
            numeric_points.append((str(row.get(period_col, "")).strip() or None, value))
        if not numeric_points:
            continue

        first_period, first_value = numeric_points[0]
        latest_period, latest_value = numeric_points[-1]
        previous_value = numeric_points[-2][1] if len(numeric_points) > 1 else None
        change = latest_value - previous_value if previous_value is not None else None

        if change is None:
            trend = "unknown"
        elif abs(change) < 1e-9:
            trend = "flat"
        elif change > 0:
            trend = "up"
        else:
            trend = "down"

        unit = "%" if "%" in col or "rate" in col.lower() else "$" if "$" in col else None
        indicators.append({
            "metric": col,
            "latest_value": latest_value,
            "previous_value": previous_value,
            "change": change,
            "trend": trend,
            "latest_period": latest_period,
            "source_id": source_id,
            "unit": unit,
        })

        if previous_value is None:
            summary_lines.append(f"{col}: latest value {latest_value:g}{unit or ''} at {latest_period or first_period or 'latest period'}.")
        else:
            summary_lines.append(
                f"{col}: {previous_value:g}{unit or ''} → {latest_value:g}{unit or ''} ({trend}) by {latest_period or 'latest period'}."
            )

    metadata = {
        "row_count": len(rows),
        "columns": columns,
        "period_column": period_col,
        "indicator_snapshots": indicators,
    }
    return "\n".join(summary_lines), metadata


def _pdf_summary(text: str) -> str:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    if not paragraphs:
        return ""
    return " ".join(paragraphs[:2]).strip()[:600]


def _source_response(record: dict) -> ContextSourceResponse:
    return ContextSourceResponse(
        id=record["id"],
        kind=record["kind"],
        filename=record["filename"],
        label=record["label"],
        status=record["status"],
        preview_text=record["preview_text"],
        summary=record["summary"],
        metadata=record["metadata"],
    )


@router.post("/context/sources", response_model=ContextSourceResponse)
async def upload_context_source(
    file: UploadFile,
    label: str | None = Form(default=None),
) -> ContextSourceResponse:
    data = await file.read()
    filename = (file.filename or "source").lower()
    source_label = label or file.filename or "Source"

    logger.info("context source upload: file=%s size=%d", filename, len(data))

    if filename.endswith(".pdf"):
        text = await _extract_pdf(data)
        if not text.strip():
            raise HTTPException(status_code=422, detail="No text could be extracted from the PDF.")
        summary = _pdf_summary(text)
        record = create_source_record(
            kind="pdf",
            filename=file.filename or "policy.pdf",
            label=source_label,
            preview_text=summary or text[:500],
            summary=summary or "Primary policy document ready.",
            metadata={"page_count_estimate": max(1, text.count("\n\n"))},
            content_text=text.strip(),
        )
        return _source_response(record)

    if filename.endswith(".csv"):
        provisional_id = f"src_preview_{filename.replace('.', '_')}"
        summary, metadata = _extract_csv(data, provisional_id)
        record = create_source_record(
            kind="csv",
            filename=file.filename or "trend.csv",
            label=source_label,
            preview_text=summary[:500],
            summary=summary,
            metadata=metadata,
            content_text=data.decode("utf-8", errors="replace").strip(),
        )
        for indicator in record["metadata"].get("indicator_snapshots", []):
            indicator["source_id"] = record["id"]
        return _source_response(record)

    raise HTTPException(status_code=415, detail=f"Unsupported file type: {filename}. Upload a PDF (policy) or CSV (trend data).")


@router.post("/extract")
async def extract_file(file: UploadFile) -> dict[str, str]:
    data = await file.read()
    filename = (file.filename or "").lower()

    logger.info("extract: file=%s size=%d", filename, len(data))
    try:
        if filename.endswith(".pdf"):
            text = await _extract_pdf(data)
        elif filename.endswith(".csv"):
            text, _ = _extract_csv(data, "extract_preview")
        else:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {filename}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("extract: failed for %s", filename)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}") from e

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the file.")

    logger.info("extract: extracted %d chars from %s", len(text), filename)
    return {"text": text.strip()}
