"""Prompt templates for the policy simulation LangGraph nodes."""

PARSE_POLICY_PROMPT = """\
You are an expert policy analyst specializing in economic impact assessment.

<task>
Given the policy text below, perform a thorough analysis and extract structured information about its potential effects.
</task>

<dimensions>
<dimension name="sectors">Identify every industry, market, or sector that would feel direct or indirect effects.</dimension>
<dimension name="stakeholders">People, groups, or institutions impacted. Include a mix of powerful actors (corporations, government bodies) and everyday people (workers, consumers, small business owners).</dimension>
<dimension name="economic_impacts">Be specific. Think about employment, prices, trade, investment, innovation, housing, wages, and inequality. Include both intended and unintended consequences.</dimension>
<dimension name="controversy_level">How politically divisive is this policy? Consider who wins and who loses.</dimension>
<dimension name="ideological_valence">A number from -1 to 1: which political side would usually favour this measure? -1 = left/progressive voters, +1 = right/conservative voters, 0 = no clear lean. Example: a tax increase for schools is about -0.4; a tax cut is about 0.5.</dimension>
</dimensions>

<policy_text>
{policy_text}
</policy_text>

<supporting_notes>
{notes_text}
</supporting_notes>

<historical_trend_context>
{trend_summary}
</historical_trend_context>

<user_objective>
The user is specifically curious about: {objective}
Tailor your analysis to surface insights most relevant to this objective. If no objective is given, perform a general analysis.
</user_objective>

<output_format>
Output a single JSON object — not an array.
Respond ONLY with valid JSON (no markdown fences, no commentary):
{{
  "sectors": ["Manufacturing", "Retail", "Agriculture"],
  "stakeholders": ["Factory workers face job displacement", "Small business owners bear higher input costs", "Consumers see rising prices"],
  "economic_impacts": ["Consumer prices rise 5-10% in the short term", "Domestic manufacturing employment grows long-term", "Trade deficits narrow as imports become more expensive"],
  "controversy_level": "high",
  "ideological_valence": -0.4
}}
</output_format>"""

EXTRACT_CHARACTERS_PROMPT = """\
You are a character analyst. Your job is to extract named individuals from the source text below and map them to simulation personas.

<task>
Read the source text carefully. Extract every named individual person that has enough detail to form a character. Each entry MUST be a single specific person with a proper first and last name — never a group, demographic, archetype, or category (e.g. NOT "American Workers", "Low-Income Families", "Typical Family"). Return only what you can genuinely infer — do not invent details not present in the text.
</task>

<source_text>
{source_text}
</source_text>

<policy_context>
{entities_json}
</policy_context>

<output_format>
Output a single JSON object — not an array.
Respond ONLY with valid JSON (no markdown fences, no commentary).
Omit any field you cannot reasonably infer — only include fields with real signal from the text:
{{
  "characters": [
    {{
      "name": "First and Last Name (a real individual, never a group or category)",
      "category": "short label for their social/economic role, e.g. 'factory worker', 'small business owner', 'retiree'",
      "role": "worker|business_owner|politician|student|retiree|activist|farmer|shopkeeper|driver|teacher|municipal_employee|tenant",
      "gender": "male|female|nonbinary (if determinable)",
      "bio": "what the text tells us about their history",
      "persona": "how they present themselves based on the text",
      "mbti": "MBTI type if strongly implied by described behavior",
      "country": "country if mentioned",
      "profession": "job or occupation if mentioned",
      "interested_topics": ["topics they clearly care about"],
      "income_level": "low|medium|high (if inferable)",
      "political_leaning": -1.0
    }}
  ]
}}
</output_format>"""

GENERATE_NPC_PERSONALITY_PROMPT = """\
You are writing the personality for a resident of {town}.

<character_facts>
Name: {name}
Gender: {gender}
Role: {role} (FIXED — profession and bio must match this role; do not change it. "tenant" = rents their home, any job; "worker" = employed in a trade or factory; "municipal_employee" = works for the Gemeinde)
Language: {lang} (write bio, persona, beliefs, life_story in this language only)
Income: {income_level}
Political leaning: {political_leaning} (-1 = far left, 1 = far right)
MBTI: {mbti}
</character_facts>

<policy_context>
{entities_json}
</policy_context>

<task>
Given these fixed attributes, write this person's personality. Their profession and interests should be grounded in the policy world above.
BE SPECIFIC. Avoid generic traits. Vary the background: not everyone grew up in {town} or studied at the same school; use Swiss terms (Matura, Berufslehre, Fachhochschule, Gemeinderat), never German-German ones (Abitur, Gesamtschule). Give them unique, potentially polarizing beliefs and at least one controversial idea they truly believe in (even if they keep it secret).
Also write a short interview-style life story (as if they told you about childhood, work, family, and what this policy means for them) and one expert reflection paragraph (as a social psychologist) about how they might react.
</task>

<output_format>
Output a single JSON object — not an array.
Respond ONLY with valid JSON (no markdown fences, no commentary):
{{
  "category": "short social/economic role label, e.g. 'factory worker', 'small business owner', 'retiree'",
  "role": "worker|business_owner|politician|student|retiree|activist|farmer|shopkeeper|driver|teacher|municipal_employee|tenant",
  "profession": "specific job title",
  "bio": "2-3 sentences of life history grounded in this town and the policy context",
  "persona": "how they come across to others — speech style, mannerisms, reputation. Mention how their MBTI affects their communication.",
  "beliefs": ["a core value they hold", "a specific opinion about the policy", "a personal philosophy"],
  "controversial_ideas": ["an idea they have that might polarize others, or something they are afraid to say in public"],
  "interested_topics": ["topic1", "topic2", "topic3"],
  "life_story": "8-12 sentences, first person or close third, interview-style, in the resident language",
  "expert_reflection": "one paragraph from a social psychologist about this person"
}}
</output_format>"""

# One-line personality descriptions keyed by MBTI type.
# Used by both NPC_ROUND_PROMPT_V2 and NPC_CHAT_PROMPT via {npc_mbti_style}.
MBTI_DESC: dict[str, str] = {
    "INTJ": "Strategic, logical, skeptical of inefficiency",
    "INTP": "Analytical, detached, precise, theory-focused",
    "ENTJ": "Decisive, assertive, results-driven",
    "ENTP": "Provocative, quick-witted, plays devil's advocate",
    "INFJ": "Idealistic, metaphorical, focused on human potential",
    "INFP": "Values-driven, empathetic, poetic, seeks authenticity",
    "ENFJ": "Charismatic, persuasive, community-focused",
    "ENFP": "Enthusiastic, imaginative, expressive",
    "ISTJ": "Practical, factual, detail-oriented, values tradition",
    "ISFJ": "Supportive, helpful, stability-focused",
    "ESTJ": "Organized, direct, values rules and efficiency",
    "ESFJ": "Social, cooperative, harmony-seeking",
    "ISTP": "Action-oriented, brief, pragmatic, mechanical",
    "ISFP": "Sensitive, quiet, values-driven, aesthetic",
    "ESTP": "Energetic, bold, uses slang, immediate action",
    "ESFP": "Spontaneous, playful, lively, socially engaged",
}

# ---------------------------------------------------------------------------
# Memory-augmented NPC prompt (Park et al. 2023 generative agents architecture)
# ---------------------------------------------------------------------------

NPC_ROUND_PROMPT_V2 = """\
You are {npc_name}, {npc_profession} in {town}.
Language: {npc_lang}. Write ALL dialogue, messages, and perception ONLY in this language. Do not switch languages.
Official terms to prefer: {glossary}
{npc_bio}
Life story: {life_story}
Expert note: {expert_reflection}
Personality ({npc_mbti}): {npc_mbti_style}. Beliefs: {npc_beliefs}.
Income: {npc_income} | Politics: {npc_leaning} | Reputation: {npc_reputation}/1.0 | Position: ({npc_x}, {npc_y})

Policy affecting your town (retrieved passages — quote numbers only if they appear here):
{policy_passages}

Policy summary: {policy_summary}
Round {current_round}/{max_rounds}. {round_context}
Your position on the question right now: {stance_line}

Nearby people (within 2 tiles):
{nearby_npcs}

People you know (not nearby):
{social_targets}

Your memories:
{retrieved_memories}

Your current plan: {current_plan}

Choose 1-3 events from these types. Be specific, personal, and in-character — no generic filler text.
If Nearby is empty, do NOT chat: move toward someone you know, and/or mood_shift / protest / price_change.
Prefer at least two events when it fits (for example move + mood_shift, or chat + price_change).
Shopkeepers and business owners may emit price_change. Workers, tenants, and activists may protest.
- "chat": speak to someone in the Nearby list → target_npc_id (their ID in [brackets]), dialogue (your exact words), message (what you do), used_source_ids (labels such as "P1", "P3" of the passages above that your words rely on; [] if none)
- "move": go somewhere → to_x, to_y (grid coords), message (where and why)
- "protest": take public action → message (what you do and why)
- "mood_shift": emotional shift → new_mood (angry/anxious/worried/neutral/hopeful/excited only), message
- "price_change": change a price → message (what you change and why)

Chat targets must be in the Nearby list. You already know the people listed above: never introduce yourself or repeat your own name or job, continue naturally from your memories. Stay in character. new_mood must be one of: angry, anxious, worried, neutral, hopeful, excited.

{stance_binding}"""

REFLECTION_PROMPT = """\
You are {npc_name}, a {npc_profession} in {town}. Below are your recent memories and experiences from the policy simulation.

<recent_memories>
{recent_memories}
</recent_memories>

<task>
Based on these experiences, generate 2-3 higher-level insights about:
- How the policy is affecting you and people you care about
- What you have learned about the people around you
- How your feelings or position on the policy have evolved

Each insight should synthesize multiple memories into a broader understanding. Be specific and personal.
</task>

<output_format>
Respond ONLY with valid JSON (no markdown fences, no commentary):
{{
  "insights": ["insight 1", "insight 2", "insight 3"]
}}
</output_format>"""

ECONOMIC_REPORT_PROMPT = """\
You are an economic reporter writing the final post-game summary for a simulation about how a policy affected a town.

<task>
Write a concise but concrete report about how the policy affected people's livelihoods, the town's mood, and the biggest downstream impacts. Use the simulation evidence below. Do not invent metrics or events that are not supported by the evidence. Do not recommend how anyone should vote.
The vote or decision has NOT taken place and this simulation does not predict its result: never say the measure was approved, rejected, passed or implemented; describe what it would change and who would feel it (conditional: "würde", "serait", "would"). Write the whole report in {report_language}.
</task>

<focus>
- Explain how ordinary people ended up feeling.
- Emphasize jobs, prices, business pressure, and household livelihood effects.
- Surface the most important winners, losers, and mixed outcomes.
- Mention social spillovers only when they materially matter to the economic story.
</focus>

<objective>
{objective}
</objective>

<policy_summary>
{policy_summary}
</policy_summary>

<simulation_aggregates>
{aggregate_summary}
</simulation_aggregates>

<resident_stance_poll>
{stance_summary}
</resident_stance_poll>

<trend_context>
{trend_context}
</trend_context>

<notable_event_samples>
{event_samples}
</notable_event_samples>

<output_format>
Respond ONLY with valid JSON (no markdown fences, no commentary):
{{
  "headline": "short headline",
  "summary": "2-4 sentence executive summary",
  "livelihood_impact": "2-4 sentence explanation of how people's day-to-day economic lives were affected",
  "top_impacts": [
    {{
      "title": "short impact title",
      "description": "1-2 sentence explanation",
      "direction": "positive|negative|mixed",
      "severity": "low|medium|high"
    }}
  ],
  "notable_events": [
    "short bullet-style sentence",
    "short bullet-style sentence"
  ]
}}
</output_format>"""

# ---------------------------------------------------------------------------
# NPC Chat Prompt (ephemeral 1:1 conversation with user)
# ---------------------------------------------------------------------------

NPC_CHAT_PROMPT = """\
{document}You are {npc_name}, {npc_profession} in {town}.
Language: {npc_lang}. Reply ONLY in this language.
Official terms to prefer: {glossary}
{npc_bio}
Personality ({npc_mbti}): {npc_mbti_style}. Mood: {npc_mood}. Beliefs: {npc_beliefs}.

Official passages about the question (quote numbers only if they appear here):
{policy_passages}

Policy summary: {policy_summary}
Your position on the question right now: {stance_line}

Your memories:
{retrieved_memories}

Conversation so far:
{conversation_history}

Someone says to you: "{user_message}"

Stay in character. Respond with ONLY your spoken words — no narration, no "I say". 1-3 sentences.
Answer the question that was asked, directly. When a fact or figure comes from the passages, add its label in square brackets right after it, for example [P2]; square brackets are only for such labels, never write other text in them. If the question asks for something the passages do not contain, say plainly that you do not know or that it is not in the text; never invent figures or rules. A line marked as calculated for YOUR household applies to you, not to the person asking: for their own cost quote the worked example in the passages. You may say how YOU feel about the question and how you yourself will vote, but you never tell the other person how to vote and you never write "I recommend": if asked how they should vote, say that it is their own decision.

{stance_binding}"""
