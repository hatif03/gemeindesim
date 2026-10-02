# Apertus probe and GemeindeSim plan

Reference for the **GemeindeSim** build (`C:\Users\mdhat\Desktop\gemeindesim`). Written 2 October 2026 after live calls against the Hack Apertus inference endpoint.

This is not a Simulacra clone. [Simulacra](https://github.com/0xABAN/simulacra) is the reference for a generative-agent town (memory, rounds, a map). We keep that shape only where it helps, and point it at Swiss civic situations: a national or cantonal vote, a municipal budget, and residents who speak German or French. The model is used for what Apertus 1.5 is actually good at: multilingual instruction following, long context, and a single structured step. Everything it is weak at stays in our code.

The product explains official material. It does not write campaign copy, pick a side, or tell a user how to vote. That matches the Apertus Charter constraints already noted in `track-2a/fact-checking/README.md` (cite sources, no partisan side-taking, not legal advice).

## 1. What we already know about the model

Sources, checked 2 October 2026:

- [Apertus site](https://www.apertus-ai.org/) and [documentation](https://www.apertus-ai.org/pages/documentation/)
- [Getting started with Apertus 1.5](https://blog.nlp-lab.ai/2026/10/01/Apertus15GettingStarted.html) (DS-NLP Lab)
- [8B benchmark write-up](https://blog.nlp-lab.ai/2026/07/29/Apertus15Bench.html) (DS-NLP Lab, independent harness)
- Model cards: [Apertus-v1.5-8B](https://huggingface.co/swiss-ai/Apertus-v1.5-8B), [Apertus-v1.5-70B](https://huggingface.co/swiss-ai/Apertus-v1.5-70B)

Apertus 1.5 is a dense decoder-only model (8B and 70B) from the Swiss AI Initiative (EPFL, ETH Zurich, CSCS). Continued pretraining plus a second post-training pass added image and experimental audio input, a 262,144-token context, optional thinking mode, and better tool use. Output is text only. Tool calling and thinking mode are officially mutually exclusive: the vLLM thinking recipe omits `--enable-auto-tool-choice` on purpose.

Published 8B numbers from the NLP Lab study (their harness, not the missing technical report):

| Benchmark | 1.5 normal | 1.5 thinking | What it means for us |
| --- | --- | --- | --- |
| IFEval prompt-strict | 85.8 | 72.1 | Strong format-following with thinking off. Thinking makes exact JSON worse. |
| GSM8K | 79.6 | 85.3 | Everyday arithmetic is fine. Still verify civic numbers ourselves. |
| MATH-500 | 54.0 | 71.0 | Multi-step math needs a separate thinking call, then a format call. |
| MMLU-Pro | 45.9 | 45.5 | Broad knowledge is mid-pack. Do not let the model be the source of vote facts. |
| GPQA-Diamond | 29.8 | 26.3 (different setup) | Hard factual reasoning is not a reason to pick this model. |
| Global-MMLU, 10 languages | 62.1 | n/a | Multilingual gains over 1.0 are real and broad. |
| Belebele, 14 languages | 77.6 | n/a | Reading comprehension improved in every language they tested. |

The model card lists BFCL v3 (tool use) among evaluated benchmarks. Numeric BFCL scores were not public on 2 October 2026. The technical report was still listed as forthcoming. Our own calls are the tool-use evidence below. They are spot checks at temperature 0, not a leaderboard.

## 2. Endpoint

Hack Apertus inference, OpenAI-compatible chat completions.

- Base URL: `https://hackapertus.livemap.sh/v1`
- Model ids returned by `GET /v1/models`: `apertus-v1.5-8b`, `apertus-v1.5-70b`
- Advertised context: 262,144 input and output tokens
- Auth: bearer key issued for the hackathon. Do not commit the key, and do not paste it into this file.

Hugging Face ids (`swiss-ai/Apertus-v1.5-8B`) are not the ids this gateway accepts.

## 3. How we probed

All calls were chat completions at `temperature: 0`. Two passes on 2 October 2026.

Pass 1, both sizes: exact arithmetic, one weather tool, two cities in one turn, abstention when told not to use tools, a forced function name, a two-step tool loop (call, then read the tool result), policy JSON, and an NPC event JSON with and without `response_format: {"type": "json_object"}`.

Pass 2, both sizes: an explicit demand for two function calls in one response, tool choice among three functions, abstention with no “do not use tools” instruction, a stricter NPC schema (`event_type`, required `message`, nearby-id constraint), and a dependent second hop (weather says rain, so post a notice). Thinking mode was tried on 8B only, via `extra_body.chat_template_kwargs.enable_thinking = true`.

## 4. Probe results

### 4.1 Tool calling works for one call

Both sizes speak the OpenAI tool protocol on this gateway. A weather request finished with `finish_reason: tool_calls` and:

```json
{"city": "Zurich", "unit": "celsius"}
```

The gateway parses Apertus tool tokens into `message.tool_calls`. Application code does not need to scrape `<|tools_prefix|>` for the single-call case.

Also solid on both sizes:

- Forced `tool_choice` of `lookup_price` with argument `{"item": "milk"}`.
- Choosing `lookup_price` on its own when three tools were available (weather, price, notice).
- Refusing tools for ordinary questions: capital of Switzerland (Bern), author of *The Magic Mountain* (Thomas Mann).
- After a tool result of 14°C and cloudy in Geneva, answering from that result. The 70B kept “cloudy”. The 8B reported the temperature.
- After a tool result of rain at 11°C in Zurich, the next turn called `post_notice` with a shopkeeper warning. Both sizes. The 70B also wrote a short prose sentence alongside the call.

`17 × 23` returned `391` on both, in well under two seconds.

Rough latencies at temperature 0, short outputs: 8B about 0.5–1.9s, 70B about 0.6–4.4s. A round of residents can be parallelized. A full town does not have to be one long serial chain.

### 4.2 Parallel tool calls fail

Asked for Zurich and Bern together, both models emitted one structured call, for Zurich only.

Asked again, explicitly, to return two function calls in the same response and no prose:

- 8B: still one `tool_calls` entry, Zurich only. Bern disappeared.
- 70B: `finish_reason: stop` and **no** `tool_calls`. The text was two pseudo-calls:

```text
get_weather(city="Zurich", unit="celsius")
get_weather(city="Bern", unit="celsius")
```

So the 70B understood the request and still missed the protocol. A client that only reads `tool_calls` would see an empty turn and might think the model declined.

This is the main agentic shortcoming. Do not design a planner that expects one assistant message to fan out into several tools.

### 4.3 Structured JSON is usable, and brittle when the example is loose

`response_format: {"type": "json_object"}` succeeded for a policy object (sectors, stakeholders, impacts, controversy) on both sizes. The 70B was more specific (it kept the small-business exemption). The same NPC prompt without `response_format` also returned JSON, so the format flag is helpful and not the only thing keeping output parseable on these short prompts.

Failure mode we did hit: a looser NPC example that included `message` produced valid-looking JSON from the 8B with `message` omitted. The 70B kept the field. When the second prompt showed the full object (`event_type`, `message`, `target_npc_id`, `dialogue`, null coordinates, `perception`), both sizes filled it and both talked only to the nearby resident.

Both then invented a mood that was not in any closed list: 8B wrote `confused`, 70B wrote `considerate`. If mood is a free string, that is flavor. If the app has an enum, it is a validation failure.

### 4.4 Thinking works, and it leaks into `content`

On 8B, `enable_thinking: true` solved the bat-and-ball item correctly (ball costs 0.05 CHF). The reasoning was inside `content`, between `<|inner_prefix|>` and `<|inner_suffix|>`, followed by the answer. `provider_specific_fields.reasoning` was null. This gateway does not split the deliberation span for us.

Official guidance still stands: do not send tools and thinking in the same request. The NLP Lab IFEval drop (85.8 to 72.1) matches what we would see if we asked a thinking call to emit a strict resident schema.

### 4.5 What this means in one paragraph

Apertus on this endpoint is a reliable single-step function caller and a decent JSON emitter when the prompt contains a concrete example and thinking is off. It is not a parallel tool orchestrator. Thinking is a separate mode we have to parse ourselves, and it fights strict schemas. The 70B writes more specific civic-sounding sentences. The 8B follows the schema and sounds flatter. Neither should be the system of record for a vote booklet or a budget table.

## 5. Shortcomings we will hit in the civic sim

| Shortcoming | Where it shows up | If we ignore it |
| --- | --- | --- |
| No parallel `tool_calls` | “Look up the DE booklet, the FR booklet, and the budget line.” | Silent drop (8B) or fake text calls (70B). The round hangs or skips a source. |
| Thinking vs tools vs JSON | A resident turn that reasons about a Steuerfuss and must emit an enum. | Either a tool call with no deliberation, or a smart answer that fails validation. |
| Thinking markers stay in `content` | Any thinking call whose text is shown in the UI. | Users see `<|inner_prefix|>` or we store reasoning as the utterance. |
| Dropped required fields | 8B, when the example object is incomplete. | Pydantic rejects the turn, or worse, a default hides a missing action. |
| Invented enums | Mood, stance, language, action type. | A resident “mood” the UI cannot draw, or a stance outside the vote question. |
| Shallow economics and generic voice | 15 rounds of the same shopkeeper or tenant. | The map moves and the German/French flattens into textbook sentences. |
| Mid-pack factual recall | “What does a Yes do to this Gemeinde budget?” | Invented percentages that are not in the Erläuterungen. |
| US-default framing | Prompts that say “town” and “minimum wage” the way Simulacra does. | Residents talk like an American city even when the corpus is Swiss. |
| One completion, two languages | “Answer in German and French.” | Code-switching, or one language silently winning. |

Simulacra’s `backend/graph/llm.py` already fights a different model’s failure mode (K2 Think dumps reasoning, echoes schemas, wraps one object in an array, so they retry three times and scan for JSON). We should copy the idea of a gate in front of the model, and change the gate to match Apertus: single tool call, example instance, thinking split into its own request, closed enums, no parallel fan-out.

## 6. Engineering: what our code owns

Yes. The shortfalls are narrow enough to engineer around. The rule is: **the model narrates one grounded step; the application decides, retrieves, computes, and checks.**

We do not fine-tune for the prototype. A wrapper, a schema gate, and a closed corpus get us further than a training run, and they stay compatible with both sizes on this endpoint.

### 6.1 Split every model call into one mode

Three call types. A request is never more than one of them.

| Mode | Thinking | Tools | `response_format` | Used for |
| --- | --- | --- | --- | --- |
| `json` | off | none | `json_object` | Resident action, stance, report sections |
| `tool_one` | off | exactly one function, `tool_choice` forced | none | A retrieval the planner already chose |
| `think` | on | none | none | Hard explanation only: budget tradeoff, what a Yes/No changes |

`think` is never shown raw. The client splits on `<|inner_prefix|>` and `<|inner_suffix|>`. The inner span is discarded or stored as debug. The visible answer, if it still needs a schema, is fed to a second `json` call: “Turn this analysis into the object. Do not add facts.”

If a `think` call never closes `<|inner_suffix|>`, treat it as truncated, raise `max_tokens`, and retry once. Do not display the prefix to the user.

### 6.2 Never ask for parallel tool calls

The planner returns a JSON list of steps, in `json` mode, not via the tools API:

```json
{"steps": ["booklet_de", "booklet_fr", "budget_line"]}
```

Our executor runs those lookups in code, in parallel if we want. Results are concatenated into the next prompt as sourced passages. The model does not see a `tools` array unless the executor has already decided on exactly one function and sets `tool_choice` to that name.

Repair, only as a safety net for `tool_one`: if `tool_calls` is empty and `content` matches `name(key="value")` lines, parse those lines into one call when there is exactly one line and the name is in the allowed set. If there are two lines, do not execute them. That was the 70B failure shape. Log it and fall back to the code planner. Executing a parsed fan-out would hide the bug we are designing around.

### 6.3 Schema gate

Every resident and report call goes through the same function:

1. Prompt includes a **filled example object**, with every required key present. The first probe showed the 8B dropping `message` when the example was casual.
2. Send `response_format: {"type": "json_object"}` and thinking off.
3. Parse JSON. On failure, scan for the first balanced object (Simulacra already does this; keep it).
4. Validate with Pydantic. Enums are closed: `lang` is `de` or `fr`, `action` is a small set (`say`, `ask`, `move`, `shift_stance`), `stance` is `yes` / `no` / `undecided` / `abstain` for a vote, or a signed integer the budget rules allow. Mood, if we keep it, is the same closed list the UI can draw.
5. On validation error, one repair call. The user message is the invalid JSON plus the Pydantic error. Same mode, no new facts.
6. After two failures, use a deterministic fallback line from the persona card (“I want to read the official explanation again before I decide.”) in that resident’s language. A round must not block on a bad sample.

Do not ask the model to copy a JSON Schema. Simulacra found that K2 echoed the schema; a concrete example is the more reliable prompt for this class of model too.

Numeric fields that come from the world (tax rate, deficit, turnout) are **not** model outputs. They are inputs the model may quote. The checker drops any numeral in the utterance that is not in the retrieved pack or the calculator output.

### 6.4 Facts live in a closed corpus

Before any resident speaks, retrieval has already run.

- Vote path: official booklet and Erläuterungen for that Vorlage, German and French PDFs kept as separate documents. Same idea as the OST fact-checking track: the open web is out of bounds.
- Budget path: the adopted municipal budget or the proposal PDF, plus a small table we extract once (department, amount, year). A calculator in code answers “what is 2% of the education line”. The model explains the result in character.
- Each passage carries `source_id`, language, and page. The utterance schema includes `used_source_ids`. If that list is empty on a factual sentence, the line is rejected and repaired once.

This is how we cover MMLU-Pro / GPQA being mid-pack. The model is a reader and a speaker, not an encyclopedia.

Long context (262k) means we can put a short booklet section in the prompt when retrieval is ambiguous. We still retrieve first. Stuffing both full booklets into every resident turn will wash out the persona and burn latency.

### 6.5 One language per call

Each resident has `lang: de` or `fr` (Italian can be a later resident type; do not add it until DE and FR pass the eval). The system line says to write only in that language. The glossary for that language is a short block of official terms, for example:

- German: Vorlage, Abstimmungsfrage, Erläuterungen, Stimmvolk, Steuerfuss, Gemeinderat, Rechnung, Budget
- French: objet, question votée, explications du Conseil fédéral, souverain, taux d’imposition, conseil communal, comptes, budget

We do not ask one call to produce both languages. If the UI needs the other language, that is a separate `json` or plain call whose only job is translation of an already accepted utterance, with the glossary, and with numbers copied exactly.

Swiss German dialect is optional flavor, not the default. The official documents are Standard German and French. Dialect in the mouth of a resident is a later experiment, and only if a spot check shows the 70B staying understandable. Audio understanding in 1.5 is experimental; this prototype stays text.

### 6.6 Shrink the cognitive loop

Simulacra runs perceive, retrieve, reflect, plan, and act as model calls, for 25 people, for 15 rounds. That volume is where a mid-pack model goes generic. We keep the memory stream and the opinion update, and we delete model work that code can do.

Per round, per resident, the model sees a pack assembled in code:

- Frozen persona card (name, role, language, household situation, one concrete stake). Written once by the 70B, then not rewritten.
- At most three retrieved memories.
- The passages retrieved for this Vorlage or budget line.
- Who is nearby, as ids the model is allowed to address.
- The phase: official text just published, discussion, vote week or budget hearing.

The model returns **one** action. Code applies it: append memory, update stance with a bounded shift, move on the grid if the coordinates are in range, record a chat only if the target was in the nearby list. Opinion dynamics (bounded confidence, compromise with people they know) stay numeric, as in Simulacra. The model does not do the math of social influence.

Reflections are rare. Trigger them the way Park et al. do, from an importance sum, and run them on the 70B in `json` mode. Most rounds have no reflection call.

Who speaks is also code. Not every resident needs a model call every round. A round can sample the residents whose stake matches the agenda item, plus one neighbor conversation. That keeps the 70B on the lines a user will actually read.

### 6.7 Which size, when

| Job | Model | Mode |
| --- | --- | --- |
| Seed personas from a stakeholder list | 70B | `json` |
| Explain a Vorlage or a budget delta | 70B | `think`, then `json` |
| Resident turn | 70B | `json` |
| Final public report, with citations | 70B | `json` |
| Bulk fallback only if the 70B queue is long | 8B | `json`, same schema, shorter max tokens |

The 8B is good enough to keep a schema alive. It is the wrong default for the sentences we show. Use it when a turn is low-stakes and heavily constrained (a one-line reaction that must mention a supplied number). Do not use it to invent the persona.

### 6.8 Module sketch

When we build, these are the pieces. Names can change; the boundaries should not.

- `client.py` — endpoint, the three modes, thinking-span splitter, single pseudo-call repair, no key in logs.
- `schema.py` — Pydantic models and the validate-then-repair-then-fallback function.
- `corpus.py` — DE/FR booklet chunks and budget rows, each with `source_id`.
- `retrieve.py` — lexical or embedding search over that corpus only.
- `planner.py` — JSON list of retrieval steps, executed in code.
- `residents.py` — frozen cards, language, stance, memory.
- `round.py` — assemble the pack, one `json` call, apply the action in code.
- `report.py` — 70B narrative over aggregates the simulator already computed.
- `eval/` — the checks in section 8, runnable without the Phaser map.

The map, if we keep one, is a view of state the round loop already produced. It is not part of making the model reliable.

## 7. Scenario shape

One simulation has a **situation** and **residents**. The situation is one of:

1. **Vote.** A single Vorlage. Official question, DE and FR explanation, what Yes and No change, in the words of the booklet. Residents have a household stake (rent, farm, commute, small business, municipal job) tied to that question. Stance moves only when a retrieved passage or a neighbor conversation is in the pack.
2. **Municipal budget.** A handful of lines (school, roads, social aid, tax rate), taken from a real published budget we have the right to use. The calculator produces the deltas. Residents react to a line that touches them. They do not invent a new tax rate.
3. **Language.** Every resident is `de` or `fr`. A street can contain both. Conversation across languages is allowed only through an explicit translation step, so a French resident does not suddenly answer in English because the system prompt was English.

The user pastes or selects the situation. They do not get a free-form “make the town conservative” control. The objective line, if we keep one, is a question (“what happens to tenants if this passes”), and the report answers it from the trace.

Suggested first prototype, small on purpose:

- 8 residents, 4 German and 4 French.
- 5 rounds, not 15.
- One real Vorlage with both language PDFs, or one municipal budget with a two-page extract.
- No tools API in the round loop at all, until the schema eval is green. Retrieval is a function we call ourselves.

That is enough to see whether the engineering holds. Scaling toward 25 residents is a concurrency change, not a new model strategy.

## 8. Eval we run before any UI

Temperature 0. Record model id, mode, and the prompt hash. A change to the gate is a regression run, not a vibe check.

| Check | Pass |
| --- | --- |
| Schema, 20 resident fixtures | Valid object, required keys present, enums inside the list, nearby-id respected. Target: at least 18/20 on 70B without the repair call, 20/20 after one repair. |
| Numerals | Every number in the utterance appears in the pack. |
| Language | A `de` resident’s utterance is German. A `fr` resident’s is French. No English drift on the 70B for these fixtures. |
| Citation | Factual claims carry a `source_id` that was in the pack. |
| Abstain | A question with no relevant passage produces “not in the official text”, not a guessed percentage. |
| Single tool | `tool_one` returns one `tool_calls` entry for a forced function. A prompt that asks for two cities must **not** be how we retrieve; the planner test expects two code-side lookups and zero parallel `tool_calls`. |
| Thinking split | A `think` call’s user-visible field contains no `<|inner_prefix|>`. |
| Fallback | After two bad samples, the round still emits the template line and continues. |
| Side-taking | The system does not add a recommendation to vote yes or no. Residents may hold a stance. The report describes the split and the sources. |

Hand-read 10 German and 10 French lines for US framing (“city council” instead of Gemeinderat / conseil communal) and for generic filler. That reading is part of the record, next to the automatic counts.

## 9. Build order

1. Client and schema gate, with the fixtures in section 8. No town yet.
2. One Vorlage, DE and FR, chunked, with retrieval and the numeral check.
3. Eight frozen personas from the 70B, reviewed by us once, then locked.
4. Five-round loop in the terminal: print utterances, stances, and source ids.
5. Only then a small UI. The map is optional. A list of residents and a source panel is enough to judge the model.
6. Budget scenario as a second corpus and the same loop. Do not fork the prompt stack.

Out of scope until the eval is green: parallel tool use, thinking inside the round loop, dialect, audio, Italian, 25 agents, 15 rounds, campaign-style persuasion, web search.

## 10. Risks we are not pretending to have solved

- Five temperature-0 anecdotes are not BFCL. The parallel-call failure was repeated and consistent, so the ban on fan-out is justified. The success cases can still flake at temperature 0.7 with a long persona pack. The schema gate and the fallback exist for that.
- The 70B can be specific and still wrong. Citations are the control, not a larger model.
- A glossary does not guarantee Swiss administrative tone. The human read of 20 lines is mandatory before a demo.
- Hackathon rate limits and queueing were not measured under 8-way concurrency. The latency samples are single calls.
- Thinking mode on this gateway returns the span inside `content`. If the provider later strips it, the splitter should no-op when the markers are absent, and should prefer a `reasoning` field if one appears.
- Official PDFs have copyright and terms. Use documents we are allowed to process, and store source ids, not a silent scrape of the open web.

## 11. Decision log

- We will not port Simulacra’s K2 prompt stack unchanged. We will port the idea of a JSON gate, memory, and code-side social math.
- We will not use native parallel tool calls.
- We will not combine thinking and tools.
- We will not let the model emit budget or vote numbers that were not retrieved or computed.
- Default resident model is the 70B, thinking off. Thinking is a pre-pass for explanations only.
- First demo is 8 residents, 5 rounds, German and French, one official text.
