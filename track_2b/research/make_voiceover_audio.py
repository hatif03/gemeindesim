"""Turn the two voice-over scripts into MP3 files with several male neural voices (Microsoft Edge online TTS via the edge-tts package).

    python research/make_voiceover_audio.py            # all voices, both scripts
    python research/make_voiceover_audio.py Andrew     # only voices whose name contains "Andrew"

Output (track_2b/audio, not committed): samples/<voice>.mp3, <voice>/submission_full.mp3, <voice>/youtube_full.mp3 and one file per
script paragraph in <voice>/segments/ (named with its start time, so each can be placed at that time in the editor), plus a timing report.
The script text is sent to Microsoft's online speech service. Needs ffmpeg on PATH.
"""
from __future__ import annotations

import asyncio
import re
import subprocess
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audio"
RATE = "-8%"  # a little slower than the default: calmer (the long YouTube narration)
RATE_SUBMISSION = "+0%"  # the submission video must stay under two minutes: at -8% the narration is 2:01
VOICES = [  # (short name, multilingual: pronounces the German words itself)
    ("en-US-AndrewMultilingualNeural", True),
    ("en-US-BrianMultilingualNeural", True),
    ("en-US-ChristopherNeural", False),
    ("en-GB-RyanNeural", False),
    ("en-GB-ThomasNeural", False),
    ("en-IE-ConnorNeural", False),
    ("en-AU-WilliamMultilingualNeural", True),
]
RESPELL = {"GemeindeSim": "Guh-mine-duh-sim", "Steuerfuss": "Shtoy-er-foos"}  # for voices that do not speak German


def norm(text: str, multilingual: bool) -> str:
    t = text.replace("(cut)", "").replace("`", "")
    t = re.sub(r"\*+", "", t)
    t = t.replace("one-N-E", "one N E").replace("CSCS", "C S C S").replace("JSON", "Jay-son")
    if not multilingual:
        for a, b in RESPELL.items():
            t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def secs(mmss: str) -> int:
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)


def parse_submission() -> list[tuple[int, str]]:
    rows = []
    for line in (ROOT / "docs/VIDEO-VOICEOVER.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d:\d\d) \| (.*?) \| (.*) \|$", line)
        if m:
            rows.append((secs(m.group(1)), m.group(2)))
    return rows


def parse_youtube() -> list[tuple[int, str]]:
    s = (ROOT / "docs/YOUTUBE-VOICEOVER.md").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"\*\*(\d+:\d+) to (\d+:\d+): .*?\*\*\n\*Picture:.*?\*\n(.*?)\n\n", s, re.S):
        out.append((secs(m.group(1)), m.group(3)))
    return out


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


async def say(text: str, voice: str, path: Path, rate: str = RATE):
    """The online service sometimes answers a request with no audio (rate limiting): wait and try again."""
    for attempt in range(6):
        try:
            await edge_tts.Communicate(text, voice, rate=rate).save(str(path))
            await asyncio.sleep(1.0)
            return
        except edge_tts.exceptions.NoAudioReceived:
            await asyncio.sleep(3 + 3 * attempt)
    raise RuntimeError(f"no audio for: {text[:60]}")


def silence(path: Path, seconds: float):
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(seconds), "-c:a", "libmp3lame", "-b:a", "48k", str(path)])


def join(parts: list[Path], gap: Path, dst: Path):
    lst = dst.with_suffix(".txt")
    lines = []
    for i, p in enumerate(parts):
        lines.append(f"file '{p.as_posix()}'")
        if i < len(parts) - 1:
            lines.append(f"file '{gap.as_posix()}'")
    lst.write_text("\n".join(lines), encoding="utf-8")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", str(dst)])
    lst.unlink()


async def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else ""
    only = sys.argv[2] if len(sys.argv) > 2 else ""  # "submission" or "youtube"
    OUT.mkdir(exist_ok=True)
    (OUT / "samples").mkdir(exist_ok=True)
    gap = OUT / "_gap.mp3"
    silence(gap, 0.7)
    sub, yt = parse_submission(), parse_youtube()
    print(len(sub), "submission paragraphs,", len(yt), "youtube paragraphs")
    report = []
    for voice, ml in VOICES:
        short = voice.replace("Neural", "").replace("en-", "")
        if pick and pick.lower() not in voice.lower():
            continue
        d = OUT / short
        (d / "segments").mkdir(parents=True, exist_ok=True)
        # sample: the opening paragraph of the submission script
        raw = d / "_sample.mp3"
        await say(norm(sub[0][1], ml), voice, raw, RATE_SUBMISSION)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", str(OUT / "samples" / f"{short}.mp3")])
        raw.unlink()
        for name, items, prefix in (("submission", sub, "sub"), ("youtube", yt, "yt")):
            if only and only != name:
                continue
            rate = RATE_SUBMISSION if name == "submission" else RATE
            parts = []
            for i, (t0, text) in enumerate(items, 1):
                seg = d / "segments" / f"{prefix}_{i:02d}_{t0 // 60:02d}m{t0 % 60:02d}s.mp3"
                await say(norm(text, ml), voice, seg, rate)
                parts.append(seg)
                nxt = items[i][0] - t0 if i < len(items) else None
                report.append((short, name, i, t0, round(duration(seg), 1), nxt))
            join(parts, gap, d / f"{name}_full.mp3")
            print(short, name, "full:", round(duration(d / f'{name}_full.mp3')), "s", flush=True)
    lines = ["voice | script | paragraph | starts at (s) | narration (s) | room until the next paragraph starts (s)"]
    for r in report:
        flag = "" if r[5] is None or r[4] <= r[5] else "  <-- longer than its slot"
        lines.append(" | ".join(str(x) for x in r) + flag)
    (OUT / "timing_report.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
