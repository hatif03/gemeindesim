"""Render docs/MENTOR-BRIEF.md to a self-contained HTML (images embedded) and a PDF with headless Chrome/Edge.

    python research/build_brief.py        # needs `pip install markdown`; writes docs/MENTOR-BRIEF.html and .pdf
"""

import base64
import re
import subprocess
from pathlib import Path

import markdown

DOCS = Path(__file__).resolve().parents[1] / "docs"
md = (DOCS / "MENTOR-BRIEF.md").read_text(encoding="utf-8")
body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc", "sane_lists"], extension_configs={"toc": {"permalink": False}})


def embed(m):
    src = m.group(1)
    data = base64.b64encode((DOCS / src).read_bytes()).decode()
    return f'src="data:image/png;base64,{data}"'


body = re.sub(r'src="([^"]+\.png)"', embed, body)
css = """
@page { size: A4; margin: 14mm 12mm; }
body { font: 11pt/1.5 -apple-system, "Segoe UI", Arial, sans-serif; color: #1c1c1c; max-width: 900px; margin: 0 auto; padding: 0 12px; }
h1 { font-size: 22pt; border-bottom: 3px solid #3E7C34; padding-bottom: 6px; }
h2 { font-size: 16pt; margin-top: 28px; border-bottom: 1px solid #ccc; padding-bottom: 3px; page-break-after: avoid; }
h3 { font-size: 13pt; margin-top: 20px; page-break-after: avoid; }
h4 { font-size: 11.5pt; margin-top: 18px; background: #eef3ea; padding: 4px 8px; border-left: 4px solid #3E7C34; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 4px 7px; vertical-align: top; text-align: left; }
th { background: #f0eee6; }
code { background: #f3f3f3; padding: 0 3px; border-radius: 3px; font-size: 90%; }
pre { background: #f3f3f3; padding: 8px; overflow-x: auto; font-size: 9pt; }
img { max-width: 100%; height: auto; display: block; margin: 12px auto; page-break-inside: avoid; }
blockquote { border-left: 4px solid #3B6EA5; margin: 12px 0; padding: 4px 14px; background: #eef3fa; font-size: 12pt; }
a { color: #1d5fa8; }
"""
html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GemeindeSim mentor brief</title><style>{css}</style></head><body>{body}</body></html>'
out_html = DOCS / "MENTOR-BRIEF.html"
out_html.write_text(html, encoding="utf-8")

CHROME = next((p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                           "/usr/bin/google-chrome", "/usr/bin/chromium") if Path(p).exists()), None)
if CHROME:
    out_pdf = DOCS / "MENTOR-BRIEF.pdf"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}", out_html.as_uri()], check=True, capture_output=True, timeout=180)
    print("wrote", out_html.name, f"({out_html.stat().st_size // 1024} kB)", "and", out_pdf.name, f"({out_pdf.stat().st_size // 1024} kB)")
else:
    print("wrote", out_html.name, "(no Chrome/Edge found for the PDF)")
