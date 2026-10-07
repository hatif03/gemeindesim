"""Application configuration."""

import os
import re
import warnings
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# track_2b/.env (judges) then backend/.env then .env.local
_backend = Path(__file__).parent
_track = _backend.parent.parent
load_dotenv(_track / ".env")
load_dotenv(_backend / ".env")
load_dotenv(_backend / ".env.local", override=True)

# Grid dimensions
GRID_WIDTH = 20
GRID_HEIGHT = 15
MAX_X = GRID_WIDTH - 1
MAX_Y = GRID_HEIGHT - 1

MAX_NPCS = 25

# Simulation timeline: 3 phases × 5 rounds each = 15 total rounds.
NUM_PHASES = 3
ROUNDS_PER_PHASE = 5
DEFAULT_NUM_ROUNDS = NUM_PHASES * ROUNDS_PER_PHASE

# Memory stream parameters (Park et al. 2023, arXiv:2304.03442).
MEMORY_TOP_K = 8
RECENCY_DECAY = 0.8
REFLECTION_THRESHOLD = 25
REFLECTION_MAX_PER_ROUND = 5

# Hack Apertus / organizer env names (OpenAI-compatible endpoint). The same checkpoints are served by the hackathon gateway ("livemap",
# ids like `apertus-v1.5-70b`) and by the CSCS inference API (ids like `swiss-ai/Apertus-v1.5-70B`); research E20-E28 measured both.
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.inference.cscs.ch/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

_APERTUS_ID = re.compile(r"^(?:swiss-ai/)?apertus-v1\.5-(\d+)b(-thinking)?$", re.IGNORECASE)


def resolve_model(name: str, base_url: str = "") -> str:
    """Make an Apertus v1.5 id valid for the endpoint it will be sent to, so the two endpoints are interchangeable.

    CSCS: `swiss-ai/Apertus-v1.5-70B`; livemap: `apertus-v1.5-70b`. Any other id (a local vLLM, another family) is returned unchanged."""
    m = _APERTUS_ID.match((name or "").strip())
    if not m:
        return name
    size, think = m.group(1), (m.group(2) or "").lower()
    host = urlparse(base_url or LLM_BASE_URL).netloc.lower()
    if "cscs.ch" in host:
        return f"swiss-ai/Apertus-v1.5-{size}B{think}"
    if "livemap" in host:
        return f"apertus-v1.5-{size}b"  # livemap serves no thinking variant: the plain model is the closest valid id
    return name


def smaller_model(name: str) -> str:
    """The 8B that goes with a 70B id (same naming style); the name itself when there is no smaller sibling."""
    m = _APERTUS_ID.match(name or "")
    if not m or m.group(1) == "8":
        return name
    return resolve_model(re.sub(r"70b", "8b", name, flags=re.IGNORECASE), LLM_BASE_URL)


LLM_NAME = resolve_model(os.environ.get("LLM_NAME", "swiss-ai/Apertus-v1.5-70B"), LLM_BASE_URL)
LLM_FALLBACK_NAME = resolve_model(os.environ.get("LLM_FALLBACK_NAME", "") or smaller_model(LLM_NAME), LLM_BASE_URL)
# Optional: a different (usually larger) model for what the user reads (report, 1:1 chat) while the resident loop runs LLM_NAME.
LLM_VOICE_NAME = resolve_model(os.environ.get("LLM_VOICE_NAME", ""), LLM_BASE_URL)
# Requests in flight. `auto` (default) starts at 4 and adapts: +1 after 8 clean answers up to LLM_CONCURRENCY_MAX, halved on a 429 or a gateway timeout
# (research E10: livemap answers 429 above 4-5; E21: CSCS showed no limit to 96). A number fixes it.
LLM_CONCURRENCY_MAX = 32
try:
    LLM_CONCURRENCY_MAX = max(1, int(os.environ.get("LLM_CONCURRENCY_MAX", "32")))
except ValueError:
    pass
_raw_concurrency = os.environ.get("LLM_CONCURRENCY", "auto").strip().lower()
LLM_CONCURRENCY_ADAPTIVE = _raw_concurrency in ("", "auto")
try:
    LLM_CONCURRENCY = 4 if LLM_CONCURRENCY_ADAPTIVE else max(1, int(_raw_concurrency))
except ValueError:
    LLM_CONCURRENCY, LLM_CONCURRENCY_ADAPTIVE = 4, True
try:
    LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0"))
except ValueError:
    LLM_TEMPERATURE = 0.0

if not LLM_API_KEY:
    warnings.warn("LLM_API_KEY is not set — LLM calls will fail", stacklevel=1)

# 1:1 chat: send the answer sentence by sentence while the model writes (each sentence is checked before it is sent); 0 = one message at the end.
CHAT_STREAM = os.environ.get("CHAT_STREAM", "1") != "0"

# Swarm mode: two-phase NPC round execution (orchestrator picks initiators first)
SWARM = os.environ.get("SWARM", "").lower() in ("true", "1", "yes")
