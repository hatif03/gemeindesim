"use client";

import {
  type Edge,
  type Node,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import { useCallback, useMemo, useState } from "react";
import "@xyflow/react/dist/style.css";
import { useRouter } from "next/navigation";
import { type MapType, setSelectedMap } from "@/game/constants";
import { setReplayData } from "@/lib/replayStore";
import { startEnsemble, startSimulation, uploadContextSource } from "@/services/wsClient";
import type { SavedSimulation, UploadedContextSource } from "@/types/backend";
import { MIN_NOTES_CHARS_FOR_TEXT_ONLY } from "@/types/backend";
import ConfigNode from "./ConfigNode";
import { FormContext } from "./FormContext";
import PolicyNode from "./PolicyNode";
import RunNode from "./RunNode";

function isSavedSimulation(data: unknown): data is SavedSimulation {
  if (!data || typeof data !== "object") return false;
  const candidate = data as Partial<SavedSimulation>;
  return (
    candidate.initMsg?.type === "init" &&
    Array.isArray(candidate.initMsg.npcs) &&
    Array.isArray(candidate.rounds)
  );
}

const nodeTypes = {
  policyNode: PolicyNode,
  configNode: ConfigNode,
  runNode: RunNode,
};

/**
 * Horizontal layout: `width` / `height` match real DOM so the first `fitView` centers
 * correctly before ResizeObserver runs. `NODE_GAP` keeps edge paths in clear space.
 */
const NODE_GAP = 88;
/** 704 content + p-3 (24) + border (6) + shadow (~12) */
const POLICY_NODE_W = 750;
const POLICY_NODE_H = 792;
const CONFIG_NODE_W = 574;
const CONFIG_NODE_H = 616;
const RUN_NODE_W = 486;
const RUN_NODE_H = 550;

const initialNodes: Node[] = [
  {
    id: "policy",
    type: "policyNode",
    position: { x: 0, y: 0 },
    width: POLICY_NODE_W,
    height: POLICY_NODE_H,
    data: {},
  },
  {
    id: "config",
    type: "configNode",
    position: { x: POLICY_NODE_W + NODE_GAP, y: 0 },
    width: CONFIG_NODE_W,
    height: CONFIG_NODE_H,
    data: {},
  },
  {
    id: "run",
    type: "runNode",
    position: {
      x: POLICY_NODE_W + NODE_GAP + CONFIG_NODE_W + NODE_GAP,
      y: 0,
    },
    width: RUN_NODE_W,
    height: RUN_NODE_H,
    data: {},
  },
];

const edgeStyle = {
  stroke: "#C97D1A",
  strokeWidth: 3.5,
};

const initialEdges: Edge[] = [
  {
    id: "e1-2",
    source: "policy",
    target: "config",
    type: "smoothstep",
    style: edgeStyle,
    animated: true,
  },
  {
    id: "e2-3",
    source: "config",
    target: "run",
    type: "smoothstep",
    style: edgeStyle,
    animated: true,
  },
];

interface NodeCanvasProps {
  onSimulateStart?: () => void;
}

const FIT_MIN_ZOOM = 0.35;
const FIT_MAX_ZOOM = 1;

export default function NodeCanvas({ onSimulateStart }: NodeCanvasProps) {
  const router = useRouter();
  const [notesText, setNotesText] = useState("");
  const [numNpcs, setNumNpcs] = useState(5);
  const [numRounds, setNumRounds] = useState(3);
  const [objective, setObjective] = useState("");
  const mapId: MapType = "citypack";
  const setMapId = useCallback((_: MapType) => {}, []);
  const [uploadingPolicySources, setUploadingPolicySources] = useState(false);
  const [uploadingTrends, setUploadingTrends] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [policySources, setPolicySources] = useState<UploadedContextSource[]>(
    [],
  );
  const [trendSources, setTrendSources] = useState<UploadedContextSource[]>([]);
  const [record, setRecord] = useState(false);
  const [loadingCustomRun, setLoadingCustomRun] = useState(false);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handlePolicyNarrativeFiles = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      if (!files.length) return;
      setUploadingPolicySources(true);
      try {
        const uploaded = await Promise.all(
          files.map((file) => uploadContextSource(file, file.name)),
        );
        const narratives = uploaded.filter((u) => u.kind !== "csv");
        if (narratives.length < uploaded.length) {
          alert(
            "CSV files belong in Trend data — they were skipped here. Use the + Trend CSV control.",
          );
        }
        if (narratives.length) {
          setPolicySources((prev) => [...prev, ...narratives]);
        }
      } catch {
        alert("Could not upload one or more policy files.");
      } finally {
        setUploadingPolicySources(false);
        e.target.value = "";
      }
    },
    [],
  );

  const removePolicySource = useCallback((sourceId: string) => {
    setPolicySources((prev) => prev.filter((s) => s.id !== sourceId));
  }, []);

  const handleTrendFiles = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      if (!files.length) return;

      setUploadingTrends(true);
      try {
        const uploaded = await Promise.all(
          files.map((file) => uploadContextSource(file, file.name)),
        );
        setTrendSources((prev) => [...prev, ...uploaded]);
      } catch {
        alert("Could not upload one or more CSV trend files.");
      } finally {
        setUploadingTrends(false);
        e.target.value = "";
      }
    },
    [],
  );

  const removeTrendSource = useCallback((sourceId: string) => {
    setTrendSources((prev) => prev.filter((source) => source.id !== sourceId));
  }, []);

  const handleSpread = useCallback(async () => {
    const notesOk = notesText.trim().length >= MIN_NOTES_CHARS_FOR_TEXT_ONLY;
    if ((policySources.length === 0 && !notesOk) || isSimulating) return;
    setIsSimulating(true);
    try {
      const id = await startEnsemble(
        {
          policy_source_ids: policySources.map((s) => s.id),
          primary_policy_source_id: null,
          notes_text: notesText,
          trend_source_ids: trendSources.map((source) => source.id),
          num_rounds: numRounds,
          num_npcs: numNpcs,
          objective,
          map_id: mapId,
        },
        5,
      );
      router.push(`/spread?id=${id}`);
    } catch (err) {
      console.error("Failed to start the spread run:", err);
      alert(`Failed to start the spread run: ${err instanceof Error ? err.message : err}`);
      setIsSimulating(false);
    }
  }, [policySources, notesText, trendSources, numNpcs, numRounds, objective, mapId, router, isSimulating]);

  const handleSimulate = useCallback(async () => {
    const notesOk = notesText.trim().length >= MIN_NOTES_CHARS_FOR_TEXT_ONLY;
    const hasNarrativeFiles = policySources.length > 0;
    if (
      (!hasNarrativeFiles && !notesOk) ||
      isSimulating ||
      uploadingPolicySources ||
      uploadingTrends
    )
      return;

    onSimulateStart?.();
    setIsSimulating(true);
    setSelectedMap(mapId);

    const recordParam = record ? "&record=true" : "";

    try {
      const simId = await startSimulation({
        policy_source_ids: policySources.map((s) => s.id),
        primary_policy_source_id: null,
        notes_text: notesText,
        trend_source_ids: trendSources.map((source) => source.id),
        num_rounds: numRounds,
        num_npcs: numNpcs,
        objective,
        map_id: mapId,
      });

      router.push(`/simulate?id=${simId}${recordParam}`);
    } catch (err) {
      console.error("Failed to start simulation:", err);
      alert("Failed to start simulation. Is the backend running?");
      setIsSimulating(false);
    }
  }, [
    policySources,
    notesText,
    trendSources,
    numNpcs,
    numRounds,
    objective,
    record,
    router,
    isSimulating,
    uploadingPolicySources,
    uploadingTrends,
    onSimulateStart,
  ]);

  const handleLoadCustomRun = useCallback(async () => {
    if (loadingCustomRun) return;
    setLoadingCustomRun(true);
    try {
      const res = await fetch("/example-replay.json");
      const bundledReplay = (await res.json()) as unknown;
      if (!isSavedSimulation(bundledReplay)) {
        console.error("Bundled custom run is invalid");
        setLoadingCustomRun(false);
        return;
      }
      setReplayData(bundledReplay);
      router.push("/simulate?mode=replay&map=citypack");
    } catch (err) {
      console.error("Failed to load bundled custom run:", err);
      setLoadingCustomRun(false);
    }
  }, [loadingCustomRun, router]);

  const handleLoadFile = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const parsed = JSON.parse(reader.result as string) as SavedSimulation;
          if (!isSavedSimulation(parsed)) {
            console.error("Invalid simulation file: missing initMsg or rounds");
            return;
          }
          setReplayData(parsed);
          router.push(`/simulate?mode=replay&map=${mapId}`);
        } catch (err) {
          console.error("Failed to parse simulation file:", err);
        }
      };
      reader.readAsText(file);
      e.target.value = "";
    },
    [router],
  );

  const formValue = useMemo(
    () => ({
      notesText,
      setNotesText,
      numNpcs,
      setNumNpcs,
      numRounds,
      setNumRounds,
      objective,
      setObjective,
      mapId,
      setMapId,
      policySources,
      trendSources,
      uploadingPolicySources,
      uploadingTrends,
      isSimulating,
      record,
      setRecord,
      handlePolicyNarrativeFiles,
      removePolicySource,
      handleTrendFiles,
      removeTrendSource,
      handleSimulate,
      handleSpread,
      handleLoadCustomRun,
      handleLoadFile,
      loadingCustomRun,
    }),
    [
      notesText,
      numNpcs,
      numRounds,
      objective,
      policySources,
      trendSources,
      uploadingPolicySources,
      uploadingTrends,
      isSimulating,
      record,
      handlePolicyNarrativeFiles,
      removePolicySource,
      handleTrendFiles,
      removeTrendSource,
      handleSimulate,
      handleSpread,
      handleLoadCustomRun,
      handleLoadFile,
      loadingCustomRun,
      setMapId,
    ],
  );

  return (
    <FormContext.Provider value={formValue}>
      <style>{`
        .node-canvas-flow, .node-canvas-flow .react-flow__pane, .node-canvas-flow .react-flow__renderer, .node-canvas-flow .react-flow__background { background: transparent !important; }
        .node-canvas-flow .react-flow__edge-path {
          stroke-linecap: round;
          stroke-linejoin: round;
          filter: drop-shadow(0 1px 2px rgba(45, 28, 12, 0.45));
        }
        .node-canvas-flow .react-flow__edge.animated path { animation-duration: 1.35s; }
        .node-canvas-flow .react-flow__edges { z-index: 2; }
        .node-canvas-flow .react-flow__nodes { z-index: 3; }
      `}</style>
      <ReactFlow
        className="node-canvas-flow"
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        proOptions={{ hideAttribution: true }}
        fitView
        fitViewOptions={{
          padding: 0.1,
          maxZoom: FIT_MAX_ZOOM,
          minZoom: FIT_MIN_ZOOM,
        }}
        nodesDraggable
        nodesConnectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        minZoom={FIT_MIN_ZOOM}
        maxZoom={1}
        selectNodesOnDrag={false}
      />

    </FormContext.Provider>
  );
}
