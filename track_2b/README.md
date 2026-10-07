# GemeindeSim — Track 2B: Own Project

**GemeindeSim** is a generative-agent town: paste a policy (Swiss vote/budget or an English economic shock), spawn residents on a pixel map, and watch prices, protests, moods, and conversations unfold. It runs on **Apertus 1.5**. The default demo uses German- and French-speaking residents in a fictional Gemeinde.

The product **explains** official material and livelihood effects. It does not campaign, recommend a vote, or replace legal advice. Design aligns with the [Apertus Charter](https://www.apertus-ai.org/pages/charter/).

**Judge briefing:** [docs/FOR-JUDGES.md](docs/FOR-JUDGES.md)  
**Research record (measured limits of Apertus 1.5, validity tests, audit, paper draft):** [docs/research/](docs/research/README.md)  
**Research foundations:** Park et al. 2023 (generative agents, arXiv:2304.03442); Park et al. 2024 interview grounding (arXiv:2411.10109); Peralta et al. 2022 (opinion dynamics); Apertus probe in `docs/PROBE-AND-PLAN.md`.

---

## Problem

How does a Vorlage, a municipal budget, or a tariff land across a mixed community — not a single average opinion? GemeindeSim uses Apertus 1.5 for structured resident turns while the application owns retrieval, dashboard math, schema validation, and social dynamics.

## What Apertus does here

- Structured JSON resident turns (`json` mode, thinking off): 1–3 events (chat, move, protest, mood_shift, price_change), one language per completion, translation as a separate call.
- Writes each resident's persona, the best argument **for and against** the measure in the resident's language, and the final report.
- Default model: **`apertus-v1.5-70b`** on the hackathon endpoint; `apertus-v1.5-8b` is ≈ 4× faster and works for the same schema.

## What the application owns (and why)

Measured on the hosted gateway (see [docs/research/](docs/research/README.md)): asked for a stance, every resident says *yes*; the model gets the booklet's arithmetic wrong; `temperature 0` is not reproducible; parallel tool calls and thinking-with-JSON do not work. So the **stance** (household cost, ideology, judged impact), the **household arithmetic**, the **citations** and the **opinion dynamics** are computed and checked in code; the model only voices them. GemeindeSim is a what-if explainer, **not a vote predictor** (tested on 54 real Swiss votes).

## Run it

Keep `track_2b/` as-is (Hack Apertus template rule). From the **repository root**:

```bash
cp track_2b/.env.example track_2b/.env   # set LLM_API_KEY
make run
```

Open **http://localhost:3000** (also published on **8080**; if that port is taken set `UI_ALT_PORT=18080` in `.env`). Backend API: **http://localhost:8000**.

The defaults are the **CSCS inference API** (`LLM_BASE_URL=https://api.inference.cscs.ch/v1`, `LLM_NAME=swiss-ai/Apertus-v1.5-70B`); the hackathon gateway works with the same build ([`docs/ENDPOINTS.md`](docs/ENDPOINTS.md)). The simulation screen has a collapsible **Run metrics** panel (tokens, cache share, context use, latency, requests in flight).

Optional `.env` switches: `LLM_CONCURRENCY` (default `auto`: adapts to the endpoint; a number fixes it), `LLM_VOICE_NAME` (another model for the report and the chat), `CHAT_STREAM`, `CHAT_STUFF_MAX_CHARS`, `EMBEDDING_MODEL` (optional hybrid retrieval), `SWARM=true|false` (two-phase initiator/reactor rounds), `LLM_NAME=swiss-ai/Apertus-v1.5-8B` for a fast run. The engineering questions behind these choices are answered in [`docs/ENGINEERING-QA.md`](docs/ENGINEERING-QA.md).

### Local development (without Docker)

```bash
cd track_2b
cp .env.example .env   # set LLM_API_KEY

cd src/backend && uv sync && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd src/frontend && npm install --legacy-peer-deps && npm run dev   # bun.lock lacks Linux native packages
```

Sample policies: `data/steuerfuss_linden_de.txt` + `_fr.txt` (bilingual default) or `data/tariff_millfield_en.txt`.

Screenshots from a live 70B Linden run: `docs/screenshots/`.

## Data

- `data/` holds **small, redistributable** samples. Max. **100 MB**.
- Do not commit full copyrighted PDFs without permission.

## Submission (Hack Apertus)

| Item | Where |
| --- | --- |
| Git repo (public) | This repository |
| Technical report | `technical_report.md` (export to PDF before the form) |
| Demo video | Max. 2 minutes (URL in submission form) |
| Submit form | [hackapertus.ch/online-hack/submissions](http://hackapertus.ch/online-hack/submissions) |

**Deadline:** 16 October 2026, 12:00 CEST.

## Judging criteria (Track 2B)

1. Purposeful use of AI
2. Technical rigour
3. Value, cost & scalability
4. Sovereign deployability (on-prem, air-gapped, or Swiss sovereign cloud)
5. Implementation feasibility
