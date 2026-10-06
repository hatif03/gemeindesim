# Source this to point the research harness and the app at the CSCS inference API (key stays in the git-ignored .env.cscs):
#   . research/cscs_env.sh        (from track_2b/)
# Results of every research script then go to research/results/cscs/ instead of research/results/.
set -a
. "$(dirname "${BASH_SOURCE[0]}")/../.env.cscs"
set +a
export LLM_BASE_URL="$CSCS_BASE_URL" LLM_API_KEY="$CSCS_API_KEY"
export LLM_NAME="swiss-ai/Apertus-v1.5-70B" LLM_FALLBACK_NAME="swiss-ai/Apertus-v1.5-8B"
export RESEARCH_SUBDIR=cscs RESEARCH_M70="swiss-ai/Apertus-v1.5-70B" RESEARCH_M8="swiss-ai/Apertus-v1.5-8B"
