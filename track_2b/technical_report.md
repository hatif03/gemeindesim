# Technical report — GemeindeSim

A deeper write-up than the README: what you built, how it works, and what the
numbers say.

- **Track:** Track 2B — Own Project (GemeindeSim)
- **Event:** Hack Apertus online stage, October 2026
- **Team:** _TBD_
- **Demo:** _TBD (max. 2 min video URL)_

## 1. Summary

_GemeindeSim simulates how German- and French-speaking residents in a Swiss Gemeinde might discuss an official vote or municipal budget, with every factual claim tied to a closed corpus (Abstimmungsbüchlein excerpts or budget tables). Apertus 1.5-70B generates one schema-valid resident action per turn; the application owns retrieval, arithmetic, and validation. Headline result: TBD after eval harness (see `docs/PROBE-AND-PLAN.md` §8)._

## 2. Architecture

Components, data flow, and where each one runs. Put diagrams in `docs/` and
reference them here.

### Target architecture (mandatory)

**Primary:** **(c) Sovereign Swiss cloud** — app container + on-disk corpus; inference via Swiss-hosted OpenAI-compatible endpoint (`LLM_BASE_URL`, hackathon: `https://hackapertus.livemap.sh/v1`).

**Also supported:** **(a) On-premise** / **(b) Air-gapped** by pointing `LLM_BASE_URL` to local vLLM serving `swiss-ai/Apertus-v1.5-70B` and disabling outbound network in compose.

Build-time: Docker image build, optional `pip install`. Runtime: HTTP to configured LLM only; no open-web retrieval.

## 3. Use of Apertus

- **Model:** `apertus-v1.5-70b` (gateway id); weights `swiss-ai/Apertus-v1.5-70B` on Hugging Face
- **How it is used:** inference — structured JSON resident turns; optional thinking pass for explanations (separate from tools)
- **Where it runs:** Hack Apertus hosted endpoint for development; production story = Swiss sovereign provider or on-prem vLLM

Prompts, adapters, quantisation, serving stack — whatever a reader needs to
rebuild your setup.

## 4. Data

What you used, where it came from, and its licence. Flag anything personal or
non-redistributable, and keep it out of the repository (see `.gitignore`).
If data comes from human subjects or contains personal information, describe
how consent was obtained.

## 5. Evaluation

How you measured success: task, metric, baseline.

| Setup    | Metric | Result |
|----------|--------|--------|
| Baseline |        |        |
| Ours     |        |        |

## 6. Limitations

Where it breaks, what you did not test, and known failure modes.

## 7. Reproducibility

What a judge needs to get your numbers back: hardware, runtime, seeds, and the
exact commit. `make run` should do the rest.

## 8. Next steps

What you would build with another month.

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced.

## References
