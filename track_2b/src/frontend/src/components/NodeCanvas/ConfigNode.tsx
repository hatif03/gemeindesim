"use client";

import { useForm } from "./FormContext";
import NodeWrapper from "./NodeWrapper";

export default function ConfigNode() {
  const {
    numNpcs,
    setNumNpcs,
    numRounds,
    setNumRounds,
    objective,
    setObjective,
  } = useForm();

  return (
    <NodeWrapper
      badge="02"
      title="CONFIG"
      description="Adjust agents, rounds, and focus."
    >
      <div
        className="nodrag nopan cursor-default space-y-4"
        style={{ width: 528 }}
      >
        {/* NPCs */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-end">
            <div className="flex flex-col">
              <span
                className="text-[11px] font-mono uppercase tracking-tight"
                style={{ color: "#A0824A" }}
              >
                Scale
              </span>
              <label
                className="text-[13px] font-mono font-bold"
                style={{ color: "#3D2510" }}
              >
                NPCS
              </label>
            </div>
            <div className="flex items-baseline gap-1">
              <span
                className="text-[18px] font-mono font-bold"
                style={{ color: "#D4A520" }}
              >
                {numNpcs}
              </span>
              <span
                className="text-[11px] font-mono"
                style={{ color: "#8B7355" }}
              >
                units
              </span>
            </div>
          </div>
          <input
            type="range"
            min="5"
            max="50"
            step="1"
            value={numNpcs}
            onChange={(e) => setNumNpcs(Number.parseInt(e.target.value))}
            className="rpg-slider"
            data-testid="npcs-slider"
          />
        </div>

        {/* Rounds */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-end">
            <div className="flex flex-col">
              <span
                className="text-[11px] font-mono uppercase tracking-tight"
                style={{ color: "#A0824A" }}
              >
                Depth
              </span>
              <label
                className="text-[13px] font-mono font-bold"
                style={{ color: "#3D2510" }}
              >
                ROUNDS
              </label>
            </div>
            <div className="flex items-baseline gap-1">
              <span
                className="text-[18px] font-mono font-bold"
                style={{ color: "#D4A520" }}
              >
                {numRounds}
              </span>
              <span
                className="text-[11px] font-mono"
                style={{ color: "#8B7355" }}
              >
                steps
              </span>
            </div>
          </div>
          <input
            type="range"
            min="3"
            max="20"
            step="1"
            value={numRounds}
            onChange={(e) => setNumRounds(Number.parseInt(e.target.value))}
            className="rpg-slider"
            data-testid="rounds-slider"
          />
        </div>

        {/* Objective (merged from ObjectiveNode) */}
        <div className="space-y-1.5">
          <div className="flex flex-col">
            <span
              className="text-[11px] font-mono uppercase tracking-tight"
              style={{ color: "#A0824A" }}
            >
              Focus
            </span>
            <label
              className="text-[13px] font-mono font-bold uppercase"
              style={{ color: "#3D2510" }}
            >
              Objective
            </label>
          </div>
          <div className="relative">
            <textarea
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              data-testid="objective-textarea"
              placeholder={
                "What are you curious about?\ne.g. 'How does this affect low-income workers?'"
              }
              rows={8}
              maxLength={500}
              className="rpg-panel w-full resize-none p-2 text-[15px] leading-relaxed font-mono outline-none transition-colors"
              style={{
                color: "#3D2510",
                background: "#FFF8DC",
                borderColor: objective.length > 0 ? "#D4A520" : undefined,
              }}
            />
            <span
              className="absolute right-2 bottom-2 text-[12px] font-mono"
              style={{ color: "#A0824A" }}
            >
              {objective.length}/500
            </span>
          </div>
        </div>
      </div>
    </NodeWrapper>
  );
}
