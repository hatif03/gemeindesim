"""E2: structured-output reliability of Apertus on the app's REAL resident-turn prompts.

Replays prompts logged by run_sim.py under format conditions:
  A_current   placeholder example ("..."), json_object            (what the app does)
  B_filled    realistic filled 2-event example in resident language, json_object
  C_nojson    placeholder example, NO response_format
  D_noexample no example at all (prompt text only), json_object
Models: 70B, 8B. Temperature 0. Measures first-attempt validity (no repair, no retry).
Usage: python research/exp02_structured.py base70_s1 [base70_s2 ...]
"""
import asyncio
import json
import re
import sys

from pydantic import ValidationError

from common import M70, M8, Gateway, load_jsonl, RESULTS
from graph.llm import _extract_json_from_response, strip_reasoning_spans
from models.schemas import NPCRoundResponse

SUFFIX = re.compile(r"\n\nOutput ONLY the following JSON.*$", re.S)
EX = {
 "de": {"events": [
   {"event_type": "chat", "message": "Ich spreche Frau Keller auf die Vorlage an.", "target_npc_id": "npc_02",
    "dialogue": "Guten Tag, haben Sie die Erläuterungen zum Steuerfuss schon gelesen?", "to_x": None, "to_y": None,
    "new_mood": "", "used_source_ids": ["quelle#1"], "grounded": False},
   {"event_type": "mood_shift", "message": "Ich mache mir Sorgen um mein Budget.", "target_npc_id": "", "dialogue": "",
    "to_x": None, "to_y": None, "new_mood": "worried", "used_source_ids": [], "grounded": False}],
   "perception": "Die Nachbarn diskutieren über die Steuererhöhung."},
 "fr": {"events": [
   {"event_type": "chat", "message": "J'aborde Madame Keller au sujet de l'objet.", "target_npc_id": "npc_02",
    "dialogue": "Bonjour, avez-vous déjà lu les explications sur le taux d'imposition ?", "to_x": None, "to_y": None,
    "new_mood": "", "used_source_ids": ["source#1"], "grounded": False},
   {"event_type": "mood_shift", "message": "Je m'inquiète pour mon budget.", "target_npc_id": "", "dialogue": "",
    "to_x": None, "to_y": None, "new_mood": "worried", "used_source_ids": [], "grounded": False}],
   "perception": "Les voisins discutent de la hausse d'impôt."},
}
STOP = {"de": {"der", "die", "das", "und", "ich", "nicht", "ist", "zu", "mit", "für", "den", "ein"},
        "fr": {"le", "la", "les", "et", "je", "pas", "est", "de", "des", "pour", "un", "une", "que"},
        "en": {"the", "and", "is", "to", "of", "for", "that", "with", "this", "we"}}


def lang_guess(text: str) -> str:
    w = re.findall(r"[a-zäöüéèêàç']+", text.lower())
    sc = {l: sum(x in s for x in w) for l, s in STOP.items()}
    return max(sc, key=sc.get) if any(sc.values()) else "?"


def build(base: str, cond: str, lang: str) -> tuple[str, bool]:
    if cond == "D_noexample":
        return base, True
    schema_ex = None
    if cond in ("A_current", "C_nojson"):
        from graph.llm import _flatten_schema, _schema_to_example
        schema_ex = _schema_to_example(_flatten_schema(NPCRoundResponse.model_json_schema()))
    else:  # B_filled
        schema_ex = EX[lang]
    p = (f"{base}\n\nOutput ONLY the following JSON with the placeholder values filled in. "
         f"No explanation, no reasoning, no other text — just the completed JSON:\n{json.dumps(schema_ex, indent=2, ensure_ascii=False)}")
    return p, cond != "C_nojson"


def score(content: str, lang: str, example_dialogue: str) -> dict:
    out = {"strict_json": False, "extracted": False, "valid": False, "n_events": 0, "types": [],
           "placeholder_echo": False, "xy_zero_echo": False, "lang_ok": None, "copy_example": False}
    try:
        json.loads(strip_reasoning_spans(content)); out["strict_json"] = True
    except Exception:
        pass
    try:
        parsed = _extract_json_from_response(content); out["extracted"] = True
        m = NPCRoundResponse.model_validate(parsed); out["valid"] = True
        out["n_events"] = len(m.events); out["types"] = [e.event_type for e in m.events]
        txt = " ".join(f"{e.message} {e.dialogue}" for e in m.events)
        out["placeholder_echo"] = any(e.message.strip() in ("...", "") for e in m.events)
        out["xy_zero_echo"] = any(e.event_type != "move" and e.to_x == 0 and e.to_y == 0 for e in m.events)
        out["lang_ok"] = lang_guess(txt) == lang
        out["copy_example"] = bool(example_dialogue and example_dialogue[:30] in txt)
    except (ValidationError, Exception):
        pass
    return out


async def main(tags):
    gw = Gateway("e02_structured", concurrency=4)
    items = []
    for t in tags:
        for r in load_jsonl_sims(t):
            if "Choose 1-3 events" in r["prompt"]:
                base = SUFFIX.sub("", r["prompt"])
                lang = re.search(r"Language: (\w\w)\.", r["prompt"]).group(1)
                items.append((t, base, lang))
    print("prompts", len(items))

    async def one(t, base, lang, model, cond):
        p, jm = build(base, cond, lang)
        rec = await gw.chat(p, model=model, max_tokens=1500, json_mode=jm, tag=f"{model}|{cond}|{t}")
        s = score(rec["resp"]["content"], lang, EX.get(lang, {}).get("events", [{}])[0].get("dialogue", ""))
        s.update({"model": model, "cond": cond, "lang": lang, "src": t, "lat": rec.get("latency_s"),
                  "out_tok": (rec["resp"]["usage"] or {}).get("completion_tokens"), "finish": rec["resp"]["finish"]})
        return s

    jobs = [one(t, b, l, m, c) for (t, b, l) in items for m in (M70, M8)
            for c in ("A_current", "B_filled", "C_nojson", "D_noexample")]
    res = await asyncio.gather(*jobs)
    await gw.close()
    (RESULTS / "e02_structured_scored.json").write_text(json.dumps(res, indent=1))
    import statistics as st
    print(f"{'model':18s}{'cond':13s}{'n':>3s} strict extr valid  ev  ph_echo xy0 lang_ok copyEx  lat  tok")
    for m in (M70, M8):
        for c in ("A_current", "B_filled", "C_nojson", "D_noexample"):
            r = [x for x in res if x["model"] == m and x["cond"] == c]
            f = lambda k: sum(bool(x[k]) for x in r) / len(r)
            print(f"{m:18s}{c:13s}{len(r):3d} {f('strict_json'):5.2f} {f('extracted'):4.2f} {f('valid'):5.2f} "
                  f"{st.mean(x['n_events'] for x in r):4.1f} {f('placeholder_echo'):7.2f} {f('xy_zero_echo'):4.2f} "
                  f"{sum(1 for x in r if x['lang_ok'])/len(r):7.2f} {f('copy_example'):6.2f} "
                  f"{st.mean(x['lat'] for x in r):5.1f} {st.mean(x['out_tok'] or 0 for x in r):4.0f}")


def load_jsonl_sims(tag):
    p = RESULTS / "sims" / f"{tag}.calls.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
