"""Shared utilities for LangGraph node implementations."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the range [lo, hi]."""
    return max(lo, min(hi, value))


_NPC_ID_RE = re.compile(r"npc_(\d+)")


def normalize_npc_id(
    raw_id: str,
    name_to_id: dict[str, str] | None = None,
) -> str | None:
    """Normalize an NPC reference to the canonical ``npc_XX`` format.

    Handles:
    - ``npc_1`` → ``npc_01``
    - ``Citizen 2`` → ``npc_02`` (via name lookup)
    - ``marcus_rivera`` → ``npc_03`` (via snake_case / partial name lookup)
    """
    if not raw_id:
        return None
    # Try direct regex match for npc_N or npc_NN format.
    m = _NPC_ID_RE.search(raw_id)
    if m:
        return f"npc_{int(m.group(1)):02d}"
    if not name_to_id:
        return raw_id
    # Try exact name lookup.
    if raw_id in name_to_id:
        return name_to_id[raw_id]
    # Try case-insensitive / snake_case matching.
    # Also strip "npc_" prefix if present (e.g. "npc_elias" → "elias").
    stripped = raw_id.removeprefix("npc_") if raw_id.startswith("npc_") else raw_id
    normalized = stripped.replace("_", " ").strip().lower()
    for name, npc_id in name_to_id.items():
        if name.lower() == normalized:
            return npc_id
    # Try partial match (first or last name).
    for name, npc_id in name_to_id.items():
        parts = name.lower().split()
        if normalized in parts:
            return npc_id
    return raw_id
