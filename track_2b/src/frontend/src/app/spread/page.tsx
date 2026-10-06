"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { type EnsembleRun, type EnsembleStatus, fetchEnsemble } from "@/services/wsClient";

const FOR = "#3E7C34";
const AGAINST = "#B83A52";
const UNDECIDED = "#A89A78";

function Bar({ t }: { t: EnsembleRun["initial"] }) {
  const n = t.n || 1;
  return (
    <div className="flex h-4 w-full overflow-hidden" style={{ border: "1px solid #C4A46C", background: "#E8D5A3" }} role="img"
      aria-label={`For ${t.for}, undecided ${t.undecided}, against ${t.against}`}>
      <div style={{ width: `${(100 * t.for) / n}%`, background: FOR }} />
      <div style={{ width: `${(100 * t.undecided) / n}%`, background: UNDECIDED }} />
      <div style={{ width: `${(100 * t.against) / n}%`, background: AGAINST }} />
    </div>
  );
}

const pct = (x: number) => `${Math.round(100 * x)} %`;

function SpreadView() {
  const id = useSearchParams().get("id");
  const [data, setData] = useState<EnsembleStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let stop = false;
    const tick = async () => {
      try {
        const d = await fetchEnsemble(id);
        if (stop) return;
        setData(d);
        if (d.status === "running") setTimeout(tick, 2500);
      } catch (e) {
        if (!stop) setError(e instanceof Error ? e.message : String(e));
      }
    };
    tick();
    return () => {
      stop = true;
    };
  }, [id]);

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-4 p-6" style={{ background: "#FDF5E6", color: "#3D2510" }}>
      <Link href="/" className="text-[10px] font-mono uppercase" style={{ color: "#8B7355" }}>
        {"<"} back to the editor
      </Link>
      <h1 className="text-[12px] font-pixel uppercase">Spread of the stance poll</h1>
      <p className="text-[11px] font-mono leading-relaxed">
        The same vote, run several times with fresh residents. One run is an anecdote; the range across runs is the honest summary.
      </p>
      {!id && <p className="text-[11px] font-mono">No run id given.</p>}
      {error && <p className="text-[11px] font-mono" style={{ color: AGAINST }}>{error}</p>}
      {data && (
        <>
          <p className="text-[11px] font-mono" data-testid="spread-progress">
            {data.completed}/{data.total} runs finished{data.status === "running" ? "..." : ""}
          </p>
          <div className="rpg-panel flex flex-col gap-3 p-4">
            <div className="grid grid-cols-[5rem_1fr_1fr] items-center gap-3 text-[10px] font-mono uppercase" style={{ color: "#8B7355" }}>
              <span>run</span>
              <span>start</span>
              <span>end</span>
            </div>
            {data.runs.map((r, i) => (
              <div key={`${i}-${r.events}-${r.final.mean}`} className="grid grid-cols-[5rem_1fr_1fr] items-center gap-3 text-[10px] font-mono">
                <span>
                  #{i + 1} <span style={{ color: "#8B7355" }}>({r.final.for}/{r.final.undecided}/{r.final.against})</span>
                </span>
                <Bar t={r.initial} />
                <Bar t={r.final} />
              </div>
            ))}
            <p className="text-[9px] font-mono" style={{ color: "#8B7355" }}>
              Bars: <span style={{ color: FOR }}>for</span> / <span style={{ color: "#7A6A48" }}>undecided</span> / <span style={{ color: AGAINST }}>against</span>. Counts: for/undecided/against at the end.
            </p>
          </div>
          {data.summary && (
            <div className="rpg-panel p-4 text-[11px] font-mono leading-relaxed" data-testid="spread-summary">
              Share <b style={{ color: FOR }}>for</b> at the end: mean {pct(data.summary.share_for.mean)}, range {pct(data.summary.share_for.min)} to{" "}
              {pct(data.summary.share_for.max)}.<br />
              Share <b style={{ color: AGAINST }}>against</b>: mean {pct(data.summary.share_against.mean)}, range {pct(data.summary.share_against.min)} to{" "}
              {pct(data.summary.share_against.max)}.<br />
              Mean stance: {data.summary.mean_stance.mean.toFixed(2)} (range {data.summary.mean_stance.min.toFixed(2)} to {data.summary.mean_stance.max.toFixed(2)}).
              <br />
              <span style={{ color: "#8B7355" }}>A what-if comparison, not a forecast: the stance weights are not calibrated.</span>
            </div>
          )}
          {data.errors.length > 0 && (
            <p className="text-[10px] font-mono" style={{ color: AGAINST }}>
              {data.errors.join(" | ")}
            </p>
          )}
        </>
      )}
    </main>
  );
}

export default function SpreadPage() {
  return (
    <Suspense fallback={null}>
      <SpreadView />
    </Suspense>
  );
}
