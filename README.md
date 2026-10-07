# GemeindeSim

**GemeindeSim** is our Hack Apertus Track 2B submission: a generative-agent town running on [Apertus 1.5](https://www.apertus-ai.org/). Paste a Swiss municipal vote or budget (German and French) or an English economic policy, spawn residents on a pixel map, and watch prices, protests, moods, and conversations unfold.

Start here if you are judging or reviewing the work:

- **[Briefing for judges](track_2b/docs/FOR-JUDGES.md)** — what we built, why Apertus, how the model is used, research, open questions
- **Hackathon:** [Hack Apertus](https://hackapertus.ch/) online stage, 1–16 October 2026
- **Track:** [Track 2B — Own Project](track_2b/README.md)
- **Architecture:** [track_2b/docs/ARCHITECTURE.md](track_2b/docs/ARCHITECTURE.md)
- **Apertus probe notes:** [track_2b/docs/PROBE-AND-PLAN.md](track_2b/docs/PROBE-AND-PLAN.md)
- **Screenshots:** [track_2b/docs/screenshots/](track_2b/docs/screenshots/)

Research foundations: Park et al. 2023 (generative agents, arXiv:2304.03442); Park et al. 2024 interview grounding (arXiv:2411.10109); Peralta et al. 2022 (opinion dynamics).

## Repository layout

| Path | Purpose |
| --- | --- |
| `track_2b/` | **Project root** for judges — do not rename this folder |
| `track_2b/src/backend` | FastAPI + LangGraph |
| `track_2b/src/frontend` | Next.js + Phaser |
| `track_2b/data/` | Sample policies (max. 100 MB) |
| `track_2b/docs/` | Architecture, hackathon links, judge briefing, probe notes |
| `track_2b/technical_report.md` | Submission write-up |

## Quick start

1. Copy `track_2b/.env.example` to `track_2b/.env` and set `LLM_API_KEY`.
2. From this repository root:

```bash
make run
```

UI: **http://localhost:3000** (also on **8080**; set `UI_ALT_PORT` in `track_2b/.env` if 8080 is already in use). API: **http://localhost:8000**.

## Environment variables (required by organizers)

| Variable | Example |
| --- | --- |
| `LLM_NAME` | `swiss-ai/Apertus-v1.5-70B` (CSCS) or `apertus-v1.5-70b` (hackathon gateway): either style is accepted on either endpoint |
| `LLM_BASE_URL` | `https://api.inference.cscs.ch/v1` (CSCS, used for judging) or `https://hackapertus.livemap.sh/v1` |
| `LLM_API_KEY` | The key of that endpoint |

One build runs on both endpoints (model ids are mapped, concurrency adapts): [`track_2b/docs/ENDPOINTS.md`](track_2b/docs/ENDPOINTS.md).

## License

Apache-2.0 for template-derived files; see [LICENSE](LICENSE) and [Hack Apertus Terms](https://hackapertus.ch/terms-and-conditions).
