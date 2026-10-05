"""E14: does resident DIALOGUE tilt toward 'yes' independently of the code-owned stance?

For every chat line and mood_shift message in the baseline and v2.1 runs, a classifier says what position toward
the measure the speaker expresses (for / against / mixed / neutral). Two classifiers (70B, 8B) so one model's bias
cannot hide the result. Compared with: (a) the baseline, which had no stance variable; (b) v2.1, where each speaker
has a code stance, so we can ask whether 'against' residents sound 'for'.
Usage: python research/exp14_tilt.py
"""
import asyncio
import json
import re
import sys
from collections import Counter

from common import M70, M8, RESULTS, Gateway

RUNS = {"baseline70": ["base70_s1", "base70_s2", "base70_s3"], "baseline8": ["base8_s1", "base8_s2"],
        "v21_70": ["v21_70_s1", "v21_70_s2", "v21_70_s3"], "v21_8": ["v21_8_s1", "v21_8_s2"]}
if len(sys.argv) > 1:  # e.g.  v22_70=v22_70_s1,v22_70_s2  v22_8=v22_8_s1  (output goes to e14_tilt_<first group>.json)
    RUNS = {a.split("=")[0]: a.split("=")[1].split(",") for a in sys.argv[1:]}
OUT = "e14_tilt.json" if len(sys.argv) == 1 else f"e14_tilt_{sys.argv[1].split('=')[0]}.json"
PROMPT = (
    "A resident of the Swiss municipality Linden speaks about a vote: raising the tax rate from 118 % to 124 % and a "
    "4.8 million CHF credit for a new school building.\n\nText (German or French):\n\"\"\"{text}\"\"\"\n\n"
    "What position toward the measure does the SPEAKER express in this text? Answer with exactly one word in JSON: "
    '{{"position": "for"}} or {{"position": "against"}} or {{"position": "mixed"}} (clear arguments on both sides) or '
    '{{"position": "neutral"}} (no position, e.g. only asks a question or moves).'
)


def label(x):
    return "for" if x > 0.15 else "against" if x < -0.15 else "undecided"


async def main():
    items = []
    for group, tags in RUNS.items():
        for t in tags:
            d = json.loads((RESULTS / "sims" / f"{t}.json").read_text(encoding="utf-8"))
            stance = {n["id"]: n.get("stance") for n in d["npcs0"]}
            for r in d["rounds"]:
                for e in r["events"]:
                    if e["event_type"] not in ("chat", "mood_shift"):
                        continue
                    text = (e["data"].get("dialogue") or e["message"] or "").strip()
                    if len(text) < 15:
                        continue
                    items.append({"group": group, "run": t, "npc": e["npc_id"], "type": e["event_type"], "round": e["round"],
                                  "code": label(stance[e["npc_id"]]) if stance.get(e["npc_id"]) is not None else None,
                                  "code_val": stance.get(e["npc_id"]), "text": text[:600]})
    print("utterances", len(items))
    gw = Gateway("e14_tilt", concurrency=3)

    async def cls(it, model):
        rec = await gw.chat(PROMPT.format(text=it["text"]), model=model, max_tokens=30, json_mode=True, tag=f"{it['run']}|{it['npc']}|{model[-3:]}")
        m = re.search(r'"position"\s*:\s*"(for|against|mixed|neutral)"', rec["resp"]["content"])
        return m.group(1) if m else None

    r70 = await asyncio.gather(*[cls(it, M70) for it in items])
    r8 = await asyncio.gather(*[cls(it, M8) for it in items])
    await gw.close()
    for it, a, b in zip(items, r70, r8):
        it["c70"], it["c8"] = a, b
    (RESULTS / OUT).write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

    ok = [i for i in items if i["c70"] and i["c8"]]
    print("classifier agreement 70B vs 8B:", round(sum(i["c70"] == i["c8"] for i in ok) / len(ok), 2), "n", len(ok))
    for clf in ("c70", "c8"):
        print(f"\n== classifier {clf} ==")
        for g in RUNS:
            sub = [i for i in items if i["group"] == g and i[clf]]
            c = Counter(i[clf] for i in sub)
            print(f"{g:11s} n={len(sub):3d}  " + "  ".join(f"{k} {c.get(k, 0) / len(sub):.2f}" for k in ("for", "against", "mixed", "neutral")))
        for g in ("v21_70", "v21_8"):
            print(f"-- {g}: expressed position by the speaker's CODE stance")
            for code in ("for", "against", "undecided"):
                sub = [i for i in items if i["group"] == g and i["code"] == code and i[clf]]
                if sub:
                    c = Counter(i[clf] for i in sub)
                    print(f"   code={code:9s} n={len(sub):3d}  " + "  ".join(f"{k} {c.get(k, 0) / len(sub):.2f}" for k in ("for", "against", "mixed", "neutral")))
        for typ in ("chat", "mood_shift"):
            sub = [i for i in items if i["group"].startswith("v21") and i["type"] == typ and i["code"] == "against" and i[clf]]
            if sub:
                c = Counter(i[clf] for i in sub)
                print(f"   v21 code=against, {typ:10s} n={len(sub):3d}  " + "  ".join(f"{k} {c.get(k, 0) / len(sub):.2f}" for k in ("for", "against", "mixed", "neutral")))


if __name__ == "__main__":
    asyncio.run(main())
