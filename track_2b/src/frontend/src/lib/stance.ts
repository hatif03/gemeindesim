import type { BackendNPC } from "@/types/backend";

/** Same thresholds as the backend (graph/nodes/stance.py: stance_label). */
export const STANCE_THRESHOLD = 0.15;

export type StanceLabel = "for" | "against" | "undecided";

export interface StancePoll {
  for: number;
  against: number;
  undecided: number;
  n: number;
}

export function stanceLabel(x: number): StanceLabel {
  if (x > STANCE_THRESHOLD) return "for";
  if (x < -STANCE_THRESHOLD) return "against";
  return "undecided";
}

/** Poll over residents that carry a numeric stance; null when the backend sent none. */
export function stancePoll(npcs: Pick<BackendNPC, "stance">[]): StancePoll | null {
  const withStance = npcs.filter((n) => typeof n.stance === "number");
  if (withStance.length === 0) return null;
  const poll: StancePoll = { for: 0, against: 0, undecided: 0, n: withStance.length };
  for (const n of withStance) poll[stanceLabel(n.stance as number)] += 1;
  return poll;
}
