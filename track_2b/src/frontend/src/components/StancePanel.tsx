"use client";

import { useEffect, useRef, useState } from "react";
import { type StancePoll, stancePoll } from "@/lib/stance";
import type { BackendNPC } from "@/types/backend";

interface StancePanelProps {
  npcs: BackendNPC[];
  /** Bumped by the simulation hook whenever the resident list changes. */
  version: number;
}

const FOR = "#3E7C34";
const AGAINST = "#B83A52";
const UNDECIDED = "#A89A78";

function Bar({ poll }: { poll: StancePoll }) {
  const pct = (v: number) => `${(100 * v) / poll.n}%`;
  return (
    <div
      className="flex h-3 w-full overflow-hidden"
      style={{ border: "1px solid #C4A46C", borderRadius: "2px", background: "#E8D5A3" }}
      role="img"
      aria-label={`For ${poll.for}, undecided ${poll.undecided}, against ${poll.against}`}
    >
      <div style={{ width: pct(poll.for), background: FOR }} />
      <div style={{ width: pct(poll.undecided), background: UNDECIDED }} />
      <div style={{ width: pct(poll.against), background: AGAINST }} />
    </div>
  );
}

function Counts({ poll }: { poll: StancePoll }) {
  return (
    <span className="font-mono tabular-nums">
      <span style={{ color: FOR }}>{poll.for} for</span>
      {" · "}
      <span style={{ color: "#7A6A48" }}>{poll.undecided} undecided</span>
      {" · "}
      <span style={{ color: AGAINST }}>{poll.against} against</span>
    </span>
  );
}

/**
 * Stance poll of the residents. The stance is computed in code (household cost, ideology, judged impact) and moved by
 * the opinion dynamics; it is not a number the language model reports. Renders nothing for backends without stance.
 */
export function StancePanel({ npcs, version }: StancePanelProps) {
  const now = stancePoll(npcs);
  const first = useRef<StancePoll | null>(null);
  const [, force] = useState(0);

  useEffect(() => {
    if (npcs.length === 0) {
      first.current = null; // new run
    } else if (first.current === null && now) {
      first.current = now;
      force((x) => x + 1);
    }
  }, [npcs.length, now, version]);

  if (!now) return null;
  const start = first.current ?? now;
  const changed = start.for !== now.for || start.against !== now.against || start.undecided !== now.undecided;

  return (
    <div className="rpg-panel flex w-56 flex-col" data-testid="stance-panel">
      <div
        className="flex items-center justify-between px-3 py-2"
        style={{ background: "#E8D5A3", borderBottom: "2px solid #C4A46C" }}
      >
        <span className="text-[8px] font-pixel uppercase" style={{ color: "#5B3A1E" }}>
          Stance poll
        </span>
        <span className="text-[10px] font-mono tabular-nums" style={{ color: "#8B7355" }}>
          n={now.n}
        </span>
      </div>
      <div className="flex flex-col gap-1.5 px-3 py-2 text-[9px]">
        <Bar poll={now} />
        <Counts poll={now} />
        {changed && (
          <div style={{ color: "#8B7355" }} className="font-mono">
            start (for/undecided/against): {start.for}/{start.undecided}/{start.against}
          </div>
        )}
        <p className="leading-snug" style={{ color: "#A0824A" }}>
          Computed from household cost, ideology and judged impact, then moved by conversations. Not predicted by the model.
        </p>
      </div>
    </div>
  );
}
