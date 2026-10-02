"use client";

import {
  BankIcon,
  CoinIcon,
  CrownIcon,
  EggIcon,
  FistIcon,
  ShopIcon,
  WorkerIcon,
} from "@/components/dashboard/PixelStatBar";
import type { SimMetrics } from "@/types";

interface StatsLegendProps {
  metrics: SimMetrics;
  phase: number;
  month: number;
}

type Severity = "good" | "warn" | "bad" | "neutral";

const SEVERITY_COLOR: Record<Severity, string> = {
  good: "#3E7C34",
  warn: "#C97D1A",
  bad: "#B83A52",
  neutral: "#5A8DB8",
};

function eggSeverity(v: number): Severity {
  if (v < 1.5) return "good";
  if (v < 3.0) return "warn";
  return "bad";
}

function priceSeverity(v: number): Severity {
  const abs = Math.abs(v);
  if (abs < 3) return "good";
  if (abs < 7) return "warn";
  return "bad";
}

function unempSeverity(v: number): Severity {
  if (v < 4.5) return "good";
  if (v < 5.5) return "warn";
  return "bad";
}

function zeroOneSeverity(v: number, invert = false): Severity {
  const effective = invert ? 1 - v : v;
  if (effective > 0.7) return "good";
  if (effective > 0.4) return "warn";
  return "bad";
}

interface StatItemProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  severity: Severity;
}

function StatItem({ icon, label, value, severity }: StatItemProps) {
  const color = SEVERITY_COLOR[severity];
  return (
    <div className="flex items-center gap-0.5">
      <span className="shrink-0 flex items-center" style={{ width: 12, height: 12 }}>
        {icon}
      </span>
      <span
        className="text-[6px] font-mono uppercase tracking-tight truncate"
        style={{ color: "#8B7355", minWidth: 0, width: 32 }}
      >
        {label}
      </span>
      <span
        className="text-[7px] font-mono font-bold tabular-nums shrink-0"
        style={{ color }}
      >
        {value}
      </span>
    </div>
  );
}

export function StatsLegend({ metrics, phase, month }: StatsLegendProps) {
  return (
    <div
      className="rpg-panel flex flex-col gap-0.5 p-1.5"
      style={{
        background: "rgba(232, 213, 163, 0.92)",
        width: 130,
      }}
    >
      {/* Phase and Month header */}
      <div
        className="flex items-center justify-between mb-0.5 pb-0.5"
        style={{ borderBottom: "1px solid #C4A46C" }}
      >
        <span
          className="text-[6px] font-pixel uppercase"
          style={{ color: "#5B3A1E" }}
        >
          P{phase || "-"}
        </span>
        <span
          className="text-[6px] font-mono uppercase tracking-widest tabular-nums"
          style={{ color: "#8B7355" }}
        >
          M{month || "-"}
        </span>
      </div>

      {/* Stats */}
      <StatItem
        icon={<EggIcon />}
        label="EGG"
        value={`$${metrics.eggIndex.toFixed(2)}`}
        severity={eggSeverity(metrics.eggIndex)}
      />
      <StatItem
        icon={<CoinIcon />}
        label="PRC"
        value={`${metrics.priceIndex >= 0 ? "+" : ""}${metrics.priceIndex.toFixed(1)}%`}
        severity={priceSeverity(metrics.priceIndex)}
      />
      <StatItem
        icon={<WorkerIcon />}
        label="UNE"
        value={`${metrics.unemploymentRate.toFixed(1)}%`}
        severity={unempSeverity(metrics.unemploymentRate)}
      />
      <StatItem
        icon={<BankIcon />}
        label="INT"
        value={`${metrics.interestRate.toFixed(2)}%`}
        severity="neutral"
      />
      <StatItem
        icon={<FistIcon />}
        label="UNR"
        value={`${(metrics.socialUnrest * 100).toFixed(0)}%`}
        severity={zeroOneSeverity(metrics.socialUnrest, true)}
      />
      <StatItem
        icon={<ShopIcon />}
        label="BIZ"
        value={`${(metrics.businessSurvival * 100).toFixed(0)}%`}
        severity={zeroOneSeverity(metrics.businessSurvival)}
      />
      <StatItem
        icon={<CrownIcon />}
        label="GOV"
        value={`${(metrics.govApproval * 100).toFixed(0)}%`}
        severity={zeroOneSeverity(metrics.govApproval)}
      />
    </div>
  );
}
