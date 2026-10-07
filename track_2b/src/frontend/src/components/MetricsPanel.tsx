"use client";

import { useState } from "react";
import type { RunMetrics } from "@/types/backend";

interface MetricsPanelProps {
  metrics: RunMetrics | null;
}

const fmt = (n: number) => n.toLocaleString("en-US");
const pct = (x: number) => `${(100 * x).toFixed(x < 0.01 ? 2 : 1)} %`;

function Row({ label, value, testId }: { label: string; value: string; testId?: string }) {
  return (
    <div className="flex justify-between gap-3" data-testid={testId}>
      <span style={{ color: "#8B7355" }}>{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}

/**
 * What the run cost: tokens in and out, how much of the prompt the endpoint served from its cache, call latency and how much of the
 * context window one prompt uses. Numbers come from the endpoint's own `usage` field, counted in code; nothing is estimated.
 */
export function MetricsPanel({ metrics }: MetricsPanelProps) {
  const [open, setOpen] = useState(false); // collapsed by default: three panels would crowd the map
  if (!metrics || metrics.calls === 0) return null;
  const trouble = metrics.rate_limited + metrics.gateway_retries + metrics.downgraded + metrics.failed;
  return (
    <div className="rpg-panel flex w-56 flex-col" data-testid="metrics-panel">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex items-center justify-between px-3 py-2 text-left"
        style={{ background: "#E8D5A3", borderBottom: open ? "2px solid #C4A46C" : "none" }}
      >
        <span className="text-[8px] font-pixel uppercase" style={{ color: "#5B3A1E" }}>
          Run metrics {open ? "[-]" : "[+]"}
        </span>
        <span className="text-[10px] font-mono tabular-nums" style={{ color: "#8B7355" }}>
          {fmt(metrics.prompt_tokens + metrics.completion_tokens)} tok
        </span>
      </button>
      {open && (
      <div className="flex flex-col gap-1 px-3 py-2 text-[9px] font-mono" style={{ color: "#3D2510" }}>
        <Row label="tokens in" value={fmt(metrics.prompt_tokens)} testId="metrics-in" />
        <Row label="tokens out" value={fmt(metrics.completion_tokens)} testId="metrics-out" />
        <Row label="cached" value={pct(metrics.cache_hit_rate)} />
        <Row label="mean prompt" value={`${fmt(metrics.mean_prompt_tokens)} tok`} />
        <Row label="context use (max)" value={`${pct(metrics.max_context_use)} of ${fmt(Math.round(metrics.context_window / 1000))}k`} testId="metrics-context" />
        <Row label="latency mean / p95" value={`${metrics.mean_latency_s.toFixed(1)} / ${metrics.p95_latency_s.toFixed(1)} s`} />
        <Row label="decode speed" value={`${Math.round(metrics.decode_tokens_per_s)} tok/s`} />
        {metrics.in_flight_limit !== null && <Row label="in flight (limit)" value={String(Math.floor(metrics.in_flight_limit))} />}
        <Row label="retries 429 / 5xx" value={`${metrics.rate_limited} / ${metrics.gateway_retries}`} />
        {trouble > 0 && metrics.downgraded + metrics.failed > 0 && (
          <Row label="downgraded / failed" value={`${metrics.downgraded} / ${metrics.failed}`} />
        )}
        <p className="mt-1 leading-snug" style={{ color: "#A0824A" }}>
          {metrics.model} @ {metrics.endpoint || "endpoint"}. Counted from the usage field the endpoint returns.
        </p>
      </div>
      )}
    </div>
  );
}
