# Technical report — GemeindeSim

A deeper write-up than the README: what we built, how it works, and what the
numbers say.

- **Track:** Track 2B — Own Project (GemeindeSim)
- **Event:** Hack Apertus online stage, October 2026
- **Team:** hatif03
- **Demo:** screenshots in `docs/screenshots/`; video TBD (max. 2 min)

## 1. Summary

GemeindeSim is a generative-agent town simulation (Park et al. 2023 memory/retrieve/reflect/plan/act; Peralta et al. 2022 opinion dynamics) running on Apertus 1.5-70B. Users paste a Swiss municipal policy (bilingual Steuerfuss sample in `data/`) or an English tariff scenario. Residents act on a Phaser map with chat, move, protest, mood, and price events. Apertus emits schema-valid JSON; the application owns retrieval, dashboard arithmetic, validation, and social math.

Headline eval (measured, `research/`, logged calls): on 49 real resident prompts the instruction-placeholder example gives 49/49 schema-valid first attempts on both sizes (the original gate: 86 % on the 70B); 112/112 utterances in the resident's language; on identical seeds v2.1 vs the first version: cited ids that exist 0 → 99–100 %, ballot question present in the resident prompt 13–30 % → 100 %, reports asserting an invented outcome 12/30 → 0/30. Model limits we measured: no parallel tool calls (11/11), thinking unusable with JSON mode, `T=0` not reproducible, 4 requests in flight, yes-biased and authority-deferential electorate on 54 real Swiss votes. Details: `docs/research/`.

Judge briefing: `docs/FOR-JUDGES.md`.

## 2. Architecture

Two Docker services: FastAPI/LangGraph backend (`:8000`) and Next.js/Phaser frontend (`:3000` / `:8080`). Closed corpus on disk (`data/` mounted read-only). No open-web retrieval.

```text
policy upload → chunk/retrieve → parse → NPCs → N× run_round → Socket.IO → Phaser + report
```

### Target architecture (mandatory)

**Primary:** **(c) Sovereign Swiss cloud** — app containers + on-disk corpus; inference via Swiss-hosted OpenAI-compatible endpoint (`LLM_BASE_URL`, hackathon: `https://hackapertus.livemap.sh/v1`).

**Also supported:** **(a) On-premise** / **(b) Air-gapped** by pointing `LLM_BASE_URL` to local vLLM serving `swiss-ai/Apertus-v1.5-70B`. **Status:** configuration only. The application's only outbound call is `LLM_BASE_URL`, and a clean-clone Docker stack starts and serves; but the model behaviours reported below were measured on the hosted gateway, and a local deployment was not run (no GPU available). `research/probe_endpoint.py` reproduces the behaviour table (tool calls, thinking, determinism, in-flight limit) on any OpenAI-compatible endpoint and was validated on the hosted 8B, so the sovereign claim can be completed in minutes on a GPU host.

## 3. Use of Apertus

- **Model:** `apertus-v1.5-70b` (gateway id); `apertus-v1.5-8b` on overflow
- **How:** `json` mode (thinking off, `response_format: json_object`, a three-event example with `<instruction>` placeholders in the resident's language) for rounds, personas, stance arguments and the economic report. No thinking pre-pass is wired (the helper exists, unused); thinking is never combined with JSON mode (it silently skips the reasoning, research E1). One language per completion; cross-language chat uses a separate translation call. The model **voices**; the application **owns** the stance, the household arithmetic (a deterministic calculator) and the sources (validated citation labels).
- **Where:** Hack Apertus hosted endpoint for development; production story = Swiss provider or on-prem vLLM.

Concurrency is a semaphore (default 4: the hosted gateway returns 429 above ≈ 4 in flight) around completions, not native parallel `tool_calls`; a 429 is retried on the same model. Dashboard metrics are computed in code. Probe details: `docs/PROBE-AND-PLAN.md` (replicated and corrected in `docs/research/`).

## 4. Data

Synthetic bilingual Linden Steuerfuss/school-credit excerpts (`data/steuerfuss_linden_{de,fr}.txt`) and an English Millfield tariff sample (`data/tariff_millfield_en.txt`). Redistributable, fictional. No personal data. Official Swiss PDFs are not vendored.

## 5. Evaluation

Offline pytest (`cd src/backend && uv run pytest --deselect tests/test_e2e.py`; the new regression tests in `tests/test_research_fixes.py` each pin a finding). The earlier "schema fixtures 20/20" validated hand-written objects, not model output, and is no longer cited.

Measured on the live hackathon gateway (5 October 2026; every call logged in `research/results/`; method and caveats in `docs/research/05-paper-draft.md`):

| Question | Result |
| --- | --- |
| Structured output on 49 real resident prompts | 49/49 first-attempt valid (both sizes) with `<instruction>` example; old gate 86 % on the 70B (nulls in string fields) |
| Language fidelity | 112/112 utterances in the resident's language |
| Retrieval / grounding, baseline → final code (16 runs) | ballot question in prompt 13–30 % → 100 %; valid citation labels 0 → 100 % |
| Real 48-page Federal Council booklet | recall@4 11/14 (old retriever 10/14); grounded QA 12/14 (hand-graded), 3/3 unanswerable questions abstained; retrieval is the bottleneck |
| Speech vs stance (465 lines, two classifiers) | resident's words match their code stance 0.46–0.55 → **0.85–0.92** (undecided residents: 0.5–0.7) |
| Report (6 objectives × 5 samples) | invented outcome 12/30 → 0/30; explicit vote advice 0/30 before and after |
| Swiss civic facts (15 questions) | 70B 12/15, 8B 9/15; both wrong on *Steuerfuss* and on 4 000 × 6 % |
| Stance when asked directly | 15/15 "yes" under every persona condition, also with a balanced booklet (stance is therefore code-owned) |
| 54 real federal votes, ballot title only | simulated yes-share 34–37 pp too high; Spearman 0.25–0.38 (70B personas); Federal Council position alone: 0.63 |
| Throughput | 4 requests in flight; 70B ≈ 156 tok/s, 8B ≈ 555 tok/s at that limit |

Baseline vs final code on identical seeds (5 residents × 3 rounds; standard graph 70B n = 5, 8B n = 5; swarm graph n = 3 + 3; baseline n = 3 + 2): events 27 → 33 (70B), 15 → 32 (8B); self-introductions 27 % → 0 %; reports asserting a result or mixing languages 2/3 and 3/3 → 0/16; influence log 0 → 49–77 outcomes per group (it had been silently dropped). The stance poll differs a lot from seed to seed (share *for* at the end 0.00–0.80 on the 70B), so the demo shows a distribution, not one run.

**Deployment check.** A clean clone of the original repository could not build the frontend image (no Linux native packages in either lockfile); fixed and verified from a fresh clone (UI and API serve; concurrency 4). `SWARM` now defaults to `false` (swarm: +27 % wall time, no gain). A local Apertus was not run (no GPU); `research/probe_endpoint.py` produces the behaviour table for any OpenAI-compatible endpoint and was validated on the hosted 8B.

## 6. Limitations

Model: no parallel tool calls in one completion (11/11); thinking markers stay in `content` and thinking is skipped under JSON mode; `temperature 0` is not reproducible; a strong *yes* default and near-total deference to an official recommendation (8B: 98 %); elementary Swiss facts and arithmetic are unreliable, so numbers come from the corpus or the calculator. Application: **not a vote predictor** (54 real votes; only a weak signal after bias correction); the stance prior weights are assumptions, not calibrated; the Linden sample (1.6 k characters per language) does not stress retrieval; n is small (3 and 2 simulations per group, 15 residents in population tests). German/French register still needs native-speaker review (Swiss orthography is enforced in code). Gateway behaviour must be re-probed on a local vLLM before claiming sovereign parity. Open defects: `price_pressure` indicator is always 0, `invoke_llm_think` is unused. Swarm remains code-side initiator scoring.

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
