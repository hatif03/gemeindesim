/**
 * Generates public/example-replay.json — a SavedSimulation for the
 * "25% Steel Tariff" scenario with 25 NPCs, 35 relationships, 15 rounds.
 *
 * Usage: node scripts/generate-example-replay.js
 */

const fs = require("fs");
const path = require("path");

// ── Helpers ─────────────────────────────────────────────────

let _id = 0;
function uid() {
  return `npc-${String(++_id).padStart(2, "0")}`;
}

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function round2(n) {
  return Math.round(n * 100) / 100;
}

function round3(n) {
  return Math.round(n * 1000) / 1000;
}

// ── Constants ───────────────────────────────────────────────

const DRIVER_POSITIONS = [
  { x: 6, y: 5 },
  { x: 13, y: 5 },
  { x: 6, y: 12 },
  { x: 18, y: 5 },
  { x: 13, y: 12 },
];

const MBTI_TYPES = ["ENFP", "ISTJ", "INFJ", "ESTP", "INTP", "ESFJ", "ENTJ", "ISFP"];

const COUNTRIES = [
  "United States", "Canada", "Mexico", "South Korea",
  "Japan", "India", "Germany", "Brazil",
];

// ── NPC Roster (hand-crafted for steel tariff scenario) ─────

const NPC_DEFS = [
  // Workers (0-4)
  { name: "Maria Rodriguez", role: "worker", gender: "female", industry: "steel", profession: "steel mill operator", persona: "hardworking and stoic", income: "medium", pol: 0.15, topics: ["jobs", "trade", "manufacturing"], beliefs: ["American steel jobs must be protected.", "Trade policy should put workers first."], controversial: ["Tariffs are worth the short-term pain for long-term job security."] },
  { name: "James Chen", role: "worker", gender: "male", industry: "construction", profession: "construction foreman", persona: "cautious and pragmatic", income: "medium", pol: 0.25, topics: ["housing", "jobs", "infrastructure"], beliefs: ["Construction keeps the economy moving.", "Steel costs hit us directly."], controversial: ["We should source all materials domestically even if it costs more."] },
  { name: "Dmitri Petrov", role: "worker", gender: "male", industry: "manufacturing", profession: "auto parts machinist", persona: "skeptical of government", income: "medium", pol: -0.30, topics: ["manufacturing", "trade", "jobs"], beliefs: ["Government intervention always backfires.", "Free markets find the best price."], controversial: ["Tariffs just make politicians look tough while workers suffer."] },
  { name: "Kenji Tanaka", role: "worker", gender: "male", industry: "steel", profession: "steel quality inspector", persona: "quiet but determined", income: "medium", pol: -0.10, topics: ["trade", "jobs", "community safety"], beliefs: ["Quality domestic steel is a matter of national pride.", "Workers deserve stable employment."], controversial: ["We should accept lower wages to keep factories competitive."] },
  { name: "Priya Sharma", role: "worker", gender: "female", industry: "tech", profession: "hardware engineer", persona: "anxious about the future", income: "high", pol: -0.45, topics: ["tech", "trade", "education"], beliefs: ["Supply chain diversity matters.", "Tech depends on global material sourcing."], controversial: ["Tariffs will push tech manufacturing offshore permanently."] },

  // Business owners (5-8)
  { name: "Sarah Williams", role: "business_owner", gender: "female", industry: "construction", profession: "general contractor", persona: "outspoken and passionate", income: "high", pol: 0.40, topics: ["small business", "housing", "infrastructure"], beliefs: ["Small businesses are the backbone of the economy.", "Regulation kills entrepreneurship."], controversial: ["I'll pass every cost increase directly to customers."] },
  { name: "Roberto Garcia", role: "business_owner", gender: "male", industry: "manufacturing", profession: "machine shop owner", persona: "optimistic and entrepreneurial", income: "high", pol: 0.10, topics: ["manufacturing", "trade", "small business"], beliefs: ["American manufacturing can compete globally.", "Innovation comes from small firms."], controversial: ["This tariff is a gift — our competitors just got 25% more expensive."] },
  { name: "Aisha Hassan", role: "business_owner", gender: "female", industry: "retail", profession: "appliance store owner", persona: "anxious about the future", income: "medium", pol: -0.20, topics: ["small business", "inflation", "trade"], beliefs: ["Customers care about price above all.", "Retailers get squeezed from both ends."], controversial: ["Half the stores on Main Street won't survive this tariff."] },
  { name: "Thomas Mueller", role: "business_owner", gender: "male", industry: "food_service", profession: "restaurant owner", persona: "community-oriented", income: "medium", pol: 0.05, topics: ["small business", "community safety", "food service"], beliefs: ["Local businesses keep communities alive.", "We all rise and fall together."], controversial: ["Restaurant equipment costs will force menu prices up 20%."] },

  // Politicians (9-10)
  { name: "Marcus Johnson", role: "politician", gender: "male", industry: "finance", profession: "city council member", persona: "fiscally conservative", income: "high", pol: 0.65, topics: ["jobs", "trade", "energy"], beliefs: ["Protecting domestic industry is a national security issue.", "Strong trade policy means strong communities."], controversial: ["We need even higher tariffs on Chinese steel specifically."] },
  { name: "Elena Popov", role: "politician", gender: "female", industry: "education", profession: "state representative", persona: "progressive and idealistic", income: "high", pol: -0.70, topics: ["education", "healthcare", "trade"], beliefs: ["Trade policy must consider working families first.", "We need safety nets before tariffs."], controversial: ["This tariff is a handout to steel executives, not workers."] },

  // Students (11-12)
  { name: "Luis Martinez", role: "student", gender: "male", industry: "education", profession: "economics student", persona: "progressive and idealistic", income: "low", pol: -0.55, topics: ["education", "trade", "inflation"], beliefs: ["Free trade lifts all boats.", "Tariffs are a hidden tax on consumers."], controversial: ["Every economics textbook says tariffs are a net loss — why are we doing this?"] },
  { name: "Yuki Yamamoto", role: "student", gender: "female", industry: "education", profession: "engineering student", persona: "quiet but determined", income: "low", pol: -0.15, topics: ["tech", "education", "manufacturing"], beliefs: ["Innovation requires global collaboration.", "Students will inherit whatever mess policy creates."], controversial: ["If steel gets expensive, we should just 3D-print alternatives."] },

  // Retirees (13-14)
  { name: "Olga Ivanova", role: "retiree", gender: "female", industry: "steel", profession: "retired steel union rep", persona: "outspoken and passionate", income: "low", pol: 0.30, topics: ["jobs", "trade", "healthcare"], beliefs: ["Unions built the middle class.", "We fought for these steel jobs — tariffs help protect them."], controversial: ["Back in my day we didn't import steel and we were better for it."] },
  { name: "Ahmed Ali", role: "retiree", gender: "male", industry: "manufacturing", profession: "retired factory manager", persona: "cautious and pragmatic", income: "medium", pol: 0.20, topics: ["manufacturing", "inflation", "healthcare"], beliefs: ["Tariffs helped in the 80s but the world is different now.", "Fixed incomes can't absorb price shocks."], controversial: ["Retirees are the forgotten casualties of trade wars."] },

  // Activists (15-16)
  { name: "Rosa Lopez", role: "activist", gender: "female", industry: "retail", profession: "labor organizer", persona: "outspoken and passionate", income: "low", pol: -0.60, topics: ["jobs", "community safety", "inflation"], beliefs: ["Workers deserve living wages and job security.", "Policy must center the most vulnerable."], controversial: ["A general strike is the only language corporations understand."] },
  { name: "Omar Said", role: "activist", gender: "male", industry: "energy", profession: "environmental activist", persona: "progressive and idealistic", income: "low", pol: -0.75, topics: ["energy", "trade", "community safety"], beliefs: ["Steel tariffs will prop up dirty domestic furnaces.", "Green alternatives need a chance to compete."], controversial: ["We should ban domestic coal-fired steel production entirely."] },

  // Farmers (17-18)
  { name: "Anna Taylor", role: "farmer", gender: "female", industry: "agriculture", profession: "soybean farmer", persona: "hardworking and stoic", income: "medium", pol: 0.35, topics: ["agriculture", "trade", "energy"], beliefs: ["Farmers always pay the price for trade wars.", "Retaliatory tariffs will crush exports."], controversial: ["If China retaliates on soybeans, half the farms in this county go under."] },
  { name: "Jin Wei", role: "farmer", gender: "male", industry: "agriculture", profession: "dairy farmer", persona: "skeptical of government", income: "low", pol: 0.10, topics: ["agriculture", "inflation", "small business"], beliefs: ["Equipment costs are already crushing us.", "Steel tariffs mean more expensive tractors and silos."], controversial: ["Family farms are being sacrificed to score political points."] },

  // Shopkeepers (19)
  { name: "Fatima Patel", role: "shopkeeper", gender: "female", industry: "retail", profession: "hardware store owner", persona: "community-oriented", income: "medium", pol: -0.05, topics: ["small business", "inflation", "housing"], beliefs: ["A hardware store is the heartbeat of a working town.", "Steel product prices will spike and customers will blame me."], controversial: ["I'm stockpiling inventory now before prices jump — everyone should."] },

  // Drivers (20-24)
  { name: "Diego Hernandez", role: "driver", gender: "male", industry: "retail", profession: "delivery driver", persona: "hardworking and stoic", income: "low", pol: 0.05, topics: ["transit", "jobs", "inflation"], beliefs: ["Drivers see the real economy every day.", "If businesses close, there's nothing to deliver."], controversial: ["Gig economy drivers have zero safety net when things go south."] },
  { name: "Emma Brown", role: "driver", gender: "female", industry: "retail", profession: "taxi driver", persona: "cautious and pragmatic", income: "low", pol: -0.10, topics: ["transit", "community safety", "jobs"], beliefs: ["I talk to everyone — the mood in town is shifting fast.", "People are scared."], controversial: ["Crime goes up when the economy goes down — I see it every night shift."] },
  { name: "Raj Singh", role: "driver", gender: "male", industry: "construction", profession: "delivery driver", persona: "optimistic and entrepreneurial", income: "low", pol: 0.00, topics: ["transit", "small business", "trade"], beliefs: ["More construction means more deliveries.", "Tariffs could actually boost local demand."], controversial: ["Delivery drivers should unionize before automation replaces us all."] },
  { name: "Svetlana Volkov", role: "driver", gender: "female", industry: "food_service", profession: "taxi driver", persona: "anxious about the future", income: "low", pol: -0.25, topics: ["transit", "inflation", "healthcare"], beliefs: ["Everything is getting more expensive.", "My car repair costs are linked to steel prices too."], controversial: ["If gas and parts keep rising I'll have to stop driving."] },
  { name: "Chen Kim", role: "driver", gender: "nonbinary", industry: "tech", profession: "delivery driver", persona: "quiet but determined", income: "low", pol: -0.35, topics: ["transit", "tech", "jobs"], beliefs: ["Tech platforms exploit drivers.", "Steel tariffs are just one more cost that rolls downhill."], controversial: ["Autonomous vehicles will make this debate irrelevant in five years."] },
];

// ── Steel tariff scenario messages ──────────────────────────

const CHAT_PHASE1 = [
  "Just heard about the 25% steel tariff. This changes everything for our supply chain.",
  "I'm cautiously optimistic — domestic steel could see a real boost from this.",
  "My supplier already warned me prices are going up next month.",
  "The tariff announcement hit the news this morning. Everyone at work is talking about it.",
  "I need to recalculate all my project bids with 25% higher steel costs.",
  "My union rep says this is a win for American steelworkers. I hope they're right.",
  "Twenty-five percent! That's going to ripple through every industry that uses steel.",
  "I'm telling my customers to lock in current prices before the tariff kicks in.",
  "The stock market seems to like it — steel company shares are up.",
  "Trade wars never end well. I remember what happened last time.",
  "City council is meeting next week to discuss how this affects local construction projects.",
  "My economics professor says tariffs create deadweight loss. But real life is more complicated.",
  "I've been sourcing steel from three countries — now I need to find domestic alternatives fast.",
  "The farmers' co-op is worried about retaliatory tariffs on agricultural exports.",
  "At least the steel mill is hiring again. That hasn't happened in years.",
];

const CHAT_PHASE2 = [
  "Appliance prices jumped 18% at my store. Customers are furious.",
  "The construction company just froze all new projects until costs stabilize.",
  "I heard two auto parts suppliers in the county are laying off workers.",
  "My restaurant needs new kitchen equipment but everything steel-based costs a fortune now.",
  "Grocery prices are creeping up too — steel tariffs affect packaging and transport.",
  "The steel mill hired 30 new workers. That's real, that matters.",
  "But at what cost? My hardware store sales are down 25% this month.",
  "Someone spray-painted 'TARIFFS KILL JOBS' on the old factory wall.",
  "I'm organizing a town hall meeting to discuss the economic impact.",
  "China just announced retaliatory tariffs on soybeans. I'm ruined.",
  "My pension isn't keeping up with these price increases.",
  "Local news says the county lost 200 jobs in manufacturing this quarter.",
  "I had to cut my delivery routes — businesses are ordering less inventory.",
  "The school board is delaying the new gymnasium because steel framing costs doubled.",
  "Some people are protesting downtown. I understand their frustration.",
];

const CHAT_PHASE3 = [
  "Aisha's appliance store on Main Street just closed permanently.",
  "The protest last weekend drew 500 people. City hall is finally paying attention.",
  "Three more families on my street put their houses up for sale.",
  "I started a community food bank. People are too proud to ask for help but they need it.",
  "The steel mill is running at full capacity but the rest of the town is suffering.",
  "My farm is facing foreclosure. The soybean export market collapsed.",
  "Crime reports are up 30% according to the police blotter.",
  "I'm running for city council. Somebody needs to fight for working people.",
  "The irony is steel workers are doing great while everyone else drowns.",
  "We need a comprehensive support package, not just tariffs.",
  "My neighbors and I started a mutual aid network. We share groceries and childcare.",
  "The state representative is pushing for a tariff adjustment — too little, too late.",
  "I've never seen this community so divided. Families are arguing at dinner tables.",
  "We're adapting. I found a non-steel alternative for half my product line.",
  "This town survived the coal bust. We'll survive this too. But it hurts.",
];

const PROTEST_MESSAGES_BY_PHASE = {
  2: [
    "Steel tariffs are crushing small business! Roll them back!",
    "Fair trade, not free trade! Protect American workers!",
    "We demand a public hearing on tariff impacts!",
    "Our jobs matter! Support domestic steel!",
    "Stop the trade war before it's too late!",
  ],
  3: [
    "Enough! People are losing their homes because of this tariff!",
    "Roll back the tariff NOW! Save our community!",
    "Workers united against corporate welfare tariffs!",
    "Main Street is dying — is this what 'winning' looks like?",
    "We the people demand economic justice!",
    "Tariff profiteers out! Community needs first!",
    "Our children deserve better than a trade war!",
  ],
};

const PRICE_CHANGE_ITEMS = [
  { item: "steel beams", base: 12 },
  { item: "appliances", base: 15 },
  { item: "auto parts", base: 10 },
  { item: "construction materials", base: 18 },
  { item: "kitchen equipment", base: 14 },
  { item: "farm equipment", base: 20 },
  { item: "hardware supplies", base: 8 },
  { item: "canned goods", base: 5 },
  { item: "vehicle repairs", base: 11 },
];

const MOOD_EVOLUTION = {
  // Phase 1: mostly neutral/hopeful with some anxiety
  1: { angry: 0.02, anxious: 0.15, worried: 0.20, neutral: 0.35, hopeful: 0.23, excited: 0.05 },
  // Phase 2: growing anxiety and worry
  2: { angry: 0.10, anxious: 0.25, worried: 0.30, neutral: 0.15, hopeful: 0.15, excited: 0.05 },
  // Phase 3: angry and anxious dominate
  3: { angry: 0.30, anxious: 0.25, worried: 0.20, neutral: 0.10, hopeful: 0.10, excited: 0.05 },
};

// ── NPC Generation ──────────────────────────────────────────

function generateNPCs() {
  const occupied = new Set();
  // Pre-reserve driver positions so random placement doesn't collide
  for (const pos of DRIVER_POSITIONS) {
    occupied.add(`${pos.x},${pos.y}`);
  }
  const npcs = [];

  for (let i = 0; i < NPC_DEFS.length; i++) {
    const def = NPC_DEFS[i];
    let x, y;

    if (i >= 20) {
      // Driver positions
      const pos = DRIVER_POSITIONS[i - 20];
      x = pos.x;
      y = pos.y;
    } else {
      do {
        x = randInt(0, 19);
        y = randInt(0, 14);
      } while (occupied.has(`${x},${y}`));
    }
    occupied.add(`${x},${y}`);

    npcs.push({
      id: uid(),
      name: def.name,
      gender: def.gender,
      bio: `${def.name} works as a ${def.profession} and is known around town for being ${def.persona}.`,
      persona: def.persona,
      mbti: MBTI_TYPES[i % MBTI_TYPES.length],
      country: COUNTRIES[i % COUNTRIES.length],
      profession: def.profession,
      role: def.role,
      industry: def.industry,
      interested_topics: def.topics,
      income_level: def.income,
      political_leaning: def.pol,
      reputation: round2(0.35 + Math.random() * 0.45),
      beliefs: def.beliefs,
      controversial_ideas: def.controversial,
      x,
      y,
      mood: "neutral",
    });
  }

  return npcs;
}

// ── Relationships ───────────────────────────────────────────

const REL_TYPES = ["friend", "family", "employer", "neighbor", "colleague"];

function generateRelationships(npcs) {
  const rels = [];
  const seen = new Set();

  // Hand-craft some meaningful relationships first
  const meaningful = [
    // Steel workers know each other
    [0, 3, "colleague", 0.8, 0.6, 0.7],
    // Construction foreman ↔ general contractor (employer)
    [1, 5, "employer", 0.9, 0.5, 0.8],
    // Machine shop owner ↔ steel mill operator
    [6, 0, "colleague", 0.7, 0.7, 0.6],
    // Retired union rep ↔ current steel worker (family friend)
    [13, 0, "family", 0.85, 0.8, 0.9],
    // Politicians know each other
    [9, 10, "colleague", 0.6, -0.3, 0.4],
    // Students are friends
    [11, 12, "friend", 0.75, 0.5, 0.7],
    // Farmers are neighbors
    [17, 18, "neighbor", 0.8, 0.6, 0.8],
    // Labor organizer ↔ steel worker
    [15, 0, "friend", 0.7, 0.5, 0.6],
    // Hardware store ↔ contractor
    [19, 5, "friend", 0.65, 0.4, 0.7],
    // Restaurant owner ↔ taxi driver
    [7, 21, "friend", 0.5, 0.3, 0.5],
    // Appliance store ↔ hardware store (neighbors on Main St)
    [8, 19, "neighbor", 0.7, 0.6, 0.7],
    // Delivery driver ↔ restaurant owner
    [20, 7, "employer", 0.6, 0.4, 0.6],
    // Environmental activist ↔ soybean farmer
    [16, 17, "neighbor", 0.4, -0.2, 0.3],
    // Retirees are neighbors
    [13, 14, "neighbor", 0.75, 0.7, 0.8],
    // Politician ↔ labor organizer
    [10, 15, "friend", 0.5, 0.4, 0.5],
  ];

  for (const [a, b, relType, str, aff, tru] of meaningful) {
    const key = `${Math.min(a, b)}-${Math.max(a, b)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    rels.push({
      source_id: npcs[a].id,
      target_id: npcs[b].id,
      rel_type: relType,
      strength: str,
      affinity: aff,
      trust: tru,
    });
  }

  // Fill to 35 with random relationships
  while (rels.length < 35) {
    const a = randInt(0, npcs.length - 1);
    const b = randInt(0, npcs.length - 1);
    if (a === b) continue;
    const key = `${Math.min(a, b)}-${Math.max(a, b)}`;
    if (seen.has(key)) continue;
    seen.add(key);

    rels.push({
      source_id: npcs[a].id,
      target_id: npcs[b].id,
      rel_type: pick(REL_TYPES),
      strength: round2(Math.random()),
      affinity: round2(Math.random() * 2 - 1),
      trust: round2(Math.random()),
    });
  }

  return rels;
}

// ── Round Generation ────────────────────────────────────────

function pickWeightedMood(phase) {
  const weights = MOOD_EVOLUTION[phase];
  const r = Math.random();
  let cumulative = 0;
  for (const [mood, prob] of Object.entries(weights)) {
    cumulative += prob;
    if (r <= cumulative) return mood;
  }
  return "neutral";
}

function generateRound(npcs, relationships, round) {
  const phase = round < 5 ? 1 : round < 10 ? 2 : 3;
  const events = [];
  const updated = npcs.map((n) => ({ ...n }));

  // 3-8 active NPCs per round
  const activeCount = randInt(3, 8);
  const activeIndices = new Set();
  while (activeIndices.size < activeCount) {
    activeIndices.add(randInt(0, updated.length - 1));
  }

  for (const idx of activeIndices) {
    const npc = updated[idx];
    const roll = Math.random();

    // Phase-dependent event distribution
    if (phase === 1) {
      // Phase 1: 65% chat, 15% move, 15% mood_shift, 3% protest, 2% price_change
      if (roll < 0.15) {
        emitMove(events, npc, round);
      } else if (roll < 0.30) {
        emitMoodShift(events, npc, round, phase);
      } else if (roll < 0.95) {
        emitChat(events, npc, updated, round, phase);
      } else if (roll < 0.98) {
        emitProtest(events, npc, round, phase);
      } else {
        emitPriceChange(events, npc, round, phase);
      }
    } else if (phase === 2) {
      // Phase 2: 40% chat, 10% move, 15% mood_shift, 20% price_change, 15% protest
      if (roll < 0.10) {
        emitMove(events, npc, round);
      } else if (roll < 0.25) {
        emitMoodShift(events, npc, round, phase);
      } else if (roll < 0.65) {
        emitChat(events, npc, updated, round, phase);
      } else if (roll < 0.80) {
        emitProtest(events, npc, round, phase);
      } else {
        emitPriceChange(events, npc, round, phase);
      }
    } else {
      // Phase 3: 35% chat, 5% move, 15% mood_shift, 30% protest, 15% price_change
      if (roll < 0.05) {
        emitMove(events, npc, round);
      } else if (roll < 0.20) {
        emitMoodShift(events, npc, round, phase);
      } else if (roll < 0.55) {
        emitChat(events, npc, updated, round, phase);
      } else if (roll < 0.85) {
        emitProtest(events, npc, round, phase);
      } else {
        emitPriceChange(events, npc, round, phase);
      }
    }
  }

  // Generate influence events from chat events
  const influenceEvents = events
    .filter((e) => e.event_type === "chat" && e.data.target_npc_id)
    .map((e) => {
      const behaviors = ["keep", "compromise", "adopt"];
      // Phase affects behavior distribution
      const bRoll = Math.random();
      let behavior;
      if (phase === 1) {
        behavior = bRoll < 0.5 ? "keep" : bRoll < 0.85 ? "compromise" : "adopt";
      } else if (phase === 2) {
        behavior = bRoll < 0.3 ? "keep" : bRoll < 0.75 ? "compromise" : "adopt";
      } else {
        behavior = bRoll < 0.2 ? "keep" : bRoll < 0.6 ? "compromise" : "adopt";
      }

      const influence =
        behavior === "keep"
          ? round3(Math.random() * 0.24)
          : behavior === "adopt"
            ? round3(0.85 + Math.random() * 0.15)
            : round3(0.25 + Math.random() * 0.6);

      return {
        speaker_id: e.npc_id,
        target_id: e.data.target_npc_id,
        influence,
        behavior,
        political_delta: behavior === "keep" ? 0 : round3(Math.random() * 0.2 - 0.1),
        mood_delta: behavior === "keep" ? 0 : round3(Math.random() * 0.3 - 0.15),
      };
    });

  // Apply influence to political leanings
  for (const ie of influenceEvents) {
    const target = updated.find((n) => n.id === ie.target_id);
    if (target) {
      target.political_leaning = round2(
        clamp(target.political_leaning + ie.political_delta, -1, 1)
      );
    }
  }

  // Evolve perception and plans in later rounds
  if (round > 0) {
    for (const npc of updated) {
      npc.perception = generatePerception(npc, phase);
      npc.current_plan = generatePlan(npc, phase);
    }
  }

  return { events, updatedNpcs: updated, influenceEvents };
}

function emitMove(events, npc, round) {
  const dx = randInt(-1, 1);
  const dy = randInt(-1, 1);
  const newX = clamp(npc.x + dx, 0, 19);
  const newY = clamp(npc.y + dy, 0, 14);
  events.push({
    round,
    npc_id: npc.id,
    event_type: "move",
    message: "",
    data: { from_x: npc.x, from_y: npc.y, to_x: newX, to_y: newY },
  });
  npc.x = newX;
  npc.y = newY;
}

function emitMoodShift(events, npc, round, phase) {
  const newMood = pickWeightedMood(phase);
  events.push({
    round,
    npc_id: npc.id,
    event_type: "mood_shift",
    message: `Feeling ${newMood} about the steel tariff situation.`,
    data: { old_mood: npc.mood, new_mood: newMood },
  });
  npc.mood = newMood;
}

function emitChat(events, npc, allNpcs, round, phase) {
  const others = allNpcs.filter((n) => n.id !== npc.id);
  const target = pick(others);
  const msgs = phase === 1 ? CHAT_PHASE1 : phase === 2 ? CHAT_PHASE2 : CHAT_PHASE3;
  events.push({
    round,
    npc_id: npc.id,
    event_type: "chat",
    message: pick(msgs),
    data: { target_npc_id: target.id },
  });
}

function emitProtest(events, npc, round, phase) {
  // Phase 1 protests are very rare and mild
  const msgs = phase === 1
    ? ["We should pay attention to how this tariff affects everyday people."]
    : PROTEST_MESSAGES_BY_PHASE[phase] || PROTEST_MESSAGES_BY_PHASE[3];
  events.push({
    round,
    npc_id: npc.id,
    event_type: "protest",
    message: pick(msgs),
    data: {},
  });
}

function emitPriceChange(events, npc, round, phase) {
  const item = pick(PRICE_CHANGE_ITEMS);
  const pctChange = phase === 1
    ? randInt(2, 8)
    : phase === 2
      ? randInt(8, 22)
      : randInt(15, 35);
  const direction = Math.random() < 0.85 ? 1 : -1;
  events.push({
    round,
    npc_id: npc.id,
    event_type: "price_change",
    message: direction > 0
      ? `Raised ${item.item} prices by ${pctChange}% due to steel tariff cost increases.`
      : `Cut ${item.item} prices by ${pctChange}% trying to stay competitive.`,
    data: { pct_change: pctChange * direction, item: item.item },
  });
}

function generatePerception(npc, phase) {
  const perceptions = {
    worker: {
      1: "The tariff could protect my job but co-workers are divided on whether it will last.",
      2: "Some factories are hiring but others are cutting hours. The picture is mixed.",
      3: "The community is hurting. Even though steel jobs are stable, everything else is falling apart.",
    },
    business_owner: {
      1: "I need to figure out how to absorb or pass on increased material costs.",
      2: "Sales are down and costs are up. Several businesses nearby have already closed.",
      3: "Survival mode. I'm cutting every expense I can to keep the doors open.",
    },
    politician: {
      1: "Constituents are watching closely. I need to position myself carefully on this issue.",
      2: "Calls to my office have tripled. People want answers about rising prices.",
      3: "The community is deeply divided. I need to propose concrete relief measures.",
    },
    student: {
      1: "This is a real-world test of everything we study in economics class.",
      2: "My classmates can't afford textbooks anymore with prices going up everywhere.",
      3: "Students are joining the protests. This is about our future.",
    },
    retiree: {
      1: "My fixed income should be fine for now but I'm keeping an eye on prices.",
      2: "Grocery and medicine costs are eating into my savings faster than expected.",
      3: "I've seen economic downturns before but this one feels different — more personal.",
    },
    activist: {
      1: "This tariff will hit the most vulnerable hardest. I need to start organizing.",
      2: "The community response is growing. People are ready to take to the streets.",
      3: "The movement is strong but we need concrete demands, not just anger.",
    },
    farmer: {
      1: "Watching trade news carefully. Retaliatory tariffs could devastate exports.",
      2: "Equipment costs are up and export markets are shrinking. Double hit.",
      3: "I'm talking to the bank about restructuring my farm loan. It's that bad.",
    },
    shopkeeper: {
      1: "Customers are asking about price changes. I'm being transparent about costs.",
      2: "Foot traffic is down 30%. People are cutting back on non-essentials.",
      3: "I may need to lay off my only employee. This keeps me up at night.",
    },
    driver: {
      1: "Business seems normal for now but everyone I pick up is talking about the tariff.",
      2: "Fewer deliveries, shorter rides. People are spending less.",
      3: "Gas and repairs cost more. Fewer customers. I'm barely breaking even.",
    },
  };
  return (perceptions[npc.role] || perceptions.worker)[phase];
}

function generatePlan(npc, phase) {
  const plans = {
    worker: {
      1: "Keep working hard and hope the tariff protects my job long-term.",
      2: "Look into retraining programs just in case. Update my resume.",
      3: "Join the community mutual aid effort while keeping my head down at work.",
    },
    business_owner: {
      1: "Review all supplier contracts and find domestic alternatives where possible.",
      2: "Cut non-essential expenses. Consider reducing staff hours.",
      3: "Apply for small business emergency loans. Consider pivoting product lines.",
    },
    politician: {
      1: "Schedule public listening sessions to hear constituent concerns.",
      2: "Draft a local economic impact assessment and request state aid.",
      3: "Introduce an emergency relief package for affected small businesses.",
    },
    student: {
      1: "Research the economic theory behind tariffs for my thesis.",
      2: "Organize a campus teach-in about trade policy impacts.",
      3: "Lead a student coalition joining the community protests.",
    },
    retiree: {
      1: "Review my budget and identify where I can cut if prices rise.",
      2: "Attend town hall meetings and share my experience from past downturns.",
      3: "Help organize the community food bank and mutual aid network.",
    },
    activist: {
      1: "Build a coalition of affected workers and businesses.",
      2: "Plan a peaceful demonstration at city hall.",
      3: "Escalate to sustained protest actions and media outreach.",
    },
    farmer: {
      1: "Diversify crops to reduce dependence on export markets.",
      2: "Join the farmers' cooperative lobbying effort for relief funds.",
      3: "Negotiate with creditors and explore alternative income streams.",
    },
    shopkeeper: {
      1: "Stockpile current inventory at pre-tariff prices.",
      2: "Shift to non-steel product alternatives where possible.",
      3: "Consider closing unprofitable product lines to stay afloat.",
    },
    driver: {
      1: "Keep driving and save extra for potential lean times.",
      2: "Add a second gig to supplement declining delivery income.",
      3: "Join the drivers' cooperative to share costs and negotiate better rates.",
    },
  };
  return (plans[npc.role] || plans.worker)[phase];
}

// ── Main ────────────────────────────────────────────────────

function main() {
  // Seed for reproducibility (simple seeded PRNG would be better but fine for hackathon)
  const npcs = generateNPCs();
  const relationships = generateRelationships(npcs);

  const initMsg = {
    type: "init",
    npcs: [...npcs],
    relationships,
  };

  const rounds = [];
  let currentNpcs = npcs;

  for (let r = 0; r < 15; r++) {
    const { events, updatedNpcs, influenceEvents } = generateRound(
      currentNpcs,
      relationships,
      r
    );
    currentNpcs = updatedNpcs;
    rounds.push({
      type: "round",
      round: r,
      events,
      npcs: currentNpcs.map((n) => ({ ...n })),
      influence_events: influenceEvents,
    });
  }

  const savedSimulation = {
    version: 1,
    savedAt: "2026-03-29T00:00:00.000Z",
    policyText:
      "Effective immediately, a 25% tariff is imposed on all imported steel and steel-derivative products entering the country. This measure aims to protect domestic steel manufacturing, preserve industrial jobs, and reduce dependency on foreign steel suppliers. All steel imports — including raw steel, steel alloys, structural beams, steel pipe, rebar, and finished steel components — will be subject to the new duty rate at port of entry. Domestic steel producers are expected to increase output to meet demand previously filled by imports. The tariff applies to all trading partners without exception. The administration projects this will create approximately 15,000 new steelworking jobs within 18 months and generate $2.4 billion in annual tariff revenue. Critics warn the measure could raise consumer prices on automobiles, appliances, and construction materials by 8-20%, potentially triggering retaliatory tariffs from major trading partners including China, the EU, Japan, and South Korea. Small businesses in construction, manufacturing, and retail sectors may face significant cost increases. The policy includes no exemption process for downstream manufacturers or hardship provisions for affected industries.",
    maxRounds: 15,
    initMsg,
    rounds,
  };

  const outPath = path.join(__dirname, "..", "public", "example-replay.json");
  fs.writeFileSync(outPath, JSON.stringify(savedSimulation, null, 2));

  // Summary stats
  const totalEvents = rounds.reduce((sum, r) => sum + r.events.length, 0);
  const eventTypes = {};
  for (const r of rounds) {
    for (const e of r.events) {
      eventTypes[e.event_type] = (eventTypes[e.event_type] || 0) + 1;
    }
  }
  const totalInfluence = rounds.reduce(
    (sum, r) => sum + (r.influence_events || []).length,
    0
  );

  console.log(`Written: ${outPath}`);
  console.log(`NPCs: ${initMsg.npcs.length}`);
  console.log(`Relationships: ${relationships.length}`);
  console.log(`Rounds: ${rounds.length}`);
  console.log(`Total events: ${totalEvents}`);
  console.log(`Event breakdown:`, eventTypes);
  console.log(`Total influence events: ${totalInfluence}`);
}

main();
