"use client";

import { useRef } from "react";
import { MIN_NOTES_CHARS_FOR_TEXT_ONLY } from "@/types/backend";
import { useForm } from "./FormContext";
import NodeWrapper from "./NodeWrapper";

export default function RunNode() {
  const {
    policySources,
    notesText,
    uploadingPolicySources,
    uploadingTrends,
    handleSimulate,
    isSimulating,
    record,
    setRecord,
    handleLoadCustomRun,
    handleLoadFile,
    loadingCustomRun,
  } = useForm();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const notesOk = notesText.trim().length >= MIN_NOTES_CHARS_FOR_TEXT_ONLY;
  const canRun =
    (policySources.length > 0 || notesOk) &&
    !isSimulating &&
    !uploadingPolicySources &&
    !uploadingTrends;

  return (
    <NodeWrapper badge="03" title="OUTPUT" description="Go." hasSource={false}>
      <div
        className="nodrag nopan cursor-default flex flex-col items-center gap-5 py-6"
        style={{ width: 440 }}
      >
        {/* Run button */}
        <button
          type="button"
          onClick={handleSimulate}
          disabled={!canRun}
          data-testid="run-button"
          className="rpg-panel w-full py-4 text-[13px] font-pixel uppercase tracking-wide transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed active:translate-y-px hover:opacity-85"
          style={{
            color: "#3D2510",
            background: "#E8D5A3",
            borderColor: canRun ? "#D4A520" : undefined,
          }}
        >
          {isSimulating ? "\u2605 Running... \u2605" : "\u2605 Run Sim \u2605"}
        </button>

        {/* Status */}
        <span
          className="text-[12px] font-mono text-center"
          style={{
            color: canRun
              ? "#3E7C34"
              : uploadingPolicySources
                ? "#C97D1A"
                : "#B83A52",
          }}
        >
          {isSimulating
            ? "SIMULATING..."
            : canRun
              ? "\u2605 READY"
              : uploadingPolicySources
                ? "PROCESSING UPLOAD..."
                : `ADD DOCS OR ${MIN_NOTES_CHARS_FOR_TEXT_ONLY}+ CHAR NOTES`}
        </span>

        {/* Record toggle */}
        <button
          type="button"
          onClick={() => setRecord(!record)}
          className="rpg-panel w-full px-3 py-1.5 text-[12px] font-mono transition-all duration-150 active:translate-y-px"
          style={{
            color: record ? "#B83A52" : "#8B7355",
            background: record ? "#FADED4" : "#FFF8DC",
            borderColor: record ? "#B83A52" : undefined,
          }}
        >
          [{record ? "REC" : "OFF"}] Record
        </button>

        {/* Replay loaders */}
        <button
          type="button"
          onClick={handleLoadCustomRun}
          disabled={loadingCustomRun}
          className="rpg-panel w-full px-3 py-1.5 text-[12px] font-mono text-center transition-opacity hover:opacity-80 disabled:opacity-40"
          style={{ color: "#5B3A1E", background: "#FFF8DC" }}
        >
          {loadingCustomRun ? "Loading..." : "Load Custom Run"}
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleLoadFile}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="rpg-panel w-full px-3 py-1.5 text-[12px] font-mono text-center transition-opacity hover:opacity-80"
          style={{ color: "#5B3A1E", background: "#FFF8DC" }}
        >
          Load Saved Sim
        </button>
      </div>
    </NodeWrapper>
  );
}
