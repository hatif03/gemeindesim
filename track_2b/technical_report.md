# Technical report — GemeindeSim

A deeper write-up than the README: what we built, how it works, and what the
numbers say.

- **Track:** Track 2B — Own Project (GemeindeSim)
- **Event:** Hack Apertus online stage, October 2026
- **Team:** hatif03
- **Demo:** screenshots in `docs/screenshots/`; video TBD (max. 2 min)

## 1. Summary

GemeindeSim is a generative-agent town simulation (Park et al. 2023 memory/retrieve/reflect/plan/act; Peralta et al. 2022 opinion dynamics) running on Apertus 1.5-70B. Users paste a Swiss municipal policy (bilingual Steuerfuss sample in `data/`) or an English tariff scenario. Residents act on a Phaser map with chat, move, protest, mood, and price events. Apertus emits schema-valid JSON; the application owns retrieval, dashboard arithmetic, validation, and social math.

Headline eval: offline schema fixtures 20/20. Live 70B Linden run (5 NPCs, 3 rounds): PolicyAnalysis valid (`controversy=medium`, `kind=vote`), DE/FR in-character chat on the map, economic report with no vote recommendation.

Judge briefing: `docs/FOR-JUDGES.md`.

## 2. Architecture

Two Docker services: FastAPI/LangGraph backend (`:8000`) and Next.js/Phaser frontend (`:3000` / `:8080`). Closed corpus on disk (`data/` mounted read-only). No open-web retrieval.

```text
policy upload → chunk/retrieve → parse → NPCs → N× run_round → Socket.IO → Phaser + report
```

### Target architecture (mandatory)

**Primary:** **(c) Sovereign Swiss cloud** — app containers + on-disk corpus; inference via Swiss-hosted OpenAI-compatible endpoint (`LLM_BASE_URL`, hackathon: `https://hackapertus.livemap.sh/v1`).

**Also supported:** **(a) On-premise** / **(b) Air-gapped** by pointing `LLM_BASE_URL` to local vLLM serving `swiss-ai/Apertus-v1.5-70B`.

## 3. Use of Apertus

- **Model:** `apertus-v1.5-70b` (gateway id); `apertus-v1.5-8b` on overflow
- **How:** `json` mode (thinking off, `response_format: json_object`, filled example object) for rounds, personas, and the economic report. Optional thinking pre-pass for hard explanations, never combined with tools. One language per completion; cross-language chat uses a separate translation call.
- **Where:** Hack Apertus hosted endpoint for development; production story = Swiss provider or on-prem vLLM.

Concurrency is a semaphore around completions (not native parallel `tool_calls`). Dashboard metrics are computed in code. Probe details: `docs/PROBE-AND-PLAN.md`.

## 4. Data

Synthetic bilingual Linden Steuerfuss/school-credit excerpts (`data/steuerfuss_linden_{de,fr}.txt`) and an English Millfield tariff sample (`data/tariff_millfield_en.txt`). Redistributable, fictional. No personal data. Official Swiss PDFs are not vendored.

## 5. Evaluation

Offline pytest: schema fixtures, mood enum mapping, numeral grounding, language detection (`src/backend/tests/test_apertus_gate.py`, `test_eval_schema.py`).

Live 70B (hackathon gateway, 3 October 2026): parse ~13s; 5 personalities; 3 rounds with 9–10 events each; reflections produced 3 insights per reflecting NPC; economic report narrative ~11s. Residents used Swiss names and mixed DE/FR chat (e.g. tenant Steuerfuss discussion vs. French shop-owner reply).

## 6. Limitations

Apertus does not emit parallel tool calls in one completion; thinking markers stay in `content` on this gateway; factual recall is mid-pack so numbers must appear in the retrieved pack. Swarm remains code-side initiator scoring. German/French administrative register still needs native-speaker review.

## 7. Reproducibility

`make run` from the repository root with `track_2b/.env` (`LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`). Python 3.12, Docker. Tests: `cd track_2b/src/backend && uv run pytest`.

## 8. Next steps

2-minute demo video; on-prem vLLM against the Swiss-AI container; native-speaker pass on DE/FR lines. Optional later: Italian, Swiss-German dialect, activation probes (`swiss-ai/apertus-probes`) when weights are local.

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced.

## References

- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. arXiv:2304.03442.
- Park, J. S., Zou, C. Q., Shaw, A., Hill, B. M., Cai, C., Morris, M. R., Willer, R., Liang, P., & Bernstein, M. S. (2024). Generative Agent Simulations of 1,000 People. arXiv:2411.10109.
- Peralta, A. F., Kertész, J., & Iñiguez, G. (2022). Opinion dynamics in social networks: From models to data. arXiv:2201.01322.
- Ramnath, K. et al. (2025). A Survey on Automatic Prompt Optimization. arXiv:2502.16923.
- Apertus 1.5 getting started: https://blog.nlp-lab.ai/2026/10/01/Apertus15GettingStarted.html
- Apertus Charter: https://www.apertus-ai.org/pages/charter/
- Data transparency: https://github.com/swiss-ai/apertus-data-transparency
