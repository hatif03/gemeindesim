"""Closed-corpus chunking and lexical retrieval (no open web)."""

from __future__ import annotations

import re
from typing import Any

_TOKEN = re.compile(r"[A-Za-zÀ-ÿ0-9]+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text or "")}


def detect_lang(text: str) -> str:
    """Cheap language hint for a passage. Default English."""
    sample = (text or "")[:4000]
    if re.search(r"[äöüÄÖÜß]|\b(und|der|die|das|nicht|Gemeinde|Vorlage|Steuerfuss)\b", sample):
        return "de"
    if re.search(
        r"[éèêëàâùûçœÉÈÀ]|\b(les|des|une|pour|avec|conseil|taux|budget)\b",
        sample,
        re.IGNORECASE,
    ):
        return "fr"
    return "en"


def detect_situation_kind(text: str, explicit: str | None = None) -> str:
    """Tag the input as policy, vote, or budget without changing the pipeline.

    Explicit vote/budget from the client wins. A default of ``policy`` still
    lets Swiss Vorlage text be tagged as a vote from the corpus.
    """
    if explicit in ("vote", "budget"):
        return explicit
    t = (text or "").lower()
    vote_markers = (
        "vorlage",
        "abstimm",
        "stimmvolk",
        "stimmzettel",
        "abstimmungsfrage",
        "objet soumis",
        "question vot",
        "wollen sie",
        "acceptez-vous",
    )
    if any(m in t for m in vote_markers):
        return "vote"
    budget_markers = ("voranschlag", "jahresrechnung", "budget communal")
    if any(m in t for m in budget_markers):
        return "budget"
    return explicit or "policy"


def detect_setting(policy_text: str) -> str:
    """Return 'ch' for Swiss civic/municipal text, otherwise 'us'."""
    t = (policy_text or "").lower()
    markers = (
        "gemeinde",
        "steuerfuss",
        "vorlage",
        "abstimm",
        "erläuterungen",
        "erlaeuterungen",
        "conseil communal",
        "taux d",
        "souverain",
        "linden",
        "schweiz",
        "suisse",
        "chf",
    )
    if any(m in t for m in markers):
        return "ch"
    return "us"


def chunk_text(
    text: str,
    source_id: str,
    lang: str | None = None,
    size: int = 420,
    overlap: int = 80,
) -> list[dict[str, Any]]:
    body = (text or "").strip()
    if not body:
        return []
    lang = lang or detect_lang(body)
    chunks: list[dict[str, Any]] = []
    i = 0
    n = len(body)
    idx = 0
    while i < n:
        piece = body[i : i + size]
        chunks.append(
            {
                "source_id": f"{source_id}#{idx}",
                "parent_id": source_id,
                "lang": lang,
                "text": piece.strip(),
            }
        )
        idx += 1
        if i + size >= n:
            break
        i += max(1, size - overlap)
    return chunks


def chunk_policy_document(policy_text: str) -> list[dict[str, Any]]:
    """Split a merged policy document (possibly several --- Source: --- blocks)."""
    body = policy_text or ""
    parts = re.split(r"\n--- Source: ", body)
    chunks: list[dict[str, Any]] = []
    for i, part in enumerate(parts):
        block = part if i == 0 else "--- Source: " + part
        header = block.split("\n", 1)[0]
        sid = re.sub(r"[^a-zA-Z0-9_-]+", "_", header)[:40] or f"src{i}"
        chunks.extend(chunk_text(block, sid, detect_lang(block)))
    return chunks


def retrieve_passages(
    chunks: list[dict[str, Any]],
    query: str,
    top_k: int = 4,
    lang: str | None = None,
) -> list[dict[str, Any]]:
    if not chunks:
        return []
    pool = [c for c in chunks if not lang or c.get("lang") == lang] or chunks
    q = _tokens(query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for c in pool:
        t = _tokens(c.get("text", ""))
        overlap = len(q & t)
        score = overlap / max(1, len(q))
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [c for s, c in scored[:top_k] if s > 0]
    return picked or [c for _, c in scored[:top_k]]


def format_passages(passages: list[dict[str, Any]]) -> str:
    if not passages:
        return "(no retrieved passages — do not invent official numbers)"
    lines = []
    for p in passages:
        sid = p.get("source_id", "src")
        lines.append(f"[{sid}] {p.get('text', '')}")
    return "\n\n".join(lines)


def passage_source_ids(passages: list[dict[str, Any]]) -> set[str]:
    return {str(p.get("source_id", "")) for p in passages if p.get("source_id")}
