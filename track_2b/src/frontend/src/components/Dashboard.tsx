"use client";

import {
  BankIcon,
  CoinIcon,
  CrownIcon,
  EggIcon,
  FistIcon,
  PixelStatBar,
  ShopIcon,
  WorkerIcon,
} from "@/components/dashboard/PixelStatBar";
import type { SimMetrics } from "@/types";

interface DashboardProps {
  metrics: SimMetrics;
  metricsHistory: SimMetrics[];
  phase: number;
  round: number;
  maxRounds: number;
}

/* ─── Severity helpers ─── */

function priceSeverity(v: number) {
  const abs = Math.abs(v);
  if (abs < 3) return "good" as const;
  if (abs < 7) return "warn" as const;
  return "bad" as const;
}

function unempSeverity(v: number) {
  if (v < 4.5) return "good" as const;
  if (v < 5.5) return "warn" as const;
  return "bad" as const;
}

function zeroOneSeverity(v: number, invert = false) {
  const effective = invert ? 1 - v : v;
  if (effective > 0.7) return "good" as const;
  if (effective > 0.4) return "warn" as const;
  return "bad" as const;
}

function eggSeverity(v: number) {
  if (v < 1.5) return "good" as const;
  if (v < 3.0) return "warn" as const;
  return "bad" as const;
}

/* ─── Fill ratio normalization ─── */

function normalizePrices(v: number): number {
  return Math.min(1, Math.abs(v) / 10);
}

function normalizeUnemployment(v: number): number {
  return Math.max(0, Math.min(1, (v - 3) / 7));
}

function normalizeInterestRate(v: number): number {
  return Math.max(0, Math.min(1, (v - 3) / 5));
}

function normalizeEggIndex(v: number): number {
  return Math.max(0, Math.min(1, (v - 0.5) / 4.5));
}

/* ─── Trend computation ─── */

function computeTrend(
  history: SimMetrics[],
  getter: (m: SimMetrics) => number,
): "up" | "down" | null {
  if (history.length < 2) return null;
  const prev = getter(history[history.length - 2]);
  const curr = getter(history[history.length - 1]);
  const diff = curr - prev;
  if (Math.abs(diff) < 0.001) return null;
  return diff > 0 ? "up" : "down";
}

export function Dashboard({
  metrics,
  metricsHistory,
  phase,
  round,
  maxRounds,
}: DashboardProps) {
  return (
    <div
      className="rpg-panel flex w-56 flex-col"
      data-testid="dashboard"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2"
        style={{ background: "#E8D5A3", borderBottom: "2px solid #C4A46C" }}
      >
        <span
          className="text-[8px] font-pixel uppercase"
          style={{ color: "#5B3A1E" }}
        >
          Phase {phase || "-"}
        </span>
        <span
          className="text-[10px] font-mono tabular-nums uppercase tracking-widest"
          style={{ color: "#8B7355" }}
        >
          Round {round}/{maxRounds}
        </span>
      </div>

      {/* Stats */}
      <div className="flex flex-col px-1 py-1">
        <PixelStatBar
          icon={<EggIcon />}
          label="Egg Index"
          value={metrics.eggIndex}
          formatValue={(v) => `$${v.toFixed(2)}`}
          severity={eggSeverity(metrics.eggIndex)}
          fillRatio={normalizeEggIndex(metrics.eggIndex)}
          trend={computeTrend(metricsHistory, (m) => m.eggIndex)}
        />
        <PixelStatBar
          icon={<CoinIcon />}
          label="Prices"
          value={metrics.priceIndex}
          formatValue={(v) => `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`}
          severity={priceSeverity(metrics.priceIndex)}
          fillRatio={normalizePrices(metrics.priceIndex)}
          trend={computeTrend(metricsHistory, (m) => m.priceIndex)}
        />
        <PixelStatBar
          icon={<WorkerIcon />}
          label="Unemployment"
          value={metrics.unemploymentRate}
          formatValue={(v) => `${v.toFixed(1)}%`}
          severity={unempSeverity(metrics.unemploymentRate)}
          fillRatio={normalizeUnemployment(metrics.unemploymentRate)}
          trend={computeTrend(metricsHistory, (m) => m.unemploymentRate)}
        />
        <PixelStatBar
          icon={<BankIcon />}
          label="Interest Rate"
          value={metrics.interestRate}
          formatValue={(v) => `${v.toFixed(2)}%`}
          severity={"neutral"}
          fillRatio={normalizeInterestRate(metrics.interestRate)}
          trend={computeTrend(metricsHistory, (m) => m.interestRate)}
        />
        <PixelStatBar
          icon={<FistIcon />}
          label="Social Unrest"
          value={metrics.socialUnrest}
          formatValue={(v) => `${(v * 100).toFixed(0)}%`}
          severity={zeroOneSeverity(metrics.socialUnrest, true)}
          fillRatio={metrics.socialUnrest}
          trend={computeTrend(metricsHistory, (m) => m.socialUnrest)}
        />
        <PixelStatBar
          icon={<ShopIcon />}
          label="Businesses Open"
          value={metrics.businessSurvival}
          formatValue={(v) => `${(v * 100).toFixed(0)}%`}
          severity={zeroOneSeverity(metrics.businessSurvival)}
          fillRatio={metrics.businessSurvival}
          trend={computeTrend(metricsHistory, (m) => m.businessSurvival)}
        />
        <PixelStatBar
          icon={<CrownIcon />}
          label="Gov. Approval"
          value={metrics.govApproval}
          formatValue={(v) => `${(v * 100).toFixed(0)}%`}
          severity={zeroOneSeverity(metrics.govApproval)}
          fillRatio={metrics.govApproval}
          trend={computeTrend(metricsHistory, (m) => m.govApproval)}
        />
      </div>
    </div>
  );
}
