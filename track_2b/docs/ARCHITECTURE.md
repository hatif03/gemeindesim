# GemeindeSim architecture

The shipped engine is FastAPI + LangGraph + Phaser, with an Apertus 1.5 adapter.

```text
User pastes / uploads policy (DE/FR/EN)
        │
        ▼
┌───────────────────┐
│ PDF/CSV/notes     │  routers/extract.py + context_store
│ chunk + retrieve  │  graph/corpus.py (closed corpus)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     Apertus json mode (70B)
│ parse_policy      │
│ generate_npcs     │──── frozen cards + life_story (de|fr|en)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ run_round         │  Park loop: retrieve → reflect → plan → act
│  (or swarm)       │  1–3 events: chat/move/protest/mood/price
│                   │  opinion dynamics in code
└─────────┬─────────┘
          │ Socket.IO
          ▼
┌───────────────────┐
│ Phaser + dashboard│  Egg Index, prices, unrest, social graph
│ economic report   │  no vote recommendation
└───────────────────┘
```

## Code map (`src/`)

| Path | Role |
| --- | --- |
| `src/backend/config.py` | `LLM_*`, swarm, concurrency, grid |
| `src/backend/graph/llm.py` | json / think modes, inner-span strip, repair, semaphore |
| `src/backend/graph/corpus.py` | chunk + lexical retrieve |
| `src/backend/graph/language.py` | glossaries, translation hop, numeral check |
| `src/backend/graph/nodes/run_round.py` | cognitive loop + five event types |
| `src/backend/models/schemas.py` | Pydantic contract |
| `src/frontend/` | Next.js + Phaser |

## Sovereign deployability (Track 2B)

**Primary:** Dockerized app + on-disk corpus; `LLM_BASE_URL` is a Swiss-hosted OpenAI-compatible endpoint (hackathon gateway now).

**Air-gapped / on-prem:** point `LLM_BASE_URL` at local vLLM serving `swiss-ai/Apertus-v1.5-70B`; no outbound network except that URL.
