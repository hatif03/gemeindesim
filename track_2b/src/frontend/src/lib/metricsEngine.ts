// Client-side metrics computation from backend NPC/event data

import type { SimMetrics } from "@/types";
import type { BackendNPC, BackendSimEvent } from "@/types/backend";
import { CLOSURE_RE, LAYOFF_RE } from "./adapter";

const MOOD_SCORES: Record<string, number> = {
  angry: 0.1,
  anxious: 0.25,
  worried: 0.4,
  neutral: 0.55,
  hopeful: 0.75,
  excited: 0.9,
};

/** Running accumulators — updated incrementally per round, not rescanned. */
export interface MetricsAccumulator {
  eggIndex: number;
  priceIndex: number;
  closureCount: number;
  layoffCount: number;
}

export function createAccumulator(): MetricsAccumulator {
  return { eggIndex: 1.0, priceIndex: 0, closureCount: 0, layoffCount: 0 };
}

/**
 * Update accumulator with only the NEW events from this round, then
 * compute full metrics from accumulator + current NPC state.
 */
export function updateMetrics(
  acc: MetricsAccumulator,
  npcs: BackendNPC[],
  newEvents: BackendSimEvent[],
): Partial<SimMetrics> {
  const total = npcs.length || 1;

  // Incrementally update accumulators with this round's events only
  for (const e of newEvents) {
    if (e.event_type === "price_change") {
      const pctChange = Number(e.data.pct_change);
      if (Number.isFinite(pctChange)) {
        acc.priceIndex += pctChange;
      } else {
        const oldPrice = Number(e.data.old_price);
        const newPrice = Number(e.data.new_price);
        if (
          Number.isFinite(oldPrice) &&
          oldPrice !== 0 &&
          Number.isFinite(newPrice)
        ) {
          acc.priceIndex += ((newPrice - oldPrice) / oldPrice) * 100;
        }
      }
    }
    if (e.event_type === "chat") {
      const npc = npcs.find((n) => n.id === e.npc_id);
      if (
        npc &&
        (npc.role === "business_owner" || npc.role === "shopkeeper") &&
        CLOSURE_RE.test(e.message)
      ) {
        acc.closureCount++;
      }
      if (LAYOFF_RE.test(e.message)) {
        acc.layoffCount++;
      }
    }
  }

  // Derive metrics from current NPC state + accumulators
  let unrestCount = 0;
  let moodSum = 0;
  for (const npc of npcs) {
    if (npc.mood === "angry" || npc.mood === "anxious") unrestCount++;
    moodSum += MOOD_SCORES[npc.mood] ?? 0.55;
  }

  return {
    eggIndex: Math.max(0.5, Math.min(2.0, 1.0 + acc.priceIndex / 100)),
    priceIndex: Math.max(-50, Math.min(50, acc.priceIndex)),
    unemploymentRate: Math.min(15, 4.2 + acc.layoffCount * 0.4),
    socialUnrest: unrestCount / total,
    businessSurvival: Math.max(0, 0.95 - acc.closureCount * 0.03),
    govApproval: moodSum / total,
    interestRate:
      Math.round((5.25 + (Math.abs(acc.priceIndex) / 50) * 2) * 100) / 100,
  };
}
