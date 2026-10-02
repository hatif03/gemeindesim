# Hack Apertus — context for GemeindeSim

Living reference for deadlines, links, and submission mechanics. Notion pages may require login; URLs below are the canonical entry points organizers publish.

## What this hackathon is

[Hack Apertus](https://hackapertus.ch/) is an open hackathon series around **Apertus**, Switzerland’s fully open LLM (weights, training story, alignment charter). The **online stage** (1–16 October 2026) is the first step; top work can advance toward **Grand Finals** (14 May 2027, St.Gallen).

GemeindeSim competes in **Track 2B — Own Project**: a new prototype started during the hackathon that must **use Apertus** as the core model.

## Official links

| Resource | URL |
| --- | --- |
| Programme site | https://hackapertus.ch/ |
| Devpost (register, dates) | https://hackapertus.devpost.com/ |
| Getting started guide (Notion) | https://hackapertus.notion.site/getting-started-guide-onlinehack |
| Resources & tools (Notion) | https://hackapertus.notion.site/resources-tools |
| Notion hub | https://hackapertus.notion.site/ |
| Project template | https://github.com/HackApertus/project-template |
| **Submissions (required)** | http://hackapertus.ch/online-hack/submissions |
| Code of conduct | https://hackapertus.ch/code-of-conduct |
| FAQ | https://hackapertus.ch/faq |
| Terms (open source, §6) | https://hackapertus.ch/terms-and-conditions |
| Discord | https://discord.gg/hack-apertus |
| Contact | hello@hackapertus.ch |

## Timeline (2026 online stage)

| When (CEST) | What |
| --- | --- |
| 13 Aug 2026 | Registrations open |
| **1 Oct 2026, 12:00** | Challenges released; hacking starts |
| 1 Oct 2026, 18:00 | Kick-off (see Devpost / Luma) |
| **16 Oct 2026, 12:00** | **Final submission deadline** (no extension) |
| 16–22 Oct 2026 | Judging |
| **23 Oct 2026, 12:00** | Estimated winners |

Devpost submission window: 1–16 October 2026. **Track deliverables** still go through the hackapertus.ch submission form, not Devpost alone.

## Tracks (where GemeindeSim fits)

| Track | Focus |
| --- | --- |
| 1A | Red-teaming Apertus |
| 1B | Swiss Voices (dialects, localization) |
| 2A | Academia challenges (five partner problems) |
| **2B** | **Own project** — GemeindeSim |

Track 2A challenges (for cross-pollination only):

- FHGR — job interview coach  
- OpenParlData — parliamentary PDF extraction  
- **OST — multilingual inference over official voting booklets** (closest to our corpus)  
- UZH — cross-lingual semantic diffs on government sites  
- ZHAW — vision-language robot arm  

We are **not** submitting as an OST team project unless we explicitly adopt their rubric; we reuse the **closed-corpus vote** idea under 2B.

## Track 2B judging (0–5 each)

1. **Purposeful use of AI** — simulation + citations, not generic chat  
2. **Technical rigour** — schema gate, eval harness, probe-backed limits  
3. **Value, cost & scalability** — small resident count, parallelizable rounds  
4. **Sovereign deployability** — target: Swiss sovereign cloud or on-prem Apertus weights  
5. **Implementation feasibility** — `make run`, Docker, clear env vars  

## Mandatory deployability story

Pick at least one and document it in `technical_report.md`:

- **(a) On-premise** — Gemeinde IT runs Apertus + our service internally  
- **(b) Air-gapped** — corpus and weights on sealed hardware; no runtime internet  
- **(c) Sovereign Swiss cloud** — e.g. CSCS / Swiss hosting with data residency  

GemeindeSim’s default demo path: **(c)** hackathon hosted endpoint for the model, **(a)** or **(b)** for corpus + app container without outbound calls except the configured `LLM_BASE_URL`.

## Repository rules (template)

- Work inside **`track_2b/`** — do not rename or move that folder  
- Delete other track directories (done in this repo)  
- **`make run`** from repo root must work on a clean checkout (Docker)  
- `data/` ≤ **100 MB** in repo  
- Repo **public** before submission  
- Env vars for judges:

```text
LLM_NAME
LLM_BASE_URL
LLM_API_KEY
```

## Submission checklist

- [ ] Public GitHub repo from [project-template](https://github.com/HackApertus/project-template)  
- [ ] `technical_report.md` complete → export **`TeamName_Report.pdf`** (max. 6 pages) into `track_2b/`  
- [ ] Demo video ≤ 2 minutes  
- [ ] Submit URLs via [online-hack/submissions](http://hackapertus.ch/online-hack/submissions)  
- [ ] Optional HF dataset from [HackApertus/online_hack_template](https://huggingface.co/datasets/HackApertus/online_hack_template)  
- [ ] Register on Devpost and join Discord  

## Apertus 1.5 (model)

| Asset | Link |
| --- | --- |
| Documentation | https://www.apertus-ai.org/pages/documentation/ |
| 8B weights | https://huggingface.co/swiss-ai/Apertus-v1.5-8B |
| 70B weights | https://huggingface.co/swiss-ai/Apertus-v1.5-70B |
| Getting started (API, tools, thinking) | https://blog.nlp-lab.ai/2026/10/01/Apertus15GettingStarted.html |
| 8B benchmarks (independent) | https://blog.nlp-lab.ai/2026/07/29/Apertus15Bench.html |

### Hackathon inference (our probe target)

| Setting | Value |
| --- | --- |
| Base URL | `https://hackapertus.livemap.sh/v1` |
| Model ids | `apertus-v1.5-8b`, `apertus-v1.5-70b` |
| API key | Issued per participant — store in `track_2b/.env`, never commit |

Gateway model ids differ from Hugging Face repo names.

### Engineering reminders (from probe)

- Tool calling: **one call per turn**; no parallel fan-out in a single completion  
- Do not combine **thinking mode** and **tools** in one request  
- Resident turns: **`json` mode**, filled example object, Pydantic repair  
- Facts: **closed corpus** + calculator; model quotes sources  

Full tables and build order: [PROBE-AND-PLAN.md](PROBE-AND-PLAN.md).

## Academia deep dives (optional viewing)

If we borrow datasets or rubrics from Track 2A partners, their sessions were advertised on [hackapertus.ch](https://hackapertus.ch/) and Discord (e.g. UZH SwissGov-RSD, FHGR SmartStart, OST fact-checking). Challenge READMEs in the study repo: `Desktop/apertus/track-2a/`.

## Next actions for this repo

1. Demo video ≤ 2 minutes
2. Export `TeamName_Report.pdf` from `technical_report.md`
3. Public GitHub + [submission form](http://hackapertus.ch/online-hack/submissions)
4. Native-speaker review of DE/FR resident lines (see `docs/FOR-JUDGES.md`)
