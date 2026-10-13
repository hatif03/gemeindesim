"""One-off: last cuts to reach six pages."""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "report" / "report.html"
s = P.read_text(encoding="utf-8")


def cut_div(marker):
    """Remove the <div class="fig"> that contains marker."""
    global s
    k = s.index(marker)
    i = s.rfind('<div class="fig">', 0, k)
    j = s.index("</div>", k) + 7
    s = s[:i] + s[j:]


cut_div("fig08-endpoints.png")
cut_div("fig10-time-budget.png")
s = s.replace("<b>One build, both endpoints (E31):</b>", "<b>One build, both endpoints (E31; same code and seeds, the 5-resident 3-round run took 61 s on CSCS and 126 s on the gateway; the gateway answers 429 above 4&ndash;5 requests in flight, CSCS took 2,496 requests up to 96 in flight without one; Python used 2.2&ndash;5.0&nbsp;% of the wall time, E29):</b>", 1)
s = s.replace(".refs { font-size: 6.2pt;", ".refs { font-size: 5.9pt;", 1)
P.write_text(s, encoding="utf-8")
print("ok")
