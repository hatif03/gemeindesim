# GemeindeSim architecture

The shipped engine is FastAPI + LangGraph + Phaser, with an Apertus 1.5 adapter.

![GemeindeSim end to end](figures/fig01-pipeline.png)

*Blue = Apertus voices it; green = code owns it; red = code check or guardrail; sand = user input / screen.* Stance, household arithmetic, retrieval and citations, number gate, opinion dynamics and report guardrails are code; the model writes personas, dialogue and the report prose, and judges impact. How a stance is computed and moves: ![stance](figures/fig02-stance.png)

Figures are drawn by `research/make_figures.py` (PNG, so they render in any viewer).

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
