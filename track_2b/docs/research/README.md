# GemeindeSim research record

Everything we analysed, decided and measured while testing what Apertus 1.5 can and cannot
do inside a multi-agent civic simulation. Written to be the raw material of a paper.

| File | What it is |
| --- | --- |
| [05-paper-draft.md](05-paper-draft.md) | The paper: question, method, results, discussion, limits |
| [LAB-NOTEBOOK.md](LAB-NOTEBOOK.md) | Chronological, append-only record of every analysis, decision, experiment, failure and correction |
| [03-results.md](03-results.md) | Consolidated results tables, baseline vs v2 |
| [04-pitch-audit.md](04-pitch-audit.md) | Every claim of the original pitch checked against evidence |
| [02-codebase-audit.md](02-codebase-audit.md) | Static audit written *before* the experiments (hypotheses stated up front) |
| [01-literature-review.md](01-literature-review.md) | ≈ 55 papers/pages, each tagged verified / search-snippet-only, with implications |
| [06-next-steps.md](06-next-steps.md) | What to do next, ranked |
| [ensemble_final_70.md](ensemble_final_70.md), [ensemble_final_8.md](ensemble_final_8.md) | Spread of the stance poll across 5 seeds (table + chart) |
| [../DEMO-SCRIPT.md](../DEMO-SCRIPT.md), [../SUBMISSION-CHECKLIST.md](../SUBMISSION-CHECKLIST.md) | Video shot list; submission checklist with what still needs a person |
| [../review/NATIVE-SPEAKER-REVIEW.md](../review/NATIVE-SPEAKER-REVIEW.md) | German/French review pack (49 items, rubric) + `research/summarize_review.py` |

## Research questions

1. **RQ1 (capabilities and limits).** Which of Apertus 1.5's documented and undocumented
   behaviours (tool calling, thinking, JSON, determinism, language fidelity, Swiss knowledge,
   long context, rate limits) matter for an agent loop, and how large are they?
2. **RQ2 (validity).** Does a population of Apertus residents behave like a population? Do
   personas produce disagreement, and does the simulated electorate resemble real Swiss
   voting?
3. **RQ3 (engineering).** Which parts of the pipeline fail *independently of the model*
   (retrieval, grounding, citations, dynamics, reporting), and what do fixes buy?

## Reproduce

All experiments are scripts in [`../../research/`](../../research); every gateway call is
logged in full (request + response) to `research/results/*.jsonl`.

```bash
cd track_2b
# needs track_2b/.env with LLM_API_KEY (the gateway allows ~4 requests in flight)
uv run --project src/backend python research/exp04_drift_artifact.py     # offline
uv run --project src/backend python research/exp06_numeral_gate.py       # offline
uv run --project src/backend python research/exp10_throughput.py         # key must be idle
uv run --project src/backend python research/exp01_probe.py
uv run --project src/backend python research/run_sim.py base_s1 --seed 1 # instrumented full run
uv run --project src/backend python research/analyze_sims.py base_s1
uv run --project src/backend python research/exp08_swissvotes.py         # ≈ 3 700 calls, ≈ 15 min
uv run --project src/backend python research/analyze_swissvotes.py
```

Run experiments **one at a time**: they share one API key and one 4-in-flight limit; an early
run of ours was contaminated by running two jobs together (notebook, E2 first attempt).

## Conventions

* Temperature 0 unless stated — which is *not* deterministic on this endpoint (E1).
* A single run is an anecdote; where we have only one, we say so.
* Numbers in the paper come from the logged data; nothing is quoted from memory.
* Negative results are kept (E2 first attempt, derived-arithmetic gate, balanced corpus).
