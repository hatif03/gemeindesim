"""Summarise the native-speaker review sheet (docs/review/review-sheet.csv, filled in).

Prints mean ratings per criterion and language (REG, TERM, CH, NAT; 1-5), the lowest-rated items, and every correction, so the
fixes can go into the glossary (graph/language.py), the prompts (graph/prompts.py) or the sample texts (data/).
Usage: python research/summarize_review.py [path/to/filled-review-sheet.csv]
"""
import csv
import statistics as st
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "docs" / "review" / "review-sheet.csv"
rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
CRIT = ("REG", "TERM", "CH", "NAT")


def num(x):
    try:
        return float(str(x).replace(",", ".").strip())
    except ValueError:
        return None


rated = [r for r in rows if any(num(r[c]) is not None for c in CRIT)]
print(f"{len(rated)} of {len(rows)} items rated")
for lang in ("de", "fr"):
    for kind in sorted({r["kind"] for r in rated if r["lang"] == lang}):
        sub = [r for r in rated if r["lang"] == lang and r["kind"] == kind]
        means = {c: [num(r[c]) for r in sub if num(r[c]) is not None] for c in CRIT}
        print(f"{lang} {kind:48s} n={len(sub):2d}  " + "  ".join(f"{c} {st.mean(v):.1f}" if v else f"{c} -" for c, v in means.items()))
low = sorted(rated, key=lambda r: st.mean([num(r[c]) for c in CRIT if num(r[c]) is not None]))[:10]
print("\nlowest-rated items:")
for r in low:
    print(f"  {r['id']} ({r['lang']}, {r['kind']}): {r['text'][:90]!r}")
print("\ncorrections and errors reported:")
for r in rows:
    if (r.get("ERR") or "").strip() or (r.get("correction") or "").strip():
        print(f"  {r['id']}: ERR={r['ERR'].strip()!r} -> {r['correction'].strip()!r}")
