// Socket.IO client for communicating with the FastAPI backend

import { io, type Socket } from "socket.io-client";
import type {
  BackendSimEvent,
  EconomicReport,
  StartSimulationRequest,
  UploadedContextSource,
  WSInitMsg,
  WSNPCAddedMsg,
  WSNPCEventsMsg,
  WSPolicyAnalysisMsg,
  WSRoundMsg,
  WSSetupProgressMsg,
} from "@/types/backend";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface WSCallbacks {
  onPolicyAnalysis: (msg: WSPolicyAnalysisMsg) => void;
  onNPCAdded?: (msg: WSNPCAddedMsg) => void;
  onSetupProgress?: (msg: WSSetupProgressMsg) => void;
  onInit: (msg: WSInitMsg) => void;
  onRound: (msg: WSRoundMsg) => void;
  onNPCEvents?: (msg: WSNPCEventsMsg) => void;
  onDone: () => void;
  onEconomicReport?: (report: EconomicReport) => void;
  onError: (message: string) => void;
}

/**
 * POST to /simulate to create a new simulation, returns the simulation_id.
 */
export async function uploadContextSource(
  file: File,
  label?: string,
): Promise<UploadedContextSource> {
  const form = new FormData();
  form.append("file", file);
  if (label) form.append("label", label);
  const res = await fetch(`${API_BASE}/context/sources`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return (await res.json()) as UploadedContextSource;
}

export async function extractFile(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/extract`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Extraction failed: ${res.status}`);
  const data = await res.json();
  return data.text as string;
}

export async function fetchEconomicReport(
  simulationId: string,
): Promise<EconomicReport> {
  const res = await fetch(
    `${API_BASE}/simulate/${simulationId}/economic-report`,
  );
  if (!res.ok) {
    throw new Error(`Economic report failed: ${res.status}`);
  }
  return (await res.json()) as EconomicReport;
}

export async function startSimulation(
  request: StartSimulationRequest,
): Promise<string>;
export async function startSimulation(
  policyText: string,
  numRounds?: number,
  numNpcs?: number,
  objective?: string,
  mapId?: string,
): Promise<string>;
export async function startSimulation(
  requestOrText: StartSimulationRequest | string,
  numRounds?: number,
  numNpcs?: number,
  objective?: string,
  mapId?: string,
): Promise<string> {
  if (typeof requestOrText === "string") {
    throw new Error(
      "Pass a StartSimulationRequest object (upload files and/or use notes_text).",
    );
  }

  const res = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      primary_policy_source_id:
        requestOrText.primary_policy_source_id ?? null,
      policy_source_ids: requestOrText.policy_source_ids ?? [],
      notes_text: requestOrText.notes_text ?? "",
      trend_source_ids: requestOrText.trend_source_ids ?? [],
      num_rounds: requestOrText.num_rounds ?? numRounds ?? 75,
      num_npcs: requestOrText.num_npcs ?? numNpcs ?? 25,
      objective: requestOrText.objective ?? objective ?? "",
      map_id: requestOrText.map_id ?? mapId ?? "citypack",
      situation_kind: requestOrText.situation_kind ?? "policy",
    }),
  });

  if (!res.ok) {
    throw new Error(`Failed to start simulation: ${res.status}`);
  }

  const data = await res.json();
  return data.simulation_id;
}

/**
 * Connect via Socket.IO and start streaming simulation events.
 * Returns a cleanup function that disconnects the socket.
 */
export function connectSimulation(
  simulationId: string,
  callbacks: WSCallbacks,
): () => void {
  const socket: Socket = io(API_BASE, {
    transports: ["websocket"],
    reconnection: true,
    reconnectionAttempts: 3,
    reconnectionDelay: 1000,
  });

  socket.on("connect", () => {
    socket.emit("start_sim", { simulation_id: simulationId });
  });

  socket.on("policy_analysis", (data: WSPolicyAnalysisMsg) => {
    callbacks.onPolicyAnalysis(data);
  });

  socket.on("npc_added", (data: WSNPCAddedMsg) => {
    callbacks.onNPCAdded?.(data);
  });

  socket.on("setup_progress", (data: WSSetupProgressMsg) => {
    callbacks.onSetupProgress?.(data);
  });

  socket.on("init", (data: WSInitMsg) => {
    callbacks.onInit(data);
  });

  socket.on("round", (data: WSRoundMsg) => {
    callbacks.onRound(data);
  });

  socket.on("npc_events", (data: WSNPCEventsMsg) => {
    callbacks.onNPCEvents?.(data);
  });

  socket.on("done", () => {
    callbacks.onDone();
  });

  socket.on("economic_report", (data: EconomicReport) => {
    callbacks.onEconomicReport?.(data);
  });

  socket.on("sim_error", (data: { message: string }) => {
    callbacks.onError(data.message);
  });

  socket.on("connect_error", (err: Error) => {
    callbacks.onError(`Connection error: ${err.message}`);
  });

  socket.on("disconnect", (reason: string) => {
    if (reason !== "io client disconnect") {
      callbacks.onError(`Disconnected: ${reason}`);
    }
  });

  return () => {
    socket.disconnect();
  };
}
