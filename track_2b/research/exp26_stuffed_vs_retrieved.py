"""E26: retrieve-first versus stuffing the whole booklet (mentor topic 5), now that a fast long-context endpoint is available.

Same 14 answerable + 3 unanswerable questions as E17 (28 Sept 2025 Federal Council booklet, 83 k characters ≈ 30 k tokens), 70B and 8B:
  retrieved4  v2 retriever, top 4 passages (what a resident sees)
  retrieved8  v2 retriever, top 8 passages
  stuffed     the whole booklet in the prompt
The answer must carry a verbatim quote; the quote is checked against the booklet (a quote that is not in the text is a hallucinated source).
Automatic score = gold regex on the answer (it undercounted in E17: read the answers and grade by hand into e26_manual_grading.json).

    . research/cscs_env.sh && uv run --project src/backend python research/exp26_stuffed_vs_retrieved.py
"""
import asyncio
import json
import re

from common import M70, M8, RESULTS, Gateway
from exp17_real_booklet import QA, TEXT, UNANSWERABLE, v2_pack

NORM = lambda s: " ".join(s.split())
BOOK = NORM(TEXT)


def prompt(q, source_label, source):
    return (f"Beantworte die Frage ausschliesslich anhand von {source_label} aus den Erläuterungen des Bundesrates.\n\n{source}\n\nFrage: {q}\n"
            'Wenn die Antwort nicht im Text steht, antworte mit "NICHT IM TEXT". '
            'Antworte nur mit JSON: {"answer": "<kurze Antwort>", "quote": "<wörtliches Zitat aus dem Text, das die Antwort belegt, sonst leer>"}')


async def main():
    gw = Gateway("e26_stuffed_vs_retrieved", concurrency=4)
    jobs, meta = [], []
    for model in (M70, M8):
        for q, gold in [(q, g) for q, g in QA] + [(q, None) for q in UNANSWERABLE]:
            for cond in ("retrieved4", "retrieved8", "stuffed"):
                if cond == "stuffed":
                    p = prompt(q, "des folgenden Textes", TEXT)
                    hit = True
                else:
                    ps = v2_pack(q, 4 if cond == "retrieved4" else 8)
                    pack = "\n\n".join(f"[P{i}] {NORM(x['text'])}" for i, x in enumerate(ps, 1))
                    p = prompt(q, "dieser Passagen", pack)
                    hit = bool(gold) and any(re.search(gold, NORM(x["text"]), re.I) for x in ps)
                jobs.append(gw.chat(p, model=model, max_tokens=300, json_mode=True, tag=f"{model}|{cond}|{q[:30]}"))
                meta.append((model, cond, q, gold, hit))
    recs = await asyncio.gather(*jobs)
    await gw.close()
    rows = []
    for (model, cond, q, gold, hit), rec in zip(meta, recs):
        c = rec["resp"]["content"]
        a = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', c)
        qu = re.search(r'"quote"\s*:\s*"((?:[^"\\]|\\.)*)"', c)
        ans, quote = (a.group(1) if a else c), (qu.group(1) if qu else "")
        abst = "NICHT IM TEXT" in ans.upper()
        rows.append({"model": model, "cond": cond, "q": q, "answerable": gold is not None, "answer": ans, "quote": quote, "abstained": abst,
                     "gold_in_prompt": hit, "auto_correct": (bool(re.search(gold, NORM(ans), re.I)) if gold else abst),
                     "quote_in_text": (NORM(quote).lower() in BOOK.lower()) if quote.strip() else None,
                     "prompt_tokens": (rec["resp"]["usage"] or {}).get("prompt_tokens"), "lat": rec.get("latency_s")})
    (RESULTS / "e26_stuffed_vs_retrieved.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("model                       cond        answerable auto-correct   wrongly abstained   unanswerable abstained   quotes in text   mean prompt tokens   mean latency s")
    for model in (M70, M8):
        for cond in ("retrieved4", "retrieved8", "stuffed"):
            r = [x for x in rows if x["model"] == model and x["cond"] == cond]
            a = [x for x in r if x["answerable"]]
            u = [x for x in r if not x["answerable"]]
            qs = [x for x in r if x["quote_in_text"] is not None]
            print(f"{model:27s} {cond:11s} {sum(x['auto_correct'] for x in a):2d}/{len(a)}          {sum(x['abstained'] for x in a):2d}                  "
                  f"{sum(x['auto_correct'] for x in u)}/{len(u)}                      {sum(x['quote_in_text'] for x in qs)}/{len(qs)}            "
                  f"{sum(x['prompt_tokens'] or 0 for x in r) / len(r):8.0f}             {sum(x['lat'] or 0 for x in r) / len(r):.1f}")


if __name__ == "__main__":
    asyncio.run(main())
