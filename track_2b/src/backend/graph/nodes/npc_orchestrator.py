"""Node: orchestrate NPC generation — extract from source, fill gaps with RNG + LLM personality."""

from __future__ import annotations

import asyncio
import json
import logging
import random

from langchain_openai import ChatOpenAI

from config import GRID_HEIGHT, GRID_WIDTH, MAX_NPCS, MAX_X, MAX_Y
from graph.corpus import detect_setting
from graph.language import TOWN, assign_langs, swissify_persona
from graph.llm import get_llm, invoke_llm_json
from graph.names import name_pools_for_lang
from graph.nodes.stance import elicit_stances
from graph.prompts import (
    EXTRACT_CHARACTERS_PROMPT,
    GENERATE_NPC_PERSONALITY_PROMPT,
)
from models.state import SimState

logger = logging.getLogger(__name__)

_MBTI_TYPES = [
    "INTJ",
    "INTP",
    "ENTJ",
    "ENTP",
    "INFJ",
    "INFP",
    "ENFJ",
    "ENFP",
    "ISTJ",
    "ISFJ",
    "ESTJ",
    "ESFJ",
    "ISTP",
    "ISFP",
    "ESTP",
    "ESFP",
]
_MOODS = [
    "hopeful",
    "anxious",
    "angry",
    "neutral",
    "excited",
    "worried",
]
_INCOME_LEVELS = ["low", "medium", "high"]
_ROLE_VALUES = [
    "worker",
    "business_owner",
    "politician",
    "student",
    "retiree",
    "activist",
    "farmer",
    "shopkeeper",
    "driver",
    "teacher",
    "municipal_employee",
    "tenant",
]
_ROLE_VALUES_CH = [
    "tenant",
    "shopkeeper",
    "farmer",
    "teacher",
    "municipal_employee",
    "retiree",
    "worker",
    "business_owner",
    "politician",
    "activist",
]


def _random_name(gender: str, lang: str = "en") -> str:
    first_m, first_f, lasts = name_pools_for_lang(lang)
    pool = first_f if gender == "female" else first_m
    return f"{random.choice(pool)} {random.choice(lasts)}"


def _random_base(
    index: int,
    used_names: set[str],
    lang: str = "en",
    country: str = "USA",
    role: str | None = None,
) -> dict:
    """Generate all non-personality attributes via RNG."""
    gender = random.choice(["male", "female", "nonbinary"])
    name = _random_name("female" if gender == "female" else "male", lang)
    # Ensure uniqueness without LLM involvement
    attempts = 0
    while name in used_names and attempts < 20:
        name = _random_name("female" if gender == "female" else "male", lang)
        attempts += 1
    used_names.add(name)

    pool = _ROLE_VALUES_CH if country == "Switzerland" else _ROLE_VALUES
    assigned_role = role if role in _ROLE_VALUES else pool[index % len(pool)]

    return {
        "name": name,
        "gender": gender,
        "mbti": random.choice(_MBTI_TYPES),
        "country": country,
        "lang": lang,
        "role": assigned_role,
        "income_level": random.choice(_INCOME_LEVELS),
        "political_leaning": round(random.uniform(-1.0, 1.0), 2),
        "x": random.randint(0, MAX_X),
        "y": random.randint(0, MAX_Y),
        "mood": random.choice(_MOODS),
        "life_story": "",
        "expert_reflection": "",
    }


def _infer_role(npc: dict) -> str:
    role = str(npc.get("role", "")).strip().lower()
    if role in _ROLE_VALUES:
        return role

    text = " ".join(
        str(npc.get(key, ""))
        for key in ("category", "profession", "bio", "persona")
    ).lower()

    if any(k in text for k in ["driver", "taxi", "truck", "delivery", "courier", "rideshare", "uber", "lyft"]):
        return "driver"
    if any(k in text for k in ["shopkeeper", "shop owner", "store owner", "merchant", "grocer", "clerk"]):
        return "shopkeeper"
    if any(k in text for k in ["business owner", "entrepreneur", "founder", "proprietor", "owner"]):
        return "business_owner"
    if any(
        k in text
        for k in [
            "politician",
            "mayor",
            "council",
            "senator",
            "representative",
            "governor",
            "gemeinderat",
            "conseil communal",
            "conseiller",
        ]
    ):
        return "politician"
    if any(k in text for k in ["student", "undergrad", "college", "high school"]):
        return "student"
    if any(k in text for k in ["retiree", "retired", "pensioner"]):
        return "retiree"
    if any(k in text for k in ["activist", "organizer", "protester", "union organizer"]):
        return "activist"
    if any(k in text for k in ["teacher", "lehrer", "enseignant", "school", "schule"]):
        return "teacher"
    if any(k in text for k in ["municipal", "gemeinde", "communal", "civil servant", "beamte"]):
        return "municipal_employee"
    if any(k in text for k in ["tenant", "renter", "mieter", "locataire"]):
        return "tenant"
    if any(k in text for k in ["farmer", "rancher", "grower", "agriculture"]):
        return "farmer"
    if any(k in text for k in ["worker", "laborer", "technician", "operator", "staff", "employee", "factory"]):
        return "worker"

    return "worker"


def _clamp_positions(npcs: list[dict]) -> list[dict]:
    """Ensure every NPC has valid, unique grid coordinates.

    Default 5-NPC runs sit on a 20x15 grid; without clustering, Chebyshev-2
    chats almost never happen. Pack small towns onto a square; keep spread
    for large rosters.
    """
    occupied: set[tuple[int, int]] = set()
    n = len(npcs)
    cluster = n <= 10
    origin_x, origin_y, width = (8, 6, 6) if cluster else (0, 0, GRID_WIDTH)
    for i, npc in enumerate(npcs):
        if cluster:
            x = origin_x + (i % width)
            y = origin_y + (i // width)
        else:
            x = max(0, min(MAX_X, int(npc.get("x", 0))))
            y = max(0, min(MAX_Y, int(npc.get("y", 0))))
        while (x, y) in occupied:
            x = (x + 1) % GRID_WIDTH
            if x == 0:
                y = (y + 1) % GRID_HEIGHT
        occupied.add((x, y))
        npc["x"] = x
        npc["y"] = y
    return npcs


async def _extract_characters(
    source_text: str, entities_json: str, llm: ChatOpenAI
) -> list[dict]:
    """Try to extract named characters from the source text."""
    prompt = EXTRACT_CHARACTERS_PROMPT.format(
        source_text=source_text[:4000],
        entities_json=entities_json,
    )
    data = await invoke_llm_json(prompt, llm=llm)
    # "Extract" means literal: keep a character only if the name is in the text (the model
    # otherwise invents residents, or returns the document title as a person: E3 8B run).
    return [
        c for c in data.get("characters", [])
        if isinstance(c, dict) and c.get("name") and str(c["name"]) in source_text
    ]


async def _generate_personality(
    base: dict, entities_json: str, llm: ChatOpenAI, town: str
) -> dict:
    """Ask LLM only for personality fields; all other attrs are pre-generated."""
    prompt = GENERATE_NPC_PERSONALITY_PROMPT.format(
        name=base["name"],
        gender=base["gender"],
        income_level=base["income_level"],
        political_leaning=base["political_leaning"],
        mbti=base["mbti"],
        lang=base.get("lang", "en"),
        role=base.get("role", "worker"),
        town=town,
        entities_json=entities_json,
    )
    data = await invoke_llm_json(prompt, llm=llm)
    data.pop("role", None)
    return {**base, **data, "role": base.get("role", "worker")}


def _affinity_heuristic(npc_a: dict, npc_b: dict) -> tuple[float, float]:
    """Compute affinity and trust between two NPCs heuristically."""
    affinity = 0.0

    # Same profession keywords → cooperative bond
    prof_a = npc_a.get("profession", "").lower()
    prof_b = npc_b.get("profession", "").lower()
    PROF_KEYWORDS = ["steel", "metal", "factory", "union", "worker", "retail", "shop",
                     "teacher", "school", "medical", "farm", "driver", "tech", "build"]
    if any(k in prof_a and k in prof_b for k in PROF_KEYWORDS):
        affinity += 0.3
    elif any(k in prof_a for k in PROF_KEYWORDS) and any(k in prof_b for k in PROF_KEYWORDS):
        # Different industries but both working class
        affinity += 0.1

    # Same income level → shared economic reality
    if npc_a.get("income_level") == npc_b.get("income_level"):
        affinity += 0.2

    # Political divergence → tension
    delta_politics = abs(
        npc_a.get("political_leaning", 0.0) - npc_b.get("political_leaning", 0.0)
    ) / 2.0  # normalise: max delta is 2.0
    affinity -= 0.4 * delta_politics

    # Grid proximity → familiarity
    dx = abs(npc_a.get("x", 0) - npc_b.get("x", 0))
    dy = abs(npc_a.get("y", 0) - npc_b.get("y", 0))
    if max(dx, dy) < 3:
        affinity += 0.15

    affinity = round(max(-1.0, min(1.0, affinity)), 2)
    trust = round(max(0.1, min(0.95, 0.5 + 0.3 * affinity)), 2)
    return affinity, trust


async def _generate_relationships(
    npcs: list[dict], entities_json: str, llm: ChatOpenAI
) -> list[dict]:
    """Generate a social network across the assembled NPC roster using heuristics."""
    n = len(npcs)
    if n < 2:
        return []

    max_unique = n * (n - 1) // 2
    target_rels = min(max(n, int(n * 1.5)), max_unique)

    # Build every candidate pair and shuffle, then pick target_rels of them.
    all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    random.shuffle(all_pairs)
    selected_pairs = all_pairs[:target_rels]

    result = []
    for i, j in selected_pairs:
        affinity, trust = _affinity_heuristic(npcs[i], npcs[j])
        result.append({
            "source_id": npcs[i]["id"],
            "target_id": npcs[j]["id"],
            "affinity": affinity,
            "trust": trust,
        })
    return result


def _initial_reputation(npc: dict) -> float:
    """Heuristic for starting reputation based on social standing."""
    rep = 0.5
    if npc.get("income_level") == "high":
        rep += 0.1
    elif npc.get("income_level") == "low":
        rep -= 0.05

    prof = npc.get("profession", "").lower()
    if any(
        k in prof for k in ["doctor", "lawyer", "owner", "professor", "judge", "mayor"]
    ):
        rep += 0.2
    if any(k in prof for k in ["activist", "drifter", "protester"]):
        rep -= 0.1
    return round(max(0.1, min(0.95, rep)), 2)


async def generate_npcs(state: SimState) -> dict:
    num_npcs = min(MAX_NPCS, max(1, int(state.get("num_npcs", 5))))
    logger.info("generate_npcs: starting for %d NPCs …", num_npcs)
    llm = get_llm(max_tokens=8192)
    entities_json = json.dumps(state["entities"])
    callback = state.get("npc_added_callback")
    progress_cb = state.get("setup_progress_callback")

    async def _progress(label: str, current: int = 0, total: int = 0) -> None:
        if progress_cb:
            try:
                await progress_cb(label, current, total)
            except Exception:
                pass

    await _progress(f"Starting simulation with {num_npcs} residents...", 0, num_npcs)

    setting = detect_setting(state.get("policy_text", ""))
    town = TOWN[setting]
    country = "Switzerland" if setting == "ch" else "USA"
    langs = assign_langs(num_npcs, setting)

    extracted = await _extract_characters(state["policy_text"], entities_json, llm)
    extracted = extracted[:num_npcs]
    logger.info("generate_npcs: extracted %d characters from policy (setting=%s)", len(extracted), setting)
    await _progress(f"Extracted {len(extracted)} characters from source", len(extracted), num_npcs)

    used_names: set[str] = {c.get("name", "") for c in extracted if c.get("name")}

    # Process extracted NPCs to have base attributes for personality generation
    npc_bases: list[dict] = []
    for i, char in enumerate(extracted):
        lang = langs[i] if i < len(langs) else "en"
        char.setdefault("role", _infer_role(char))
        char.setdefault("gender", random.choice(["male", "female", "nonbinary"]))
        char.setdefault("mbti", random.choice(_MBTI_TYPES))
        char.setdefault("country", country)
        char.setdefault("lang", lang)
        char.setdefault("income_level", random.choice(_INCOME_LEVELS))
        char.setdefault("political_leaning", round(random.uniform(-1.0, 1.0), 2))
        char.setdefault("x", random.randint(0, MAX_X))
        char.setdefault("y", random.randint(0, MAX_Y))
        char.setdefault("mood", random.choice(_MOODS))
        char.setdefault("bio", f"A resident of {town}.")
        char.setdefault("life_story", "")
        char.setdefault("expert_reflection", "")
        npc_bases.append(char)

    needed = num_npcs - len(npc_bases)
    if needed > 0:
        logger.info("generate_npcs: generating %d random NPC bases …", needed)
        await _progress(f"Generating {needed} random residents...", 0, needed)
        npc_bases.extend(
            [
                _random_base(
                    len(npc_bases) + i,
                    used_names,
                    lang=langs[len(npc_bases) + i] if len(npc_bases) + i < len(langs) else langs[-1],
                    country=country,
                    role=(
                        (_ROLE_VALUES_CH if country == "Switzerland" else _ROLE_VALUES)[i % len(_ROLE_VALUES_CH if country == "Switzerland" else _ROLE_VALUES)]
                    ),
                )
                for i in range(needed)
            ]
        )

    # Pre-assign IDs before launching tasks so IDs are deterministic regardless of completion order.
    for i, base in enumerate(npc_bases):
        base["id"] = f"npc_{i + 1:02d}"
        base.setdefault("lang", langs[i] if i < len(langs) else "en")
        base.setdefault("country", country)

    logger.info("generate_npcs: generating personalities for %d NPCs …", len(npc_bases))
    await _progress(f"Generating {len(npc_bases)} personalities...", 0, len(npc_bases))
    tasks = [
        asyncio.create_task(_generate_personality(b, entities_json, llm, town))
        for b in npc_bases
    ]

    npcs: list[dict] = []
    for future in asyncio.as_completed(tasks):
        npc = await future
        if npc.get("role") not in _ROLE_VALUES:
            npc["role"] = _infer_role(npc)
        npc["reputation"] = _initial_reputation(npc)
        npc.setdefault("lang", "en")
        npc.setdefault("life_story", npc.get("bio", ""))
        npc.setdefault("expert_reflection", "")
        npcs.append(swissify_persona(npc))
        if callback:
            await callback(npc)

    await _progress("Eliciting initial stances...", 0, len(npcs))
    valence = float((state.get("entities") or [{}])[0].get("ideological_valence", 0.0) or 0.0)
    await elicit_stances(npcs, state["policy_text"], town, llm, valence=valence)

    logger.info("generate_npcs: generating relationships …")
    await _progress("Building social network...", 0, 0)
    relationships = await _generate_relationships(npcs, entities_json, llm)

    logger.info("generate_npcs: created %d relationships", len(relationships))

    npcs = _clamp_positions(npcs)
    return {
        "npcs": npcs,
        "relationships": relationships,
        "current_round": 0,
        "memory_streams": {npc["id"]: [] for npc in npcs},
    }
