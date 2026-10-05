"""E15: can the stance be bound to what residents SAY? (follow-up to E14 / F49)

Replays the logged v2.1 resident prompts (the 70B prompts on the 70B, the 8B prompts on the 8B) under:
  A control    the shipped prompt
  B bound      the stance line is replaced by a binding instruction + the chosen argument (the reason in the
               resident's language): speak FROM this position, deliver this argument
  C reminder   the shipped prompt plus the same binding as a last paragraph (recency)
Outcome: position expressed in chat/mood lines (two classifiers) vs the resident's code stance. Side effects:
events per turn, event types, schema validity, verbatim copying of the supplied argument, language.
Usage: python research/exp15_speech_binding.py
"""
import asyncio
import json
import re
from collections import Counter

from common import M70, M8, RESULTS, Gateway
from exp14_tilt import PROMPT as CLS_PROMPT
from graph.llm import _extract_json_from_response
from models.schemas import NPCRoundResponse

RUNS = {M70: ["v21_70_s1", "v21_70_s2", "v21_70_s3"], M8: ["v21_8_s1", "v21_8_s2"]}
STANCE_LINE = re.compile(r"Your position on the question right now: (for|against|undecided) \(([+-]\d\.\d+)[^\n]*?\)\.?( Your reason: ([^\n]*))?\n")
HOW = {
    "for": "you SUPPORT the measure and make the case for it in every line (you may acknowledge a concern, but you never argue against it)",
    "against": "you OPPOSE the measure and make the case against it in every line",
    "undecided": "you are torn and say so openly, weighing both sides",
}


def binding(label, val, reason):
    r = f" The argument you carry: {reason}" if reason else ""
    return f"Your position on the question: {label} ({val}). In everything you say, {HOW[label]}.{r}"


def variant(prompt, cond):
    m = STANCE_LINE.search(prompt)
    if not m or cond == "A":
        return prompt
    label, val, reason = m.group(1), m.group(2), (m.group(4) or "").strip()
    if cond == "B":
        return prompt[:m.start()] + binding(label, val, reason) + "\n" + prompt[m.end():]
    head, sep, tail = prompt.partition("\n\nOutput ONLY a JSON object of this shape")
    return head + "\n\nREMINDER before you answer: " + binding(label, val, reason) + sep + tail  # C


def expected_ok(code, pos):
    return pos == "for" if code == "for" else pos == "against" if code == "against" else pos in ("mixed", "neutral")


async def main():
    gw = Gateway("e15_binding", concurrency=3)
    items = []
    for model, tags in RUNS.items():
        for t in tags:
            for l in (RESULTS / "sims" / f"{t}.calls.jsonl").read_text(encoding="utf-8").splitlines():
                r = json.loads(l)
                if "Choose 1-3 events" in r["prompt"]:
                    m = STANCE_LINE.search(r["prompt"])
                    if m and r["model"] == model:
                        items.append({"model": model, "run": t, "prompt": r["prompt"], "code": m.group(1), "reason": (m.group(4) or "").strip(),
                                      "lang": re.search(r"Language: (\w\w)\.", r["prompt"]).group(1)})
    print("prompts", len(items), Counter(i["code"] for i in items))

    async def gen(it, cond):
        rec = await gw.chat(variant(it["prompt"], cond), model=it["model"], max_tokens=1500, json_mode=True, tag=f"{it['run']}|{cond}")
        out = {"cond": cond, "model": it["model"], "code": it["code"], "lang": it["lang"], "valid": False, "events": [], "copied": False}
        try:
            parsed = NPCRoundResponse.model_validate(_extract_json_from_response(rec["resp"]["content"]))
            out["valid"] = True
            out["events"] = [{"type": e.event_type, "text": (e.dialogue or e.message or "").strip()} for e in parsed.events]
            rs = it["reason"][:40]
            out["copied"] = bool(rs) and any(rs in e["text"] for e in out["events"])
        except Exception:
            pass
        return out

    gens = await asyncio.gather(*[gen(it, c) for it in items for c in "ABC"])
    utts = [(g, e) for g in gens for e in g["events"] if e["type"] in ("chat", "mood_shift") and len(e["text"]) >= 15]

    async def cls(g, e, model):
        rec = await gw.chat(CLS_PROMPT.format(text=e["text"][:600]), model=model, max_tokens=30, json_mode=True, tag=f"cls|{g['cond']}")
        m = re.search(r'"position"\s*:\s*"(for|against|mixed|neutral)"', rec["resp"]["content"])
        return m.group(1) if m else None

    c70 = await asyncio.gather(*[cls(g, e, M70) for g, e in utts])
    c8 = await asyncio.gather(*[cls(g, e, M8) for g, e in utts])
    await gw.close()
    rows = [{**{k: g[k] for k in ("cond", "model", "code", "lang")}, "type": e["type"], "text": e["text"], "c70": a, "c8": b}
            for (g, e), a, b in zip(utts, c70, c8)]
    (RESULTS / "e15_speech_binding.json").write_text(json.dumps({"gens": gens, "utterances": rows}, ensure_ascii=False, indent=1), encoding="utf-8")

    for clf in ("c70", "c8"):
        print(f"\n== classifier {clf}: share of utterances whose expressed position matches the speaker's code stance ==")
        for model in (M70, M8):
            for cond in "ABC":
                sub = [r for r in rows if r["model"] == model and r["cond"] == cond and r[clf]]
                ok = sum(expected_ok(r["code"], r[clf]) for r in sub)
                by = {c: (sum(expected_ok(r["code"], r[clf]) for r in sub if r["code"] == c), sum(1 for r in sub if r["code"] == c)) for c in ("for", "against", "undecided")}
                print(f"{model[-3:]} {cond} n={len(sub):3d}  match {ok / len(sub):.2f}   " + "  ".join(f"{c}: {a}/{b}" for c, (a, b) in by.items()))
        sub = [r for r in rows if r["code"] == "for" and r[clf]]
        for model in (M70, M8):
            for cond in "ABC":
                s = [r for r in sub if r["model"] == model and r["cond"] == cond]
                if s:
                    c = Counter(r[clf] for r in s)
                    print(f"   code=for  {model[-3:]} {cond} n={len(s):3d}: " + "  ".join(f"{k} {c.get(k, 0) / len(s):.2f}" for k in ("for", "against", "mixed", "neutral")))
    print("\n== side effects (per model, condition) ==")
    for model in (M70, M8):
        for cond in "ABC":
            g = [x for x in gens if x["model"] == model and x["cond"] == cond]
            types = Counter(e["type"] for x in g for e in x["events"])
            print(f"{model[-3:]} {cond} n={len(g)} valid {sum(x['valid'] for x in g) / len(g):.2f}  events/turn {sum(len(x['events']) for x in g) / len(g):.2f}  "
                  f"argument copied verbatim {sum(x['copied'] for x in g) / len(g):.2f}  types {dict(types)}")


if __name__ == "__main__":
    asyncio.run(main())
