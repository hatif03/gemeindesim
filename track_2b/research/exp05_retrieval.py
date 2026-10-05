"""E5 (offline): what does lexical retrieval put in front of each resident?

Reads logged resident prompts from a baseline run, extracts the passage block, and
checks coverage of the corpus' key facts. Then replays alternative retrievers on
the SAME logged queries' resident language.
"""
import json, re, sys
from common import RESULTS, read_sample

KEY_FACTS = {  # fact -> regexes that mean the passage carries it (DE or FR)
    "rate 118->124": r"118\s*%.{0,40}124|124\s*%",
    "credit 4.8M": r"4[.,]8\s*Millionen|4[.,]8\s*millions",
    "deficit 1.2M": r"1[.,]2\s*Million",
    "240 CHF example": r"240\s*CHF",
    "yes/no consequences": r"Was ein Ja|Was ein Nein|Ce que change un oui|Ce que change un non",
    "savings 400k/200k": r"400.000|200.000",
}

def passages_of(prompt):
    m = re.search(r"quote numbers only if they appear here\):\n(.*?)\n\nPolicy summary:", prompt, re.S)
    return m.group(1) if m else ""

tag = sys.argv[1] if len(sys.argv) > 1 else "base70_s1"
rows = [json.loads(l) for l in open(RESULTS / "sims" / f"{tag}.calls.jsonl", encoding="utf-8")]
rnd = [r for r in rows if "Choose 1-3 events" in r["prompt"]]
res = []
for r in rnd:
    p = passages_of(r["prompt"])
    ids = re.findall(r"^\[([^\]]+)\]", p, re.M)
    lang = re.search(r"Language: (\w\w)\.", r["prompt"]).group(1)
    cov = {k: bool(re.search(v, p, re.S)) for k, v in KEY_FACTS.items()}
    res.append({"lang": lang, "n_passages": len(ids), "ids": ids, "chars": len(p), "coverage": cov,
                "n_facts": sum(cov.values())})
for x in res: print(x["lang"], x["n_passages"], x["chars"], x["n_facts"], x["ids"])
import statistics as st
print("mean key facts in pack:", round(st.mean(x["n_facts"] for x in res), 2), "of", len(KEY_FACTS))
for k in KEY_FACTS: print(f"  {k:24s}", sum(x["coverage"][k] for x in res), "/", len(res))
(RESULTS / f"e05_retrieval_{tag}.json").write_text(json.dumps(res, indent=1))
