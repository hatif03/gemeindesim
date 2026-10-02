"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { adaptEvent, roundToPhase } from "@/lib/adapter";
import {
  createAccumulator,
  type MetricsAccumulator,
  updateMetrics,
} from "@/lib/metricsEngine";
import { generateMockSimulation } from "@/mocks/mockBackend";
import { connectSimulation } from "@/services/wsClient";
import type { SimEvent, SimMetrics } from "@/types";
import type {
  BackendInfluenceEvent,
  BackendNPC,
  BackendRelationship,
  EconomicReport,
  SavedSimulation,
  WSNPCEventsMsg,
  WSRoundMsg,
} from "@/types/backend";

export interface GraphData {
  relationships: BackendRelationship[];
  npcs: BackendNPC[];
  influenceEvents: BackendInfluenceEvent[];
  version: number;
}

export interface SetupProgress {
  stage: "waiting" | "analyzing" | "generating" | "ready";
  npcsReady: number;
  numNpcs: number;
  label: string;
}

const USE_MOCK = process.env.NEXT_PUBLIC_MOCK_BACKEND === "true";

const INITIAL_METRICS: SimMetrics = {
  eggIndex: 1.0,
  priceIndex: 0,
  unemploymentRate: 4.2,
  socialUnrest: 0.05,
  businessSurvival: 0.95,
  govApproval: 0.62,
  interestRate: 5.25,
};

const MOOD_SCORE: Record<string, number> = {
  excited: 1,
  hopeful: 0.7,
  neutral: 0.5,
  worried: 0.3,
  anxious: 0.2,
  angry: 0,
};

function computePhaseLabel(
  phase: number,
  npcs: BackendNPC[],
): { label: string; sentiment: number } {
  if (npcs.length === 0) return { label: `Phase ${phase}`, sentiment: 0.5 };

  const avgScore =
    npcs.reduce((s, n) => s + (MOOD_SCORE[n.mood] ?? 0.5), 0) / npcs.length;

  const outcomes: Record<number, [string, string, string]> = {
    1: [
      "Policy Announced — Initial Optimism",
      "Policy Announced — Mixed Reactions",
      "Policy Announced — Public Concern",
    ],
    2: [
      "Economic Growth Emerging",
      "Economic Ripple Effects",
      "Economic Strain Deepening",
    ],
    3: ["Social Prosperity", "Social Reckoning", "Social Crisis"],
  };

  const [pos, mid, neg] = outcomes[phase] ?? [
    `Phase ${phase}`,
    `Phase ${phase}`,
    `Phase ${phase}`,
  ];
  const label = avgScore >= 0.6 ? pos : avgScore <= 0.35 ? neg : mid;
  return { label, sentiment: avgScore };
}

/** Cap EventFeed to last N events to avoid unbounded React state growth */
const MAX_FEED_EVENTS = 200;

/** Cap history to last N snapshots (one per round). */
const MAX_HISTORY = 30;

interface SimulationState {
  events: SimEvent[];
  metrics: SimMetrics;
  metricsHistory: SimMetrics[];
  phase: number;
  phaseLabel: string;
  round: number;
  maxRounds: number;
  isRunning: boolean;
  isComplete: boolean;
  latestEvent: SimEvent | null;
  error: string | null;
}

// Cache EventBridge module to avoid per-event dynamic import overhead
let bridgePromise: Promise<typeof import("@/game/bridge/EventBridge")> | null =
  null;
function getBridge() {
  if (!bridgePromise) {
    bridgePromise = import("@/game/bridge/EventBridge");
  }
  return bridgePromise;
}

function waitForQueueDrain(
  queueRef: React.RefObject<SimEvent[]>,
  setDone: React.Dispatch<React.SetStateAction<SimulationState>>,
) {
  let checks = 0;
  const tick = () => {
    if (queueRef.current.length === 0 || ++checks > 300) {
      setDone((prev) => ({ ...prev, isRunning: false, isComplete: true }));
    } else {
      setTimeout(tick, 1000);
    }
  };
  tick();
}

export function useSimulation(simulationId?: string, record = false) {
  const [state, setState] = useState<SimulationState>({
    events: [],
    metrics: { ...INITIAL_METRICS },
    metricsHistory: [{ ...INITIAL_METRICS }],
    phase: 0,
    phaseLabel: "",
    round: 0,
    maxRounds: 1,
    isRunning: false,
    isComplete: false,
    latestEvent: null,
    error: null,
  });

  const [setupProgress, setSetupProgress] = useState<SetupProgress>({
    stage: "waiting",
    npcsReady: 0,
    numNpcs: 0,
    label: "",
  });

  const [graphData, setGraphData] = useState<GraphData>({
    relationships: [],
    npcs: [],
    influenceEvents: [],
    version: 0,
  });
  const [report, setReport] = useState<EconomicReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  const cleanupRef = useRef<(() => void) | null>(null);
  const recordingRef = useRef<SavedSimulation | null>(null);
  const npcsStreamedRef = useRef(false);
  const npcLookupRef = useRef<Map<string, BackendNPC>>(new Map());
  const relationshipsRef = useRef<BackendRelationship[]>([]);
  const influenceLogRef = useRef<BackendInfluenceEvent[]>([]);
  const metricsAccRef = useRef<MetricsAccumulator>(createAccumulator());
  const eventQueueRef = useRef<SimEvent[]>([]);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const maxRoundsRef = useRef(15);
  const lastPhaseRef = useRef(0);
  const reportRequestedRef = useRef(false);

  const drainQueue = useCallback(() => {
    const queue = eventQueueRef.current;
    if (queue.length === 0) {
      timerRef.current = null;
      return;
    }

    const event = queue.shift();
    if (!event) return;

    getBridge().then(({ eventBridge }) => {
      if (event.type === "phase_change") {
        const sentiment =
          typeof event.data?.sentiment === "number"
            ? event.data.sentiment
            : undefined;
        eventBridge.emitPhaseChange(event.phase, event.round, sentiment);
      }
      eventBridge.emitSimEvent(event);
    });

    setState((prev) => {
      const events =
        prev.events.length >= MAX_FEED_EVENTS
          ? [...prev.events.slice(-MAX_FEED_EVENTS + 1), event]
          : [...prev.events, event];
      return {
        ...prev,
        events,
        latestEvent: event,
        phase: event.phase > prev.phase ? event.phase : prev.phase,
        phaseLabel:
          event.type === "phase_change" ? event.message : prev.phaseLabel,
        round: event.round > prev.round ? event.round : prev.round,
        maxRounds: event.maxRounds,
      };
    });

    const delay =
      event.type === "phase_change" ? 2000 : 1200 + Math.random() * 600;
    timerRef.current = setTimeout(drainQueue, delay);
  }, []);

  /** Process streamed NPC events that arrive before the full round completes. */
  const processNPCEvents = useCallback((msg: WSNPCEventsMsg) => {
    getBridge().then(({ eventBridge }) => {
      for (const be of msg.events) {
        if (
          be.event_type === "move" &&
          be.data.to_x != null &&
          be.data.to_y != null
        ) {
          eventBridge.emitNPCMove(
            be.npc_id,
            Number(be.data.to_x),
            Number(be.data.to_y),
          );
        }
        if (be.event_type === "mood_shift" && be.data.new_mood) {
          eventBridge.emitNPCMood(be.npc_id, String(be.data.new_mood));
        }
      }
    });
  }, []);

  /** Feed a single WSRoundMsg through the same pipeline as the real backend. */
  const processRound = useCallback(
    (msg: WSRoundMsg) => {
      if (typeof msg.max_rounds === "number" && msg.max_rounds > 0) {
        maxRoundsRef.current = msg.max_rounds;
      }

      const round = msg.round;
      const lookup = npcLookupRef.current;
      for (const npc of msg.npcs) {
        lookup.set(npc.id, npc);
      }

      const { phase } = roundToPhase(round, maxRoundsRef.current);
      if (phase > lastPhaseRef.current) {
        lastPhaseRef.current = phase;
        const npcValues = Array.from(lookup.values());
        const { label, sentiment } = computePhaseLabel(phase, npcValues);
        eventQueueRef.current.push({
          id: `phase-${phase}`,
          type: "phase_change",
          agentId: "system",
          agentName: "System",
          message: label,
          phase,
          round,
          maxRounds: maxRoundsRef.current,
          timestamp: Date.now(),
          data: { sentiment },
        });
      }

      getBridge().then(({ eventBridge }) => {
        for (const be of msg.events) {
          if (
            be.event_type === "move" &&
            be.data.to_x != null &&
            be.data.to_y != null
          ) {
            eventBridge.emitNPCMove(
              be.npc_id,
              Number(be.data.to_x),
              Number(be.data.to_y),
            );
          }
          if (be.event_type === "mood_shift" && be.data.new_mood) {
            eventBridge.emitNPCMood(be.npc_id, String(be.data.new_mood));
          }
        }
      });

      for (const be of msg.events) {
        const adapted = adaptEvent(be, lookup, round, maxRoundsRef.current);
        if (adapted) {
          eventQueueRef.current.push(adapted);
        }
      }

      if (msg.influence_events) {
        influenceLogRef.current = [
          ...influenceLogRef.current,
          ...msg.influence_events,
        ];
      }
      if (msg.relationships) {
        relationshipsRef.current = msg.relationships;
      }
      setGraphData((prev) => ({
        relationships: relationshipsRef.current,
        npcs: Array.from(npcLookupRef.current.values()),
        influenceEvents: msg.influence_events || [],
        version: prev.version + 1,
      }));

      const newMetrics = updateMetrics(
        metricsAccRef.current,
        msg.npcs,
        msg.events,
      );
      setState((prev) => {
        let merged = { ...prev.metrics, ...newMetrics };
        // Override with real backend economic indicators when available
        const ind = msg.economic_indicators;
        if (ind && Object.keys(ind).length > 0) {
          merged = {
            ...merged,
            priceIndex: ind.price_pressure ?? merged.priceIndex,
            socialUnrest:
              (ind.social_unrest_index ?? merged.socialUnrest * 100) / 100,
            govApproval:
              (ind.policy_approval ?? merged.govApproval * 100) / 100,
          };
        }
        return {
          ...prev,
          metrics: merged,
          metricsHistory: [...prev.metricsHistory, merged].slice(-MAX_HISTORY),
          maxRounds: maxRoundsRef.current,
        };
      });

      if (!timerRef.current && eventQueueRef.current.length > 0) {
        timerRef.current = setTimeout(drainQueue, 800);
      }
    },
    [drainQueue],
  );

  const start = useCallback(async () => {
    setState({
      events: [],
      metrics: { ...INITIAL_METRICS },
      metricsHistory: [{ ...INITIAL_METRICS }],
      phase: 0,
      phaseLabel: "",
      round: 0,
      maxRounds: 1,
      isRunning: true,
      isComplete: false,
      latestEvent: null,
      error: null,
    });
    npcLookupRef.current = new Map();
    relationshipsRef.current = [];
    influenceLogRef.current = [];
    metricsAccRef.current = createAccumulator();
    eventQueueRef.current = [];
    lastPhaseRef.current = 0;
    setGraphData({
      relationships: [],
      npcs: [],
      influenceEvents: [],
      version: 0,
    });
    setSetupProgress({ stage: "waiting", npcsReady: 0, numNpcs: 0, label: "" });
    setReport(null);
    setReportLoading(false);
    setReportError(null);
    reportRequestedRef.current = false;

    // ── Mock backend path ──────────────────────────────────
    if (USE_MOCK) {
      const mock = generateMockSimulation(maxRoundsRef.current);
      if (record) {
        recordingRef.current = {
          version: 1,
          savedAt: new Date().toISOString(),
          maxRounds: maxRoundsRef.current,
          initMsg: mock.initMsg,
          rounds: mock.rounds,
        };
      }
      const lookup = npcLookupRef.current;
      for (const npc of mock.initMsg.npcs) lookup.set(npc.id, npc);
      relationshipsRef.current = mock.initMsg.relationships;
      setGraphData((prev) => ({
        ...prev,
        relationships: mock.initMsg.relationships,
        npcs: mock.initMsg.npcs,
        version: prev.version + 1,
      }));
      getBridge().then(({ eventBridge }) => {
        eventBridge.emitInitNPCs(mock.initMsg.npcs);
      });
      setSetupProgress({ stage: "ready", npcsReady: mock.initMsg.npcs.length, numNpcs: mock.initMsg.npcs.length, label: "Loading world..." });
      let i = 0;
      const feedNext = () => {
        if (i >= mock.rounds.length) {
          waitForQueueDrain(eventQueueRef, setState);
          return;
        }
        processRound(mock.rounds[i++]);
        const t = setTimeout(feedNext, 150 + Math.random() * 100);
        cleanupRef.current = () => clearTimeout(t);
      };
      feedNext();
      return;
    }

    // ── Real backend path ──────────────────────────────────
    const simId = simulationId || "";
    if (!simId) {
      console.warn("[sim] no simulation ID — aborting");
      setState((prev) => ({ ...prev, isRunning: false }));
      return;
    }

    if (record) {
      recordingRef.current = {
        version: 1,
        savedAt: new Date().toISOString(),
        maxRounds: maxRoundsRef.current,
        initMsg: { type: "init", npcs: [], relationships: [] },
        rounds: [],
      };
    }

    npcsStreamedRef.current = false;
    getBridge().then(({ eventBridge }) => eventBridge.emitResetNPCs());

    console.log("[sim] start() called — connecting WS for sim=%s", simId);

    try {
      const cleanup = connectSimulation(simId, {
        onPolicyAnalysis: (msg) => {
          console.log(
            "[sim] policy_analysis received — %d entities",
            msg.entities?.length ?? 0,
          );
          setSetupProgress(p => ({ ...p, stage: "analyzing", label: "Analyzing policy..." }));
        },

        onSetupProgress: (msg) => {
          setSetupProgress(p => ({ ...p, label: msg.label }));
        },

        onNPCAdded: (msg) => {
          const npc = msg.npc;
          npcLookupRef.current.set(npc.id, npc);
          npcsStreamedRef.current = true;
          getBridge().then(({ eventBridge }) => eventBridge.emitAddNPC(npc));
          setSetupProgress(p => ({
            stage: "generating",
            npcsReady: p.npcsReady + 1,
            numNpcs: p.numNpcs,
            label: `Generating personalities... ${p.npcsReady + 1}${p.numNpcs > 0 ? `/${p.numNpcs}` : ""}`,
          }));
        },

        onInit: (msg) => {
          setSetupProgress({ stage: "ready", npcsReady: msg.npcs.length, numNpcs: msg.npcs.length, label: "Loading world..." });
          console.log(
            "[sim] init received — %d NPCs, %d relationships",
            msg.npcs.length,
            msg.relationships.length,
          );
          const initMaxRounds =
            typeof msg.max_rounds === "number" && msg.max_rounds > 0
              ? msg.max_rounds
              : null;
          if (initMaxRounds !== null) {
            maxRoundsRef.current = initMaxRounds;
            setState((prev) => ({ ...prev, maxRounds: initMaxRounds }));
          }
          if (recordingRef.current) {
            recordingRef.current.initMsg = msg;
            if (initMaxRounds !== null) {
              recordingRef.current.maxRounds = initMaxRounds;
            }
          }
          const lookup = npcLookupRef.current;
          for (const npc of msg.npcs) {
            lookup.set(npc.id, npc);
          }
          relationshipsRef.current = msg.relationships;
          setGraphData((prev) => ({
            ...prev,
            relationships: msg.relationships,
            npcs: msg.npcs,
            version: prev.version + 1,
          }));

          if (!npcsStreamedRef.current) {
            getBridge().then(({ eventBridge }) => {
              eventBridge.emitInitNPCs(msg.npcs);
            });
          }
        },

        onRound: (msg: WSRoundMsg) => {
          console.log(
            "[sim] round %d — %d events, %d NPCs",
            msg.round,
            msg.events.length,
            msg.npcs.length,
          );
          if (recordingRef.current) {
            recordingRef.current.rounds.push(msg);
            recordingRef.current.maxRounds =
              typeof msg.max_rounds === "number" && msg.max_rounds > 0
                ? msg.max_rounds
                : Math.max(recordingRef.current.maxRounds, msg.round + 1);
          }
          processRound(msg);
        },

        onNPCEvents: (msg) => {
          processNPCEvents(msg);
        },

        onDone: () => {
          console.log(
            "[sim] done — draining event queue (%d remaining)",
            eventQueueRef.current.length,
          );
          waitForQueueDrain(eventQueueRef, setState);
        },

        onEconomicReport: (report) => {
          console.log("[sim] economic_report received");
          setReport(report);
          setReportLoading(false);
          setReportError(null);
          reportRequestedRef.current = true;
        },

        onError: (message) => {
          console.error("[sim] error:", message);
          setState((prev) => ({ ...prev, isRunning: false, error: message }));
        },
      });

      cleanupRef.current = cleanup;
    } catch (err) {
      console.error("Failed to start simulation:", err);
      setState((prev) => ({
        ...prev,
        isRunning: false,
        error: err instanceof Error ? err.message : "Connection failed",
      }));
    }
  }, [simulationId, record, processRound, processNPCEvents]);

  const startFromRecording = useCallback(
    (recording: SavedSimulation) => {
      setState({
        events: [],
        metrics: { ...INITIAL_METRICS },
        metricsHistory: [{ ...INITIAL_METRICS }],
        phase: 0,
        phaseLabel: "",
        round: 0,
        maxRounds: 1,
        isRunning: true,
        isComplete: false,
        latestEvent: null,
        error: null,
      });
      npcLookupRef.current = new Map();
      relationshipsRef.current = [];
      influenceLogRef.current = [];
      metricsAccRef.current = createAccumulator();
      eventQueueRef.current = [];
      lastPhaseRef.current = 0;
      setGraphData({
        relationships: [],
        npcs: [],
        influenceEvents: [],
        version: 0,
      });
      setSetupProgress({ stage: "waiting", npcsReady: 0, numNpcs: 0, label: "" });
      setReport(null);
      setReportLoading(false);
      setReportError(null);
      reportRequestedRef.current = false;

      maxRoundsRef.current = recording.maxRounds || recording.rounds.length;
      const lookup = npcLookupRef.current;
      for (const npc of recording.initMsg.npcs) lookup.set(npc.id, npc);
      relationshipsRef.current = recording.initMsg.relationships;
      setGraphData((prev) => ({
        ...prev,
        relationships: recording.initMsg.relationships,
        npcs: recording.initMsg.npcs,
        version: prev.version + 1,
      }));
      getBridge().then(({ eventBridge }) => {
        eventBridge.emitInitNPCs(recording.initMsg.npcs);
      });
      setSetupProgress({ stage: "ready", npcsReady: recording.initMsg.npcs.length, numNpcs: recording.initMsg.npcs.length, label: "Loading world..." });

      let i = 0;
      const feedNext = () => {
        if (i >= recording.rounds.length) {
          waitForQueueDrain(eventQueueRef, setState);
          return;
        }
        processRound(recording.rounds[i++]);
        const t = setTimeout(feedNext, 150 + Math.random() * 100);
        cleanupRef.current = () => clearTimeout(t);
      };
      feedNext();
    },
    [processRound],
  );

  const getRecording = useCallback(() => recordingRef.current, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      cleanupRef.current?.();
    };
  }, []);

  // Economic report is now delivered via the "economic_report" Socket.IO event
  // (handled in onEconomicReport callback above). No HTTP fetch needed.

  const getNpc = useCallback((id: string) => npcLookupRef.current.get(id), []);

  return {
    ...state,
    start,
    startFromRecording,
    getRecording,
    graphData,
    getNpc,
    report,
    reportLoading,
    reportError,
    setupProgress,
  };
}
