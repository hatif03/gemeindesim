"""Headless, fully instrumented run of the real GemeindeSim pipeline.

Usage: uv run --project src/backend python research/run_sim.py TAG [--seed 1] [--npcs 5]
         [--rounds 3] [--model apertus-v1.5-70b] [--sample linden|millfield]
Every LLM call goes to results/sims/TAG.calls.jsonl, final state to TAG.json.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import time

from common import RESULTS, read_sample

SIMS = RESULTS / "sims"
SIMS.mkdir(exist_ok=True)


_T0 = time.perf_counter()  # call timeline origin (research E29: how much of the wall time is Python?)


def install_call_logger(path):
    import graph.llm as L
    orig = L._ainvoke

    async def logged(llm, prompt, **kw):
        t0 = time.perf_counter()
        err = None
        resp = None
        try:
            resp = await orig(llm, prompt, **kw)
            return resp
        except Exception as exc:  # noqa: BLE001
            err = repr(exc)
            raise
        finally:
            rec = {"model": getattr(llm, "model_name", "?"), "prompt": prompt,
                   "latency_s": round(time.perf_counter() - t0, 3), "t_start": round(t0 - _T0, 3), "t_end": round(time.perf_counter() - _T0, 3), "error": err,
                   "content": getattr(resp, "content", None),
                   "usage": (getattr(resp, "usage_metadata", None) or {})}
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    L._ainvoke = logged


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--npcs", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--model", default="apertus-v1.5-70b")
    ap.add_argument("--sample", default="linden")
    ap.add_argument("--swarm", action="store_true", help="use the swarm graph (the Docker default: SWARM=true)")
    ap.add_argument("--corpus", default="original", choices=["original", "balanced"])
    ap.add_argument("--recommendation", default="none", choices=["none", "yes", "no"],
                    help="replace the 'no recommendation' line by an official recommendation (compare-conditions, research E19)")
    ap.add_argument("--objective", default="How the Steuerfuss and school credit land on households and shops")
    args = ap.parse_args()

    random.seed(args.seed)
    calls = SIMS / f"{args.tag}.calls.jsonl"
    calls.unlink(missing_ok=True)
    import graph.llm as L
    L.LLM_NAME = args.model  # get_llm reads the module global
    install_call_logger(calls)

    from graph.builder import build_graph
    from graph.builder_swarm import build_swarm_graph
    from services.economic_report import generate_economic_report

    if args.sample == "linden":
        stem = "steuerfuss_linden_balanced" if args.corpus == "balanced" else "steuerfuss_linden"
        notes = read_sample(f"{stem}_de.txt").strip() + "\n\n" + read_sample(f"{stem}_fr.txt").strip()
        kind = "vote"
        if args.recommendation != "none":
            yes = args.recommendation == "yes"
            notes = notes.replace("Keine Abstimmungsempfehlung in diesem Auszug.", f"Empfehlung des Gemeinderats: {'Ja' if yes else 'Nein'}.")
            notes = notes.replace("Pas de recommandation de vote dans cet extrait.", f"Recommandation du conseil communal : {'oui' if yes else 'non'}.")
    else:
        notes = read_sample("tariff_millfield_en.txt").strip()
        kind = "policy"
    state = {
        "policy_text": "", "notes_text": notes, "trend_summary": "", "context_summary": "",
        "indicator_snapshots": [], "source_summaries": [], "policy_sources": [], "trend_sources": [],
        "objective": args.objective, "max_rounds": args.rounds, "num_npcs": args.npcs,
        "entities": [], "npcs": [], "relationships": [], "events": [], "current_round": 0,
        "economic_indicators": {}, "memory_streams": {}, "situation_kind": kind,
    }
    t0 = time.perf_counter()
    cpu0 = time.process_time()
    final: dict = {}
    rounds_log = []
    last_memories: dict = {}
    async for chunk in (build_swarm_graph() if args.swarm else build_graph()).astream(state):
        for node, upd in chunk.items():
            if node in ("run_round", "run_round_swarm"):
                rounds_log.append({"round": upd["current_round"] - 1, "events": upd["events"],
                                   "npcs": upd["npcs"], "influence": upd.get("influence_events"),
                                   "indicators": upd.get("economic_indicators")})
                last_memories = upd.get("memory_streams", {})
            final.setdefault(node, upd)
            if node not in ("run_round", "run_round_swarm"):
                final[node] = upd
    t_sim = time.perf_counter() - t0
    cpu_sim = time.process_time() - cpu0
    last = rounds_log[-1] if rounds_log else {}
    t1 = time.perf_counter()
    import inspect
    extra = {}
    if "stance_summary" in inspect.signature(generate_economic_report).parameters:
        from graph.nodes.stance import stance_summary
        extra["stance_summary"] = {"initial": stance_summary(final["generate_npcs"]["npcs"]), "final": stance_summary(last.get("npcs", []))}
    import graph.llm as _L
    report = await generate_economic_report(
        policy_text=final["build_context"]["policy_text"], objective=args.objective,
        entities=final["parse_policy"]["entities"], source_summaries=[], indicator_snapshots=[],
        final_npcs=last.get("npcs", []), events=[e for r in rounds_log for e in r["events"]],
        completed_rounds=len(rounds_log), max_rounds=args.rounds, situation_kind=kind, **extra)
    out = {"args": vars(args), "t_sim_s": round(t_sim, 1), "cpu_sim_s": round(cpu_sim, 2), "t_report_s": round(time.perf_counter() - t1, 1),
           "entities": final["parse_policy"]["entities"], "npcs0": final["generate_npcs"]["npcs"],
           "relationships": final["generate_npcs"]["relationships"], "rounds": rounds_log,
           "report": report.model_dump(), "memories": last_memories,
           "llm_stats": dict(getattr(_L, "STATS", {}))}
    (SIMS / f"{args.tag}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"{args.tag}: sim {t_sim:.0f}s, events {sum(len(r['events']) for r in rounds_log)}")


if __name__ == "__main__":
    asyncio.run(main())
