"""Download the real Federal Council booklet used in E17 (not vendored: the repo does not commit official PDFs).

Source: Bundeskanzlei, "Erläuterungen des Bundesrates", Volksabstimmung vom 28. September 2025 (collection page
https://www.bk.admin.ch/bk/de/home/dokumentation/abstimmungsbuechlein.html). Official Swiss federal documents are not
protected by copyright (URG Art. 5); the repo still keeps them out of version control.
Usage: python research/download_booklet.py   ->  research/data/booklets/erlaeuterungen_2025-09-28_de.{pdf,txt}
"""
from pathlib import Path

import httpx
from pypdf import PdfReader

URL = "https://www.bk.admin.ch/dam/de/sd-web/6DaWglL-N7NM/2025-09-28_erlaeuterungen_des_bundesrates.pdf"
OUT = Path(__file__).resolve().parent / "data" / "booklets"
OUT.mkdir(parents=True, exist_ok=True)
pdf = OUT / "erlaeuterungen_2025-09-28_de.pdf"
if not pdf.exists():
    r = httpx.get(URL, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True, timeout=120)
    r.raise_for_status()
    pdf.write_bytes(r.content)
text = "\n".join((p.extract_text() or "") for p in PdfReader(pdf).pages)
(OUT / "erlaeuterungen_2025-09-28_de.txt").write_text(text, encoding="utf-8")
print(f"{pdf.name}: {len(text)} characters")
