"""E16: can an UNDECIDED resident sound undecided? (open item F51/F53)

Replays the 41 logged prompts of residents whose code stance is 'undecided' (70B prompts on the 70B, 8B prompts on
the 8B; v2.1 and v2.2 logs, the binding paragraph removed and re-added per condition). Conditions:
  U0 current binding        'you are torn and say so openly, weighing both sides' + the two arguments joined by ' / '
  U1 two-sided structure    say plainly you are undecided; ONE concrete reason for + ONE against (own words); never only costs
  U2 U1 + opening phrase    U1 and the line must open with 'Ich bin noch unentschieden' / 'Je n'ai pas encore décidé'
  U3 U0 + 'never argue only about costs'
Outcome: share of lines the classifier calls 'mixed' (strict) and 'mixed or neutral'. Side effects: validity, events/turn,
verbatim copying of the supplied arguments, lexical diversity.
Usage: python research/exp16_undecided.py
"""
import asyncio
import json
import re
from collections import Counter

from common import M70, M8, RESULTS, Gateway
from exp14_tilt import PROMPT as CLS_PROMPT
from graph.llm import _extract_json_from_response
from models.schemas import NPCRoundResponse

TAGS = {M70: ["v21_70_s1", "v21_70_s2", "v21_70_s3", "v22_70_s1", "v22_70_s2", "v22_70_s3"],
        M8: ["v21_8_s1", "v21_8_s2", "v22_8_s1", "v22_8_s2"]}
STANCE = re.compile(r"Your position on the question right now: undecided \(([+-]\d\.\d+)[^\n]*?\)\.?( Your reason: ([^\n]*))?\n")
REMINDER = re.compile(r"\n\nREMINDER before you answer:[^\n]*(?=\n\nOutput ONLY)")
OPEN = {"de": "Ich bin noch unentschieden", "fr": "Je n'ai pas encore décidé", "en": "I have not decided yet"}
TAIL = "\n\nOutput ONLY a JSON object of this shape"


def split_args(reason):
    parts = [p.strip() for p in reason.split(" / ")]
    return (parts[0], parts[1]) if len(parts) >= 2 else (reason, "")


def hint(text, n=55):
    """First ~n characters, cut at a word boundary: a topic, not a sentence to copy."""
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + " ..."


def build(prompt, cond, lang):
    m = STANCE.search(prompt)
    val, reason = m.group(1), (m.group(3) or "").strip()
    a, b = split_args(reason)
    base = REMINDER.sub("", prompt)
    head, sep, tail = base.partition(TAIL)
    if cond == "U0":
        para = (f"REMINDER before you answer: Your position on the question: undecided ({val}). In everything you say, you are torn and "
                f"say so openly, weighing both sides. The argument you carry: {reason}")
    elif cond == "U3":
        para = (f"REMINDER before you answer: Your position on the question: undecided ({val}). In everything you say, you are torn and "
                f"say so openly, weighing both sides, and you never argue only about costs. The argument you carry: {reason}")
    elif cond == "U1h":  # hints instead of full sentences: nothing to copy verbatim
        ha, hb = hint(a), hint(b)
        para = (f"REMINDER before you answer: Your position on the question: undecided ({val}). You have NOT made up your mind and you say "
                f"so in your own words. In every line you do three things: (1) state plainly that you are still undecided; (2) give ONE "
                f"concrete reason in favour, developed in your own words from this hint: {ha} (3) give ONE concrete reason against, "
                f"developed in your own words from this hint: {hb} You never take a side and you never argue only about costs.")
    else:
        para = (f"REMINDER before you answer: Your position on the question: undecided ({val}). You have NOT made up your mind and you say "
                f"so in your own words. In every line you do three things: (1) state plainly that you are still undecided; (2) give ONE "
                f"concrete reason in favour (in your own words): {a} (3) give ONE concrete reason against (in your own words): {b} "
                f"You never take a side and you never argue only about costs.")
        if cond == "U1p":
            para += " Do NOT repeat the sentences above word for word: say the same thing with new wording every time."
        if cond == "U2":
            para += f" Start the line with: \"{OPEN.get(lang, OPEN['en'])}\"."
    return head + "\n\n" + para + sep + tail


async def main():
    gw = Gateway("e16b_undecided", concurrency=3)
    items = []
    for model, tags in TAGS.items():
        for t in tags:
            for l in (RESULTS / "sims" / f"{t}.calls.jsonl").read_text(encoding="utf-8").splitlines():
                r = json.loads(l)
                if "Choose 1-3 events" in r["prompt"] and STANCE.search(r["prompt"]) and r["model"] == model:
                    items.append({"model": model, "run": t, "prompt": r["prompt"], "lang": re.search(r"Language: (\w\w)\.", r["prompt"]).group(1)})
    print("undecided prompts", len(items), Counter(i["model"][-3:] for i in items))

    async def gen(it, cond):
        rec = await gw.chat(build(it["prompt"], cond, it["lang"]), model=it["model"], max_tokens=1500, json_mode=True, tag=f"{it['run']}|{cond}")
        out = {"cond": cond, "model": it["model"], "lang": it["lang"], "valid": False, "events": [], "copied": False}
        try:
            parsed = NPCRoundResponse.model_validate(_extract_json_from_response(rec["resp"]["content"]))
            out["valid"] = True
            out["events"] = [{"type": e.event_type, "text": (e.dialogue or e.message or "").strip()} for e in parsed.events]
            args = [x for x in split_args((STANCE.search(it["prompt"]).group(3) or "").strip()) if x]
            out["copied"] = any(a[:40] in e["text"] for a in args for e in out["events"])
        except Exception:
            pass
        return out

    conds = ("U1", "U1p", "U1h")
    gens = await asyncio.gather(*[gen(it, c) for it in items for c in conds])
    utts = [(g, e) for g in gens for e in g["events"] if e["type"] in ("chat", "mood_shift") and len(e["text"]) >= 15]

    async def cls(g, e, model):
        rec = await gw.chat(CLS_PROMPT.format(text=e["text"][:600]), model=model, max_tokens=30, json_mode=True, tag=f"cls|{g['cond']}")
        m = re.search(r'"position"\s*:\s*"(for|against|mixed|neutral)"', rec["resp"]["content"])
        return m.group(1) if m else None

    c70 = await asyncio.gather(*[cls(g, e, M70) for g, e in utts])
    c8 = await asyncio.gather(*[cls(g, e, M8) for g, e in utts])
    await gw.close()
    rows = [{"cond": g["cond"], "model": g["model"], "lang": g["lang"], "type": e["type"], "text": e["text"], "c70": a, "c8": b}
            for (g, e), a, b in zip(utts, c70, c8)]
    (RESULTS / "e16b_undecided.json").write_text(json.dumps({"gens": gens, "utterances": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    for clf in ("c70", "c8"):
        print(f"\n== classifier {clf}: positions expressed by UNDECIDED residents ==")
        for model in (M70, M8):
            for cond in conds:
                s = [r for r in rows if r["model"] == model and r["cond"] == cond and r[clf]]
                c = Counter(r[clf] for r in s)
                print(f"{model[-3:]} {cond} n={len(s):3d}  mixed {c['mixed'] / len(s):.2f}  mixed+neutral {(c['mixed'] + c['neutral']) / len(s):.2f}  "
                      f"for {c['for'] / len(s):.2f}  against {c['against'] / len(s):.2f}")
    print("\n== side effects ==")
    for model in (M70, M8):
        for cond in conds:
            g = [x for x in gens if x["model"] == model and x["cond"] == cond]
            toks = [w for x in g for e in x["events"] for w in re.findall(r"\w+", e["text"].lower())]
            tri = set(zip(toks, toks[1:], toks[2:]))
            print(f"{model[-3:]} {cond} n={len(g)} valid {sum(x['valid'] for x in g) / len(g):.2f} events/turn {sum(len(x['events']) for x in g) / len(g):.2f} "
                  f"argument copied verbatim {sum(x['copied'] for x in g) / len(g):.2f} distinct-trigram {len(tri) / max(1, len(toks) - 2):.3f} "
                  f"types {dict(Counter(e['type'] for x in g for e in x['events']))}")


if __name__ == "__main__":
    asyncio.run(main())
