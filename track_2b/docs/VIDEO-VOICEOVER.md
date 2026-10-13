# Demo video: voice-over script (target 1:45, hard limit 2:00)

Read at a calm pace (about 150 words per minute). 252 words, so about 1:42, which leaves a few seconds for the title card and the closing card.
Every figure in the script is measured and written down: see `docs/research/LAB-NOTEBOOK.md` (experiment ids below) and `docs/PITCH-LANDSCAPE.md` (sources for the Swiss facts).
The footage is in `footage/` (index: `footage/INDEX.md`). The app has no sound, so every clip is silent; add music and the voice-over yourself.

| time | voice-over | picture |
| --- | --- | --- |
| 0:00 | Swiss voters decide on a written text, and that text can be wrong. In 2019 a federal vote was annulled, because the booklet said eighty thousand couples were affected. The real number was four hundred and fifty-four thousand. | Black card "80,000 vs 454,000", then the intro and title screen (`01_intro_title`) |
| 0:16 | As far as we found, nobody pre-tests the wording of a Swiss voting text with simulated readers; citizen panels do it for a few questions, over weeks. GemeindeSim is the cheap first pass: a what-if tool, not a vote predictor. | Editor opening and the German and French text pasted (`02_editor_config`) |
| 0:31 | Paste a vote text in German and French. Apertus one-point-five, Switzerland's open model, running on CSCS, plays every resident of a fictional town. They read the text, talk to their neighbours and argue, each in their own language, citing the passages they used. | Press Run; the town map with speech bubbles, the event log, a citation chip (`03_live_run`, first minutes) |
| 0:51 | Here is what we measured. Asked directly, Apertus said yes for all fifteen residents, even with no persona. On fifty-four real Swiss votes it was thirty-four points too favourable. So the model only speaks. Our code owns the stance, the household arithmetic and every citation, and checks each line. | Cards `docs/figures/fig04-yes-bias.png` and `fig05-real-votes-signal.png`, then `fig01-pipeline.png` |
| 1:14 | Before, none of one hundred fifty-nine citations pointed at a real passage, and twelve of thirty reports invented an outcome. Now every citation is valid and no report does. This run: twenty-five residents, five rounds, three hundred sixteen calls, four minutes, no failures. | Card `fig07-fixes.png`; the influence graph, the stance poll and the run-metrics panel (`03_live_run`) |
| 1:34 | The report says who is affected and why, never how to vote. Three environment variables switch between CSCS, the hackathon gateway or your own server. One command: make run. | The report (`03_live_run`, end), a resident chat answer if recorded |
| 1:50 | GemeindeSim: test the text before the town reads it. | Card with the repository URL |

## Rules of thumb

* Say "fictional town", "what-if", "pre-test"; never "predicts the vote".
* Say "this run" only over footage of a real run. `03_live_run` is a real run on CSCS; the replay file in `docs/replays/` is the same kind of run recorded earlier (316 calls, 237 s). Do not call a replay live.
* Do not claim native-speaker review of the German and French lines (still pending) and do not claim a local or on-premise run (not measured).
* To cut seconds: drop the sentence "As far as we found, nobody pre-tests ... over weeks."
* Never show `.env`, the terminal that prints it, or the API key.

## Where each number comes from

| said in the video | source |
| --- | --- |
| 80,000 vs 454,000 couples, annulled 2019 | Federal Supreme Court, 10 Apr 2019 (the 2016 Heiratsstrafe vote); `docs/PITCH-LANDSCAPE.md` section 4 |
| 15 of 15 yes, also with no persona | E11 (`docs/research/LAB-NOTEBOOK.md`) |
| 54 real votes, 34 points too favourable | E8 (simulated yes-share 83 % vs real 46.5 %: 34 to 37 points) |
| 0 of 159 citations valid, then all valid | E3 baseline vs E3d final |
| 12 of 30 reports with an invented outcome, then 0 | E9 / E9b |
| 25 residents, 5 rounds, 316 calls, about 4 minutes, no failures | `docs/replays/linden_25x5_cscs.config.json` (237 s, 316 calls, 0 failed) |
