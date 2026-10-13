# Ready-to-paste situations

Every text here is **fictional** (no real municipality, no real figures) and short enough to paste into the notes field of the editor. Press PLAY, click the text box, paste the whole file, set the numbers below, press RUN SIM. A run with 5 residents and 3 rounds takes about 1 to 1.5 minutes on the CSCS endpoint; 25 residents and 5 rounds take about 4 minutes of model time (the map then plays the events for several more minutes).

Residents are generated at run time. In a Swiss setting (a text with words such as *Gemeinde*, *Vorlage*, *Steuerfuss*, *CHF*) the town alternates German and French residents whatever the language of the text, and the report is written in the residents' majority language (German for an odd number of residents). A text without those markers (the two English files) gives an all-English town.

| file | language | what it is | settings to try | what to look at |
| --- | --- | --- | --- | --- |
| `../steuerfuss_linden_balanced_de.txt` and `_fr.txt` (paste both) | DE + FR | tax rise and school credit, with the referendum committee's arguments (the reference scenario of the research) | 25 residents, 5 rounds | the demo run in `docs/replays/` was made from this text |
| `01_birkenau_steuerfuss_de.txt` | DE | fire-station credit with a tax-rate rise from 95 % to 100 %, with a worked example (80'000 CHF income: about 200 CHF) | 5 to 10 residents, 3 rounds | residents quote a personal yearly cost that code calculated from the worked example (about 120, 200 or 360 CHF by income band), cited as passages [P#] |
| `02_bellevue_piscine_fr.txt` | FR | swimming-pool renovation credit and a higher entrance fee; no tax change | 5 to 10 residents, 3 rounds | a French text read by German- and French-speaking residents; no household figure (the calculator only knows tax-rate examples) |
| `03_parking_zentrum_de.txt` | DE | paid parking in a village centre (a municipal assembly motion) | 5 to 10 residents, 3 rounds | shopkeepers against commuters and residents; try the "what if": delete paragraphs 6 to 8 (the minority arguments) and run again |
| `04_voranschlag_gebuehren_de.txt` | DE | a budget with a higher waste fee and shorter swimming-pool hours | 5 to 10 residents, 3 rounds | a flat fee hits low incomes harder; the text has no tax-rate worked example, so there is no calculated figure |
| `05_bike_lane_trial_en.txt` | EN | a bike-lane trial on a town road | 5 to 10 residents, 3 rounds | an all-English town and report; the same loop on a non-Swiss text |
| `06_unklare_vorlage_de.txt` | DE | a speed-limit vote whose wording is **deliberately ambiguous** | 5 to 10 residents, 3 rounds | the pre-test use: a double negative in the question, two dates, two household counts (3'000 and 4'200), an open tax consequence and no minority argument; read how residents paraphrase the text |
| `../tariff_millfield_en.txt` | EN | an English steel-tariff policy (not a vote) | 5 to 10 residents, 3 rounds | a policy rather than a vote: price events, layoffs, a different report |

## What happened when we ran them (13 Oct 2026, CSCS, Apertus 70B, 5 residents, 3 rounds, standard graph)

All eight ran without a failed call (33 to 51 calls, 57 to 94 seconds). Every dialogue line was tied to a passage; the validator removed a few labels that do not exist (2 in the French pool text, 1 in the ambiguous text, none in the others). No report asserted an outcome or recommended a vote.

| situation | residents | stance poll, start to end (for / against / undecided) | notes |
| --- | --- | --- | --- |
| Birkenau (DE) | 3 DE, 2 FR | 3/1/1 to 3/1/1 | calculated household figures appear in the lines |
| Bellevue (FR) | 3 DE, 2 FR | 3/1/1 to 3/0/2 | German report for a French text (the majority language); the report headline says "Steuerfuss" although the text rules out a tax rise: a model wording slip that a human reader catches |
| Parking (DE) | 3 DE, 2 FR | 3/1/1 to 4/1/0 | |
| Budget (DE) | 3 DE, 2 FR | 4/0/1 to 4/0/1 | |
| Bike lane (EN) | 5 EN | 2/3/0 to 2/3/0 | English report |
| Ambiguous (DE) | 3 DE, 2 FR | 4/0/1 to 5/0/0 | residents quote the text and all treat the vote as "keep the zone"; one turns "possibly 1 to 2 points" into "at most 1 to 2 points". Nobody names the double negative or the two household counts: **the simulation does not detect the flaws by itself**; it shows how the text is paraphrased, and a person reads that |
| Millfield (EN) | 5 EN | 4/0/1 to 5/0/0 | English report |

These are single runs: the stance starts from a random draw per run and `temperature 0` is not reproducible, so another run gives a different poll. Use **RUN 5X: SHOW THE SPREAD** for the range across seeds. The stance numbers are a what-if, not a forecast: the model alone said "yes" for every resident in our tests, so the stance comes from code (household cost, leaning, judged impact) and moves only through conversations.

## Make your own

Keep the shape of the files: the question, numbered explanations of the authority, the minority's arguments, and a line saying that no recommendation is given. A sentence such as "for 80'000 CHF taxable income about 200 CHF more per year" together with "95 % auf 100 %" lets the calculator give residents a personal figure. Do not paste the name of this tool into an English text: the word *Gemeinde* inside it makes the app treat the text as Swiss.
