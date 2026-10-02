"use client";

import type { EconomicReport } from "@/types/backend";

/* ── Stardew Valley palette ─────────────────────────────────────────── */

const TREND_CFG: Record<
  string,
  { arrow: string; color: string; label: string }
> = {
  up: { arrow: "\u25B2", color: "#3E7C34", label: "UP" },
  down: { arrow: "\u25BC", color: "#B83A52", label: "DOWN" },
  flat: { arrow: "\u2500", color: "#5A8DB8", label: "FLAT" },
  mixed: { arrow: "\u25C6", color: "#C97D1A", label: "MIXED" },
};

const DIR_BADGE: Record<
  string,
  { text: string; bg: string; fg: string; border: string }
> = {
  positive: {
    text: "POSITIVE",
    bg: "#E4F2DC",
    fg: "#3E7C34",
    border: "#9FCC90",
  },
  negative: {
    text: "NEGATIVE",
    bg: "#FADED4",
    fg: "#B83A52",
    border: "#DDA0AA",
  },
  mixed: {
    text: "MIXED",
    bg: "#FBF0D1",
    fg: "#9A6C10",
    border: "#D9B95C",
  },
};

const SEV_BADGE: Record<
  string,
  { text: string; bg: string; fg: string; border: string }
> = {
  low: {
    text: "LOW",
    bg: "#EDE4D3",
    fg: "#8B7355",
    border: "#C4A46C",
  },
  medium: {
    text: "MED",
    bg: "#FBF0D1",
    fg: "#9A6C10",
    border: "#D4A520",
  },
  high: {
    text: "HIGH",
    bg: "#FADED4",
    fg: "#B83A52",
    border: "#DDA0AA",
  },
};

const EVENT_COLORS = [
  { color: "#3E7C34", symbol: "\u2605" },
  { color: "#D4A520", symbol: "\u2726" },
  { color: "#5A8DB8", symbol: "\u25C6" },
  { color: "#7B68EE", symbol: "\u25CF" },
];

const PIE_COLORS = [
  "#3E7C34",
  "#D4A520",
  "#D07020",
  "#5A8DB8",
  "#7B68EE",
  "#B83A52",
  "#8B6914",
  "#94A3B8",
];

/* ── Shared inline-style objects ────────────────────────────────────── */

const woodFrame: React.CSSProperties = {
  border: "4px solid #6B4226",
  borderRadius: "8px",
  boxShadow:
    "inset 2px 2px 0 rgba(196,164,108,.55), inset -2px -2px 0 rgba(61,37,16,.35), 6px 6px 0 rgba(61,37,16,.45)",
  background: "#F5E6C8",
};

const innerPanel: React.CSSProperties = {
  border: "2px solid #C4A46C",
  borderRadius: "4px",
  background: "#FDF5E6",
  boxShadow: "inset 1px 1px 2px rgba(61,37,16,.08)",
};

const headerBar: React.CSSProperties = {
  background: "#E8D5A3",
  borderBottom: "2px solid #C4A46C",
};

/* ── Sub-components ─────────────────────────────────────────────────── */

interface EconomicReportModalProps {
  report: EconomicReport | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

function Divider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 py-2">
      <div
        className="h-px flex-1"
        style={{
          background:
            "linear-gradient(to right, transparent, #C4A46C, transparent)",
        }}
      />
      <span
        className="text-[8px] font-pixel uppercase tracking-[0.3em]"
        style={{ color: "#A0824A" }}
      >
        {"\u2726"} {label} {"\u2726"}
      </span>
      <div
        className="h-px flex-1"
        style={{
          background:
            "linear-gradient(to right, transparent, #C4A46C, transparent)",
        }}
      />
    </div>
  );
}

function StatCard({
  label,
  value,
  trend,
}: {
  label: string;
  value: string;
  trend?: "up" | "down" | "flat" | "mixed" | null;
}) {
  const t = TREND_CFG[trend ?? "flat"];
  return (
    <div
      className="rounded p-3"
      style={{
        border: "2px solid #C4A46C",
        borderLeft: `3px solid ${t.color}`,
        background: "#FFF8DC",
        boxShadow: "inset 1px 1px 0 rgba(255,248,220,.5)",
      }}
    >
      <div
        className="text-[8px] font-pixel uppercase tracking-widest"
        style={{ color: "#A0824A" }}
      >
        {label}
      </div>
      <div className="mt-2 text-[16px] font-pixel" style={{ color: t.color }}>
        {value}
      </div>
      <div className="mt-1 flex items-center gap-1.5">
        <span className="text-[10px] font-mono" style={{ color: t.color }}>
          {t.arrow}
        </span>
        <span
          className="text-[8px] font-mono uppercase tracking-[0.25em]"
          style={{ color: `${t.color}88` }}
        >
          {t.label}
        </span>
      </div>
    </div>
  );
}

function PieChart({
  title,
  slices,
}: {
  title: string;
  slices: EconomicReport["pie_chart"]["slices"];
}) {
  const total = slices.reduce((s, sl) => s + sl.value, 0);

  let offset = 0;
  const segments = slices.map((sl, i) => {
    const pct = total > 0 ? (sl.value / total) * 100 : 0;
    const seg = {
      ...sl,
      color: PIE_COLORS[i % PIE_COLORS.length],
      dashArray: `${pct} ${100 - pct}`,
      dashOffset: -offset,
      percent: total > 0 ? Math.round(pct) : 0,
    };
    offset += pct;
    return seg;
  });

  return (
    <div className="rounded p-4" style={innerPanel}>
      <div
        className="text-[9px] font-pixel uppercase tracking-widest"
        style={{ color: "#A0824A" }}
      >
        {title}
      </div>
      <div className="mt-4 flex items-center gap-6">
        <div className="relative h-44 w-44 shrink-0">
          <svg viewBox="0 0 36 36" className="h-full w-full -rotate-90">
            <circle
              cx="18"
              cy="18"
              r="15.915"
              fill="none"
              stroke="#E8D5A3"
              strokeWidth="3.8"
            />
            {segments.map((seg) => (
              <circle
                key={seg.label}
                cx="18"
                cy="18"
                r="15.915"
                fill="none"
                stroke={seg.color}
                strokeWidth="3.8"
                strokeDasharray={seg.dashArray}
                strokeDashoffset={seg.dashOffset}
                pathLength="100"
              />
            ))}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div
              className="text-[8px] font-mono uppercase tracking-[0.3em]"
              style={{ color: "#A0824A" }}
            >
              Total
            </div>
            <div
              className="text-[18px] font-pixel"
              style={{ color: "#3D2510" }}
            >
              {total}
            </div>
          </div>
        </div>

        <div className="flex-1 space-y-2">
          {segments.map((seg) => (
            <div key={seg.label} className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: seg.color }}
              />
              <span
                className="flex-1 text-[10px] font-mono"
                style={{ color: "#6B4C2A" }}
              >
                {seg.label}
              </span>
              <span
                className="text-[10px] font-mono"
                style={{ color: "#A0824A" }}
              >
                {seg.value} ({seg.percent}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function BarChart({
  title,
  bars,
}: {
  title: string;
  bars: EconomicReport["bar_chart"]["bars"];
}) {
  const max = Math.max(...bars.map((b) => b.value), 1);

  return (
    <div className="rounded p-4" style={innerPanel}>
      <div
        className="text-[9px] font-pixel uppercase tracking-widest"
        style={{ color: "#A0824A" }}
      >
        {title}
      </div>
      <div className="mt-4 space-y-3">
        {bars.map((bar) => (
          <div key={bar.label}>
            <div className="mb-1 flex items-center justify-between gap-3">
              <span
                className="text-[10px] font-mono"
                style={{ color: "#6B4C2A" }}
              >
                {bar.label}
              </span>
              <span
                className="text-[10px] font-mono"
                style={{ color: "#A0824A" }}
              >
                {bar.value}
              </span>
            </div>
            <div
              className="h-2.5 overflow-hidden rounded-full"
              style={{ background: "#E8D5A3" }}
            >
              <div
                className="h-full rounded-full"
                style={{
                  width: `${(bar.value / max) * 100}%`,
                  background: "linear-gradient(to right, #3E7C34, #6EC254)",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main modal ─────────────────────────────────────────────────────── */

export function EconomicReportModal({
  report,
  loading,
  error,
  onClose,
}: EconomicReportModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative flex max-h-[88vh] w-[min(1080px,92vw)] flex-col overflow-hidden animate-[modalIn_200ms_ease-out]"
        style={woodFrame}
        data-testid="economic-report-modal"
      >
        {/* ── Header ───────────────────────────────────────────────── */}
        <div
          className="flex items-center justify-between px-5 py-3"
          style={headerBar}
        >
          <div className="text-center flex-1">
            <div
              className="text-[10px] font-pixel uppercase tracking-[0.35em]"
              style={{ color: "#5B3A1E" }}
            >
              {"\u2605"} Economic Report {"\u2605"}
            </div>
            <div
              className="mt-1 text-[8px] font-mono uppercase tracking-widest"
              style={{ color: "#8B7355" }}
            >
              End-of-season summary
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[10px] font-mono uppercase tracking-widest transition-opacity hover:opacity-70"
            style={{ color: "#8B7355" }}
          >
            [{"\u00D7"}]
          </button>
        </div>

        {/* ── Scrollable content ───────────────────────────────────── */}
        <div className="overflow-y-auto px-5 py-5 scrollbar-thin">
          {/* Loading */}
          {loading && (
            <div className="flex min-h-80 flex-col items-center justify-center gap-4">
              <div
                className="text-[32px] animate-bounce"
                style={{ color: "#D4A520" }}
              >
                {"\u2605"}
              </div>
              <div
                className="text-[10px] font-mono uppercase tracking-[0.3em]"
                style={{ color: "#8B7355" }}
              >
                Tallying the harvest report...
              </div>
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div
              className="rounded p-4 text-[10px] font-mono uppercase tracking-widest"
              style={{
                border: "2px solid #B83A52",
                background: "#FADED4",
                color: "#B83A52",
              }}
            >
              {error}
            </div>
          )}

          {/* Report body */}
          {!loading && !error && report && (
            <div className="space-y-5">
              {/* ── Headline ─────────────────────────────────────── */}
              <div
                className="relative overflow-hidden rounded-md p-5"
                style={{
                  border: "3px solid #A0824A",
                  background:
                    "linear-gradient(180deg, #E8D5A3 0%, #F5E6C8 100%)",
                  boxShadow:
                    "inset 1px 1px 0 rgba(255,248,220,.7), inset -1px -1px 0 rgba(139,105,20,.15)",
                }}
              >
                {/* Gold accent stripe */}
                <div
                  className="absolute inset-x-0 top-0 h-[3px]"
                  style={{
                    background:
                      "linear-gradient(to right, #D4A520, #E8B84B, #D4A520)",
                  }}
                />
                <div
                  className="text-[8px] font-pixel uppercase tracking-[0.3em] mb-2"
                  style={{ color: "#A0824A" }}
                >
                  {"\u2605"} Season Report {"\u2605"}
                </div>
                <div
                  className="text-[16px] font-pixel uppercase tracking-wide leading-relaxed"
                  style={{ color: "#3D2510" }}
                >
                  {report.headline}
                </div>
                <p
                  className="mt-3 max-w-4xl text-[12px] font-mono leading-6"
                  style={{ color: "#6B4C2A" }}
                >
                  {report.summary}
                </p>
              </div>

              <Divider label="Analysis" />

              {/* ── Livelihood ────────────────────────────────────── */}
              <div className="rounded p-5" style={innerPanel}>
                <div
                  className="text-[9px] font-pixel uppercase tracking-widest"
                  style={{ color: "#A0824A" }}
                >
                  Livelihood Impact
                </div>
                <p
                  className="mt-3 text-[12px] font-mono leading-6"
                  style={{ color: "#6B4C2A" }}
                >
                  {report.livelihood_impact}
                </p>
              </div>

              {/* ── Stats 4×2 grid ───────────────────────────────── */}
              <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
                {report.key_stats.map((s) => (
                  <StatCard
                    key={s.label}
                    label={s.label}
                    value={s.value}
                    trend={s.trend}
                  />
                ))}
              </div>

              <Divider label="Data" />

              {/* ── Charts ───────────────────────────────────────── */}
              <div className="grid gap-5 lg:grid-cols-2">
                <PieChart
                  title={report.pie_chart.title}
                  slices={report.pie_chart.slices}
                />
                <BarChart
                  title={report.bar_chart.title}
                  bars={report.bar_chart.bars}
                />
              </div>

              <Divider label="Details" />

              {/* ── Impacts + Events ─────────────────────────────── */}
              <div className="grid gap-5 lg:grid-cols-2">
                {/* Top Impacts */}
                <div className="rounded p-5" style={innerPanel}>
                  <div
                    className="text-[9px] font-pixel uppercase tracking-widest"
                    style={{ color: "#A0824A" }}
                  >
                    Top Impacts
                  </div>
                  <div className="mt-4 space-y-4">
                    {report.top_impacts.map((imp) => {
                      const dir = DIR_BADGE[imp.direction] ?? DIR_BADGE.mixed;
                      const sev = SEV_BADGE[imp.severity] ?? SEV_BADGE.medium;
                      const accent =
                        imp.direction === "positive"
                          ? "#3E7C34"
                          : imp.direction === "negative"
                            ? "#B83A52"
                            : "#C97D1A";
                      return (
                        <div
                          key={`${imp.title}-${imp.direction}`}
                          className="pl-3"
                          style={{ borderLeft: `3px solid ${accent}` }}
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <div
                              className="text-[11px] font-pixel uppercase tracking-wide"
                              style={{ color: "#3D2510" }}
                            >
                              {imp.title}
                            </div>
                            <span
                              className="rounded px-1.5 py-0.5 text-[7px] font-mono uppercase tracking-widest"
                              style={{
                                background: dir.bg,
                                color: dir.fg,
                                border: `1px solid ${dir.border}`,
                              }}
                            >
                              {dir.text}
                            </span>
                            <span
                              className="rounded px-1.5 py-0.5 text-[7px] font-mono uppercase tracking-widest"
                              style={{
                                background: sev.bg,
                                color: sev.fg,
                                border: `1px solid ${sev.border}`,
                              }}
                            >
                              {sev.text}
                            </span>
                          </div>
                          <p
                            className="mt-2 text-[11px] font-mono leading-5"
                            style={{ color: "#6B4C2A" }}
                          >
                            {imp.description}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Notable Events */}
                <div className="rounded p-5" style={innerPanel}>
                  <div
                    className="text-[9px] font-pixel uppercase tracking-widest"
                    style={{ color: "#A0824A" }}
                  >
                    Notable Events
                  </div>
                  <div className="mt-4 space-y-3">
                    {report.notable_events.map((ev, i) => {
                      const accent = EVENT_COLORS[i % EVENT_COLORS.length];
                      return (
                        <div
                          key={`${ev}-${i}`}
                          className="flex items-start gap-2 rounded px-3 py-2"
                          style={{
                            border: "1px solid #E8D5A3",
                            borderLeft: `3px solid ${accent.color}`,
                            background: "#FFF8DC",
                          }}
                        >
                          <span
                            className="mt-0.5 text-[10px] font-mono"
                            style={{ color: accent.color }}
                          >
                            {accent.symbol}
                          </span>
                          <span
                            className="text-[11px] font-mono leading-5"
                            style={{ color: "#6B4C2A" }}
                          >
                            {ev}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── Footer ───────────────────────────────────────────────── */}
        <div
          className="flex items-center justify-between px-5 py-2"
          style={{
            background: "#E8D5A3",
            borderTop: "2px solid #C4A46C",
          }}
        >
          <span
            className="text-[8px] font-mono uppercase tracking-widest"
            style={{ color: "#8B7355" }}
          >
            {"\u2605"} Linden Economic Bureau {"\u2605"}
          </span>
          <span
            className="text-[8px] font-mono uppercase"
            style={{ color: "#A0824A" }}
          >
            Press ESC to close
          </span>
        </div>
      </div>
    </div>
  );
}
