# GemeindeSim — Track 2B: Own Project

Multilingual **civic simulation** for Swiss democracy: paste or select an official **vote** or **municipal budget** context, spawn German- and French-speaking residents, run a short grounded simulation, and inspect utterances with **source citations** from a closed corpus.

The product **explains** official material. It does not campaign, recommend a vote, or replace legal advice. Design aligns with the [Apertus Charter](https://www.apertus-ai.org/pages/charter/).

**Team / repo:** fill in before submission.  
**Inspired by (not a copy of):** generative-agent town sims; OST-style closed-corpus vote materials; our Apertus probe in `docs/PROBE-AND-PLAN.md`.

---

## Problem

Voters and municipal staff need to see how a Vorlage or budget line might land across a mixed **DE/FR** community—not a single average opinion. GemeindeSim uses Apertus 1.5 for **one grounded narrative step per resident** while the application owns retrieval, numbers, schema validation, and social dynamics.

## What Apertus does here

- Structured JSON resident turns (`json` mode, thinking off)
- Optional `think` then `json` for hard explanations (never combined with tools in one request)
- Multilingual dialogue per resident (`de` or `fr` per call)
- Default model for visible copy: **`apertus-v1.5-70b`** on the hackathon endpoint

## Run it

Keep `track_2b/` as-is (Hack Apertus template rule). From the **repository root**:

```bash
make run
```

Implementation status: Docker entrypoint is stubbed until the simulation service lands in `src/`. See `Makefile` and `docker-compose.yml`.

### Local development (before Docker is complete)

```bash
cd track_2b
cp .env.example .env   # set LLM_API_KEY
# python -m venv .venv && pip install -e .
# uv run python -m gemeindesim  # when CLI exists
```

Requirements for judges: documented in `technical_report.md` (runtime, hardware, API keys).

## Data

- `data/` holds **small, redistributable** samples (booklet excerpts, budget tables). Max. **100 MB**.
- Do not commit full copyrighted PDFs without permission; store `source_id` metadata and fetch instructions in the technical report.

## Submission (Hack Apertus)

| Item | Where |
| --- | --- |
| Git repo (public) | This repository |
| Technical report PDF | `track_2b/TeamName_Report.pdf` + `technical_report.md` |
| Demo video | Max. 2 minutes (URL in submission form) |
| Submit form | [hackapertus.ch/online-hack/submissions](http://hackapertus.ch/online-hack/submissions) — **not** Devpost alone |
| Getting started guide | [Notion — Getting started](https://hackapertus.notion.site/getting-started-guide-onlinehack) |
| Resources & tools | [Notion — Resources](https://hackapertus.notion.site/resources-tools) |

**Deadline:** 16 October 2026, 12:00 CEST (no extension).  
**Devpost:** [hackapertus.devpost.com](https://hackapertus.devpost.com/) for registration and timeline.

## Judging criteria (Track 2B)

1. Purposeful use of AI  
2. Technical rigour  
3. Value, cost & scalability  
4. Sovereign deployability (on-prem, air-gapped, or Swiss sovereign cloud)  
5. Implementation feasibility  

## Support

- Discord: [discord.gg/hack-apertus](https://discord.gg/hack-apertus)  
- Email: hello@hackapertus.ch  
- FAQ: [hackapertus.ch/faq](https://hackapertus.ch/faq)  
- Terms: [hackapertus.ch/terms-and-conditions](https://hackapertus.ch/terms-and-conditions)
