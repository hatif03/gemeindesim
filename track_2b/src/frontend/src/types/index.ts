// Shared types for GemeindeSim frontend

export type SimEventType =
  | "chat"
  | "move"
  | "reaction"
  | "price_change"
  | "layoff"
  | "protest"
  | "closure"
  | "strike"
  | "policy_response"
  | "phase_change"
  | "mood_shift";

export interface SimEvent {
  id: string;
  type: SimEventType;
  agentId: string;
  agentName: string;
  agentCategory?: string;
  message: string;
  phase: number; // 1-3
  round: number; // 0-N
  maxRounds: number; // Total rounds
  metrics?: Partial<SimMetrics>;
  timestamp: number;
  /** Target NPC ID for chat events (who the speaker is addressing) */
  targetNpcId?: string;
  grounded?: boolean;
  usedSourceIds?: string[];
  /** Arbitrary event-specific data (e.g. sentiment score for phase_change) */
  data?: Record<string, unknown>;
}

export interface SimMetrics {
  eggIndex: number; // Joke metric: price of eggs (multiplier)
  priceIndex: number; // % change from baseline
  unemploymentRate: number; // %
  socialUnrest: number; // 0-1
  businessSurvival: number; // 0-1
  govApproval: number; // 0-1
  interestRate: number; // %
}

export interface NPCState {
  id: string;
  name: string;
  profession?: string;
  role?: string;
  category?: string;
  reputation?: number;
  x: number;
  y: number;
  direction: "up" | "down" | "left" | "right";
  state: "idle" | "walking" | "protesting";
  message?: string;
}

export interface NPCHoverInfo {
  id: string;
  name: string;
  profession: string;
  role?: string;
  reputation: number;
  x: number;
  y: number;
  sentiment: "happy" | "neutral" | "worried" | "angry";
  state: NPCState["state"];
}

export interface BuildingPositions {
  government: { x: number; y: number };
  shops: { id: string; x: number; y: number }[];
  factories: { id: string; x: number; y: number }[];
  houses: { id: string; x: number; y: number }[];
}
