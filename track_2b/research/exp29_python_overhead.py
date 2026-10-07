"""E29: is Python the bottleneck? Where does the wall time of a simulation go?

Inputs: instrumented runs (`run_sim.py`: per-call start/end, process CPU time) and micro-benchmarks of the pure-Python parts of a resident turn
(retrieval, numeral gate, JSON parse + Pydantic validation, opinion dynamics). Offline except for the runs themselves.

    . research/cscs_env.sh && uv run --project src/backend python research/exp29_python_overhead.py prof70B_s1 prof8B_s1
"""
import json
import re
import statistics as st
import sys
import time
from pathlib import Path

from common import RESULTS, read_sample
from graph.corpus import chunk_policy_document, retrieve_passages
from graph.language import strip_ungrounded_numerals
from graph.llm import _extract_json_from_response, strip_reasoning_spans
from models.schemas import NPCRoundResponse

CLASSES = [("resident turn", "Choose 1-3 events"), ("translation", "Translate the utterance"), ("persona", "life_story"),
           ("impact", "support_reason"), ("reflection", "insights"), ("relationships", "relationship"), ("policy parse", "situation_kind")]


def classify(prompt):
    for name, key in CLASSES:
        if key in prompt:
            return name
    return "other"


def profile(tag):
    d = json.loads((RESULTS / "sims" / f"{tag}.json").read_text(encoding="utf-8"))
    calls = [json.loads(l) for l in (RESULTS / "sims" / f"{tag}.calls.jsonl").read_text(encoding="utf-8").splitlines()]
    t0 = min(c["t_start"] for c in calls)
    ev = sorted([(c["t_start"] - t0, 1) for c in calls] + [(c["t_end"] - t0, -1) for c in calls])
    span = max(c["t_end"] for c in calls) - t0
    inflight, last, busy, area, peak = 0, 0.0, 0.0, 0.0, 0
    for t, dlt in ev:
        dt = t - last
        if inflight > 0:
            busy += dt
        area += inflight * dt
        inflight += dlt
        peak = max(peak, inflight)
        last = t
    by = {}
    for c in calls:
        by.setdefault(classify(c["prompt"]), []).append(c["latency_s"])
    wall, cpu = d["t_sim_s"], d["cpu_sim_s"]
    print(f"\n== {tag}: wall {wall:.1f} s, CPU {cpu:.2f} s ({100 * cpu / wall:.1f} % of wall), {len(calls)} calls, sum of call latencies {sum(c['latency_s'] for c in calls):.0f} s")
    print(f"   span of calls {span:.1f} s; at least one call in flight {100 * busy / span:.1f} % of it; mean in flight {area / span:.1f}; peak {peak}")
    print("   class            n   mean s   max s   sum s")
    for k, v in sorted(by.items(), key=lambda kv: -sum(kv[1])):
        print(f"   {k:15s} {len(v):3d}  {st.mean(v):6.1f}  {max(v):6.1f}  {sum(v):6.0f}")
    usage = [c["usage"] for c in calls if c.get("usage")]
    ct = [u["output_tokens"] for u in usage]
    lat = [c["latency_s"] for c in calls if c.get("usage")]
    if len(ct) > 5:
        # decode-bound: latency ~ completion tokens / speed + overhead
        xs, ys = ct, lat
        mx, my = st.mean(xs), st.mean(ys)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        print(f"   call latency vs completion tokens: {1 / slope:.0f} tok/s decode, correlation r = {r:.2f}; mean {st.mean(ct):.0f} tokens out, {st.mean(u['input_tokens'] for u in usage):.0f} in")
    return d, calls


def micro():
    print("\n== micro-benchmarks of the pure-Python parts (median of 200 runs)")
    de = read_sample("steuerfuss_linden_de.txt")
    booklet = (Path(__file__).resolve().parent / "data" / "booklets" / "erlaeuterungen_2025-09-28_de.txt")
    texts = {"Linden sample (1.6 k chars)": de}
    if booklet.exists():
        texts["real booklet (83 k chars)"] = "--- Author notes / pasted text ---\n" + booklet.read_text(encoding="utf-8")

    def bench(fn, n=200):
        ts = []
        for _ in range(n):
            t = time.perf_counter()
            fn()
            ts.append(time.perf_counter() - t)
        return st.median(ts) * 1000

    for name, txt in texts.items():
        chunks = chunk_policy_document(txt)
        print(f"   {name}: chunking {bench(lambda: chunk_policy_document(txt), 5):7.1f} ms once ({len(chunks)} chunks); retrieval per query {bench(lambda: retrieve_passages(chunks, 'Schuldzinsen Abzug Mieter Steuer', top_k=4, lang='de')):6.2f} ms")
    pack = " ".join(c["text"] for c in chunk_policy_document(de))
    utt = "Der Steuerfuss steigt von 118 % auf 124 %, das sind für mich 240 CHF mehr und nicht 37 % wie behauptet."
    print(f"   numeral gate per utterance: {bench(lambda: strip_ungrounded_numerals(utt, pack)):.3f} ms")
    contents = [json.loads(l)["content"] for l in (RESULTS / "sims" / "cscs70_s1.calls.jsonl").read_text(encoding="utf-8").splitlines() if "events" in (json.loads(l)["content"] or "")]
    if contents:
        def parse():
            NPCRoundResponse.model_validate(_extract_json_from_response(strip_reasoning_spans(contents[0])))
        print(f"   JSON extraction + Pydantic validation of a resident turn: {bench(parse):.3f} ms")


if __name__ == "__main__":
    for t in sys.argv[1:]:
        profile(t)
    micro()
