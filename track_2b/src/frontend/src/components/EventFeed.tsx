"use client";

import { useEffect, useRef } from "react";
import type { SimEvent } from "@/types";

interface EventFeedProps {
  events: SimEvent[];
  onEventClick?: (event: SimEvent) => void;
}

function eventIcon(type: SimEvent["type"]): string {
  switch (type) {
    case "chat":
      return "\u275D";
    case "move":
      return "\u2192";
    case "protest":
      return "!";
    case "mood_shift":
      return "\u007E";
    case "price_change":
      return "$";
    case "layoff":
      return "\u2715";
    case "closure":
      return "\u2715";
    case "strike":
      return "\u26A0";
    case "policy_response":
      return "\u2605";
    case "phase_change":
      return "\u25C6";
    case "reaction":
      return "\u25B7";
    default:
      return "\u25CB";
  }
}

function eventAccent(type: SimEvent["type"]): string {
  switch (type) {
    case "reaction":
      return "sdv-text-muted";
    case "price_change":
      return "sdv-text-gold";
    case "layoff":
      return "sdv-text-berry";
    case "protest":
      return "sdv-text-orange";
    case "closure":
      return "sdv-text-berry";
    case "strike":
      return "sdv-text-orange";
    case "policy_response":
      return "sdv-text-green";
    case "phase_change":
      return "sdv-text-purple";
    default:
      return "sdv-text-muted";
  }
}

function eventBorderColor(type: SimEvent["type"]): string {
  switch (type) {
    case "chat":
      return "#3E7C34";
    case "move":
      return "#5A8DB8";
    case "protest":
    case "layoff":
    case "closure":
    case "strike":
      return "#B83A52";
    case "price_change":
      return "#D4A520";
    case "mood_shift":
    case "policy_response":
      return "#7B68EE";
    default:
      return "#C4A46C";
  }
}

// Stardew color classes applied via inline style below
const SDV_COLORS: Record<string, string> = {
  "sdv-text-muted": "#8B7355",
  "sdv-text-gold": "#C97D1A",
  "sdv-text-berry": "#B83A52",
  "sdv-text-orange": "#C97D1A",
  "sdv-text-green": "#3E7C34",
  "sdv-text-purple": "#7B68EE",
};

export function EventFeed({ events, onEventClick }: EventFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  const eventRows: Array<{ event: SimEvent; showRoundSep: boolean }> = [];
  let prevRound = -1;
  for (const event of events) {
    const showRoundSep =
      event.type !== "phase_change" &&
      event.round !== undefined &&
      event.round !== prevRound &&
      prevRound !== -1;
    if (event.round !== undefined) prevRound = event.round;
    eventRows.push({ event, showRoundSep });
  }

  return (
    <div className="flex h-full flex-col" data-testid="event-feed">
      {/* Events */}
      <div className="flex-1 overflow-y-auto px-2 py-1 scrollbar-thin">
        {events.length === 0 && (
          <div
            className="flex h-full items-center justify-center text-[10px] font-mono uppercase tracking-widest"
            style={{ color: "#A0824A" }}
          >
            Awaiting simulation...
          </div>
        )}

        {eventRows.map(({ event, showRoundSep }) => {
          if (event.type === "phase_change") {
            return (
              <div
                key={event.id}
                className="my-2 py-1.5 text-center text-[8px] font-pixel"
                style={{
                  color: "#5B3A1E",
                  borderTop: "1px solid #C4A46C",
                  borderBottom: "1px solid #C4A46C",
                }}
                data-testid="phase-marker"
              >
                {event.message}
              </div>
            );
          }

          const accentClass = eventAccent(event.type);
          const accentColor = SDV_COLORS[accentClass] ?? "#8B7355";

          return (
            <div key={event.id}>
              {showRoundSep && (
                <div
                  className="my-2 flex items-center gap-2"
                  data-testid="round-separator"
                >
                  <div className="flex-1" style={{ borderTop: "1px dashed #C4A46C" }} />
                  <span
                    className="text-[7px] font-pixel uppercase tracking-widest"
                    style={{ color: "#A0824A" }}
                  >
                    ◆ Round {event.round}
                  </span>
                  <div className="flex-1" style={{ borderTop: "1px dashed #C4A46C" }} />
                </div>
              )}
              <div
                className={`event-entry mb-1 py-1.5 rounded ${onEventClick ? "cursor-pointer transition-colors" : ""}`}
                style={{
                  borderLeft: `3px solid ${eventBorderColor(event.type)}`,
                  paddingLeft: '10px',
                }}
                onMouseEnter={
                  onEventClick
                    ? (e) => {
                        (e.currentTarget as HTMLElement).style.background =
                          "rgba(196,164,108,0.15)";
                      }
                    : undefined
                }
                onMouseLeave={
                  onEventClick
                    ? (e) => {
                        (e.currentTarget as HTMLElement).style.background = "";
                      }
                    : undefined
                }
                data-testid="event-item"
                onClick={onEventClick ? () => onEventClick(event) : undefined}
              >
                <div className="flex items-center gap-1.5">
                  <span
                    className="text-[10px] font-mono"
                    style={{ color: accentColor }}
                  >
                    {eventIcon(event.type)}
                  </span>
                  <span
                    className="text-[9px] font-pixel"
                    style={{ color: "#3D2510" }}
                  >
                    {event.agentName}
                  </span>
                  {event.agentCategory && (
                    <span
                      className="text-[9px] font-mono"
                      style={{ color: "#A0824A" }}
                    >
                      {event.agentCategory}
                    </span>
                  )}
                  {(event.sources && event.sources.length > 0
                    ? event.sources
                    : (event.usedSourceIds || []).map((id) => ({ id, text: "" }))
                  ).map((src) => (
                    <span
                      key={src.id}
                      className="text-[8px] font-mono tracking-wide"
                      style={{ color: "#3E7C34", cursor: "help" }}
                      title={src.text ? `${src.id}: ${src.text}` : src.id}
                      data-testid="citation"
                    >
                      [{src.id.split("#").pop()}]
                    </span>
                  ))}
                  {event.grounded === false && (
                    <span
                      className="text-[8px] font-mono uppercase tracking-wide"
                      style={{ color: "#B8860B" }}
                      title="Quotes a figure without a valid citation"
                    >
                      uncited
                    </span>
                  )}
                  <span
                    className="ml-auto text-[9px] font-mono tabular-nums"
                    style={{ color: "#A0824A" }}
                  >
                    R{event.round}
                  </span>
                </div>
                <p
                  className="mt-0.5 text-[10px] font-mono leading-relaxed"
                  style={{ color: "#6B4C2A" }}
                >
                  {event.message}
                </p>
              </div>
            </div>
          );
        })}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
