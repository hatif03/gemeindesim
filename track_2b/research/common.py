"""Shared harness for the GemeindeSim research experiments.

Every gateway call is appended to research/results/<exp>.jsonl with the full
request and response, so any number in the write-up can be re-derived.
Run scripts with:  uv run --project src/backend python research/<script>.py
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]  # track_2b/
RESULTS = Path(__file__).resolve().parent / "results" / os.environ.get("RESEARCH_SUBDIR", "")  # e.g. RESEARCH_SUBDIR=cscs for another endpoint
RESULTS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src" / "backend"))  # reuse the app's own modules
load_dotenv(ROOT / ".env")

BASE = os.environ["LLM_BASE_URL"].rstrip("/")
KEY = os.environ["LLM_API_KEY"]
M70, M8 = os.environ.get("RESEARCH_M70", "apertus-v1.5-70b"), os.environ.get("RESEARCH_M8", "apertus-v1.5-8b")


class Gateway:
    """Rate-limited chat client with raw-call logging."""

    def __init__(self, exp: str, concurrency: int | None = None):  # livemap gateway limit: ~4 in flight per key
        concurrency = int(os.environ.get("RESEARCH_CONCURRENCY", concurrency or 3))
        self.exp = exp
        self.sem = asyncio.Semaphore(concurrency)
        self.log = RESULTS / f"{exp}.jsonl"
        self.client = httpx.AsyncClient(timeout=180, trust_env=False)

    async def chat(self, prompt=None, *, messages=None, model=M70, temperature=0.0,
                   max_tokens=600, json_mode=False, thinking=False, tools=None,
                   tool_choice=None, tag="", extra=None, seed=None) -> dict:
        body = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": messages or [{"role": "user", "content": prompt}],
            "chat_template_kwargs": {"enable_thinking": thinking},
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if tools:
            body["tools"] = tools
        if tool_choice:
            body["tool_choice"] = tool_choice
        if seed is not None:
            body["seed"] = seed
        body.update(extra or {})
        rec: dict = {"exp": self.exp, "tag": tag, "ts": time.time(), "req": body}
        async with self.sem:
            for attempt in range(9):
                t0 = time.perf_counter()
                try:
                    r = await self.client.post(
                        BASE + "/chat/completions", json=body,
                        headers={"Authorization": f"Bearer {KEY}"})
                    rec["latency_s"] = round(time.perf_counter() - t0, 3)
                    rec["http"] = r.status_code
                    if r.status_code in (429, 500, 502, 503, 504):
                        rec["retries"] = attempt + 1
                        await asyncio.sleep(min(30, 2 ** attempt))
                        continue
                    data = r.json()
                    break
                except (httpx.HTTPError, ValueError) as exc:
                    rec["error"] = repr(exc)
                    await asyncio.sleep(min(30, 2 ** attempt))
            else:
                data = {}
                rec["api_failed"] = True
        ch = (data.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        rec["resp"] = {
            "content": msg.get("content") or "",
            "tool_calls": msg.get("tool_calls"),
            "reasoning": (msg.get("provider_specific_fields") or {}).get("reasoning") or msg.get("reasoning") or msg.get("reasoning_content"),
            "finish": ch.get("finish_reason"),
            "usage": data.get("usage"),
            "raw_error": data.get("error") if "error" in data else None,
        }
        with self.log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    async def close(self):
        await self.client.aclose()


def phash(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def load_jsonl(exp: str) -> list[dict]:
    p = RESULTS / f"{exp}.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def read_sample(name: str) -> str:
    return (ROOT / "data" / name).read_text(encoding="utf-8")
