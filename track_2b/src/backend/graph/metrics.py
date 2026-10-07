"""Token, cache, latency and context accounting for one simulation (or one chat / spread run).

The endpoint already reports usage with every completion (prompt, completion and, on CSCS, cached tokens); we only had it in the research logs.
`RunMetrics.record` is called from the single place every JSON call goes through (`graph.llm._ainvoke`) and from the chat; the run's metrics object is
found through a ContextVar, so concurrent tasks of one simulation write to the same object and two simulations never mix (asyncio tasks copy the context).
The frontend shows the snapshot (`round` messages carry it, plus a final `metrics` event and `GET /simulate/{id}/metrics`).
"""

from __future__ import annotations

import statistics as st
import time
from collections import Counter
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

CONTEXT_WINDOW = 262_144  # Apertus v1.5 on both endpoints (research E22); only used to express usage as a share


@dataclass
class RunMetrics:
    started: float = field(default_factory=time.monotonic)
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    max_prompt_tokens: int = 0
    latencies: list[float] = field(default_factory=list)
    by_model: Counter = field(default_factory=Counter)
    events: Counter = field(default_factory=Counter)  # rate_limited, gateway_5xx_retried, downgraded, failed

    def record(self, model: str, usage: dict[str, Any] | None, latency: float) -> None:
        usage = usage if isinstance(usage, dict) else {}
        prompt = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        out = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        cached = int(((usage.get("input_token_details") or {}).get("cache_read")) or ((usage.get("prompt_tokens_details") or {}).get("cached_tokens")) or 0)
        self.calls += 1
        self.prompt_tokens += prompt
        self.completion_tokens += out
        self.cached_tokens += cached
        self.max_prompt_tokens = max(self.max_prompt_tokens, prompt)
        self.latencies.append(latency)
        self.by_model[model] += 1

    def note(self, event: str) -> None:
        self.events[event] += 1

    def snapshot(self, model: str = "", base_url: str = "", limit: float | None = None) -> dict[str, Any]:
        lat = sorted(self.latencies)
        n = len(lat)
        mean_prompt = self.prompt_tokens / self.calls if self.calls else 0
        return {
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cached_tokens": self.cached_tokens,
            "cache_hit_rate": round(self.cached_tokens / self.prompt_tokens, 3) if self.prompt_tokens else 0.0,
            "mean_prompt_tokens": round(mean_prompt),
            "max_prompt_tokens": self.max_prompt_tokens,
            "context_window": CONTEXT_WINDOW,
            "mean_context_use": round(mean_prompt / CONTEXT_WINDOW, 4),
            "max_context_use": round(self.max_prompt_tokens / CONTEXT_WINDOW, 4),
            "mean_latency_s": round(st.mean(lat), 2) if n else 0.0,
            "p95_latency_s": round(lat[min(n - 1, int(0.95 * n))], 2) if n else 0.0,
            "decode_tokens_per_s": round(self.completion_tokens / sum(lat), 1) if n and sum(lat) else 0.0,
            "elapsed_s": round(time.monotonic() - self.started, 1),
            "rate_limited": self.events["rate_limited"],
            "gateway_retries": self.events["gateway_5xx_retried"],
            "downgraded": self.events["downgraded_to_fallback_model"],
            "failed": self.events["failed"],
            "models": dict(self.by_model),
            "model": model,
            "endpoint": urlparse(base_url).netloc if base_url else "",
            "in_flight_limit": limit,
        }


current_metrics: ContextVar[RunMetrics | None] = ContextVar("current_metrics", default=None)
PROCESS_METRICS = RunMetrics()  # everything since the process started (GET /metrics)


def record_call(model: str, usage: dict[str, Any] | None, latency: float) -> None:
    PROCESS_METRICS.record(model, usage, latency)
    m = current_metrics.get()
    if m is not None:
        m.record(model, usage, latency)


def note_event(event: str) -> None:
    PROCESS_METRICS.note(event)
    m = current_metrics.get()
    if m is not None:
        m.note(event)
