#!/bin/sh
# The final code on the CSCS inference API: 5 seeds x 70B and 8B (same seeds as final_70_s*/final_8_s* on the hackathon gateway), plus one 25-resident town.
# usage (from track_2b/research): . ./cscs_env.sh && LLM_CONCURRENCY=16 sh run_cscs_sims.sh
set -e
for s in 1 2 3 4 5; do
  uv run --project ../src/backend python run_sim.py cscs70_s$s --seed $s --model swiss-ai/Apertus-v1.5-70B
done
for s in 1 2 3 4 5; do
  uv run --project ../src/backend python run_sim.py cscs8_s$s --seed $s --model swiss-ai/Apertus-v1.5-8B
done
uv run --project ../src/backend python run_sim.py cscs70_n25_s1 --seed 1 --npcs 25 --model swiss-ai/Apertus-v1.5-70B
