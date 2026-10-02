"""One-shot gateway probe. Do not commit secrets; reads track_2b/.env."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

KEY = os.environ["LLM_API_KEY"]
BASE = os.environ["LLM_BASE_URL"].rstrip("/")
MODEL = os.environ.get("LLM_NAME", "apertus-v1.5-70b")


def chat(prompt: str, json_mode: bool = True) -> dict:
    body: dict = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}],
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def main() -> None:
    prompt = (
        "Output ONLY the following JSON with the placeholder values filled in.\n"
        '{"sectors": ["..."], "stakeholders": ["..."], '
        '"economic_impacts": ["..."], "controversy_level": "high"}\n\n'
        "Policy: Gemeinde Linden raises Steuerfuss from 118% to 124% "
        "and a 4.8 million CHF school credit."
    )
    resp = chat(prompt)
    msg = resp["choices"][0]["message"]
    content = msg.get("content") or ""
    print("finish", resp["choices"][0].get("finish_reason"))
    print("content_len", len(content))
    print("has_inner", "<|inner_prefix|>" in content)
    print("content_head:")
    print(content[:1200])
    try:
        parsed = json.loads(content)
        print("parsed_keys", list(parsed))
    except json.JSONDecodeError as exc:
        print("json_decode_error", exc)


if __name__ == "__main__":
    main()
