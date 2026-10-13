# Setting up the environment variables (guide for judges)

GemeindeSim needs **three environment variables** to reach an OpenAI-compatible Apertus endpoint. Only the key has to be filled in: the other two default to the CSCS inference API and the 70B model you are judging on.

| variable | what it is | default if you set nothing |
| --- | --- | --- |
| `LLM_API_KEY` | your key for the endpoint | none: **you must set it** (without it every model call fails) |
| `LLM_BASE_URL` | the endpoint, ending in `/v1` | `https://api.inference.cscs.ch/v1` (CSCS inference API) |
| `LLM_NAME` | the model id | `swiss-ai/Apertus-v1.5-70B` |

Nothing else is required. The app maps the model id to the style the endpoint expects (`swiss-ai/Apertus-v1.5-70B` on CSCS, `apertus-v1.5-70b` on the hackathon gateway), so either spelling works on either endpoint.

## What you need first

* Docker (Docker Desktop on Windows and macOS) running. Nothing else has to be installed: the backend and the frontend are built inside Docker.
* Free ports 3000, 8000 and 8080 (8080 can be changed, see below).
* An API key. For judging, the CSCS inference API key from the organisers.

## Option A: a `.env` file (recommended)

From the repository root:

```bash
cp track_2b/.env.example track_2b/.env
```

(Windows PowerShell: `Copy-Item track_2b\.env.example track_2b\.env`.) Open `track_2b/.env` in any editor and put the key after `LLM_API_KEY=`, with no spaces and no quotes:

```text
LLM_BASE_URL=https://api.inference.cscs.ch/v1
LLM_NAME=swiss-ai/Apertus-v1.5-70B
LLM_API_KEY=paste-your-key-here
```

Then start the app:

```bash
make run                 # from the repository root
# without make (for example on Windows):
cd track_2b
docker compose up --build
```

The first build takes a few minutes. When the log shows `GemeindeSim ready — model=... base_url=...`, open **http://localhost:3000**.

The file `track_2b/.env` is ignored by git. Never commit it, and do not paste the key into a document or a video.

## Option B: variables in your shell (no file)

Docker Compose reads the variables from the shell it is started in, and a value in the shell wins over one in `.env`.

macOS and Linux (bash, zsh):

```bash
export LLM_API_KEY="paste-your-key-here"
cd track_2b && docker compose up --build
```

Windows PowerShell:

```powershell
$env:LLM_API_KEY = "paste-your-key-here"
cd track_2b
docker compose up --build
```

Windows cmd:

```bat
set LLM_API_KEY=paste-your-key-here
cd track_2b
docker compose up --build
```

The variable exists only in that terminal window. To use another endpoint or model, set `LLM_BASE_URL` and `LLM_NAME` the same way.

## Check that it works

1. The backend log (`docker compose logs backend`) prints `GemeindeSim ready — model=<model> base_url=<url>`. If it says `LLM_API_KEY is not set`, the key did not reach the container.
2. `curl http://localhost:8000/metrics` returns JSON with `"model"` and `"endpoint"` (the host of the endpoint in use) and zero calls before the first run.
3. In the app, click **LOAD** on the title screen and pick `track_2b/docs/replays/linden_25x5_cscs.replay.json`: this replays a recorded run without calling the model, so it shows the UI works even before the key is checked.
4. For a real run: **PLAY**, paste one of the texts in `track_2b/data/situations/` (see its README), choose 5 residents and 3 rounds, press **RUN SIM**. It takes about a minute and a half on CSCS. The **Run metrics** panel (bottom right) shows tokens, latency and retries as the model answers.

To test the key without the app: `curl -s -H "Authorization: Bearer $LLM_API_KEY" https://api.inference.cscs.ch/v1/models` should list the Apertus models (PowerShell: `curl.exe -s -H "Authorization: Bearer $env:LLM_API_KEY" https://api.inference.cscs.ch/v1/models`).

## Other endpoints

| to use | `LLM_BASE_URL` | `LLM_NAME` | key |
| --- | --- | --- | --- |
| CSCS inference API (judging) | `https://api.inference.cscs.ch/v1` | `swiss-ai/Apertus-v1.5-70B` (or `-8B`, about four times faster) | the CSCS key |
| hackathon gateway | `https://hackapertus.livemap.sh/v1` | `apertus-v1.5-70b` (or `-8b`) | the hackathon key |
| your own server (on-premise, air-gapped) | `http://host.docker.internal:8001/v1` for a server on the same machine | the id the server reports, for example `swiss-ai/Apertus-v1.5-8B` | any non-empty string if the server has no authentication |

A key only works on the endpoint that issued it. The local-server row is configuration only: we have not measured a local deployment (see the technical report, section 2). A server such as vLLM must expose the OpenAI chat-completions API with JSON mode.

## Optional variables

All optional; the defaults are what we measured with.

| variable | effect |
| --- | --- |
| `LLM_CONCURRENCY` | `auto` (default): starts at 4 requests in flight and adapts to the endpoint (up to `LLM_CONCURRENCY_MAX`, default 32, and back off on 429 or timeouts); a number fixes it |
| `LLM_VOICE_NAME` | a different (usually larger) model for the report and the 1:1 chat, while the residents run `LLM_NAME` |
| `LLM_FALLBACK_NAME` | model used after a timeout or a server error; by default the 8B that matches `LLM_NAME` |
| `LLM_TEMPERATURE` | default `0` (note: `0` is not reproducible on Apertus, see the technical report) |
| `CHAT_STREAM` | `1` (default): chat answers arrive sentence by sentence, each checked first; `0`: one message |
| `SWARM` | `true`: two-phase rounds (measured, slower, no gain); default `false` |
| `UI_ALT_PORT` | the second published UI port (default 8080); set it, for example `18080`, if 8080 is taken, otherwise `docker compose up` fails |
| `ALLOWED_ORIGINS`, `LOG_LEVEL`, `EMBEDDING_MODEL` | CORS origins, log level, optional dense retrieval (needs a 2.2 GB local model) |

The full list with comments is in `track_2b/.env.example`.

## If something goes wrong

| symptom | cause and fix |
| --- | --- |
| the log says `LLM_API_KEY is not set`, or runs end at once with an error | the key did not reach the container: check the file is `track_2b/.env` (not `.env.example`), has no quotes or spaces, then recreate the container: `docker compose up -d --force-recreate backend` |
| HTTP `401` | the key does not belong to that `LLM_BASE_URL` (for example a CSCS key sent to the hackathon gateway, or the reverse) |
| HTTP `403 key not authorized for this model` | `LLM_NAME` is not a model your key reaches; the CSCS key reaches the four Apertus v1.5 models (`70B`, `8B`, `70B-thinking`, `8B-thinking`) |
| HTTP `429` | too many requests in flight on the hackathon gateway (about 4 to 5 are allowed): leave `LLM_CONCURRENCY=auto`; the app slows down and retries |
| HTTP `504` or very slow runs | the endpoint is busy; the Run metrics panel shows the speed per request (below about 20 tokens per second on the 70B means the endpoint is busy, not the app); try the 8B (`LLM_NAME=swiss-ai/Apertus-v1.5-8B`) |
| `docker compose up` fails with "port is already allocated" | set `UI_ALT_PORT=18080` (in `.env` or the shell) |
| "Cannot connect to the Docker daemon" | start Docker Desktop and wait until it says it is running |
| the page opens but a run says "Simulation not found" | an old container from an earlier version is running: `docker compose down`, then `docker compose up --build` |
| the UI works but is opened from another computer | the frontend is built to call the API at `http://localhost:8000`: open the app on the machine that runs Docker |
| you changed `.env` and nothing changed | environment is read when a container is created: `docker compose up -d --force-recreate backend` |

More detail on the two endpoints and what the app does for each: `track_2b/docs/ENDPOINTS.md`.
