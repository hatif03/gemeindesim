# 04 — Pitch audit: every claim against the evidence

Sources audited: `docs/FOR-JUDGES.md`, `technical_report.md`, `README.md`,
`docs/PROBE-AND-PLAN.md`, `docs/HACKATHON.md` at commit `0bb53b2`.
Verdicts: **Supported** (measured, holds) · **Partly** (true with a material caveat) ·
**Unsupported** (not demonstrated) · **Refuted** (measured, contradicts) · **Not testable here**.
Experiment ids refer to `LAB-NOTEBOOK.md`. "v2" = the code after this work.

## A. Claims about how Apertus behaves

| # | Claim | Verdict | Evidence |
| --- | --- | --- | --- |
| A1 | Native parallel `tool_calls` fail; one structured call, rest dropped or faked as text | **Supported**, and extended | E1: 11/11 trials per model; also with `tool_choice="required"`; 70B emits pseudo-calls as text in 11/11 on the explicit two-call prompt |
| A2 | Thinking and tools are mutually exclusive | **Partly** | E1: tools + thinking in one request is *accepted* (22/22, one tool call, no reasoning span). What is truly incompatible is **thinking + `json_object`**: reasoning is silently skipped and the 70B answers the bat-and-ball puzzle wrongly (0.10) in 15 tokens |
| A3 | Thinking markers stay in `content`; `reasoning` is null | **Supported** | E1: 16/16 |
| A4 | Strong format following with thinking off | **Supported with a caveat** | E2: strict-JSON parse 100 % (n = 49 × both sizes); but the 70B had 14 % first-attempt *type* failures under the old schema and the 8B emitted one event per turn (E3) — format-following is not behaviour-following |
| A5 | `temperature: 0` gives a reproducible gate | **Refuted** | E1: five identical prompts → 3 (70B) / 5 (8B) distinct outputs |
| A6 | One language per completion; DE/FR residents stay in language | **Supported** | E3: 100 % language-correct (112 events across the 5 baseline runs, stop-word heuristic); translation hop fluent (read) |
| A7 | "Mid-pack factual recall, so facts live in the corpus" | **Supported** (strongly) | E7: 70B 12/15, 8B 9/15 on Swiss civic facts; both define *Steuerfuss* wrongly; both fail 4 000 × 6 % |
| A8 | "Facts live in the corpus **and a calculator**" | **Refuted** (calculator absent) → fixed in v2 | grep: only docs mention it; E7 shows the need; `graph/calculator.py` added |
| A9 | Apertus follows the Charter: no partisan side-taking, no vote advice | **Partly** | E9: 0/30 explicit vote advice, even when asked in DE/FR (good); but 4/5 default reports and 4/5 "did it pass?" reports **assert an invented outcome** |
| A10 | 8B is a graceful fallback "on overflow / long queues" | **Refuted** | E3/E2: 8B yields one `chat` per turn, 0 `move`, 7.5× faster; knowledge 9/15 (E7); 98 % deference to an authority recommendation (E8) |
| A11 | 262k context "used carefully"; stuffing full booklets "washes out the persona" | **Partly** | E12: single-fact recall 60/60 up to ≈ 105 k tokens (DE/FR, both sizes; 70B ≈ 36 s at 105 k). "Washes out the persona" and multi-fact reasoning remain **untested** |

## B. Claims about the application

| # | Claim | Verdict | Evidence |
| --- | --- | --- | --- |
| B1 | "Filled example JSON instance in the prompt (not a schema dump)" | **Refuted** (it was a placeholder instance) | `_schema_to_example` emits `"..."`, `0`, `true`; E2: placeholder → `to_x=to_y=0` on 82–96 % of 70B turns; a filled example anchors and is parroted (8B 53 %); instruction placeholders fixed both (E2b) |
| B2 | "Residents cite sources (`used_source_ids`)" | **Refuted** (0 % valid) → fixed in v2 | E3: 0/44, 0/37, 0/35, 0/25, 0/18 cited ids exist in the corpus; `grounded` was always true when no unknown numeral |
| B3 | "Residents may only quote figures that were retrieved or computed" (numeral gate) | **Partly** | E6: 8/12 edge cases; list numbering grounds digits 1–5, `replace` can corrupt `124`; v2 10/12 (residual: derived arithmetic, spelled-out numbers) |
| B4 | "Closed-corpus retrieval grounds every turn" | **Unsupported** by the shipped sample | E5: corpus ≈ 1.6 k chars/language, 4 passages ≈ half of it; the ballot question reached 0–33 % of prompts; language filter was a no-op |
| B5 | "Peralta-style opinion dynamics in code; the model does not update leaning by fiat" | **Supported** as a design fact; **Refuted** as a model of the vote | the variable it moves (`political_leaning`) is random, role-independent and not the stance on the Vorlage (audit B1–B2); E4: Baumann drift polarised a *silent* town (mean abs(x) 0.51 → 0.69 in 15 rounds); E8: abstract ideology does not predict concrete votes |
| B6 | "Residents differ by role, language, income, politics" (persona design) | **Refuted for stance** | E11: 15/15 yes under every persona condition, also with no persona; E11c: balanced corpus 14/15 yes |
| B7 | "Dashboard math is computed from events (Egg Index, prices, unrest, approval)" | **Partly** | computed in code, yes; but `price_pressure` reads `pct_change`, a field that does not exist in the event schema → always 0; for a tax vote price/unrest are structurally 0 (E3) |
| B8 | "Report describes tradeoffs, does not tell anyone how to vote; live run did this" | **Partly** | no advice (E9); but the report said the measure "passed" in 2/3 of 70B runs and mixed German text with an English disclaimer |
| B9 | "Default 70B, `LLM_CONCURRENCY=6`, 8B on overflow" | **Refuted** (6 > gateway limit 4) | E10, F7; 429 → silent swap to 8B |
| B10 | "Offline schema fixtures 20/20" as technical-rigour evidence | **Unsupported** | fixtures are hand-written valid objects; real first-attempt validity was 86 % (70B, old schema) |
| B11 | "Live 70B Linden run: parse ≈ 13 s … report in ≈ 11 s" | **Partly** | single-run anecdotes; E3: 219–235 s per clean 70B simulation (548 s when sharing the key with another job), mean call 14 s, gateway latency varies several-fold between minutes (E0) |
| B12 | `invoke_llm_think`: "optional thinking pre-pass for hard explanations" | **Unsupported** | defined, never called |
| B13 | Value/scalability: "small resident count, parallelizable rounds" | **Supported**, quantified | E10: linear to 4 in flight; 25 × 15 ≈ 17 min on 70B, ≈ 3.5 min on 8B (estimate from per-call latency) |
| B14 | Sovereign deployability: "swap `LLM_BASE_URL` to local vLLM / CSCS" | **Not testable here** | no local weights/GPU in this environment; config-only claim, plausible. The gateway behaviours we measured (single tool call, thinking in `content`, 4-in-flight) are properties of *that* deployment and must be re-probed on a local vLLM |

## C. What the evidence says the product is (and is not)

* **Is:** a bilingual, grounded, explainable what-if simulator whose LLM component is
  strong at *speaking in role in DE/FR*, *abstaining when facts are missing* and
  *arguing both sides when asked* — and which keeps numbers, stance and arithmetic out of
  the model's hands.
* **Is not:** a vote predictor (E8: persona/ideology add little; the Federal Council
  position alone beats every LLM condition that is not shown it; the 8B shown it scores 0.67 by following it), nor a source of Swiss civic facts (E7).
* **Judging fit:** the "limits of the model" are now measured and reproducible (parallel
  tools, thinking/JSON exclusion, non-determinism, yes-bias, authority deference, 4-in-flight
  limit, Swiss-fact errors). That is a stronger Track 2B story than the original claims.

---

## Status after the final measurements (final code, 5 seeds standard + 3 swarm; real booklet; clean-checkout deployment)

| claim | audited verdict | status now |
| --- | --- | --- |
| A8 "facts live in the corpus **and a calculator**" | Refuted (no calculator) | **Fixed**: `graph/calculator.py`; the resident's computed figure is in the prompt and the grounding pack |
| A9 Charter: no advice, no side-taking | Partly (invented outcomes) | **Fixed** for outcomes: 0/30 (E9b), 0/5 + 0/3 reports in the final runs, both sizes, both graphs; explicit advice never occurred (0/30) |
| B1 "filled example JSON" | Refuted (placeholder) | **Fixed and documented**: `<instruction>` placeholders in the resident's language (49/49 valid, 0 % parroting) |
| B2 "residents cite sources" | Refuted (0 % valid) | **Fixed**: 100 % of citation labels valid in all 16 final runs; 48–59 % of events carry a valid citation |
| B3 numeral gate | Partly (8/12) | **10/12**; residual: derived arithmetic (240/12) and spelled-out numbers (documented) |
| B4 closed-corpus retrieval | Unsupported by the sample | **Tested on a real 48-page booklet**: recall@4 11/14, QA 12/14 hand-graded, 3/3 abstentions; retrieval is the bottleneck |
| B5/B6 opinion dynamics, persona differences | Refuted for stance | **Redesigned**: stance computed in code; drift only for residents who conversed; speech matches stance 0.85–0.92 (was ≈ 0.5). Caveat: the prior's weights are assumptions |
| B7 dashboard "computed from events" | Partly (`price_pressure` dead) | Economy bars hidden when a stance poll exists; `price_pressure` still always 0 (documented) |
| B8 report "does not recommend a vote" | Partly | Conditional wording, localised disclaimer, language fixed (0/8 mixed, 0/8 asserted in the final runs) |
| B9 default concurrency 6, silent 8B fallback | Refuted | **Fixed** in code and in `docker-compose.yml` (default 4); 429 retried on the same model |
| B10 "schema fixtures 20/20" | Unsupported | Replaced by measured first-attempt validity (49/49) and 52 regression tests tied to findings |
| B12 `invoke_llm_think` pre-pass | Unsupported | Still unused; stated as such |
| B13 value / scalability | Supported | Quantified (E10, probe): linear to ≈ 4 in flight; 8B ≈ 4× faster per simulation |
| B14 sovereign deployability | Not testable | **Still not measured on a local model** (no GPU; the Docker VM here has ≈ 7 GB). Prepared: `research/probe_endpoint.py` (validated on the hosted 8B) and a clean-clone Docker stack that starts and serves |
| *new* `make run` on a clean checkout | (not audited before) | **Was broken in the original repo** (frontend image: no Linux native packages in either lockfile). Fixed (Node 22 + `npm install --legacy-peer-deps`), verified from a clean clone: UI 200 on both ports, API 200, concurrency 4 |
| *new* Docker default `SWARM=true` | (not audited before) | Swarm measured (+27 % time, no gain); default set to `false`, swarm kept as an option |
| A11 long context | Partly | unchanged: single-fact recall 60/60 up to ≈ 105 k tokens; persona dilution untested |
