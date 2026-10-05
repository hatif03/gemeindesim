"""Closed-corpus chunking and lexical retrieval (no open web)."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Any

_TOKEN = re.compile(r"[A-Za-zÀ-ÿ0-9]+", re.UNICODE)
_HEADER = re.compile(r"^---\s*(?:Source:\s*)?(.*?)\s*---\s*$", re.MULTILINE)
_SENT = re.compile(r"(?<=[.!?:;])\s+(?=[A-ZÄÖÜÉÈÀ0-9«\"(])")
_QUESTION = re.compile(r"abstimmungsfrage|question vot[ée]e|\bwollen sie\b|acceptez-vous|voulez-vous", re.IGNORECASE)

_STOP = {
    "de": "der die das und oder nicht ist sind ein eine einen mit für von zu im in an auf aus bei dem den des als auch es wir sie ich du er".split(),
    "fr": "le la les un une des et ou ne pas est sont avec pour de du dans en au aux sur par que qui nous vous je tu il elle ce cette".split(),
    "en": "the a an and or not is are with for of to in on at by from as it that this we you i he she".split(),
}
_STOPSET = {w for ws in _STOP.values() for w in ws}
_STOP_FOLDED = {l: {unicodedata.normalize("NFKD", w) for w in ws} for l, ws in _STOP.items()}


def _fold(token: str) -> str:
    t = unicodedata.normalize("NFKD", token.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _tokens(text: str) -> list[str]:
    """Casefolded, accent-folded, stop-word-free tokens; words > 6 chars share a 6-char stem
    so 'Steuerfuss' / 'Steuererhöhung' and 'impôt' / 'impôts' match. ponytail: crude stemmer."""
    out = []
    for t in _TOKEN.findall(text or ""):
        f = _fold(t)
        if f in _STOPSET or len(f) < 2:
            continue
        out.append(f[:6] if len(f) > 6 and not f.isdigit() else f)
    return out


def detect_lang(text: str) -> str:
    """Stop-word vote between de/fr/en for a passage. Default English."""
    words = [_fold(w) for w in _TOKEN.findall((text or "")[:4000])]
    score = {l: sum(w in _STOP_FOLDED[l] for w in words) for l in _STOP}
    best = max(score, key=score.get)
    return best if score[best] > 0 else "en"


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


def _pieces(body: str, size: int) -> list[str]:
    """Paragraphs -> sentences -> packed windows <= size; never cuts inside a word."""
    out: list[str] = []
    for para in re.split(r"\n\s*\n", body):
        para = " ".join(para.split())
        if not para:
            continue
        cur = ""
        for sent in _SENT.split(para):
            while len(sent) > size:  # pathological sentence: split on whitespace
                cut = sent.rfind(" ", 0, size)
                cut = cut if cut > 0 else size
                out.append(sent[:cut].strip())
                sent = sent[cut:].strip()
            if cur and len(cur) + 1 + len(sent) > size:
                out.append(cur)
                cur = sent
            else:
                cur = f"{cur} {sent}".strip()
        if cur:
            out.append(cur)
    merged: list[str] = []
    carry = ""
    for piece in out:  # headings ("Erläuterungen des Gemeinderats:") join the next paragraph
        piece = f"{carry} {piece}".strip()
        carry = piece if len(piece) < 60 else ""
        if not carry:
            merged.append(piece)
    if carry:
        merged.append(carry)
    return merged


def chunk_text(
    text: str,
    source_id: str,
    lang: str | None = None,
    size: int = 480,
    overlap: int = 0,  # kept for API compatibility; sentence packing needs none
) -> list[dict[str, Any]]:
    body = _HEADER.sub("", (text or "")).strip()
    if not body:
        return []
    chunks = []
    for idx, piece in enumerate(_pieces(body, size)):
        chunks.append(
            {
                "source_id": f"{source_id}#{idx}",
                "parent_id": source_id,
                "lang": lang or detect_lang(piece),  # per chunk: DE and FR can share one source
                "text": piece,
                "is_question": bool(_QUESTION.search(piece)),
            }
        )
    return chunks


def chunk_policy_document(policy_text: str) -> list[dict[str, Any]]:
    """Split a merged policy document (possibly several --- Source: --- blocks)."""
    body = policy_text or ""
    parts = re.split(r"\n--- Source: ", body)
    chunks: list[dict[str, Any]] = []
    for i, part in enumerate(parts):
        block = part if i == 0 else "--- Source: " + part
        header = block.split("\n", 1)[0]
        sid = re.sub(r"[^a-zA-Z0-9]+", "_", header).strip("_")[:40] or f"src{i}"
        chunks.extend(chunk_text(block, sid))
    return chunks


def retrieve_passages(
    chunks: list[dict[str, Any]],
    query: str,
    top_k: int = 4,
    lang: str | None = None,
) -> list[dict[str, Any]]:
    """BM25 over the resident-language chunks; the ballot-question chunk is always included."""
    if not chunks:
        return []
    pool = [c for c in chunks if not lang or c.get("lang") == lang] or chunks
    docs = [Counter(_tokens(c.get("text", ""))) for c in pool]
    n = len(pool)
    avg = sum(sum(d.values()) for d in docs) / n or 1.0
    df = Counter(t for d in docs for t in d)
    q = set(_tokens(query))
    k1, b = 1.5, 0.75
    scored = []
    for c, d in zip(pool, docs):
        ln = sum(d.values()) or 1
        s = sum(
            math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * d[t] * (k1 + 1) / (d[t] + k1 * (1 - b + b * ln / avg))
            for t in q
            if t in d
        )
        scored.append((s, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [c for s, c in scored if s > 0][:top_k] or [c for _, c in scored[:top_k]]
    # A booklet can carry several ballot questions (one per measure): pin up to two, then fill with BM25.
    pinned = [c for c in pool if c.get("is_question")][:2]
    if pinned and any(p not in picked for p in pinned):
        picked = pinned + [c for c in picked if c not in pinned][: max(0, top_k - len(pinned))]
    return picked


def default_top_k(chunks: list[dict[str, Any]]) -> int:
    """4 passages for a short text (the whole sample is ~16 chunks); 6 for a real booklet (research E17:
    recall@k on 14 gold questions of the 48-page Federal Council booklet)."""
    return 4 if len(chunks) <= 40 else 6


def passage_labels(passages: list[dict[str, Any]]) -> dict[str, str]:
    """Short citation labels the model can copy exactly: P1..Pk -> source_id."""
    return {f"P{i}": p.get("source_id", f"src{i}") for i, p in enumerate(passages, 1)}


def format_passages(passages: list[dict[str, Any]]) -> str:
    if not passages:
        return "(no retrieved passages — do not invent official numbers)"
    return "\n\n".join(f"[P{i}] {p.get('text', '')}" for i, p in enumerate(passages, 1))


def passage_source_ids(passages: list[dict[str, Any]]) -> set[str]:
    return {str(p.get("source_id", "")) for p in passages if p.get("source_id")}
