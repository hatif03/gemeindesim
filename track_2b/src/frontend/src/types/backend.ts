// TypeScript interfaces mirroring backend Pydantic models

export type BackendRole =
  | "worker"
  | "business_owner"
  | "politician"
  | "student"
  | "retiree"
  | "activist"
  | "farmer"
  | "shopkeeper"
  | "driver"
  | "teacher"
  | "municipal_employee"
  | "tenant";

export type BackendMood =
  | "angry"
  | "anxious"
  | "worried"
  | "neutral"
  | "hopeful"
  | "excited";

export type BackendEventType =
  | "chat"
  | "move"
  | "protest"
  | "price_change"
  | "mood_shift";

export type BackendRelType =
  | "friend"
  | "family"
  | "employer"
  | "neighbor"
  | "colleague";

export interface BackendNPC {
  id: string;
  name: string;
  category?: string;
  gender: string;
  bio: string;
  persona: string;
  mbti: string;
  country: string;
  profession: string;
  role: BackendRole;
  industry?: string;
  interested_topics: string[];
  income_level: "low" | "medium" | "high";
  political_leaning: number; // -1 to 1
  reputation: number; // 0-1
  beliefs: string[];
  controversial_ideas: string[];
  x: number; // 0..19
  y: number; // 0..14
  lang?: "de" | "fr" | "en";
  life_story?: string;
  expert_reflection?: string;
  mood: BackendMood;
  /** Code-owned stance on the question: -1 (against) .. +1 (for). Present in v2 backends. */
  stance?: number;
  stance_reason?: string;
  impact?: "benefit" | "harm" | "mixed" | "none" | "";
  // Internal state from generative agents architecture (populated after round 1+)
  perception?: string;
  current_plan?: string;
}

export interface BackendSimEvent {
  round: number;
  npc_id: string;
  event_type: BackendEventType;
  message: string;
  data: Record<string, unknown>;
}

export interface BackendRelationship {
  source_id: string;
  target_id: string;
  rel_type?: BackendRelType;
  strength?: number; // 0-1
  affinity: number; // -1 to 1
  trust: number; // 0-1
}

export interface StakeholderInfo {
  name: string;
  type: "individual" | "group" | "institution";
  impact: string;
}

export interface EconomicImpact {
  description: string;
  direction: "positive" | "negative";
  magnitude: "low" | "medium" | "high";
  timeframe: "immediate" | "short-term" | "long-term";
}

export interface IndicatorSnapshot {
  metric: string;
  latest_value: number;
  previous_value?: number | null;
  change?: number | null;
  trend: "up" | "down" | "flat" | "unknown";
  latest_period?: string | null;
  source_id: string;
  unit?: string | null;
}

export type ContextSourceKind = "pdf" | "csv" | "text" | "book" | "video";

export interface UploadedContextSource {
  id: string;
  kind: ContextSourceKind;
  filename: string;
  label: string;
  status: "ready";
  preview_text: string;
  summary: string;
  metadata: {
    row_count?: number;
    columns?: string[];
    period_column?: string;
    indicator_snapshots?: IndicatorSnapshot[];
    page_count_estimate?: number;
  };
}

/** Minimum length for notes-only runs (must match backend PolicyInput validator). */
export const MIN_NOTES_CHARS_FOR_TEXT_ONLY = 40;

export interface StartSimulationRequest {
  primary_policy_source_id?: string | null;
  policy_source_ids?: string[];
  notes_text?: string;
  trend_source_ids?: string[];
  num_rounds?: number;
  num_npcs?: number;
  objective?: string;
  map_id?: string;
  situation_kind?: "policy" | "vote" | "budget";
}

export interface BackendPolicyAnalysis {
  sectors: string[];
  stakeholders: StakeholderInfo[];
  economic_impacts: EconomicImpact[];
  controversy_level: "low" | "medium" | "high";
}

// Discriminated union for all WebSocket message types

export interface WSPolicyAnalysisMsg {
  type: "policy_analysis";
  entities: BackendPolicyAnalysis[];
}

export interface WSInitMsg {
  type: "init";
  npcs: BackendNPC[];
  relationships: BackendRelationship[];
  max_rounds?: number;
}

export interface BackendInfluenceEvent {
  speaker_id: string;
  target_id: string;
  influence: number;
  behavior: "keep" | "compromise" | "adopt";
  political_delta: number;
  mood_delta: number;
}

/** Token, cache, latency and context accounting of the run (backend `graph/metrics.py`). */
export interface RunMetrics {
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  cached_tokens: number;
  cache_hit_rate: number;
  mean_prompt_tokens: number;
  max_prompt_tokens: number;
  context_window: number;
  mean_context_use: number;
  max_context_use: number;
  mean_latency_s: number;
  p95_latency_s: number;
  decode_tokens_per_s: number;
  elapsed_s: number;
  rate_limited: number;
  gateway_retries: number;
  downgraded: number;
  failed: number;
  models: Record<string, number>;
  model: string;
  endpoint: string;
  in_flight_limit: number | null;
}

export interface WSRoundMsg {
  type: "round";
  round: number;
  events: BackendSimEvent[];
  npcs: BackendNPC[];
  influence_events?: BackendInfluenceEvent[];
  economic_indicators?: Record<string, number>;
  relationships?: BackendRelationship[];
  max_rounds?: number;
  metrics?: RunMetrics;
}

export interface WSNPCAddedMsg {
  type: "npc_added";
  npc: BackendNPC;
}

export interface WSSetupProgressMsg {
  type: "setup_progress";
  label: string;
  current: number;
  total: number;
}

export interface WSNPCEventsMsg {
  type: "npc_events";
  events: BackendSimEvent[];
}

export interface WSDoneMsg {
  type: "done";
}

export interface WSErrorMsg {
  type: "error";
  message: string;
}

export interface ReportImpact {
  title: string;
  description: string;
  direction: "positive" | "negative" | "mixed";
  severity: "low" | "medium" | "high";
}

export interface ReportStat {
  label: string;
  value: string;
  trend?: "up" | "down" | "flat" | "mixed" | null;
}

export interface PieChartSlice {
  label: string;
  value: number;
}

export interface BarChartEntry {
  label: string;
  value: number;
}

export interface EconomicReport {
  headline: string;
  summary: string;
  livelihood_impact: string;
  top_impacts: ReportImpact[];
  key_stats: ReportStat[];
  pie_chart: {
    title: string;
    slices: PieChartSlice[];
  };
  bar_chart: {
    title: string;
    bars: BarChartEntry[];
  };
  notable_events: string[];
  /** Stance tallies computed in code at the start and end of the run (v2 backends). */
  stance_summary?: {
    initial?: StanceTally | null;
    final?: StanceTally | null;
  } | null;
}

export interface StanceTally {
  for: number;
  against: number;
  undecided: number;
  mean: number;
  spread: number;
  entropy_bits: number;
  n: number;
}

export interface BackendSource {
  id: string;
  text: string;
}

export type WSMessage =
  | WSPolicyAnalysisMsg
  | WSInitMsg
  | WSRoundMsg
  | WSNPCEventsMsg
  | WSDoneMsg
  | WSErrorMsg
  | WSSetupProgressMsg;

export interface SavedSimulation {
  version: 1;
  savedAt: string;
  policyText?: string;
  maxRounds: number;
  initMsg: WSInitMsg;
  rounds: WSRoundMsg[];
  /** Added when the run finished and the report arrived (older saves have none). */
  report?: EconomicReport;
}
