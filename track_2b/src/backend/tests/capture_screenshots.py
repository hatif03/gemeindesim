"""Capture GemeindeSim UI screenshots during a live Linden run."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "screenshots"
DATA = ROOT / "data"


def shot(page, name: str) -> None:
    path = OUT / name
    page.screenshot(path=str(path), full_page=False)
    print(f"saved {path}", flush=True)


def notes() -> str:
    de = (DATA / "steuerfuss_linden_balanced_de.txt").read_text(encoding="utf-8")
    fr = (DATA / "steuerfuss_linden_balanced_fr.txt").read_text(encoding="utf-8")
    return de.strip() + "\n\n" + fr.strip()


def launch_browser(p):
    args = [
        "--use-gl=angle",
        "--use-angle=gl",
        "--enable-webgl",
        "--ignore-gpu-blocklist",
        "--disable-features=LazyImageLoading,MSEdgeLazyImageLoading",
        "--force-device-scale-factor=1",
    ]
    for channel in ("msedge", "chrome", None):
        try:
            kwargs = {"headless": True, "args": args}
            if channel:
                kwargs["channel"] = channel
            browser = p.chromium.launch(**kwargs)
            print(f"browser channel={channel or 'chromium'}", flush=True)
            return browser
        except Exception as exc:
            print(f"launch failed channel={channel}: {exc}", flush=True)
    raise RuntimeError("could not launch a Chromium browser")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    url = "http://localhost:3000"
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.set_default_timeout(60000)
        page.on("console", lambda msg: print(f"console:{msg.type}:{msg.text}", flush=True))
        page.on("pageerror", lambda exc: print(f"pageerror:{exc}", flush=True))
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(5500)
        shot(page, "01-intro.png")

        page.get_by_test_id("play-button").wait_for(state="visible", timeout=20000)
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(2500)
        shot(page, "02-title.png")

        play = page.get_by_test_id("play-button")
        play.wait_for(state="visible", timeout=20000)
        play.click()
        page.wait_for_selector("[data-testid='policy-textarea']", timeout=30000)
        page.wait_for_timeout(1500)
        shot(page, "03-nodecanvas.png")

        textarea = page.locator("[data-testid='policy-textarea']")
        textarea.scroll_into_view_if_needed()
        textarea.fill(notes())
        page.wait_for_timeout(400)
        shot(page, "04-policy-loaded.png")

        run = page.locator("[data-testid='run-button']")
        run.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        if run.is_disabled():
            shot(page, "04b-run-disabled.png")
            print("run button still disabled", file=sys.stderr)
            browser.close()
            return 1
        run.click()
        try:
            page.wait_for_url("**/simulate**", timeout=180000)
        except PlaywrightTimeout:
            shot(page, "05-simulate-timeout.png")
            print("did not reach /simulate", file=sys.stderr)
            browser.close()
            return 1

        page.wait_for_timeout(2500)
        shot(page, "05-simulate-loading.png")

        try:
            page.wait_for_selector("[data-testid='event-item']", timeout=300000)
        except PlaywrightTimeout:
            shot(page, "06-dashboard-timeout.png")
            print("live events did not appear", file=sys.stderr)
        else:
            page.wait_for_timeout(4000)
            shot(page, "06-simulate-live.png")

        try:
            page.wait_for_selector(
                "[data-testid='economic-report-modal']", timeout=600000
            )
            page.wait_for_timeout(800)
            shot(page, "07-economic-report.png")
        except PlaywrightTimeout:
            shot(page, "07-report-timeout.png")
            print("report modal did not appear", file=sys.stderr)
            browser.close()
            return 1

        browser.close()
    print("ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
