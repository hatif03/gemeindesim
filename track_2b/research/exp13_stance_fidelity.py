"""E13: stance fidelity at the end of a v2 run.

For each resident: give Apertus the persona, the question and the resident's final memories (their own
conversation record) and ask the stance directly (yes/no/undecided). Compare with the code-owned stance.
Questions: (1) does the LLM agree with the code stance? (2) when not, does it lean 'yes' (acquiescence /
consensus pull, cf. E11)? Usage: python research/exp13_stance_fidelity.py v2_s1 v2_s2 ...
"""
import asyncio
import json
import re
import sys
from collections import Counter

from common import M70, RESULTS, Gateway, read_sample

POL = {"de": read_sample("steuerfuss_linden_de.txt"), "fr": read_sample("steuerfuss_linden_fr.txt")}


def label(x):
    return "yes" if x > 0.15 else "no" if x < -0.15 else "undecided"


async def main(tags):
    gw = Gateway("e13_fidelity", concurrency=3)
    jobs, meta = [], []
    for t in tags:
        d = json.loads((RESULTS / "sims" / f"{t}.json").read_text(encoding="utf-8"))
        final = {n["id"]: n for n in d["rounds"][-1]["npcs"]}
        for n0 in d["npcs0"]:
            n = final[n0["id"]]
            mem = d.get("memories", {}).get(n["id"], [])
            mem_txt = "\n".join(f"- {m['description']}" for m in sorted(mem, key=lambda m: m["round_created"])[-10:]) or "(none)"
            lang = n["lang"] if n["lang"] in POL else "de"
            if lang == "fr":
                p = (f"Tu es {n['name']}, {n['profession']} à Linden. {n.get('bio','')}\nTes souvenirs récents :\n{mem_txt}\n\n"
                     f"Objet soumis au vote :\n{POL['fr']}\nComment votes-tu maintenant ? Réponds uniquement en JSON : "
                     '{"stance": "yes" | "no" | "undecided"}')
            else:
                p = (f"Du bist {n['name']}, {n['profession']} in Linden. {n.get('bio','')}\nDeine jüngsten Erinnerungen:\n{mem_txt}\n\n"
                     f"Vorlage:\n{POL['de']}\nWie stimmst du jetzt? Antworte nur mit JSON: "
                     '{"stance": "yes" | "no" | "undecided"}')
            jobs.append(gw.chat(p, model=M70, max_tokens=40, json_mode=True, tag=f"{t}|{n['id']}"))
            meta.append({"src": t, "id": n["id"], "code_stance": n.get("stance", 0.0), "code_label": label(n.get("stance", 0.0)),
                         "initial_stance": n0.get("stance", 0.0), "role": n["role"]})
    recs = await asyncio.gather(*jobs)
    await gw.close()
    for m, r in zip(meta, recs):
        g = re.search(r'"stance"\s*:\s*"(yes|no|undecided)"', r["resp"]["content"])
        m["llm_label"] = g.group(1) if g else None
    (RESULTS / "e13_stance_fidelity.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    ok = [m for m in meta if m["llm_label"]]
    print("n", len(ok), "agreement", round(sum(m["llm_label"] == m["code_label"] for m in ok) / len(ok), 2))
    print("code labels:", dict(Counter(m["code_label"] for m in ok)), "| LLM labels:", dict(Counter(m["llm_label"] for m in ok)))
    print("confusion (code -> llm):", dict(Counter((m["code_label"], m["llm_label"]) for m in ok)))
    dis = [m for m in ok if m["llm_label"] != m["code_label"]]
    print("disagreements pulling toward yes:", sum(m["llm_label"] == "yes" for m in dis), "of", len(dis))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
