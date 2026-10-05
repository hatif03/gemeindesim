"""Render report/report.html to <Team>_Report.pdf with headless Chrome and check the page limit (max 6 pages).

Usage: python research/build_report_pdf.py [output_name.pdf]      (default: GemeindeSim_Report.pdf in track_2b/)
"""
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "report" / "report.html"
OUT = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "GemeindeSim_Report.pdf")
CHROME = next((p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                           "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser") if Path(p).exists()), None)
if CHROME is None:
    sys.exit("No Chrome/Edge/Chromium found; print report/report.html to PDF from any browser (A4, no headers).")
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT}", SRC.as_uri()],
               check=True, capture_output=True, timeout=120)
pages = len(PdfReader(OUT).pages)
print(f"{OUT.name}: {pages} pages" + ("" if pages <= 6 else "  **OVER THE 6-PAGE LIMIT**"))
sys.exit(0 if pages <= 6 else 1)
