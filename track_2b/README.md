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

- Structured JSON resident turns (`json` mode, thinking off) — 1–3 events: chat, move, protest, mood_shift, price_change
- Optional `think` then `json` for hard explanations (never combined with tools)
- One language per completion (`de`, `fr`, or `en`); translation is a separate call
- Default model: **`apertus-v1.5-70b`** on the hackathon endpoint

## Run it

Keep `track_2b/` as-is (Hack Apertus template rule). From the **repository root**:

```bash
cp track_2b/.env.example track_2b/.env   # set LLM_API_KEY
make run
```

Open **http://localhost:3000** (also published on **8080**). Backend API: **http://localhost:8000**.

### Local development (without Docker)

```bash
cd track_2b
cp .env.example .env   # set LLM_API_KEY

cd src/backend && uv sync && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd src/frontend && bun install && bun dev
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
