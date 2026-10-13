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
ZOOM = 1.25  # the page is drawn 25 % larger on the same 1920x1080 pixels (CSS viewport 1536x864)

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


import ctypes
import ctypes.wintypes as wt
import threading

import psutil

_user32 = ctypes.windll.user32
_HWND_TOPMOST, _SWP_NOMOVE, _SWP_NOSIZE, _SWP_SHOWWINDOW = -1, 0x2, 0x1, 0x40


def _browser_windows():
    """Visible top-level windows that belong to the Chrome processes this script started (not the user's own Chrome)."""
    pids = set()
    for c in psutil.Process().children(recursive=True):
        try:
            if "chrome" in c.name().lower():
                pids.add(c.pid)
        except psutil.Error:
            pass
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        pid = wt.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids and _user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    _user32.EnumWindows(cb, 0)
    return found, pids


def _fg_pid():
    pid = wt.DWORD()
    _user32.GetWindowThreadProcessId(_user32.GetForegroundWindow(), ctypes.byref(pid))
    return pid.value


def keep_on_top(stop):
    """A window started from a background process opens behind the foreground app and a notification can bring another window forward:
    the screen recording would then show the wrong window. Keep this script's Chrome topmost and in the foreground."""
    while not stop.is_set():
        try:
            wins, pids = _browser_windows()
            for h in wins:
                _user32.SetWindowPos(h, _HWND_TOPMOST, 0, 0, 0, 0, _SWP_NOMOVE | _SWP_NOSIZE | _SWP_SHOWWINDOW)
            if wins:
                _user32.SetForegroundWindow(wins[0])
                if _fg_pid() not in pids:
                    print("WARNING: the recorded Chrome is not the foreground window", flush=True)
        except Exception as exc:  # noqa: BLE001  (a process can vanish between listing and asking its name)
            print("keep_on_top:", repr(exc)[:80], flush=True)
        stop.wait(1.0)


SCREEN = "--vp8" not in sys.argv  # default: record the real screen (headed Chrome, ffmpeg gdigrab, hardware H.264 at a high bitrate)
if not SCREEN:
    sys.argv.remove("--vp8")


class Scene:
    """One clip. Screen mode needs a 1920x1080 primary display with nothing else on it: do not touch the machine while it records."""

    def __init__(self, p, name):
        self.name, self.t0, self.marks, self.ff = name, time.time(), {}, None
        self.out = OUT / f"{name}.mp4"
        if SCREEN:
            self.browser = p.chromium.launch(
                channel="chrome", headless=False, ignore_default_args=["--enable-automation"],
                args=["--kiosk", "--window-position=0,0", f"--force-device-scale-factor={ZOOM}", "--ignore-gpu-blocklist", "--enable-webgl",
                      "--disable-infobars", "--no-first-run", "--disable-features=Translate"])
            self.ctx = self.browser.new_context(no_viewport=True)
        else:
            self.browser = p.chromium.launch(channel="chrome", headless=True, args=["--ignore-gpu-blocklist", "--enable-webgl"])
            rd = RAW / name
            shutil.rmtree(rd, ignore_errors=True)
            self.ctx = self.browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(rd), record_video_size={"width": W, "height": H})
        self.ctx.add_init_script(CURSOR_JS)
        self.pg = self.ctx.new_page()
        if SCREEN:
            self.stop_top = threading.Event()
            threading.Thread(target=keep_on_top, args=(self.stop_top,), daemon=True).start()
            self.pg.goto("data:text/html,<body style='background:%23000;margin:0'></body>")
            cdp = self.ctx.new_cdp_session(self.pg)  # a real full-screen window: the kiosk flag alone gives a smaller one
            wid = cdp.send("Browser.getWindowForTarget")["windowId"]
            cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {"windowState": "fullscreen"}})
            self.pg.wait_for_timeout(2500)
            wins, pids = _browser_windows()
            print("browser windows on top:", len(wins), "foreground is ours:", _fg_pid() in pids, flush=True)
            print("viewport", self.pg.evaluate("[innerWidth, innerHeight, devicePixelRatio]"), flush=True)
            self._start_ffmpeg()
        self.t0 = time.time()

    def _start_ffmpeg(self):
        base = ["ffmpeg", "-y", "-loglevel", "error", "-f", "gdigrab", "-framerate", "60", "-draw_mouse", "0", "-offset_x", "0", "-offset_y", "0",
                "-video_size", f"{W}x{H}", "-i", "desktop"]
        for enc in (["-c:v", "h264_qsv", "-preset", "veryslow", "-global_quality", "13", "-look_ahead", "0", "-pix_fmt", "nv12"],
                    ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "14", "-pix_fmt", "yuv420p"]):
            self.ff = subprocess.Popen(base + enc + [str(self.out)], stdin=subprocess.PIPE)
            time.sleep(2.5)
            if self.ff.poll() is None:
                print("encoder:", enc[1], flush=True)
                return
        raise RuntimeError("ffmpeg could not start")

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
        if SCREEN:
            self.pg.wait_for_timeout(1500)
            self.stop_top.set()
            self.ff.stdin.write(b"q")
            self.ff.stdin.flush()
            self.ff.wait(timeout=120)
            self.ctx.close()
            self.browser.close()
            dst = self.out
        else:
            video = self.pg.video
            self.ctx.close()
            self.browser.close()
            src = Path(video.path())
            dst = self.out
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-r", "30", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", str(dst)], check=True)
        (OUT / f"{self.name}.marks.json").write_text(json.dumps(self.marks, indent=1), encoding="utf-8")
        print(f"[{self.name}] saved {dst.name} ({dst.stat().st_size // 1_000_000} MB, {time.time() - self.t0:.0f}s)", flush=True)


SCROLLER_JS = """
() => { let e = document.elementFromPoint(innerWidth / 2, innerHeight * 0.55);
  while (e && !(e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY))) e = e.parentElement;
  if (!e) return null; window.__sc = e; return [e.scrollTop, e.clientHeight, e.scrollHeight]; }
"""


def report_tour(s, hold_top=18, step=260, dwell=5.0, hold_end=12):
    """The report modal is already open: read the top, then scroll it to the very end in small steps with time to read."""
    pg = s.pg
    s.mark("report modal on screen")
    pg.wait_for_timeout(hold_top * 1000)
    s.still("07-report")
    vw, vh = pg.evaluate("[innerWidth, innerHeight]")
    pg.mouse.move(vw / 2, vh * 0.55, steps=25)  # the wheel acts on what is under the pointer: it must be over the report
    pg.wait_for_timeout(500)
    info = pg.evaluate(SCROLLER_JS)
    print("report scroller", info, flush=True)
    for i in range(40):
        pg.mouse.wheel(0, step)
        pg.wait_for_timeout(int(dwell * 1000))
        top, ch, sh = pg.evaluate("() => [window.__sc ? window.__sc.scrollTop : 0, window.__sc ? window.__sc.clientHeight : 0, window.__sc ? window.__sc.scrollHeight : 0]")
        if i in (3, 7):
            s.still(f"08-report-scroll-{i}")
        if top + ch >= sh - 4:
            break
    s.mark("report end reached")
    s.still("08-report-end")
    pg.wait_for_timeout(hold_end * 1000)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(2500)
    s.mark("report closed")


QUESTIONS = [
    "Wie viel mehr Steuern muesste Ihr Haushalt pro Jahr zahlen?",
    "Was sagt die Vorlage zum Schulhauskredit?",
    "Soll ich Ja oder Nein stimmen?",
]


def chat_tour(s, questions=QUESTIONS, hold=10):
    """Open a resident from the event log and ask real questions; wait for each answer to arrive, then hold on it."""
    pg = s.pg
    s.click('[data-testid="event-item"]')
    s.mark("resident opened")
    inp = pg.locator('input[placeholder="Say something..."]')
    inp.wait_for(state="visible", timeout=30000)
    pg.wait_for_timeout(5000)
    s.still("09-resident-profile")
    for i, q in enumerate(questions):
        s.click('input[placeholder="Say something..."]')
        pg.keyboard.type(q, delay=45)
        pg.keyboard.press("Enter")
        s.mark(f"question {i + 1} sent")
        pg.wait_for_timeout(1500)
        for _ in range(120):  # the input is disabled while the answer is being produced
            if inp.is_enabled():
                break
            pg.wait_for_timeout(1000)
        s.mark(f"answer {i + 1} shown")
        pg.wait_for_timeout(hold * 1000)
        s.still(f"10-chat-answer-{i + 1}")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(2500)


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
    pg.wait_for_timeout(3000)
    report_tour(s)
    chat_tour(s)
    s.finish()


def chat(p):
    """A short run (5 residents, 3 rounds), then the report and a 1:1 chat with a resident (also used to test the tours)."""
    s = Scene(p, "04_resident_chat")
    pg = s.pg
    fill_editor(s, npcs=5, rounds=3)
    s.click('[data-testid="run-button"]')
    s.mark("run pressed")
    pg.wait_for_url("**/simulate**", timeout=60000)
    pg.wait_for_selector('[data-testid="event-item"]', timeout=300000)
    s.mark("first event")
    for _ in range(300):
        pg.wait_for_timeout(2500)
        if "COMPLETE" in pg.inner_text("body"):
            break
    s.mark("complete")
    pg.wait_for_timeout(3000)
    report_tour(s, hold_top=6, hold_end=3)
    chat_tour(s, QUESTIONS, hold=4)
    s.finish()


def replay(p):
    """LOAD the recorded demo run (docs/replays/linden_25x5_cscs.replay.json) and let it play to the report."""
    s = Scene(p, "05_replay_demo_run")
    pg = s.pg
    pg.goto(URL)
    pg.wait_for_selector('[data-testid="play-button"]', timeout=60000)
    pg.wait_for_timeout(3000)
    load = pg.locator('xpath=//button[@data-testid="play-button"]/following-sibling::button').first
    box = load.bounding_box()
    pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=35)  # point at LOAD; no click: the native file dialog would show the user's folders
    pg.wait_for_timeout(2000)
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
