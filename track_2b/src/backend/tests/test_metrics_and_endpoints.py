"""Token accounting, the adaptive limiter and interchangeable endpoints (research E29)."""

import asyncio

import pytest

import config
from graph import llm as L
from graph.metrics import RunMetrics, current_metrics, record_call


def test_model_ids_are_valid_for_the_endpoint_they_are_sent_to():
    cscs, live = "https://api.inference.cscs.ch/v1", "https://hackapertus.livemap.sh/v1"
    assert config.resolve_model("apertus-v1.5-70b", cscs) == "swiss-ai/Apertus-v1.5-70B"
    assert config.resolve_model("swiss-ai/Apertus-v1.5-8B", live) == "apertus-v1.5-8b"
    assert config.resolve_model("swiss-ai/Apertus-v1.5-70B-thinking", cscs) == "swiss-ai/Apertus-v1.5-70B-thinking"
    assert config.resolve_model("swiss-ai/Apertus-v1.5-70B", "http://localhost:8000/v1") == "swiss-ai/Apertus-v1.5-70B"  # a local vLLM keeps the id
    assert config.resolve_model("some/other-model", cscs) == "some/other-model"
    assert config.resolve_model("", cscs) == ""


def test_the_fallback_is_the_8b_of_the_same_naming_style(monkeypatch):
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://api.inference.cscs.ch/v1")
    assert config.smaller_model("swiss-ai/Apertus-v1.5-70B") == "swiss-ai/Apertus-v1.5-8B"
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://hackapertus.livemap.sh/v1")
    assert config.smaller_model("apertus-v1.5-70b") == "apertus-v1.5-8b"
    assert config.smaller_model("apertus-v1.5-8b") == "apertus-v1.5-8b"  # nothing smaller: no silent switch to another model
    assert config.smaller_model("my/local") == "my/local"


def test_metrics_count_tokens_cache_and_context_use():
    m = RunMetrics()
    m.record("apertus", {"input_tokens": 2000, "output_tokens": 300, "input_token_details": {"cache_read": 500}}, 4.0)
    m.record("apertus", {"input_tokens": 1000, "output_tokens": 100, "input_token_details": {}}, 2.0)
    s = m.snapshot("apertus", "https://api.inference.cscs.ch/v1", 8)
    assert (s["calls"], s["prompt_tokens"], s["completion_tokens"], s["cached_tokens"]) == (2, 3000, 400, 500)
    assert s["cache_hit_rate"] == round(500 / 3000, 3) and s["max_prompt_tokens"] == 2000
    assert s["max_context_use"] == round(2000 / s["context_window"], 4) and s["endpoint"] == "api.inference.cscs.ch" and s["in_flight_limit"] == 8
    assert s["decode_tokens_per_s"] == round(400 / 6.0, 1)


def test_unusable_usage_does_not_break_the_run():
    m = RunMetrics()
    m.record("x", None, 1.0)
    m.record("x", object(), 1.0)  # a mock or an endpoint without usage
    assert m.calls == 2 and m.prompt_tokens == 0


@pytest.mark.asyncio
async def test_calls_are_attributed_to_the_run_that_made_them_even_in_child_tasks():
    a, b = RunMetrics(), RunMetrics()

    async def run(metrics, n):
        current_metrics.set(metrics)

        async def child():
            await asyncio.sleep(0)
            record_call("m", {"input_tokens": 10, "output_tokens": 1}, 0.1)

        await asyncio.gather(*[child() for _ in range(n)])

    await asyncio.gather(run(a, 3), run(b, 5))
    assert (a.calls, b.calls) == (3, 5)


def test_adaptive_limiter_slow_starts_then_remembers_the_ceiling_that_worked():
    lim = L.Limiter(start=4, maximum=32, adaptive=True, grow_after=2)
    for _ in range(2):
        lim.ok()
    assert lim.limit == 8  # slow start doubles
    for _ in range(2):
        lim.ok()
    assert lim.limit == 16
    lim.pushback()  # 429 at 16 in flight: 15 is the largest value known to work
    assert lim.limit == 8 and lim.ceiling == 15 and not lim.slow_start
    for _ in range(2):
        lim.ok()
    assert lim.limit == 9  # additive from here on
    for _ in range(40):
        lim.ok()
    assert lim.limit == 15  # never above the ceiling
    lim.pushback()
    assert lim.limit == 7.5 and lim.ceiling == 14
    for _ in range(64):  # a long clean streak probes the ceiling upward
        lim.ok()
    assert lim.ceiling == 15


@pytest.mark.asyncio
async def test_adaptive_limiter_respects_its_limit_and_the_floor():
    lim = L.Limiter(start=4, maximum=6, adaptive=True)
    for _ in range(5):
        lim.pushback()
    assert lim.limit == 2  # floor
    peak, now = 0, 0

    async def job():
        nonlocal peak, now
        async with lim:
            now += 1
            peak = max(peak, now)
            await asyncio.sleep(0.01)
            now -= 1

    await asyncio.gather(*[job() for _ in range(12)])
    assert peak <= 2 and lim.in_flight == 0


def test_a_fixed_limiter_never_adapts():
    lim = L.Limiter(start=4, maximum=32, adaptive=False, grow_after=1)
    lim.ok(), lim.ok()
    lim.pushback()
    assert lim.limit == 4


def test_a_server_that_queues_instead_of_answering_429_is_detected_after_a_rise_of_the_limit():
    lim = L.Limiter(start=4, maximum=32, adaptive=True, grow_after=8)
    for _ in range(8):
        lim.ok(0.03)  # 33 tok/s at 4 in flight
    assert lim.limit == 8 and lim.slow_start  # slow start doubled the limit
    for _ in range(8):
        lim.ok(0.15)  # now 5x slower per token and nobody said 429: our own load queues
    assert lim.limit == 4 and lim.ceiling == 4 and not lim.slow_start  # back one level, and 4 is remembered as the ceiling


def test_slowness_that_is_not_ours_does_not_throttle_us():
    lim = L.Limiter(start=4, maximum=32, adaptive=True, grow_after=8)
    for _ in range(8):
        lim.ok(0.03)
    assert lim.limit == 8
    for _ in range(8):
        lim.ok(0.04)  # other users slowed the gateway a little: the same at both levels, no reason to give up concurrency
    assert lim.limit >= 8
    lim2 = L.Limiter(start=4, maximum=32, adaptive=True, grow_after=8)
    for _ in range(40):
        lim2.ok(0.30)  # a gateway that is slow from the start (36 s mean latency on 6 Oct): never throttled below the start
    assert lim2.limit >= 4
