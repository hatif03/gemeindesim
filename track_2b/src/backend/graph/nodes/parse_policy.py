"""Node: parse incoming policy text into structured entities via LLM."""

from __future__ import annotations

import logging
from typing import Any

from graph.corpus import (
    chunk_policy_document,
    detect_situation_kind,
    format_passages,
    retrieve_passages,
)
from graph.llm import get_llm, invoke_llm_structured
from graph.prompts import PARSE_POLICY_PROMPT
from models.schemas import PolicyAnalysis
from models.state import SimState

logger = logging.getLogger(__name__)


async def parse_policy(state: SimState) -> dict[str, Any]:
    """Analyse raw policy text and extract sectors, stakeholders, and impacts."""

    logger.info(
        "parse_policy: analysing %d chars of policy text …", len(state["policy_text"])
    )
    chunks = chunk_policy_document(state["policy_text"])
    query = (
        f"{state.get('objective', '')} sectors stakeholders economic impacts "
        f"{state['policy_text'][:500]}"
    )
    pack = format_passages(retrieve_passages(chunks, query, top_k=8))
    policy_for_prompt = (
        state["policy_text"][:8000]
        if pack.startswith("(no retrieved")
        else pack
    )
    kind = detect_situation_kind(
        state["policy_text"], state.get("situation_kind")
    )
    prompt = PARSE_POLICY_PROMPT.format(
        policy_text=policy_for_prompt,
        notes_text=state.get("notes_text", "") or "No supporting notes provided.",
        trend_summary=state.get("trend_summary", "")
        or "No historical trend context provided.",
        objective=state.get("objective", "") or "general economic and social impact",
    )
    llm = get_llm()
    result = await invoke_llm_structured(prompt, PolicyAnalysis, llm=llm)
    entities = result.model_dump()
    entities["kind"] = kind
    logger.info(
        "parse_policy: sectors=%d  stakeholders=%d  impacts=%d  controversy=%s  kind=%s",
        len(entities["sectors"]),
        len(entities["stakeholders"]),
        len(entities["economic_impacts"]),
        entities["controversy_level"],
        kind,
    )
    return {"entities": [entities], "situation_kind": kind}
