"""Application configuration."""

import os
import warnings
from pathlib import Path

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

# Hack Apertus / organizer env names (OpenAI-compatible gateway).
LLM_NAME = os.environ.get("LLM_NAME", "apertus-v1.5-70b")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://hackapertus.livemap.sh/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_FALLBACK_NAME = os.environ.get("LLM_FALLBACK_NAME", "apertus-v1.5-8b")
# Optional: a different (usually larger) model for what the user reads (report, 1:1 chat) while the resident loop runs LLM_NAME.
LLM_VOICE_NAME = os.environ.get("LLM_VOICE_NAME", "")
# The hackathon gateway answers 429 above ~4 requests in flight (research E10), so default to 4.
try:
    LLM_CONCURRENCY = max(1, int(os.environ.get("LLM_CONCURRENCY", "4")))
except ValueError:
    LLM_CONCURRENCY = 4
try:
    LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0"))
except ValueError:
    LLM_TEMPERATURE = 0.0

if not LLM_API_KEY:
    warnings.warn("LLM_API_KEY is not set — LLM calls will fail", stacklevel=1)

# Swarm mode: two-phase NPC round execution (orchestrator picks initiators first)
SWARM = os.environ.get("SWARM", "").lower() in ("true", "1", "yes")
