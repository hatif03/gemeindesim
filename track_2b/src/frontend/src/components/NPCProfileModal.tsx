"use client";

import { useEffect } from "react";
import type { BackendNPC } from "@/types/backend";

interface NPCProfileModalProps {
  npc: BackendNPC;
  onClose: () => void;
  onOpenChat?: (npc: BackendNPC) => void;
}

const MOOD_COLOR: Record<string, string> = {
  angry: "#B83A52",
  anxious: "#C97D1A",
  worried: "#C97D1A",
  neutral: "#5A8DB8",
  hopeful: "#3E7C34",
  excited: "#7B68EE",
};

const INCOME_LABEL: Record<string, { text: string; color: string }> = {
  low: { text: "LOW", color: "#B83A52" },
  medium: { text: "MED", color: "#C97D1A" },
  high: { text: "HIGH", color: "#3E7C34" },
};

const ROLE_COLOR: Record<string, string> = {
  activist: "#B83A52",
  politician: "#7B68EE",
  business_owner: "#D4A520",
  farmer: "#3E7C34",
  worker: "#5A8DB8",
  shopkeeper: "#C97D1A",
  driver: "#8B6914",
  student: "#7B68EE",
  retiree: "#A0824A",
};

const ROLE_INITIAL: Record<string, string> = {
  activist: "A",
  politician: "P",
  business_owner: "B",
  farmer: "F",
  worker: "W",
  shopkeeper: "S",
  driver: "D",
  student: "U",
  retiree: "R",
};

function politicalLabel(v: number): string {
  if (v <= -0.6) return "strongly progressive";
  if (v <= -0.2) return "leaning progressive";
  if (v <= 0.2) return "moderate";
  if (v <= 0.6) return "leaning conservative";
  return "strongly conservative";
}

function politicalColor(v: number): string {
  if (v <= -0.4) return "#5A8DB8";
  if (v <= 0.4) return "#7B68EE";
  return "#B83A52";
}

function StatRow({
  label,
  value,
  valueColor,
}: {
  label: string;
  value: string;
  valueColor?: string;
  glowClass?: string;
}) {
  return (
    <div className="flex items-center justify-between py-[3px]">
      <span
        className="text-[9px] font-mono uppercase tracking-widest"
        style={{ color: "#A0824A" }}
      >
        {label}
      </span>
      <span
        className="text-[10px] font-mono font-bold"
        style={{ color: valueColor ?? "#3D2510" }}
      >
        {value}
      </span>
    </div>
  );
}

function SectionBlock({
  label,
  symbol,
  content,
  fallback,
}: {
  label: string;
  symbol: string;
  content?: string;
  fallback: string;
}) {
  const hasContent = content && content.trim().length > 0;
  return (
    <div className="px-3 py-2" style={{ borderTop: "1px solid #E8D5A3" }}>
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-[10px] font-mono" style={{ color: "#C4A46C" }}>
          {symbol}
        </span>
        <span
          className="text-[8px] font-pixel uppercase"
          style={{ color: "#A0824A" }}
        >
          {label}
        </span>
      </div>
      <p
        className={`text-[10px] font-mono leading-relaxed ${hasContent ? "italic" : ""}`}
        style={{ color: hasContent ? "#6B4C2A" : "#C4A46C" }}
      >
        {hasContent ? `"${content}"` : fallback}
      </p>
    </div>
  );
}

export function NPCProfileModal({ npc, onClose, onOpenChat }: NPCProfileModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const moodColor = MOOD_COLOR[npc.mood] ?? "#8B7355";
  const income = INCOME_LABEL[npc.income_level] ?? INCOME_LABEL.medium;
  const polLabel = politicalLabel(npc.political_leaning);
  const polColor = politicalColor(npc.political_leaning);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative z-10 w-[320px] max-h-[80vh] overflow-y-auto scrollbar-thin animate-[modalIn_150ms_ease-out]"
        style={{
          background: "#F5E6C8",
          border: "4px solid #6B4226",
          borderRadius: "8px",
          boxShadow:
            "inset 2px 2px 0 rgba(196,164,108,.55), inset -2px -2px 0 rgba(61,37,16,.25), 4px 4px 0 rgba(61,37,16,.4)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex items-start justify-between px-3 py-3"
          style={{ background: "#E8D5A3", borderBottom: "2px solid #C4A46C" }}
        >
          {/* Role portrait */}
          <div
            className="shrink-0 flex items-center justify-center pixel-crisp"
            style={{
              width: 48,
              height: 48,
              background: ROLE_COLOR[npc.role] ?? "#6B4226",
              border: "3px solid #6B4226",
              borderRadius: "2px",
              boxShadow: "inset 2px 2px 0 rgba(255,255,255,0.2), inset -2px -2px 0 rgba(0,0,0,0.2), 2px 2px 0 rgba(61,37,16,0.4)",
            }}
          >
            <span
              className="text-[20px] font-pixel"
              style={{ color: "rgba(255,255,255,0.95)", lineHeight: 1 }}
            >
              {ROLE_INITIAL[npc.role] ?? "?"}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span
                className="text-[10px] font-mono"
                style={{ color: "#A0824A" }}
              >
                {">>"}
              </span>
              <h2
                className="text-[9px] font-pixel uppercase tracking-wide truncate"
                style={{ color: "#5B3A1E" }}
              >
                {npc.name}
              </h2>
            </div>
            <div
              className="mt-1 ml-5 text-[9px] font-mono uppercase tracking-widest"
              style={{ color: "#8B7355" }}
            >
              {npc.profession || npc.role?.replace(/_/g, " ") || "Resident"} · {npc.mbti} · {npc.industry || npc.lang || "resident"}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[10px] font-mono px-1 -mr-1 uppercase transition-opacity hover:opacity-60"
            style={{ color: "#8B7355" }}
          >
            [{"\u00D7"}]
          </button>
        </div>

        {/* Stats */}
        <div
          className="px-3 py-2"
          style={{ background: "#EDE4D3", borderBottom: "1px solid #E8D5A3" }}
        >
          <div className="flex items-center gap-1.5 mb-1">
            <span
              className="text-[10px] font-mono"
              style={{ color: "#D4A520" }}
            >
              {"\u2605"}
            </span>
            <span
              className="text-[8px] font-pixel uppercase"
              style={{ color: "#A0824A" }}
            >
              Status
            </span>
          </div>
          <div className="ml-3">
            <div className="flex items-center justify-between py-[3px]">
              <span
                className="text-[9px] font-mono uppercase tracking-widest"
                style={{ color: "#A0824A" }}
              >
                Mood
              </span>
              <span
                className="inline-flex items-center px-2 py-0.5 text-[8px] font-pixel uppercase"
                style={{
                  background: `${moodColor}22`,
                  border: `1px solid ${moodColor}`,
                  borderRadius: "2px",
                  color: moodColor,
                }}
              >
                {npc.mood.toUpperCase()}
              </span>
            </div>
            <StatRow
              label="Reputation"
              value={`${(npc.reputation * 100).toFixed(0)}%`}
              valueColor="#2dd4bf"
              glowClass="neon-text-teal"
            />
            <StatRow
              label="Income"
              value={income.text}
              valueColor={income.color}
            />
            {/* Political leaning with bar */}
            <div className="flex flex-col py-[3px] gap-1">
              <div className="flex items-center justify-between">
                <span
                  className="text-[9px] font-mono uppercase tracking-widest"
                  style={{ color: "#A0824A" }}
                >
                  Political
                </span>
                <span
                  className="text-[9px] font-mono"
                  style={{ color: polColor }}
                >
                  {polLabel}
                </span>
              </div>
              {/* Bar: left half = progressive (blue), right half = conservative (red) */}
              <div
                className="relative h-2 w-full overflow-hidden"
                style={{
                  background: "#E8D5A3",
                  border: "1px solid #C4A46C",
                  borderRadius: "2px",
                }}
              >
                {npc.political_leaning < 0 ? (
                  /* Progressive: fill from center going left */
                  <div
                    className="absolute top-0 h-full"
                    style={{
                      right: "50%",
                      width: `${Math.abs(npc.political_leaning) * 50}%`,
                      background: "#5A8DB8",
                    }}
                  />
                ) : (
                  /* Conservative: fill from center going right */
                  <div
                    className="absolute top-0 h-full"
                    style={{
                      left: "50%",
                      width: `${npc.political_leaning * 50}%`,
                      background: "#B83A52",
                    }}
                  />
                )}
                {/* Center marker */}
                <div
                  className="absolute top-0 h-full w-px"
                  style={{ left: "50%", background: "#C4A46C" }}
                />
              </div>
            </div>
            <StatRow label="Position" value={`(${npc.x}, ${npc.y})`} />
          </div>
        </div>

        {/* Internal state sections */}
        <SectionBlock
          label="Perception"
          symbol="?"
          content={npc.perception}
          fallback="No thoughts yet..."
        />
        {/* Beliefs section */}
        <div className="px-3 py-2" style={{ borderTop: "1px solid #E8D5A3" }}>
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-[10px] font-mono" style={{ color: "#C4A46C" }}>!</span>
            <span className="text-[8px] font-pixel uppercase" style={{ color: "#A0824A" }}>
              Beliefs
            </span>
          </div>
          {npc.beliefs && npc.beliefs.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {npc.beliefs.map((belief, i) => (
                <span
                  key={`belief-${i}`}
                  className="inline-block text-[9px] font-mono px-2 py-0.5"
                  style={{
                    background: "#EDE4D3",
                    border: "1px solid #C4A46C",
                    borderRadius: "2px",
                    color: "#6B4C2A",
                  }}
                >
                  {belief}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-[10px] font-mono" style={{ color: "#C4A46C" }}>
              No defined beliefs...
            </p>
          )}
        </div>
        <SectionBlock
          label="Controversial Ideas"
          symbol="*"
          content={npc.controversial_ideas?.join(" · ")}
          fallback="No controversial ideas..."
        />
        <SectionBlock
          label="Plan"
          symbol=">"
          content={npc.current_plan}
          fallback="No plan formed yet..."
        />

        {/* Footer bar */}
        <div
          className="flex items-center justify-between px-3 py-2"
          style={{ background: "#E8D5A3", borderTop: "2px solid #C4A46C" }}
        >
          <span
            className="text-[9px] font-mono uppercase tracking-tight"
            style={{ color: "#A0824A" }}
          >
            {npc.id} · ESC TO CLOSE
          </span>
          {onOpenChat && (
            <button
              type="button"
              onClick={() => onOpenChat(npc)}
              className="px-3 py-1 text-[9px] font-pixel uppercase tracking-wide transition-opacity hover:opacity-80"
              style={{
                background: "#3E7C34",
                border: "2px solid #2A5424",
                borderRadius: "4px",
                color: "#FDF5E6",
                boxShadow: "inset 1px 1px 0 #5A9B4A, 2px 2px 0 #1A3414",
              }}
            >
              Chat
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
