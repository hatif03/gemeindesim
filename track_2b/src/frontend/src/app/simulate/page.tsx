"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "motion/react";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Dashboard } from "@/components/Dashboard";
import { StancePanel } from "@/components/StancePanel";
import { stancePoll } from "@/lib/stance";
import { EconomicReportModal } from "@/components/EconomicReportModal";
import { EventFeed } from "@/components/EventFeed";
import { NPCInteractionModal } from "@/components/NPCInteractionModal";
import { SimLoadingScreen } from "@/components/SimLoadingScreen";
import { useSimulation } from "@/hooks/useSimulation";
import { clearReplayData, getReplayData } from "@/lib/replayStore";
import type { NPCHoverInfo, SimEvent } from "@/types";

const SocialGraph = dynamic(
  () =>
    import("@/components/SocialGraph").then((m) => ({
      default: m.SocialGraph,
    })),
  {
    ssr: false,
    loading: () => (
      <div
        className="flex h-full items-center justify-center text-[8px] font-pixel uppercase tracking-widest"
        style={{ color: "#A0824A" }}
      >
        Loading graph...
      </div>
    ),
  },
);

// Mirror game/constants values here to avoid importing Phaser during SSR.
// game/config.ts imports Phaser at top level which requires `window`.
const GAME_WIDTH = 1280;
const GAME_HEIGHT = 960;
const SCALE_FACTOR = 1; // must match constants.ts — 1:1, Phaser Scale.FIT handles display

// Phaser requires browser APIs — must be client-only
const GameCanvas = dynamic(
  () =>
    import("@/components/GameCanvas").then((m) => ({ default: m.GameCanvas })),
  { ssr: false, loading: () => <GameCanvasPlaceholder /> },
);

function GameCanvasPlaceholder() {
  return (
    <div
      className="rpg-panel flex items-center justify-center box-border w-full h-full"
      style={{ background: "#E8D5A3" }}
    >
      <span
        className="text-[8px] font-pixel uppercase tracking-widest animate-pulse"
        style={{ color: "#A0824A" }}
      >
        Loading world...
      </span>
    </div>
  );
}

const SENTIMENT_LABEL: Record<
  NPCHoverInfo["sentiment"],
  { symbol: string; color: string }
> = {
  happy: { symbol: "+", color: "#3E7C34" },
  neutral: { symbol: "~", color: "#8B7355" },
  worried: { symbol: "?", color: "#C97D1A" },
  angry: { symbol: "!", color: "#B83A52" },
};

interface OverlayMetrics {
  offsetX: number;
  offsetY: number;
  width: number;
  height: number;
  scaleX: number;
  scaleY: number;
}

function NPCTooltip({
  info,
  scaleX,
  scaleY,
}: {
  info: NPCHoverInfo;
  scaleX: number;
  scaleY: number;
}) {
  const sent = SENTIMENT_LABEL[info.sentiment];
  return (
    <div
      className="pointer-events-none absolute z-50"
      style={{
        left: info.x * scaleX + 16,
        top: info.y * scaleY - 4,
      }}
    >
      <div
        className="px-2 py-1"
        style={{
          background: "#FDF5E6",
          border: "2px solid #A0824A",
          borderRadius: "0px",
          boxShadow: "2px 2px 0 rgba(61,37,16,0.5)",
        }}
      >
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-pixel" style={{ color: "#5B3A1E" }}>
            {info.name}
          </span>
          <span
            className="text-[10px] font-pixel"
            style={{ color: sent.color }}
          >
            [{sent.symbol}]
          </span>
        </div>
        <div
          className="text-[8px] font-mono tracking-widest uppercase"
          style={{ color: "#8B7355" }}
        >
          {info.role?.toUpperCase?.() ?? info.role}
        </div>
      </div>
    </div>
  );
}

const DEFAULT_OVERLAY_METRICS: OverlayMetrics = {
  offsetX: 0,
  offsetY: 0,
  width: GAME_WIDTH * SCALE_FACTOR,
  height: GAME_HEIGHT * SCALE_FACTOR,
  scaleX: SCALE_FACTOR,
  scaleY: SCALE_FACTOR,
};

export default function SimulatePage() {
  return (
    <Suspense fallback={<GameCanvasPlaceholder />}>
      <SimulateContent />
    </Suspense>
  );
}

function SimulateContent() {
  const searchParams = useSearchParams();
  const isMock = process.env.NEXT_PUBLIC_MOCK_BACKEND === "true";
  const simulationId = searchParams.get("id") || "";
  const isReplay = searchParams.get("mode") === "replay";
  const isRecording = searchParams.get("record") === "true";
  const sim = useSimulation(simulationId || undefined, isRecording);
  const { stage, npcsReady, numNpcs } = sim.setupProgress;
  const showSetupOverlay = !sim.isRunning
    ? false  // not started yet, don't show
    : stage !== "ready";  // show while generating
  const [selectedNpcId, setSelectedNpcId] = useState<string | null>(null);

  const handleEventClick = useCallback((event: SimEvent) => {
    setSelectedNpcId(event.agentId);
  }, []);

  const selectedNpc = selectedNpcId ? sim.getNpc(selectedNpcId) : undefined;
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const [focusScale, setFocusScale] = useState(1);
  const [hoverInfo, setHoverInfo] = useState<NPCHoverInfo | null>(null);
  const [showGraph, setShowGraph] = useState(false);
  const [overlayMetrics, setOverlayMetrics] = useState<OverlayMetrics>(
    DEFAULT_OVERLAY_METRICS,
  );
  const [showReport, setShowReport] = useState(false);
  const reportShownRef = useRef(false);

  useEffect(() => {
    if (focusMode) {
      setFocusScale(
        Math.max(
          window.innerWidth / GAME_WIDTH,
          window.innerHeight / GAME_HEIGHT,
        ),
      );
    } else {
      setFocusScale(1);
    }
  }, [focusMode]);

  // Auto-start simulation once we have a simulation ID (or immediately in mock/replay mode)
  const hasStartedRef = useRef(false);
  useEffect(() => {
    if (hasStartedRef.current) return;
    if (isReplay) {
      const data = getReplayData();
      if (data) {
        hasStartedRef.current = true;
        clearReplayData();
        sim.startFromRecording(data);
      }
    } else if (simulationId || isMock) {
      hasStartedRef.current = true;
      sim.start();
    }
    return () => {
      hasStartedRef.current = false;
    };
  }, [simulationId, isReplay]); // eslint-disable-line react-hooks/exhaustive-deps

  // Reset transient overlay UI when Phaser re-initializes the NPC set.
  useEffect(() => {
    let cleanup: (() => void) | undefined;
    import("@/game/bridge/EventBridge").then(({ eventBridge }) => {
      const handler = () => {
        setHoverInfo(null);
      };
      eventBridge.on("sim:init-npcs", handler);
      cleanup = () => eventBridge.off("sim:init-npcs", handler);
    });
    return () => cleanup?.();
  }, []);

  // Listen for NPC hover events from Phaser
  useEffect(() => {
    let cleanup: (() => void) | undefined;
    import("@/game/bridge/EventBridge").then(({ eventBridge }) => {
      const onHover = (info: NPCHoverInfo) => setHoverInfo(info);
      const onHoverOut = () => setHoverInfo(null);
      eventBridge.on("sim:npc-hover", onHover);
      eventBridge.on("sim:npc-hover-out", onHoverOut);
      cleanup = () => {
        eventBridge.off("sim:npc-hover", onHover);
        eventBridge.off("sim:npc-hover-out", onHoverOut);
      };
    });
    return () => cleanup?.();
  }, []);

  // Open NPC profile when clicked on canvas
  useEffect(() => {
    let cleanup: (() => void) | undefined;
    import("@/game/bridge/EventBridge").then(({ eventBridge }) => {
      const handler = (data: { npcId: string }) => {
        setSelectedNpcId(data.npcId);
        // Removed automatic camera snap to allow manual control
        // eventBridge.emitCameraSnapToNPC(data.npcId);
      };
      eventBridge.on("sim:npc-click", handler);
      cleanup = () => eventBridge.off("sim:npc-click", handler);
    });
    return () => cleanup?.();
  }, []);

  // Fullscreen toggle
  const toggleFullscreen = useCallback(() => {
    const el = canvasContainerRef.current;
    if (!el) return;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      el.requestFullscreen();
    }
  }, []);

  // Track fullscreen state
  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  // Measure the real Phaser canvas box so DOM overlays stay locked to sprite positions.
  useEffect(() => {
    const container = canvasContainerRef.current;
    if (!container) return;

    let observedTarget: Element | null = null;
    const updateMetrics = () => {
      const canvas =
        container.querySelector("canvas") ??
        container.querySelector("[data-testid='game-canvas']");
      const target = canvas instanceof HTMLElement ? canvas : null;
      if (!target) return;

      if (observedTarget !== target) {
        if (observedTarget) resizeObserver.unobserve(observedTarget);
        observedTarget = target;
        resizeObserver.observe(target);
      }

      const containerRect = container.getBoundingClientRect();
      const targetRect = target.getBoundingClientRect();
      const next: OverlayMetrics = {
        offsetX: targetRect.left - containerRect.left,
        offsetY: targetRect.top - containerRect.top,
        width: targetRect.width,
        height: targetRect.height,
        scaleX: targetRect.width / GAME_WIDTH,
        scaleY: targetRect.height / GAME_HEIGHT,
      };

      setOverlayMetrics((prev) => {
        const changed =
          Math.abs(prev.offsetX - next.offsetX) > 0.5 ||
          Math.abs(prev.offsetY - next.offsetY) > 0.5 ||
          Math.abs(prev.width - next.width) > 0.5 ||
          Math.abs(prev.height - next.height) > 0.5;
        return changed ? next : prev;
      });
    };

    const resizeObserver = new ResizeObserver(() => updateMetrics());
    resizeObserver.observe(container);

    const mutationObserver = new MutationObserver(() => updateMetrics());
    mutationObserver.observe(container, { childList: true, subtree: true });

    window.addEventListener("resize", updateMetrics);
    document.addEventListener("fullscreenchange", updateMetrics);
    updateMetrics();

    return () => {
      resizeObserver.disconnect();
      mutationObserver.disconnect();
      window.removeEventListener("resize", updateMetrics);
      document.removeEventListener("fullscreenchange", updateMetrics);
    };
  }, []);

  // Camera panning via click+drag
  useEffect(() => {
    const el = canvasContainerRef.current;
    if (!el) return;

    let dragging = false;
    let lastX = 0;
    let lastY = 0;

    const onDown = (e: PointerEvent) => {
      if (e.button !== 0) return;
      dragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      el.style.cursor = "grabbing";
      el.setPointerCapture(e.pointerId);
    };

    const onMove = (e: PointerEvent) => {
      if (!dragging) return;
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      lastX = e.clientX;
      lastY = e.clientY;
      import("@/game/bridge/EventBridge").then(({ eventBridge }) => {
        eventBridge.emitCameraPan(-dx / SCALE_FACTOR, -dy / SCALE_FACTOR);
      });
    };

    const onUp = (e: PointerEvent) => {
      if (!dragging) return;
      dragging = false;
      el.style.cursor = "grab";
      el.releasePointerCapture(e.pointerId);
    };

    el.style.cursor = "grab";
    el.addEventListener("pointerdown", onDown);
    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerup", onUp);

    // Camera zooming via mouse wheel
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 1 : -1;

      const zoomTarget =
        el.querySelector("canvas") ??
        el.querySelector("[data-testid='game-canvas']");
      const rect =
        zoomTarget instanceof HTMLElement
          ? zoomTarget.getBoundingClientRect()
          : el.getBoundingClientRect();
      const scaleX = rect.width > 0 ? GAME_WIDTH / rect.width : 1;
      const scaleY = rect.height > 0 ? GAME_HEIGHT / rect.height : 1;
      const mouseX = (e.clientX - rect.left) * scaleX;
      const mouseY = (e.clientY - rect.top) * scaleY;

      import("@/game/bridge/EventBridge").then(({ eventBridge }) => {
        eventBridge.emitCameraZoom(delta, mouseX, mouseY);
      });
    };
    el.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      el.removeEventListener("pointerdown", onDown);
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerup", onUp);
      el.removeEventListener("wheel", onWheel);
    };
  }, []);

  // Close modals / focus mode on ESC
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setFocusMode(false);
        setShowGraph(false);
        setShowReport(false);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!sim.isComplete) {
      reportShownRef.current = false;
      setShowReport(false);
      return;
    }
    if (reportShownRef.current) return;
    if (sim.reportLoading || sim.report) {
      reportShownRef.current = true;
      setShowReport(true);
    }
  }, [sim.isComplete, sim.reportLoading, sim.report]);

  const PHASE_CHIPS = [
    { label: "SPRING", activeColor: "#3E7C34", activeBorder: "#2A5424", activeText: "#FDF5E6" },
    { label: "SUMMER", activeColor: "#C97D1A", activeBorder: "#8B5510", activeText: "#FDF5E6" },
    { label: "HARVEST", activeColor: "#B83A52", activeBorder: "#7A2538", activeText: "#FDF5E6" },
  ] as const;

  const woodenBtnStyle = {
    background: "#D4A044",
    border: "2px solid #5B3010",
    borderRadius: "2px",
    boxShadow: "inset 1px 1px 0 #E8C874, inset -1px -1px 0 #A07028, 2px 2px 0 #3D1E08",
    color: "#5B3010",
  };

  if (!simulationId && !isMock && !isReplay) {
    return (
      <div
        className="flex min-h-screen flex-col items-center justify-center px-6"
        style={{ background: "#1a1208" }}
      >
        <div
          className="flex max-w-md flex-col items-center gap-4 p-8 text-center"
          style={{
            background: "#F5E6C8",
            border: "4px solid #6B4226",
            borderRadius: "8px",
            boxShadow:
              "inset 2px 2px 0 rgba(196,164,108,.55), inset -2px -2px 0 rgba(61,37,16,.25), 4px 4px 0 rgba(61,37,16,.4)",
          }}
        >
          <span
            className="text-[10px] font-pixel tracking-widest"
            style={{ color: "#5B3A1E" }}
          >
            {"\u2605"} GEMEINDESIM {"\u2605"}
          </span>
          <p
            className="text-[10px] font-mono uppercase tracking-widest"
            style={{ color: "#3D2510" }}
          >
            No policy specified.
          </p>
          <p
            className="text-[10px] font-mono uppercase tracking-widest"
            style={{ color: "#8B7355" }}
          >
            Please describe an economic policy on the home page before running a
            simulation.
          </p>
          <Link
            href="/"
            className="rpg-panel mt-2 px-6 py-2 text-[10px] font-pixel transition-opacity hover:opacity-80"
            style={{ color: "#5B3A1E", background: "#E8D5A3" }}
          >
            {">> Enter Policy <<"}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div
      className="relative flex h-screen flex-col overflow-clip"
      style={{ background: "#1a1208" }}
      data-testid="simulate-page"
    >
      {/* Phase indicator bar */}
      <div
        className={`rpg-panel flex h-10 shrink-0 items-center justify-between rounded-none border-x-0 border-t-0 px-4 panel-slide-top ${focusMode ? "panel-hidden-top" : ""}`}
        style={{ background: "#E8D5A3", borderBottom: "3px solid #6B4226" }}
        data-testid="phase-bar"
      >
        <div className="flex items-center gap-3">
          <span
            className="text-[10px] font-pixel tracking-tight"
            style={{ color: "#5B3A1E" }}
          >
            {"\u2605"} GEMEINDESIM
          </span>
          <span className="text-[10px] font-mono" style={{ color: "#C4A46C" }}>
            |
          </span>
          <div className="flex gap-1">
            {PHASE_CHIPS.map((chip, i) => {
              const p = i + 1;
              const active = sim.phase >= p;
              return (
                <div
                  key={chip.label}
                  className="px-2 py-0.5 text-[7px] font-pixel uppercase transition-colors duration-500"
                  style={{
                    border: `1px solid ${active ? chip.activeBorder : "#C4A46C"}`,
                    borderRadius: "2px",
                    background: active ? chip.activeColor : "#F5E6C8",
                    color: active ? chip.activeText : "#C4A46C",
                  }}
                >
                  {chip.label}
                </div>
              );
            })}
          </div>
          {/* Round progress bar */}
          <div className="flex items-center gap-2 ml-2">
            <div
              className="h-1.5 w-20 overflow-hidden"
              style={{
                background: "#E8D5A3",
                border: "1px solid #C4A46C",
                borderRadius: "2px",
              }}
            >
              <div
                className="h-full transition-all duration-500"
                style={{
                  width: `${sim.maxRounds > 0 ? (sim.round / sim.maxRounds) * 100 : 0}%`,
                  background: "linear-gradient(90deg, #D4A520, #C97D1A)",
                }}
              />
            </div>
            <span
              className="text-[9px] font-mono tabular-nums"
              style={{ color: "#8B7355" }}
            >
              {sim.round}/{sim.maxRounds}
            </span>
          </div>
          {sim.phase > 0 && (
            <span
              className="text-[9px] font-mono uppercase tracking-widest ml-2"
              style={{ color: "#6B4C2A" }}
            >
              {sim.phaseLabel}
            </span>
          )}
        </div>

        <div className="relative z-[2] flex items-center gap-3">
          {sim.isRunning && isRecording && (
            <span
              className="text-[9px] font-pixel animate-pulse"
              style={{ color: "#B83A52" }}
            >
              REC
            </span>
          )}
          {sim.isComplete && (
            <>
              <span
                className="text-[9px] font-pixel"
                style={{ color: "#3E7C34" }}
              >
                COMPLETE
              </span>
              <button
                type="button"
                onClick={() => setShowReport(true)}
                className="text-[9px] font-mono uppercase tracking-widest transition-opacity hover:opacity-60"
                style={{ color: "#6B4C2A" }}
              >
                {sim.reportLoading
                  ? "[Report...]"
                  : sim.report
                    ? "[Report]"
                    : "[Report Pending]"}
              </button>
              {sim.getRecording() && (
                <button
                  type="button"
                  onClick={() => {
                    const recording = sim.getRecording();
                    if (!recording) return;
                    const blob = new Blob(
                      [JSON.stringify(recording, null, 2)],
                      { type: "application/json" },
                    );
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `gemeindesim-${Date.now()}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                  className="text-[9px] font-mono uppercase tracking-widest transition-opacity hover:opacity-60"
                  style={{ color: "#6B4C2A" }}
                >
                  SAVE JSON
                </button>
              )}
            </>
          )}
          {sim.isRunning && !isRecording && (
            <span
              className="text-[9px] font-mono uppercase tracking-widest"
              style={{ color: "#8B7355" }}
            >
              Simulating...
            </span>
          )}
          <button
            type="button"
            onClick={() => setFocusMode((f) => !f)}
            className="rpg-panel px-3 py-1 text-[9px] font-mono font-bold tracking-widest transition-all hover:opacity-80"
            style={{
              color: focusMode ? "#D4A520" : "#8B7355",
              background: focusMode ? "rgba(212,165,32,0.1)" : undefined,
              borderColor: focusMode ? "#D4A520" : undefined,
            }}
            title="Toggle focus mode (hides panels)"
          >
            {focusMode ? "[ EXIT FOCUS ]" : "[ FOCUS ]"}
          </button>
        </div>
      </div>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Event feed */}
        <div
          className={`rpg-panel flex h-full w-64 shrink-0 flex-col panel-slide-left ${focusMode ? "panel-hidden-left" : ""}`}
        >
          <div
            className="flex items-center justify-between px-3 py-2"
            style={{ borderBottom: "2px solid #C4A46C" }}
          >
            <h2
              className="text-[8px] font-pixel uppercase"
              style={{ color: "#5B3A1E" }}
            >
              Event Log
            </h2>
            <button
              type="button"
              onClick={() => setShowGraph(true)}
              className="text-[9px] font-mono uppercase tracking-widest transition-opacity hover:opacity-60"
              style={{ color: "#8B7355" }}
              title="Open Social Graph"
            >
              GRAPH
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <EventFeed events={sim.events} onEventClick={handleEventClick} />
          </div>
        </div>

        {/* Center: Game canvas with overlays - now full width */}
        <div
          className={
            focusMode
              ? "fixed inset-0 z-50 flex items-center justify-center overflow-hidden"
              : "relative min-w-0 flex-1 overflow-hidden"
          }
          style={focusMode ? { background: "#060010" } : undefined}
        >
          <div
            ref={canvasContainerRef}
            className={`canvas-expand ${focusMode ? "relative shrink-0 canvas-glow" : "absolute inset-0"}`}
            style={
              focusMode
                ? {
                    width: GAME_WIDTH,
                    height: GAME_HEIGHT,
                    transform: `scale(${focusScale})`,
                    transformOrigin: "center center",
                    border: "none",
                    padding: 0,
                    boxShadow: "none",
                  }
                : {}
            }
          >
            <GameCanvas />

            {/* Fullscreen toggle + Zoom controls */}
            <div className="absolute top-2 right-2 z-40 flex gap-1">
              <motion.button
                type="button"
                onClick={() => {
                  import("@/game/bridge/EventBridge").then(({ eventBridge }) => {
                    eventBridge.emitCameraZoom(1);
                  });
                }}
                whileHover={{ y: -1 }}
                whileTap={{ y: 1 }}
                className="px-2 py-1 text-[9px] font-pixel uppercase cursor-pointer pixel-crisp"
                style={woodenBtnStyle}
                title="Zoom in"
              >
                +
              </motion.button>
              <motion.button
                type="button"
                onClick={() => {
                  import("@/game/bridge/EventBridge").then(({ eventBridge }) => {
                    eventBridge.emitCameraZoom(-1);
                  });
                }}
                whileHover={{ y: -1 }}
                whileTap={{ y: 1 }}
                className="px-2 py-1 text-[9px] font-pixel uppercase cursor-pointer pixel-crisp"
                style={woodenBtnStyle}
                title="Zoom out"
              >
                -
              </motion.button>
              <motion.button
                type="button"
                onClick={toggleFullscreen}
                whileHover={{ y: -1 }}
                whileTap={{ y: 1 }}
                className="px-2 py-1 text-[9px] font-pixel uppercase cursor-pointer pixel-crisp"
                style={woodenBtnStyle}
                title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
              >
                {isFullscreen ? "\u2199" : "\u26F6"}
              </motion.button>
            </div>

            {/* NPC hover tooltip */}
            {hoverInfo && (
              <div
                className="pointer-events-none absolute z-30 overflow-hidden"
                style={{
                  left: overlayMetrics.offsetX,
                  top: overlayMetrics.offsetY,
                  width: overlayMetrics.width,
                  height: overlayMetrics.height,
                }}
              >
                <NPCTooltip
                  info={hoverInfo}
                  scaleX={overlayMetrics.scaleX}
                  scaleY={overlayMetrics.scaleY}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Viewport-fixed dashboard so it stays fully visible instead of being clipped by the canvas area */}
      <div
        className={`fixed bottom-3 right-3 z-40 pointer-events-auto flex flex-col gap-2 ${focusMode ? "opacity-0 pointer-events-none" : ""}`}
      >
        <StancePanel npcs={sim.graphData.npcs} version={sim.graphData.version} />
        <Dashboard
          metrics={sim.metrics}
          metricsHistory={sim.metricsHistory}
          phase={sim.phase}
          round={sim.round}
          maxRounds={sim.maxRounds}
          hideEconomy={stancePoll(sim.graphData.npcs) !== null}
        />
      </div>

      {/* Focus mode exit overlay */}
      {focusMode && (
        <button
          type="button"
          className="fixed top-4 right-4 z-[60] rpg-panel px-3 py-1.5 text-[9px] font-mono transition-opacity hover:opacity-70"
          style={{
            color: "#5B3A1E",
            background: "#E8D5A3",
            border: "2px solid #6B4226",
          }}
          onClick={() => setFocusMode(false)}
        >
          [ESC] exit focus
        </button>
      )}

      {/* NPC Interaction Modal (Profile + Chat side-by-side) */}
      {selectedNpc && (
        <NPCInteractionModal
          npc={selectedNpc}
          simulationId={simulationId}
          onClose={() => setSelectedNpcId(null)}
        />
      )}

      {/* Social Graph Modal */}
      {showGraph && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowGraph(false);
          }}
        >
          <div
            className="relative flex flex-col animate-[modalIn_200ms_ease-out]"
            style={{
              width: 700,
              height: 560,
              background: "#F5E6C8",
              border: "4px solid #6B4226",
              borderRadius: "8px",
              boxShadow:
                "inset 2px 2px 0 rgba(196,164,108,.55), inset -2px -2px 0 rgba(61,37,16,.25), 4px 4px 0 rgba(61,37,16,.4)",
            }}
          >
            <div
              className="flex items-center justify-between px-4 py-2"
              style={{
                background: "#E8D5A3",
                borderBottom: "2px solid #C4A46C",
              }}
            >
              <h2
                className="text-[10px] font-pixel uppercase"
                style={{ color: "#5B3A1E" }}
              >
                {"\u2605"} Social Graph
              </h2>
              <button
                type="button"
                onClick={() => setShowGraph(false)}
                className="text-[10px] font-mono uppercase tracking-widest transition-opacity hover:opacity-60"
                style={{ color: "#8B7355" }}
              >
                [ESC]
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <SocialGraph
                npcs={sim.graphData.npcs}
                relationships={sim.graphData.relationships}
                influenceEvents={sim.graphData.influenceEvents}
                version={sim.graphData.version}
              />
            </div>
          </div>
        </div>
      )}

      {showReport && (
        <EconomicReportModal
          report={sim.report}
          loading={sim.reportLoading}
          error={sim.reportError}
          onClose={() => setShowReport(false)}
        />
      )}

      {/* NPC generation progress overlay — visible from connection until init */}
      <SimLoadingScreen
        isVisible={showSetupOverlay}
        stage={stage}
        npcsReady={npcsReady}
        numNpcs={numNpcs}
        label={sim.setupProgress.label}
      />

      {/* Error overlay — shown when backend restarts or simulation is lost */}
      {sim.error && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div
            className="rpg-panel px-6 py-4 text-center"
            style={{ background: "#FDF5E6" }}
          >
            <p
              className="font-mono text-sm font-bold"
              style={{ color: "#B83A52" }}
            >
              Connection Lost
            </p>
            <p
              className="mt-2 font-mono text-xs"
              style={{ color: "#6B4C2A" }}
            >
              The simulation server restarted. Please go back and start a new
              simulation.
            </p>
            <a
              href="/"
              className="mt-3 block font-mono text-xs underline"
              style={{ color: "#A0824A" }}
            >
              {"<-"} Back to home
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
