# 06 — Next steps, ranked

Time left (from `docs/HACKATHON.md`): submission deadline **16 Oct 2026, 12:00 CEST**.
Ranking = value to the five judging criteria ÷ effort, given what the experiments showed.

## Must do before submission

1. **Re-state the pitch honestly** (½ day). Replace the claims marked *Refuted/Unsupported* in
   [04-pitch-audit.md](04-pitch-audit.md) in `FOR-JUDGES.md`, `technical_report.md`,
   `PROBE-AND-PLAN.md`. The measured limits are a stronger story than the old claims.
2. **Show the new mechanism in the UI** (1 day). The backend now emits `stance_*` indicators,
   per-resident `stance`/`stance_reason`/`impact`, validated citations (`used_source_ids`,
   `invalid_cites`) and — for the first time — `influence_events`. Minimum: a For/Against/
   Undecided bar next to the dashboard, the stance reason in the resident card, a citation
   tooltip. The social-graph influence layer lights up by itself.
3. **Demo video ≤ 2 min and the ≤ 6-page PDF** (1 day). Use the research findings as the
   technical-rigour section (tables in [03-results.md](03-results.md)).
4. **Native-speaker pass** on DE/FR residents and glossary (outside help; the sample text
   is synthetic and machine-assisted). Swiss orthography is now enforced in code, register is not.

## High value, if time allows

5. **A real booklet** (1–2 days). The Linden sample is too small to exercise retrieval
   (E5). Ingest one official Federal Council *Abstimmungsbüchlein* (public document; check the
   terms of reuse) and re-run E5 (fact coverage, question chunk, DE/FR parity) and E3. Expected
   to be where BM25 + pinning stops being enough → try an embedding hybrid.
6. **Re-probe on local vLLM** (½–1 day, needs a GPU). Every gateway behaviour in E1/E10 is a
   property of *that deployment*. The sovereign-deployability criterion is only convincing
   with the same probe table measured on `swiss-ai/Apertus-v1.5-70B` (or 8B) behind local
   vLLM, including tool-parser flags and the 4-in-flight limit (probably a gateway artefact).
7. **Run-it-5×, show the spread** (½ day). E1 showed `T=0` is not deterministic; the app
   should offer "N seeds" and display stance/mood distributions, not one trajectory. The
   harness (`run_sim.py` + `analyze_sims.py`) already does this offline.
8. **Compare-conditions mode** (1 day). E8 says absolute shares are not predictive, while
   *differences between conditions* are what the literature (Hewitt et al., Barmettler)
   supports. Add "run this town with/without the Federal Council recommendation / with the
   committee text / in DE vs FR" and show deltas. Directly addresses F34 (authority deference)
   and F35 (language shifts stance).
9. **Hand-written, statistics-based personas** (1 day). LLM-generated personas are
   homogeneous (everyone grew up in Linden, E3 read-through; Li et al. 2025). Draw
   age/income/housing/household from federal statistics tables and let Apertus only write
   the voice.

## Research extensions

10. **Calibrate the stance prior** (`W_IDEOLOGY, W_IMPACT, W_BURDEN`) on municipality-level
    results (Emmenegger, SPSR 2025, 1866–2023 — seen in a search listing, not opened) and
    report out-of-sample error; today they are labelled knobs.
11. **Sensitivity sweep of the dynamics** (Deffuant μ/ε, keep/compromise/adopt thresholds,
    Baumann α) — the thresholds come from a numeric-estimation experiment with 85 students.
    The influence log (now preserved) provides the needed trace.
12. **Persuasion-risk test**: does any condition let a resident (or the reporter) produce a
    most-persuasive argument? We found no vote advice (E9) but never red-teamed it
    (that is Track 1A territory).
13. **Italian and Swiss-German dialect**: out of scope for the prototype; the dialect track
    (1B) has the tooling.
14. **Vote-specific indicators**: `price_pressure` is dead (no `pct_change` field), and price/unrest
    are structurally 0 for a tax vote. Replace with stance split, turnout intention, household strain.

## Known open defects (not fixed here)

* "Undecided" residents still sound like opponents (E15b: 0.58 on the 70B); try delivering one named pro and one named con argument per line.

* `price_pressure` indicator always 0 (schema lacks `pct_change`).
* `invoke_llm_think` is dead code (no thinking pre-pass is wired).
* Derived arithmetic ("240 / 12 = 20") is still stripped by the numeral gate; spelled-out numbers
  ("sechzig Prozent") are invisible to it.
* 8B never emits `move`; 70B uses it less than a chat-heavy mix.
* Resident chat radius (2 tiles) leaves 17–25 % of 70B chats with no addressee.
* Persona marginals in E8 and the stance-prior weights are assumptions, not calibrated.
