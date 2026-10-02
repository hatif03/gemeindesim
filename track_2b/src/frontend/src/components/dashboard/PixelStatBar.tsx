"use client";

import { useAnimatedValue } from "@/hooks/useAnimatedValue";

type Severity = "good" | "warn" | "bad" | "neutral";

const SEVERITY_HEX: Record<Severity, string> = {
  good: "#3E7C34",
  warn: "#C97D1A",
  bad: "#B83A52",
  neutral: "#5A8DB8",
};

const EMPTY_BG = "#E8D5A3";

/* ─── Pixel Icon renderer ─── */

function buildPixels(grid: string[], colors: Record<string, string>) {
  const rects: { x: number; y: number; fill: string; key: string }[] = [];
  for (let y = 0; y < grid.length; y++) {
    const row = grid[y];
    for (let x = 0; x < row.length; x++) {
      const ch = row[x];
      if (ch !== "." && colors[ch]) {
        rects.push({ x, y, fill: colors[ch], key: `p${y}x${x}` });
      }
    }
  }
  return rects;
}

function PixelIcon({
  grid,
  colors,
}: {
  grid: string[];
  colors: Record<string, string>;
}) {
  const pixels = buildPixels(grid, colors);
  return (
    <svg
      width={16}
      height={16}
      viewBox="0 0 16 16"
      className="pixel-crisp"
      shapeRendering="crispEdges"
      role="img"
      aria-hidden="true"
    >
      {pixels.map((p) => (
        <rect key={p.key} x={p.x} y={p.y} width={1} height={1} fill={p.fill} />
      ))}
    </svg>
  );
}

/* ─── Icon grids (16×16) ─── */

const COIN_COLORS: Record<string, string> = {
  "1": "#6B4226",
  "2": "#D4A520",
  "3": "#F5E6C8",
};
const COIN_GRID = [
  "......1111......",
  "....11222211....",
  "...1223322221...",
  "..122222222221..",
  ".12222211222221.",
  ".12222122222221.",
  "1222221.1222221.",
  "1222221.1222221.",
  "1222221.1222221.",
  "1222221.1222221.",
  ".12222122222221.",
  ".12222211222221.",
  "..122222222221..",
  "...1222222221...",
  "....11222211....",
  "......1111......",
];

const WORKER_COLORS: Record<string, string> = {
  "1": "#6B4226",
  "2": "#A0824A",
  "3": "#D4A520",
};
const WORKER_GRID = [
  "......1111......",
  ".....122221.....",
  ".....122221.....",
  ".....122221.....",
  "......1221......",
  ".....112211.....",
  "....12222221....",
  "...1222332221...",
  "...1222222221...",
  "....12222221....",
  ".....122221.....",
  ".....122221.....",
  ".....12..21.....",
  "....12...121....",
  "....12...121....",
  "...112...1121...",
];

const BANK_COLORS: Record<string, string> = {
  "1": "#3D2510",
  "2": "#5A8DB8",
  "3": "#8BAFD0",
};
const BANK_GRID = [
  ".......33.......",
  "......1331......",
  ".....132231.....",
  "....13222231....",
  "...1322222231...",
  "..111111111111..",
  "...12..12..21...",
  "...12..12..21...",
  "...12..12..21...",
  "...12..12..21...",
  "...12..12..21...",
  "...12..12..21...",
  "..111111111111..",
  "..122222222221..",
  "..111111111111..",
  "................",
];

const FIST_COLORS: Record<string, string> = {
  "1": "#6B4226",
  "2": "#B83A52",
  "3": "#D06070",
};
const FIST_GRID = [
  "................",
  ".....11.11.11...",
  "....1231231231..",
  "....1232232231..",
  ".11.1222222231..",
  "12312222222221..",
  "12322222222221..",
  "12222222222221..",
  ".1222222222221..",
  ".1222222222221..",
  "..122222222221..",
  "..122222222221..",
  "...1222222221...",
  "...1222222221...",
  "....12222221....",
  ".....111111.....",
];

const SHOP_COLORS: Record<string, string> = {
  "1": "#6B4226",
  "2": "#3E7C34",
  "3": "#5EA04E",
  "4": "#A0824A",
};
const SHOP_GRID = [
  "................",
  "...1111111111...",
  "..123232323211..",
  "..132323232311..",
  ".11111111111111.",
  ".12222222222221.",
  ".12222222222221.",
  ".12222222222221.",
  ".12211112222221.",
  ".12214412222221.",
  ".12214412222221.",
  ".12214412222221.",
  ".12211112222221.",
  ".12222222222221.",
  ".11111111111111.",
  "................",
];

const CROWN_COLORS: Record<string, string> = {
  "1": "#6B4226",
  "2": "#D4A520",
  "3": "#F5E6C8",
  "4": "#B83A52",
};
const CROWN_GRID = [
  "................",
  "..1....1....1...",
  "..12...12..12...",
  "..121..12..121..",
  "..1221.12.1221..",
  ".12222121222221.",
  ".12222212222221.",
  ".12224222242221.",
  ".12222222222221.",
  ".12222222222221.",
  "..122222222221..",
  "..133333333331..",
  "..122222222221..",
  "..111111111111..",
  "................",
  "................",
];

const EGG_COLORS: Record<string, string> = {
  "1": "#6B4226",
  "2": "#F5E6C8",
  "3": "#E8D5A3",
};
const EGG_GRID = [
  "................",
  "................",
  "......1111......",
  ".....122221.....",
  "....12222221....",
  "...1222222221...",
  "...1222222221...",
  "..122222222221..",
  "..122233332221..",
  "..122222222221..",
  "..122222222221..",
  "...1222222221...",
  "...1222222221...",
  "....12222221....",
  ".....122221.....",
  "......1111......",
];

/* ─── Exported icon components ─── */

export function CoinIcon() {
  return <PixelIcon grid={COIN_GRID} colors={COIN_COLORS} />;
}
export function WorkerIcon() {
  return <PixelIcon grid={WORKER_GRID} colors={WORKER_COLORS} />;
}
export function BankIcon() {
  return <PixelIcon grid={BANK_GRID} colors={BANK_COLORS} />;
}
export function FistIcon() {
  return <PixelIcon grid={FIST_GRID} colors={FIST_COLORS} />;
}
export function ShopIcon() {
  return <PixelIcon grid={SHOP_GRID} colors={SHOP_COLORS} />;
}
export function CrownIcon() {
  return <PixelIcon grid={CROWN_GRID} colors={CROWN_COLORS} />;
}
export function EggIcon() {
  return <PixelIcon grid={EGG_GRID} colors={EGG_COLORS} />;
}

const SEGMENT_KEYS = Array.from({ length: 20 }, (_, i) => `seg-${i}`);

/* ─── PixelStatBar ─── */

interface PixelStatBarProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  formatValue: (v: number) => string;
  severity: Severity;
  fillRatio: number;
  segments?: number;
  trend?: "up" | "down" | null;
}

export function PixelStatBar({
  icon,
  label,
  value,
  formatValue,
  severity,
  fillRatio,
  segments = 12,
  trend = null,
}: PixelStatBarProps) {
  const animatedRatio = useAnimatedValue(Math.max(0, Math.min(1, fillRatio)));
  const filledCount = Math.round(animatedRatio * segments);
  const color = SEVERITY_HEX[severity];

  return (
    <div
      className="px-2 py-1.5 last:border-b-0"
      style={{ borderBottom: "1px solid #E8D5A3" }}
    >
      {/* Label row */}
      <div className="flex items-center gap-1.5 mb-1">
        <span className="shrink-0 flex items-center">{icon}</span>
        <span
          className="flex-1 text-[9px] font-mono uppercase tracking-widest truncate"
          style={{ color: "#8B7355" }}
        >
          {label}
        </span>
        {trend && (
          <span className="text-[7px] leading-none" style={{ color }}>
            {trend === "up" ? "\u25B2" : "\u25BC"}
          </span>
        )}
        <span
          className="text-[11px] font-mono font-bold tabular-nums shrink-0"
          style={{ color }}
        >
          {formatValue(value)}
        </span>
      </div>

      {/* Segmented bar */}
      <div
        className="flex gap-[1px]"
        role="progressbar"
        aria-valuenow={Math.round(fillRatio * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        {SEGMENT_KEYS.slice(0, segments).map((key, i) => {
          const filled = i < filledCount;
          return (
            <div
              key={key}
              className={
                severity === "bad" && filled
                  ? "pixel-bar-segment-bad"
                  : undefined
              }
              style={{
                flex: 1,
                height: 6,
                background: filled ? color : EMPTY_BG,
                boxShadow: filled
                  ? "inset 0 -1px 0 rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.2)"
                  : "inset 0 1px 0 rgba(255,255,255,0.4), inset 0 -1px 0 rgba(0,0,0,0.05)",
                transition: "background 300ms",
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
