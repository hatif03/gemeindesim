# 02 — Codebase audit (static, before experiments)

Scope: `track_2b/src/backend` at commit `0bb53b2`. Read line by line before any
experiment so hypotheses are stated *before* the data. Each item lists the
evidence type: **S** = static reading only, **M** = measured (experiment id).
Severity: **A** = invalidates a claim or user-visible correctness; **B** = quality
or scientific-validity gap; **C** = hygiene.

## A. Correctness / claim-validity

| # | Where | Issue | Evidence |
| --- | --- | --- | --- |
| A1 | `services/economic_report.py`, `prompts.py:211` | The report prompt never says the vote has not happened, and the simulation computes no stance/outcome. The model therefore narrates a result ("Die Vorlage … bewilligte …"). | M: E3a, E9 |
| A2 | `config.py:41` + `graph/llm.py:278-284` | Default concurrency 6 > gateway limit 5; a 429 swaps the retry to the 8B silently. | M: F7 |
| A3 | `graph/corpus.py:112-122` | One language tag per source block → DE/FR filter is a no-op on the shipped bilingual sample. | M: E5 |
| A4 | `graph/language.py:46-61` | Numeral gate: list indices ground small integers; `str.replace` can corrupt grounded numbers; correct derived arithmetic is stripped. | M: E6 |
| A5 | `nodes/run_round.py:520-525` | `grounded` is `not extra and bool(used_source_ids or pack)`; `pack` is always non-empty so the id check is vacuous; `used_source_ids` are never validated against the pack. | M: E3a (ids are `'2','3'`) |
| A6 | `nodes/run_round.py:738-743` | Baumann drift applied to every resident every round, with no interaction required. | M: E4 |
| A7 | `models/schemas.py:176-177` | `target_npc_id: str`, `dialogue: str` reject `null`, which the model emits when it copies a placeholder; costs a retry. | M: batch log |

## B. Scientific validity / modelling

| # | Where | Issue | Literature hook |
| --- | --- | --- | --- |
| B1 | `npc_orchestrator._random_base` | `political_leaning ~ U(−1,1)` independent of role, language, canton, policy. Opinion dynamics then evolve a variable that is not the stance on the Vorlage. | Barmettler 2026 (abstract leaning ≠ concrete vote); Chuang 2024 |
| B2 | whole sim | No explicit per-resident stance on the question; "policy_approval" is derived from mood. No outcome, no distribution to compare. | Park 2024 (evaluate against ground truth) |
| B3 | `run_round.py:595-601` | Influence uses `reputation`/`trust`; Deffuant parameters (μ, ε) and Chacoma–Zanette thresholds are imported from tasks on numeric estimates (85 students), not political stance. No sensitivity analysis. | Peralta 2022 §3.3 |
| B4 | `llm.py:46-53` | Temperature fixed at 0 for every resident and every call. | Atil 2024; Ye 2026 |
| B5 | `prompts.py:149-186` | Prompt for residents lists nearby people by *name* but asks for `target_npc_id`; ids are only shown for "people you know". Chat-target repair (`_validate_chat_target`) then silently rewrites the target. | M: pending (E3 corpus of rewrites) |
| B6 | `run_round.py:464` | Retrieval query = English LLM summary + names + round blurb; corpus is DE/FR → mostly non-matching tokens; question chunk reaches 4/15 prompts. | M: E5 |
| B7 | `corpus.py:80-109` | Fixed 420-char windows cut words; no sentence/paragraph structure; header leaks into chunk 0. | M: E5 |
| B8 | dashboard indicators | `price_pressure`, `social_unrest_index`, "Egg Index" were designed for tariff scenarios; a tax vote produces 0 price events and 0 protests. | M: E3a |
| B9 | `economic_report.py:24-25,29` | Layoff/closure regexes are English-only; vote-advice regex covers few patterns; report output language not controlled; `NO_VOTE_LINE` is English inside a German report. | M: E3a, E9 |
| B10 | `npc_orchestrator._generate_relationships` | Relationships are random pairs (the `llm` argument is unused); strength comes from a keyword heuristic over *profession strings* (English keywords: `steel`, `factory`, `union`). Swiss DE/FR professions never match. | S |
| B11 | `_random_base` | `gender = choice([male, female, nonbinary])` with a name pool for male/female only → non-binary draws get male names; uniform draw is not a demographic model. | S |

## C. Hygiene

- C1 `tests/test_e2e.py::test_full_pipeline` calls the live gateway inside the "offline" suite (E0).
- C2 `test_eval_schema.py` "20/20 fixtures" validates hand-written objects, not model outputs; it cannot support a claim about Apertus.
- C3 `_ainvoke` falls back to a non-JSON call on *any* exception (including auth and rate-limit), doubling load exactly when the gateway is saturated.
- C4 `technical_report.md`/`FOR-JUDGES.md` say "filled example JSON"; `_schema_to_example` emits placeholder strings (`"..."`, `0`, `true`). E2 tests whether that matters.
- C5 `translated_dialogue` is not passed through the numeral gate.
- C6 Frontend reads `political_leaning` and `economic_indicators` (additive backend fields are safe).

## What the audit predicts (to be checked)

1. Placeholder-example prompting echoes defaults (`to_x=0,to_y=0`, `grounded=true`).
2. Filled-example prompting raises validity on 8B but invites copying.
3. `response_format=json_object` is the decisive reliability lever.
4. Residents will not differ in stance by role unless role is tied to a stake.
5. The report will assert outcomes under at least some objectives.

---

## Added during the experiments (not visible from reading the code)

| # | Finding | How it was found | Status |
| --- | --- | --- | --- |
| N1 | The promised **calculator does not exist**; the model gets the corpus' own arithmetic wrong | grep for "calculat" (docs only); E7 | fixed: `graph/calculator.py` |
| N2 | `influence_events` **dropped by LangGraph** (undeclared in `SimState`): frontend influence layer and the keep/compromise/adopt log never received data | `influence outcomes: none recorded` in all baseline runs; minimal LangGraph repro | fixed |
| N3 | `invoke_llm_think` is **dead code**; no thinking pre-pass exists | grep | open (documented) |
| N4 | `price_pressure` indicator is **always 0**: reads `pct_change`, which the event schema does not contain | reading `_compute_economic_indicators` | open (documented) |
| N5 | "Extract named characters" **hallucinates**: a resident named "Gemeinde Linden" (document title) and an invented "farmer Alice Martin" in 8B runs | persona read-through | fixed (literal-name filter) |
| N6 | `role` is assigned by list index, not by the persona: a "tenant" who is a self-employed handyman, a "tenant" who is an urban-planning consultant; role gates which events are plausible (price changes, protests) | persona read-through | open |
| N7 | LLM-written personas are homogeneous (nearly all "grew up in Linden", studied at the local school) and every persona is asked for a "secret controversial idea" (prompt-induced) | persona read-through (E3) | partly: prompt asks for varied backgrounds |
| N8 | The 8B writes German-German school vocabulary (*Abitur*, *Gesamtschule*, *Stadtplaner*) in a Swiss town | persona read-through | prompt rule added; not re-measured |
| N9 | Prompt asks for `target_npc_id` but lists nearby people by name only (24 of 39 chat targets were names) | raw output parse (F11) | fixed (ids shown) |
| N10 | The test suite contains a live-gateway test (`test_e2e.py`); its wall time swings 45 s ↔ minutes | `pytest --durations` (E0) | open (documented; deselect for offline runs) |
| N11 | Chat radius 2 tiles leaves 17–25 % of 70B chats (v2.1) without an addressee; target silently cleared | chat-reach count | open |
| N12 | Retry on JSON-decode failure resent the identical prompt at temperature 0 (same output) | reading + E1 determinism | fixed (explicit nudge) |
| N13 | Persona `profession` strings carry English glosses in German/French residents ("Sanitärinstallateur (Plumber)", "pächterbetrieb (tenant farmer)") | end-to-end run through the real server (v2.1) | open (the persona prompt's English examples; strip or localise) |
