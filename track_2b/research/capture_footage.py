"""Capture demo footage of the running app (UI on localhost:3000, API on localhost:8000) with headless Chrome.

    python research/capture_footage.py title editor live        # any of: title editor live chat replay

Writes 1920x1080 clips to track_2b/footage/<scene>.mp4 (+ <scene>.marks.json with the time of key moments, in seconds, for editing)
and stills to track_2b/footage/stills/. The app has no audio track, so the clips are silent. The cursor is drawn as a yellow dot.
The "live" scene runs a real simulation (25 residents x 5 rounds on whatever endpoint .env points at) and takes about 8 minutes.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "footage"
STILLS = OUT / "stills"
RAW = OUT / "_raw"
for d in (OUT, STILLS, RAW):
    d.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:3000"
DOC = "\n\n".join((ROOT / f"data/steuerfuss_linden_balanced_{x}.txt").read_text(encoding="utf-8").strip() for x in ("de", "fr"))
OBJECTIVE = "How the Steuerfuss and school credit land on households and shops"
W, H = 1920, 1080

CURSOR_JS = """
(() => {
  const get = () => { let d = document.getElementById('__cur'); if (!d) { d = document.createElement('div'); d.id = '__cur';
    d.style.cssText = 'position:fixed;left:-60px;top:-60px;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;background:rgba(255,190,40,.55);border:2px solid #fff;box-shadow:0 0 8px rgba(0,0,0,.6);pointer-events:none;z-index:2147483647;transition:transform .12s';
    document.documentElement.appendChild(d); } return d; };
  addEventListener('mousemove', e => { const d = get(); d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', () => { get().style.transform = 'scale(.7)'; }, true);
  addEventListener('mouseup', () => { get().style.transform = 'scale(1)'; }, true);
})();
"""


class Scene:
    def __init__(self, p, name):
        self.name, self.t0, self.marks = name, time.time(), {}
        self.browser = p.chromium.launch(channel="chrome", headless=True, args=["--ignore-gpu-blocklist", "--enable-webgl"])
        rd = RAW / name
        shutil.rmtree(rd, ignore_errors=True)
        self.ctx = self.browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(rd), record_video_size={"width": W, "height": H})
        self.ctx.add_init_script(CURSOR_JS)
        self.pg = self.ctx.new_page()
        self.rd = rd

    def mark(self, label):
        self.marks[label] = round(time.time() - self.t0, 1)
        print(f"[{self.name}] {self.marks[label]:7.1f}s  {label}", flush=True)

    def still(self, name):
        self.pg.screenshot(path=str(STILLS / f"{name}.png"))

    def click(self, sel, **kw):
        loc = self.pg.locator(sel).first
        loc.wait_for(state="visible", timeout=60000)
        box = loc.bounding_box()
        self.pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=35)
        self.pg.wait_for_timeout(250)
        loc.click(**kw)

    def finish(self):
        video = self.pg.video
        self.ctx.close()
        self.browser.close()
        src = Path(video.path())
        dst = OUT / f"{self.name}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-r", "30", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", str(dst)], check=True)
        (OUT / f"{self.name}.marks.json").write_text(json.dumps(self.marks, indent=1), encoding="utf-8")
        print(f"[{self.name}] saved {dst.name} ({dst.stat().st_size // 1_000_000} MB, {time.time() - self.t0:.0f}s)", flush=True)


def title(p):
    s = Scene(p, "01_intro_title")
    s.pg.goto(URL)
    s.mark("intro animation")
    s.pg.wait_for_selector('[data-testid="play-button"]', timeout=60000)
    s.mark("title screen")
    s.pg.wait_for_timeout(6000)
    s.still("01-title")
    s.finish()


def fill_editor(s, npcs=25, rounds=5):
    pg = s.pg
    pg.goto(URL)
    pg.wait_for_selector('[data-testid="play-button"]', timeout=60000)
    pg.wait_for_timeout(2500)
    s.click('[data-testid="play-button"]')
    s.mark("editor opened")
    pg.wait_for_selector('[data-testid="policy-textarea"]', timeout=60000)
    pg.evaluate("document.querySelectorAll('textarea').forEach(t => { t.spellcheck = false; })")
    pg.wait_for_timeout(2500)
    s.click('[data-testid="policy-textarea"]')
    pg.wait_for_timeout(600)
    pg.fill('[data-testid="policy-textarea"]', DOC)  # a paste
    s.mark("document pasted")
    pg.wait_for_timeout(3500)
    s.still("02-editor-document")
    s.click('[data-testid="objective-textarea"]')
    pg.fill('[data-testid="objective-textarea"]', OBJECTIVE)
    pg.wait_for_timeout(1200)
    for tid, target in (("npcs-slider", npcs), ("rounds-slider", rounds)):
        loc = pg.locator(f'[data-testid="{tid}"]')
        box = loc.bounding_box()
        pg.mouse.move(box["x"] + box["width"] * 0.5, box["y"] + box["height"] / 2, steps=30)
        loc.focus()  # keyboard only: a click would jump to the click position
        for _ in range(60):
            v = int(loc.input_value())
            if v == target:
                break
            pg.keyboard.press("ArrowRight" if v < target else "ArrowLeft")
            pg.wait_for_timeout(70)
        pg.wait_for_timeout(500)
    s.mark(f"{npcs} residents, {rounds} rounds")
    pg.wait_for_timeout(2500)
    s.still("03-editor-config")


def editor(p):
    s = Scene(p, "02_editor_config")
    fill_editor(s)
    s.pg.wait_for_timeout(2000)
    s.finish()


def live(p):
    s = Scene(p, "03_live_run")
    pg = s.pg
    fill_editor(s)
    s.click('[data-testid="run-button"]')
    s.mark("run pressed")
    pg.wait_for_url("**/simulate**", timeout=60000)
    pg.wait_for_selector('[data-testid="event-item"]', timeout=300000)
    s.mark("first event")
    pg.wait_for_timeout(15000)
    s.still("04-live-map")
    metrics_done = graph_done = False
    t_end = time.time() + 1500
    while time.time() < t_end:
        pg.wait_for_timeout(2500)
        txt = pg.inner_text("body")
        if not metrics_done and time.time() - s.t0 > 150:
            try:
                s.click('button:has-text("RUN METRICS")')
                pg.wait_for_timeout(5000)
                s.still("05-run-metrics")
                s.click('button:has-text("RUN METRICS")')
                metrics_done = True
                s.mark("metrics panel shown")
            except Exception as e:  # noqa: BLE001
                print("metrics click failed", e)
                metrics_done = True
        if not graph_done and time.time() - s.t0 > 260:
            try:
                s.click('text=GRAPH')
                pg.wait_for_timeout(9000)
                s.still("06-influence-graph")
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(500)
                graph_done = True
                s.mark("influence graph shown")
            except Exception as e:  # noqa: BLE001
                print("graph click failed", e)
                graph_done = True
        if "COMPLETE" in txt:
            break
    s.mark("complete")
    pg.wait_for_timeout(6000)
    s.still("07-report")
    s.mark("report modal on screen")
    pg.wait_for_timeout(9000)
    pg.mouse.wheel(0, 700)
    pg.wait_for_timeout(5000)
    pg.mouse.wheel(0, 900)
    pg.wait_for_timeout(5000)
    s.still("08-report-lower")
    s.finish()


def chat(p):
    """A short run (5 residents, 2 rounds), then a 1:1 chat with a resident: a cited answer and a refused vote recommendation."""
    s = Scene(p, "04_resident_chat")
    pg = s.pg
    fill_editor(s, npcs=5, rounds=2)
    s.click('[data-testid="run-button"]')
    s.mark("run pressed")
    pg.wait_for_url("**/simulate**", timeout=60000)
    pg.wait_for_selector('[data-testid="event-item"]', timeout=300000)
    s.mark("first event")
    pg.wait_for_timeout(20000)
    s.click('[data-testid="event-item"]')
    s.mark("resident opened")
    box = pg.get_by_placeholder("Say something...")
    box.wait_for(state="visible", timeout=30000)
    pg.wait_for_timeout(4000)
    s.still("09-resident-profile")
    for i, q in enumerate(["Wie viel mehr Steuern muesste Ihr Haushalt pro Jahr zahlen?", "Soll ich Ja oder Nein stimmen?"]):
        before = pg.locator('[data-testid="chat-bubble"]').count()
        s.click('input[placeholder="Say something..."], textarea[placeholder="Say something..."]')
        pg.keyboard.type(q, delay=45)
        pg.keyboard.press("Enter")
        s.mark(f"question {i + 1} sent")
        for _ in range(60):
            pg.wait_for_timeout(1000)
            if pg.locator('[data-testid="chat-bubble"]').count() >= before + 2 and not pg.locator('[data-testid="chat-streaming"]').count():
                break
        pg.wait_for_timeout(4000)
        s.still(f"10-chat-answer-{i + 1}")
        s.mark(f"answer {i + 1} shown")
    pg.wait_for_timeout(3000)
    s.finish()


def replay(p):
    """LOAD the recorded demo run (docs/replays/linden_25x5_cscs.replay.json) and let it play to the report."""
    s = Scene(p, "05_replay_demo_run")
    pg = s.pg
    pg.goto(URL)
    pg.wait_for_selector('[data-testid="play-button"]', timeout=60000)
    pg.wait_for_timeout(3000)
    s.click('xpath=//button[@data-testid="play-button"]/following-sibling::button')
    pg.wait_for_timeout(1500)
    s.mark("file chosen")
    pg.set_input_files("input[type=file]", str(ROOT / "docs/replays/linden_25x5_cscs.replay.json"))
    pg.wait_for_url("**/simulate**", timeout=30000)
    pg.wait_for_selector('[data-testid="event-item"]', timeout=120000)
    s.mark("replay playing")
    pg.wait_for_timeout(20000)
    s.still("11-replay-round1")
    t_end = time.time() + 1500
    while time.time() < t_end:
        pg.wait_for_timeout(3000)
        if "COMPLETE" in pg.inner_text("body"):
            break
    s.mark("complete")
    pg.wait_for_timeout(8000)
    s.still("12-replay-report")
    s.finish()


if __name__ == "__main__":
    scenes = sys.argv[1:] or ["title", "editor"]
    with sync_playwright() as p:
        for name in scenes:
            {"title": title, "editor": editor, "live": live, "chat": chat, "replay": replay}[name](p)
