"""Score instrumented simulation runs (research/results/sims/TAG.json + .calls.jsonl).

Usage: python research/analyze_sims.py base70_s1 base70_s2 ...   (prints per-run table + pooled)
All metrics are programmatic (no LLM judge). Definitions are in docs/research/03-experiments.md.
"""
import json
import re
import statistics as st
import sys
from collections import Counter

from common import RESULTS, read_sample
from graph.corpus import chunk_policy_document
from graph.language import fallback_utterance

STOP = {"de": {"der", "die", "das", "und", "ich", "nicht", "ist", "zu", "mit", "für", "den", "ein", "wir", "sie", "es"},
        "fr": {"le", "la", "les", "et", "je", "pas", "est", "de", "des", "pour", "un", "une", "que", "nous", "vous"},
        "en": {"the", "and", "is", "to", "of", "for", "that", "with", "this", "we", "i"}}
# Self-introduction = "Ich bin <Vorname> <Nachname>" / "Je suis <Prénom> <Nom>" (capitalised name parts, case-SENSITIVE: an earlier version
# ran with re.I, so "Ich bin noch unentschieden" and "je suis pour" counted as introductions) or an explicit "my name is".
INTRO = re.compile(r"\b((?i:ich bin) [A-ZÄÖÜ][a-zäöüéèê]+ [A-ZÄÖÜ][a-zäöüéèê]+|(?i:mein name ist|je m'appelle|ich heisse|ich heiße)|(?i:je suis) [A-ZÉÈ][a-zéèê]+ [A-ZÉÈ][a-zéèê]+)")
FALLBACKS = {fallback_utterance(l) for l in ("de", "fr", "en")}


def lang_guess(text):
    w = re.findall(r"[a-zäöüéèêàç']+", text.lower())
    sc = {l: sum(x in s for x in w) for l, s in STOP.items()}
    return max(sc, key=sc.get) if any(sc.values()) else "?"


def score(tag):
    d = json.loads((RESULTS / "sims" / f"{tag}.json").read_text(encoding="utf-8"))
    calls = [json.loads(l) for l in (RESULTS / "sims" / f"{tag}.calls.jsonl").read_text(encoding="utf-8").splitlines()]
    notes = "--- Author notes / pasted text ---\n" + read_sample("steuerfuss_linden_de.txt").strip() + "\n\n" + read_sample("steuerfuss_linden_fr.txt").strip()
    valid_ids = {c["source_id"] for c in chunk_policy_document(notes)}
    langs = {n["id"]: n["lang"] for n in d["npcs0"]}
    evs = [e for r in d["rounds"] for e in r["events"]]
    chats = [e for e in evs if e["event_type"] == "chat"]
    texts = [(e["npc_id"], (e["data"].get("dialogue") or "") + " " + (e["message"] or "")) for e in evs]
    cited = [i for e in evs for i in (e["data"].get("used_source_ids") or [])]
    # v2 events carry `invalid_cites` (labels that did not exist in that resident's pack); baseline events do not
    v2 = any("invalid_cites" in e["data"] for e in evs)
    n_valid = len(cited)
    n_invalid = sum(e["data"].get("invalid_cites", 0) for e in evs)
    allfinal = json.dumps(d["report"], ensure_ascii=False) + " ".join(t for _, t in texts) + " ".join(n.get("bio", "") + n.get("life_story", "") for n in d["npcs0"])
    rnd = [c for c in calls if "Choose 1-3 events" in c["prompt"]]
    attempts = Counter()
    for c in calls:
        attempts[c["prompt"].split("\n\nYour previous JSON failed validation")[0]] += 1
    out = {
        "tag": tag,
        "t_sim_s": d["t_sim_s"], "calls": len(calls), "err_calls": sum(1 for c in calls if c["error"]),
        "retry_calls": sum(v - 1 for v in attempts.values()),
        "tok_in": sum(c["usage"].get("input_tokens", 0) for c in calls), "tok_out": sum(c["usage"].get("output_tokens", 0) for c in calls),
        "lat_mean": round(st.mean(c["latency_s"] for c in calls), 1),
        "events": len(evs), "chat_share": round(len(chats) / max(1, len(evs)), 2),
        "types": dict(Counter(e["event_type"] for e in evs)),
        "intro_rate": round(sum(bool(INTRO.search(e["data"].get("dialogue") or "")) for e in chats) / max(1, len(chats)), 2),
        "intro_after_r0": round(sum(bool(INTRO.search(e["data"].get("dialogue") or "")) for e in chats if e["round"] > 0) / max(1, sum(1 for e in chats if e["round"] > 0)), 2),
        "lang_ok": round(sum(lang_guess(t) == langs.get(i) for i, t in texts if t.strip()) / max(1, len(texts)), 2),
        "eszett": allfinal.count("ß"),
        "numerals_stripped": sum(("[n]" in (e["message"] or "") + (e["data"].get("dialogue") or "")) for e in evs),
        "cite_n": (n_valid + n_invalid) if v2 else len(cited),
        "cite_valid_rate": round(n_valid / max(1, n_valid + n_invalid), 2) if v2 else round(sum(i in valid_ids for i in cited) / max(1, len(cited)), 2),
        "events_with_valid_cite": round(sum(bool(e["data"].get("used_source_ids")) for e in evs) / max(1, len(evs)), 2) if v2 else 0.0,
        "grounded_rate": round(sum(bool(e["data"].get("grounded")) for e in evs) / max(1, len(evs)), 2),
        "stance_initial": (lambda xs: {"for": sum(x > .15 for x in xs), "against": sum(x < -.15 for x in xs), "undecided": sum(abs(x) <= .15 for x in xs)})([n.get("stance", 0.0) for n in d["npcs0"]]),
        "stance_final": (lambda xs: {"for": sum(x > .15 for x in xs), "against": sum(x < -.15 for x in xs), "undecided": sum(abs(x) <= .15 for x in xs)})([n.get("stance", 0.0) for n in d["rounds"][-1]["npcs"]]),
        "llm_stats": d.get("llm_stats", {}),
        "intro_hint": None,
        "fallback_events": sum((e["message"] in FALLBACKS) for e in evs),
        "final_moods": dict(Counter(n["mood"] for n in d["rounds"][-1]["npcs"])),
        "report_lang": lang_guess(d["report"]["summary"]),
        "report_mixed_lang": bool(re.search(r"does not recommend", d["report"]["summary"]) and lang_guess(d["report"]["summary"].split("This report")[0]) != "en"),
        "report_asserts_outcome": bool(re.search(r"\b(bewilligt\w*|genehmigt\w*|wurde[n]? (angenommen|abgelehnt|verabschiedet)|verhinderte|accepté\w*|rejeté\w*|adopté\w*|approved|passed|angenommen|abgelehnt)\b", d["report"]["summary"] + " " + d["report"]["livelihood_impact"], re.I)) and not re.search(r"\b(würde|would|serait|wenn|if)\b", d["report"]["summary"], re.I),
        "retrieval_question_chunk_rate": None,
    }
    hit = [bool(re.search(r"118\s*%.{0,40}124|124\s*%", re.search(r"quote numbers only if they appear here\):\n(.*?)\n\nPolicy summary:", c["prompt"], re.S).group(1), re.S)) for c in rnd if re.search(r"quote numbers only if they appear here\):\n(.*?)\n\nPolicy summary:", c["prompt"], re.S)]
    out["retrieval_question_chunk_rate"] = round(sum(hit) / max(1, len(hit)), 2)
    return out


if __name__ == "__main__":
    rows = [score(t) for t in sys.argv[1:]]
    keys = [k for k in rows[0] if k != "tag"]
    for k in keys:
        print(f"{k:32s}", " | ".join(f"{str(r[k]):>22s}" for r in rows))
    print(f"{'tag':32s}", " | ".join(f"{r['tag']:>22s}" for r in rows))
    (RESULTS / f"sims_scores_{'_'.join(sys.argv[1:])}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
