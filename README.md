# GemeindeSim

**GemeindeSim** is our Hack Apertus submission: a multilingual civic simulation built on [Apertus 1.5](https://www.apertus-ai.org/). Residents in a Swiss Gemeinde react to an official **vote** (Vorlage / Abstimmungsbüchlein) or a **municipal budget** in German and French, grounded in a closed corpus—not the open web.

- **Hackathon:** [Hack Apertus](https://hackapertus.ch/) online stage, 1–16 October 2026  
- **Track:** [Track 2B — Own Project](track_2b/README.md) (template layout from [HackApertus/project-template](https://github.com/HackApertus/project-template))  
- **Study notes & probe report:** [track_2b/docs/PROBE-AND-PLAN.md](track_2b/docs/PROBE-AND-PLAN.md)  
- **Hackathon context:** [track_2b/docs/HACKATHON.md](track_2b/docs/HACKATHON.md)
- **Sibling submission (2A):** [OpenParlData Extract](https://github.com/hatif03/openparldata-extract)

## Repository layout

| Path | Purpose |
| --- | --- |
| `track_2b/` | **Project root** for judges—do not rename this folder |
| `track_2b/src/` | Application code |
| `track_2b/data/` | Corpus samples (max. 100 MB) |
| `track_2b/docs/` | Architecture, hackathon links, probe notes |
| `track_2b/technical_report.md` | Submission write-up (export to PDF for upload) |

## Quick start

1. Copy `track_2b/.env.example` to `track_2b/.env` and set your Hack Apertus inference key (never commit `.env`).
2. From this repository root:

```bash
make run
```

`make run` delegates to `track_2b/` and is expected to start the project via Docker once implemented.

## Environment variables (required by organizers)

| Variable | Example |
| --- | --- |
| `LLM_NAME` | `apertus-v1.5-70b` |
| `LLM_BASE_URL` | `https://hackapertus.livemap.sh/v1` |
| `LLM_API_KEY` | Your hackathon API key |

## Related material

Local crash-course notes (not part of this submission repo): `C:\Users\mdhat\Desktop\apertus\` on this machine.

## License

Apache-2.0 for template-derived files; see [LICENSE](LICENSE) and [Hack Apertus Terms](https://hackapertus.ch/terms-and-conditions).
