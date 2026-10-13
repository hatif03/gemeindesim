# Submission video: voice-over script (target 1:50, hard limit 2:00)

Team **1ne**, project **GemeindeSim**. 256 words: about 1:42 at 150 words per minute, about 1:58 at a calm 130. Read it once aloud against a stopwatch before you cut the picture; if it runs long, drop "Researchers and governments already test messages on simulated people: Singapore's GovTech does it for announcements." (keep "As far as we found, nobody does it for Swiss voting texts.") and shorten the last row.
Footage: `footage/` (index: `footage/INDEX.md`; four clips, 1080p60, silent: the app has no sound, so add music and the voice-over yourself). Every number is measured and written down in the technical report; the sources are in the table at the end.

| time | voice-over | picture |
| --- | --- | --- |
| 0:00 | Swiss voters decide on a written text, and that text can be wrong. In 2019 a federal vote was annulled, because the booklet said eighty thousand couples were affected. The real number was four hundred and fifty-four thousand. | Black card "80,000 vs 454,000", then the intro and the title screen (`01_intro_title`) |
| 0:15 | Researchers and governments already test messages on simulated people: Singapore's GovTech does it for announcements. As far as we found, nobody does it for Swiss voting texts. We are team one-N-E, and this is GemeindeSim: a what-if tool, not a vote predictor. | Editor opening, the German and French text pasted (`02_editor_config`) |
| 0:34 | Paste a vote text in German and French. Apertus one-point-five, Switzerland's open model, running on CSCS, plays every resident of a fictional town. They read the text, talk to their neighbours and argue, each in their own language, citing the passages they used. | Press Run; the town map with speech bubbles, the event log, a citation chip (`03_live_run`, 92 to 163 s) |
| 0:54 | Here is what we measured. Asked directly, Apertus said yes for all fifteen residents. On fifty-four real Swiss votes it was thirty-four points too favourable. So the model only speaks. Our code owns the stance, the household arithmetic and every citation, and checks each line. | Cards `docs/figures/fig04-yes-bias.png` and `fig05-real-votes-signal.png`, then `fig01-pipeline.png` |
| 1:15 | Before, none of one hundred fifty-nine citations pointed at a real passage, and twelve of thirty reports invented an outcome. Now every citation is valid and no report does. A run of twenty-five residents and five rounds: three hundred sixteen calls, four minutes, no failures. | Card `fig07-fixes.png`; the run-metrics panel (`03_live_run`, 163 s) and the influence graph (277 s) |
| 1:36 | The report says who is affected and why, never how to vote. Judges: three environment variables switch between CSCS and any other server, and the repository has scenarios to paste and try. GemeindeSim, team one-N-E: test the text before the town reads it. | The report (`03_live_run`, 460 to 511 s), then the resident chat answer with a cited passage (about 545 s; use questions 1 and 2 only), then a card with the repository address |

## Rules of thumb

* Say "fictional town", "what-if", "pre-test"; never "predicts the vote".
* Say "this run" only over `03_live_run`, which is a real run on CSCS. The replay clip is a run recorded earlier ("a recorded run"). The figures "316 calls, four minutes, no failures" come from the recorded 25 x 5 run.
* Do not claim native-speaker review of the German and French lines (not done yet) and do not claim a local or on-premise run (not measured).
* Do not show the third chat answer ("Ich werde Ja stimmen"): it is the resident's own position, but it reads like a recommendation.
* Never show `.env`, the terminal that prints it, or the API key.

## Where each number comes from

| said in the video | source |
| --- | --- |
| 80,000 vs 454,000 couples, annulled 2019 | Federal Supreme Court, 10 Apr 2019 (the 2016 Heiratsstrafe vote); report reference [50] |
| Singapore GovTech tests announcements on simulated people | GovTech, 11 Sep 2026 (Echo); report reference [44] |
| 15 of 15 yes, also with no persona | experiment E11 |
| 54 real votes, 34 points too favourable | E8 (simulated yes-share 83 % vs real 46.5 %: 34 to 37 points) |
| 0 of 159 citations valid, then all valid | E3 baseline vs final |
| 12 of 30 reports with an invented outcome, then 0 | E9 / E9b |
| 25 residents, 5 rounds, 316 calls, about 4 minutes, no failures | the recorded demo run (237 s, 316 calls, 0 failed) |
