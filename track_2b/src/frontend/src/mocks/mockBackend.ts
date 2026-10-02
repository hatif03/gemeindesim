/**
 * Mock backend data generator for frontend testing without a running backend.
 * Activated by NEXT_PUBLIC_MOCK_BACKEND=true in .env.local
 *
 * Generates 25 NPCs, 35 relationships, and 75 rounds of events that mirror
 * the real backend's data shapes (see backendTypes.ts).
 */

import type {
  BackendInfluenceEvent,
  BackendMood,
  BackendNPC,
  BackendRelationship,
  BackendRelType,
  BackendRole,
  BackendSimEvent,
  WSInitMsg,
  WSRoundMsg,
} from "@/types/backend";

// ── Helpers ─────────────────────────────────────────────────

let _id = 0;
function uid(): string {
  return `mock-${++_id}`;
}

function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

/**
 * Get NPCs within Chebyshev distance (max of |dx|, |dy|) of the given NPC.
 * Matches backend proximity check.
 */
function getNearbyNpcs(
  npc: BackendNPC,
  allNpcs: BackendNPC[],
  radius = 2,
): BackendNPC[] {
  return allNpcs.filter((other) => {
    if (other.id === npc.id) return false;
    const dx = Math.abs(other.x - npc.x);
    const dy = Math.abs(other.y - npc.y);
    return Math.max(dx, dy) <= radius;
  });
}

// ── NPC Generation (25 agents, grid 20x15) ──────────────────

const ROLES: BackendRole[] = [
  "worker",
  "business_owner",
  "politician",
  "student",
  "retiree",
  "activist",
  "farmer",
  "shopkeeper",
  "driver",
];

const MOODS: BackendMood[] = [
  "angry",
  "anxious",
  "worried",
  "neutral",
  "hopeful",
  "excited",
];

const INDUSTRIES = [
  "steel",
  "retail",
  "agriculture",
  "tech",
  "construction",
  "finance",
  "education",
  "healthcare",
  "manufacturing",
  "food_service",
];

const PERSONALITIES = [
  "cautious and pragmatic",
  "outspoken and passionate",
  "quiet but determined",
  "optimistic and entrepreneurial",
  "skeptical of government",
  "community-oriented",
  "fiscally conservative",
  "progressive and idealistic",
  "hardworking and stoic",
  "anxious about the future",
];

const COUNTRIES = [
  "United States",
  "Canada",
  "Mexico",
  "South Korea",
  "Japan",
  "India",
  "Germany",
  "Brazil",
];

const MBTI_TYPES = [
  "ENFP",
  "ISTJ",
  "INFJ",
  "ESTP",
  "INTP",
  "ESFJ",
  "ENTJ",
  "ISFP",
];

const INTEREST_TOPICS = [
  "housing",
  "transit",
  "small business",
  "jobs",
  "education",
  "inflation",
  "energy",
  "healthcare",
  "community safety",
  "trade",
];

const FIRST_NAMES = [
  "Maria",
  "James",
  "Chen",
  "Aisha",
  "Roberto",
  "Sarah",
  "Dmitri",
  "Kenji",
  "Fatima",
  "Luis",
  "Emma",
  "Raj",
  "Olga",
  "Marcus",
  "Yuki",
  "Ahmed",
  "Rosa",
  "Thomas",
  "Priya",
  "Diego",
  "Anna",
  "Omar",
  "Svetlana",
  "Jin",
  "Elena",
];

const LAST_NAMES = [
  "Rodriguez",
  "Chen",
  "Williams",
  "Hassan",
  "Garcia",
  "Kim",
  "Petrov",
  "Tanaka",
  "Singh",
  "Martinez",
  "Johnson",
  "Patel",
  "Ivanova",
  "Brown",
  "Yamamoto",
  "Ali",
  "Lopez",
  "Mueller",
  "Sharma",
  "Hernandez",
  "Taylor",
  "Said",
  "Volkov",
  "Wei",
  "Popov",
];

/** Fixed road positions for driver NPCs (on citypack road columns/rows) */
const DRIVER_POSITIONS: { x: number; y: number }[] = [
  { x: 6, y: 5 }, // tileX=12 (road col), tileY=10 (road row)
  { x: 13, y: 5 }, // tileX=26 (road col), tileY=10 (road row)
  { x: 6, y: 12 }, // tileX=12 (road col), tileY=24 (road row)
  { x: 20, y: 5 }, // tileX=40 (road col), tileY=10 (road row)
  { x: 13, y: 19 }, // tileX=26 (road col), tileY=38 (road row)
];

function professionForRole(role: BackendRole, industry: string, index: number): string {
  switch (role) {
    case "worker":
      return `${industry} technician`;
    case "business_owner":
      return "small business owner";
    case "politician":
      return "city council member";
    case "student":
      return "student organizer";
    case "retiree":
      return "retired foreman";
    case "activist":
      return "community organizer";
    case "farmer":
      return "market farmer";
    case "shopkeeper":
      return "corner shopkeeper";
    case "driver":
      return index % 2 === 0 ? "delivery driver" : "taxi driver";
  }
}

function generateNPCs(): BackendNPC[] {
  // Track occupied cells to avoid stacking NPCs
  const occupied = new Set<string>();
  const npcs: BackendNPC[] = [];

  for (let i = 0; i < 25; i++) {
    let x: number;
    let y: number;

    if (i >= 20) {
      // Driver NPCs (indices 20-24) placed on road tiles
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

    const role: BackendRole =
      i >= 20
        ? "driver"
        : i < 4
          ? "worker"
          : i < 7
            ? "business_owner"
            : ROLES[i % ROLES.length];

    const industry = INDUSTRIES[i % INDUSTRIES.length];
    const persona = PERSONALITIES[i % PERSONALITIES.length];
    const profession = professionForRole(role, industry, i);
    const reputation = Math.round((0.35 + Math.random() * 0.45) * 100) / 100;
    const interested_topics = [
      INTEREST_TOPICS[i % INTEREST_TOPICS.length],
      INTEREST_TOPICS[(i + 3) % INTEREST_TOPICS.length],
      industry.replace("_", " "),
    ];

    npcs.push({
      id: uid(),
      name: `${FIRST_NAMES[i]} ${LAST_NAMES[i]}`,
      gender: i % 3 === 0 ? "female" : i % 3 === 1 ? "male" : "nonbinary",
      bio: `${FIRST_NAMES[i]} works as a ${profession} and is known around town for being ${persona}.`,
      persona,
      mbti: MBTI_TYPES[i % MBTI_TYPES.length],
      country: COUNTRIES[i % COUNTRIES.length],
      profession,
      role,
      industry,
      interested_topics,
      income_level: pick(["low", "medium", "high"]),
      political_leaning: Math.round((Math.random() * 2 - 1) * 100) / 100,
      reputation,
      beliefs: [
        "Everyday residents should have a real say in local policy.",
        `${industry.replace("_", " ")} matters to the town economy.`,
      ],
      controversial_ideas: [
        `Prioritize public funding for ${industry.replace("_", " ")} over luxury development.`,
      ],
      x,
      y,
      mood: i < 8 ? "neutral" : pick(MOODS),
    });
  }

  return npcs;
}

// ── Relationships (30-40 links) ─────────────────────────────

const REL_TYPES: BackendRelType[] = [
  "friend",
  "family",
  "employer",
  "neighbor",
  "colleague",
];

function generateRelationships(npcs: BackendNPC[]): BackendRelationship[] {
  const rels: BackendRelationship[] = [];
  const seen = new Set<string>();
  const count = randInt(30, 40);

  while (rels.length < count) {
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
      strength: Math.round(Math.random() * 100) / 100,
      affinity: Math.round((Math.random() * 2 - 1) * 100) / 100,
      trust: Math.round(Math.random() * 100) / 100,
    });
  }

  return rels;
}

// ── Round Event Generation ──────────────────────────────────

const CHAT_MESSAGES_BY_PHASE: Record<number, string[]> = {
  1: [
    "I just heard about the new policy — not sure what to make of it yet.",
    "Prices might go up, we should stock up on essentials.",
    "The government says this will create jobs, but I'm skeptical.",
    "My boss called a meeting about the policy changes tomorrow.",
    "I think this could actually help our industry in the long run.",
    "People at the market are already talking about price hikes.",
    "I need to figure out how this affects my pension.",
    "This is exactly what we've been asking for!",
    "I'm worried about my small business — margins are already thin.",
    "Let's wait and see before we panic.",
  ],
  2: [
    "Prices at the grocery store went up 15% this week alone.",
    "Two shops on Main Street just closed — this is getting real.",
    "I got my hours cut. They say it's because of the new costs.",
    "The factory is talking about layoffs if things don't improve.",
    "I can barely afford rent anymore with these price increases.",
    "Some people are organizing a protest downtown this weekend.",
    "My neighbor lost their job — the whole block is worried.",
    "Business is actually up for me — imported goods cost more so people buy local.",
    "The government needs to do something about these prices.",
    "I'm thinking about moving to find better opportunities.",
  ],
  3: [
    "There's a protest every week now. People are angry.",
    "I had to close my shop. Twenty years of work, gone.",
    "The community is really coming together to support each other.",
    "Crime is up in our neighborhood — people are desperate.",
    "I've never seen so many 'For Sale' signs on this street.",
    "They're talking about rolling back the policy — too little too late.",
    "My family is splitting apart over politics because of this.",
    "We need to adapt. The old way isn't coming back.",
    "I started a mutual aid group — we help each other now.",
    "I'm going to run for local office. Someone has to fix this.",
  ],
};

const PROTEST_MESSAGES = [
  "Enough is enough! We demand fair prices!",
  "Workers unite! We won't be silenced!",
  "This policy is destroying our livelihoods!",
  "Roll back the policy! Save our jobs!",
  "We the people say NO!",
];

const PRICE_CHANGE_MESSAGES = [
  "Adjusted prices due to increased supply costs.",
  "Had to raise prices — supplier costs are through the roof.",
  "Lowered prices to attract more customers in tough times.",
  "Emergency price hike to stay afloat.",
];

function generateRoundEvents(
  npcs: BackendNPC[],
  relationships: BackendRelationship[],
  round: number,
  maxRounds: number,
): {
  events: BackendSimEvent[];
  updatedNpcs: BackendNPC[];
  influenceEvents: BackendInfluenceEvent[];
} {
  const third = Math.floor(maxRounds / 3);
  const phase = round < third ? 1 : round < third * 2 ? 2 : 3;
  const events: BackendSimEvent[] = [];
  const updated = npcs.map((n) => ({ ...n }));

  // Each round: 3-8 active NPCs produce events
  const activeCount = randInt(3, 8);
  const activeIndices = new Set<number>();
  while (activeIndices.size < activeCount) {
    activeIndices.add(randInt(0, updated.length - 1));
  }

  for (const idx of activeIndices) {
    const npc = updated[idx];

    // ~60% chat, ~15% move, ~10% mood_shift, ~10% protest (higher in later phases), ~5% price_change
    const roll = Math.random();
    const protestThreshold = phase === 1 ? 0.95 : phase === 2 ? 0.85 : 0.75;

    if (roll < 0.15) {
      // Move
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
    } else if (roll < 0.25) {
      // Mood shift
      const newMood = pick(MOODS);
      events.push({
        round,
        npc_id: npc.id,
        event_type: "mood_shift",
        message: `Feeling ${newMood} about the situation.`,
        data: { old_mood: npc.mood, new_mood: newMood },
      });
      npc.mood = newMood;
    } else if (roll < protestThreshold) {
      // Chat — pick a nearby NPC as target (within Chebyshev distance 2)
      const nearbyNpcs = getNearbyNpcs(npc, updated, 2);
      if (nearbyNpcs.length > 0) {
        const target = pick(nearbyNpcs);
        const msgs = CHAT_MESSAGES_BY_PHASE[phase];
        events.push({
          round,
          npc_id: npc.id,
          event_type: "chat",
          message: pick(msgs),
          data: { target_npc_id: target.id },
        });

        // Sprinkle in layoff/closure keywords for later phases
        if (phase >= 2 && Math.random() < 0.15) {
          const target2 = pick(nearbyNpcs);
          events.push({
            round,
            npc_id: npc.id,
            event_type: "chat",
            message:
              npc.role === "business_owner"
                ? "I might have to close up shop if this continues."
                : "I heard they're planning layoffs at the factory next week.",
            data: { target_npc_id: target2.id },
          });
        }
      } else {
        // No one nearby — NPC talks to themselves (monologue)
        const msgs = CHAT_MESSAGES_BY_PHASE[phase];
        events.push({
          round,
          npc_id: npc.id,
          event_type: "chat",
          message: pick(msgs),
          data: {}, // No target — monologue
        });
      }
    } else if (roll < protestThreshold + (1 - protestThreshold) * 0.6) {
      // Protest
      events.push({
        round,
        npc_id: npc.id,
        event_type: "protest",
        message: pick(PROTEST_MESSAGES),
        data: {},
      });
    } else {
      // Price change (shopkeepers/business_owners)
      const pctChange =
        phase === 1
          ? randInt(2, 8)
          : phase === 2
            ? randInt(5, 20)
            : randInt(10, 35);
      const direction = Math.random() < 0.8 ? 1 : -1;
      events.push({
        round,
        npc_id: npc.id,
        event_type: "price_change",
        message: pick(PRICE_CHANGE_MESSAGES),
        data: { pct_change: pctChange * direction },
      });
    }
  }

  // Generate influence events from chat events
  const BEHAVIORS: BackendInfluenceEvent["behavior"][] = [
    "keep",
    "compromise",
    "adopt",
  ];
  const influenceEvents: BackendInfluenceEvent[] = events
    .filter((e) => e.event_type === "chat" && e.data.target_npc_id)
    .map((e) => {
      const behavior = pick(BEHAVIORS);
      const influence =
        behavior === "keep"
          ? Math.random() * 0.24
          : behavior === "adopt"
            ? 0.85 + Math.random() * 0.15
            : 0.25 + Math.random() * 0.6;
      return {
        speaker_id: e.npc_id,
        target_id: e.data.target_npc_id as string,
        influence: Math.round(influence * 1000) / 1000,
        behavior,
        political_delta:
          behavior === "keep"
            ? 0
            : Math.round((Math.random() * 0.2 - 0.1) * 1000) / 1000,
        mood_delta:
          behavior === "keep"
            ? 0
            : Math.round((Math.random() * 0.3 - 0.15) * 1000) / 1000,
      };
    });

  return { events, updatedNpcs: updated, influenceEvents };
}

// ── Public API ──────────────────────────────────────────────

export interface MockSimulation {
  initMsg: WSInitMsg;
  rounds: WSRoundMsg[];
}

/**
 * Generate a complete mock simulation: init + rounds of events.
 * Data shapes match the real backend WebSocket messages exactly.
 */
export function generateMockSimulation(maxRounds = 15): MockSimulation {
  _id = 0; // reset for deterministic-ish IDs
  let npcs = generateNPCs();
  const relationships = generateRelationships(npcs);

  const initMsg: WSInitMsg = {
    type: "init",
    npcs: [...npcs],
    relationships,
    max_rounds: maxRounds,
  };

  const rounds: WSRoundMsg[] = [];
  for (let r = 0; r < maxRounds; r++) {
    const { events, updatedNpcs, influenceEvents } = generateRoundEvents(
      npcs,
      relationships,
      r,
      maxRounds,
    );
    npcs = updatedNpcs;
    rounds.push({
      type: "round",
      round: r,
      events,
      npcs: npcs.map((n) => ({ ...n })),
      influence_events: influenceEvents,
      max_rounds: maxRounds,
    });
  }

  return { initMsg, rounds };
}
