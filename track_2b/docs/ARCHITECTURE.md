# GemeindeSim architecture (draft)

High-level design aligned with [PROBE-AND-PLAN.md](PROBE-AND-PLAN.md). Update as `src/` lands.

```text
User selects Vorlage / budget
        │
        ▼
┌───────────────────┐
│ Corpus + retrieve │  data/ + source_id chunks (DE/FR)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     LLM json mode (70B)
│ Persona seed      │────► frozen resident cards (de | fr)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Round loop        │  code: memory, nearby ids, stance math
│  └► one action   │────► Apertus: single ResidentAction JSON
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Report            │────► cited summary (no vote recommendation)
└───────────────────┘
```

## Planned `src/` modules

| Module | Role |
| --- | --- |
| `gemeindesim/client.py` | `LLM_*` env, json / tool_one / think modes |
| `gemeindesim/schema.py` | Pydantic + repair + fallback line |
| `gemeindesim/corpus.py` | Chunk store |
| `gemeindesim/retrieve.py` | Search over corpus only |
| `gemeindesim/residents.py` | Personas, memory, stance |
| `gemeindesim/round.py` | One action per speaking resident |
| `gemeindesim/report.py` | Final narrative from aggregates |
| `gemeindesim/eval/` | Schema, language, citation checks |

## Sovereign deployability (Track 2B)

**Primary story:** Dockerized app + on-disk corpus; `LLM_BASE_URL` points to a **Swiss-hosted** Apertus endpoint (hackathon gateway for demo, CSCS / Swiss provider in production).

**Air-gapped variant:** swap endpoint for local vLLM serving `swiss-ai/Apertus-v1.5-70B` weights; no outbound network at runtime.
