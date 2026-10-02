# GemeindeSim — repo setup

## Layout

- Template: [HackApertus/project-template](https://github.com/HackApertus/project-template)
- Track: **`track_2b/`** (Track 2B — Own Project)
- App: `track_2b/src/backend` (FastAPI) and `track_2b/src/frontend` (Next.js + Phaser)

Template remote is **`template-upstream`**. GitHub origin is the public submission repo.

## Local config

```bash
cp track_2b/.env.example track_2b/.env
# Edit track_2b/.env — set LLM_API_KEY (never commit)
```

## Run

From the repository root:

```bash
make run
```

UI: http://localhost:3000 (also 8080). Backend: http://localhost:8000.

Without Docker:

```bash
cd track_2b/src/backend && uv sync && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd track_2b/src/frontend && bun install && bun dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` for the frontend.

## Key docs

| File | Purpose |
| --- | --- |
| `track_2b/docs/FOR-JUDGES.md` | Briefing for judges and the Apertus team |
| `track_2b/docs/HACKATHON.md` | Deadlines, links, submission checklist |
| `track_2b/docs/PROBE-AND-PLAN.md` | Apertus probe + engineering plan |
| `track_2b/docs/ARCHITECTURE.md` | Module map |
| `track_2b/technical_report.md` | Submission report (export to PDF) |
| `track_2b/docs/screenshots/` | Live UI captures |
