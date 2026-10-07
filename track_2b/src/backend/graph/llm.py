"""Shared LLM client factory for Apertus 1.5 (OpenAI-compatible gateway)."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections import Counter, deque
from typing import Any, TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_CONCURRENCY,
    LLM_CONCURRENCY_ADAPTIVE,
    LLM_CONCURRENCY_MAX,
    LLM_FALLBACK_NAME,
    LLM_NAME,
    LLM_TEMPERATURE,
)
from graph.metrics import note_event, record_call

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_INNER = re.compile(
    r"<\|inner_prefix\|>.*?<\|inner_suffix\|>",
    flags=re.DOTALL,
)
# Observability for the paper: how often did the gateway push back / did we downgrade?
STATS: Counter[str] = Counter()
_RATE_RETRIES = 6  # ponytail: fixed 1.5s..20s back-off; the hackathon gateway allows ~4 in flight


class Limiter:
    """Requests in flight, optionally adaptive so one build works on both endpoints (livemap: 429 above 4-5, CSCS: no limit found to 96).

    Slow start (double after `grow_after` clean answers) until the first 429 / gateway timeout, then the limit is halved and the largest value known
    to work (`ceiling`) is remembered: it grows by +1 per `grow_after` clean answers up to the ceiling, and the ceiling itself is probed upward by 1
    after 64 further clean answers. Measured (E29): additive-only growth from 4 needed 141 s for a 25-resident run on CSCS (fixed 16: 105 s for 3 rounds)."""

    def __init__(self, start: int, maximum: int, adaptive: bool, grow_after: int = 6) -> None:
        self.limit = float(start)
        self.maximum, self.adaptive, self.grow_after = maximum, adaptive, grow_after
        self.ceiling = float(maximum)
        self.slow_start = True
        self.in_flight = 0
        self._streak = 0
        self._clean = 0
        self._spt: deque[float] = deque(maxlen=8)
        self._level_spt: float | None = None  # latency per token at the level before the last rise
        self._prev_limit: float | None = None
        self._cond: asyncio.Condition | None = None

    def _c(self) -> asyncio.Condition:
        if self._cond is None:
            self._cond = asyncio.Condition()
        return self._cond

    async def __aenter__(self) -> "Limiter":
        async with self._c():
            while self.in_flight >= int(self.limit):
                await self._c().wait()
            self.in_flight += 1
        return self

    async def __aexit__(self, *exc: object) -> None:
        async with self._c():
            self.in_flight -= 1
            self._c().notify_all()

    def ok(self, seconds_per_token: float | None = None) -> None:
        """A clean answer. `seconds_per_token` (latency / output tokens) detects a server that queues instead of answering 429: on 6 Oct the
        hackathon gateway took 32 requests in flight and answered each at 7.5 tok/s instead of 30, with no error at all. Slowness that is not caused by
        our own limit (other users) leaves both levels equally slow, so only a >2x slow-down right after a *rise* of the limit counts: we go back one level."""
        if not self.adaptive:
            return
        if seconds_per_token:
            self._spt.append(seconds_per_token)
            if len(self._spt) >= 8 and self._level_spt is not None:
                recent = sum(self._spt) / len(self._spt)
                worse = recent > 2.0 * self._level_spt
                self._level_spt = None
                if worse and self._prev_limit is not None:
                    self.limit = self._prev_limit
                    self.ceiling = min(self.ceiling, self._prev_limit)
                    self.slow_start = False
                    self._spt.clear()
                    self._streak = 0
                    return
        self._streak += 1
        if not self.slow_start:
            self._clean += 1
            if self._clean >= 64 and self.ceiling < self.maximum:
                self.ceiling += 1
                self._clean = 0
        if self._streak >= self.grow_after and self.limit < self.ceiling:
            self._prev_limit = self.limit
            self._level_spt = sum(self._spt) / len(self._spt) if len(self._spt) >= 4 else None
            self._spt.clear()
            self.limit = min(self.ceiling, self.limit * 2 if self.slow_start else self.limit + 1)
            self._streak = 0

    def pushback(self) -> None:
        if not self.adaptive:
            return
        self._streak = self._clean = 0
        self.ceiling = max(2.0, min(self.ceiling, float(int(self.limit) - 1)))
        self.limit = max(2.0, self.limit / 2)
        self.slow_start = False


_LIMITER: Limiter | None = None


def _limiter() -> Limiter:
    global _LIMITER
    if _LIMITER is None:
        _LIMITER = Limiter(LLM_CONCURRENCY, LLM_CONCURRENCY_MAX, LLM_CONCURRENCY_ADAPTIVE)
    return _LIMITER


def current_limit() -> float:
    return _limiter().limit


def get_llm(
    max_tokens: int | None = None,
    *,
    enable_thinking: bool = False,
    model: str | None = None,
    temperature: float | None = None,
    stream_usage: bool = False,
    **_kwargs: Any,
) -> ChatOpenAI:
    """Create a ChatOpenAI instance pointed at the configured Apertus endpoint.

    Thinking and tools must never be combined in one request. Round JSON calls
    use enable_thinking=False.
    """
    kwargs: dict[str, Any] = {
        "model": model or LLM_NAME,
        "api_key": LLM_API_KEY,
        "base_url": LLM_BASE_URL,
        "temperature": LLM_TEMPERATURE if temperature is None else temperature,
        "extra_body": {
            "chat_template_kwargs": {"enable_thinking": bool(enable_thinking)}
        },
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if stream_usage:
        kwargs["stream_usage"] = True  # the last streamed chunk then carries the token usage (metrics)
    return ChatOpenAI(**kwargs)  # pyright: ignore[reportCallIssue]


def strip_think_tags(content: str) -> str:
    """Remove reasoning spans from raw model output (Apertus inner tokens; also <think>)."""
    return strip_reasoning_spans(content)


def strip_reasoning_spans(content: str) -> str:
    """Drop deliberation so user-visible text has no <|inner_prefix|> markers."""
    if not content:
        return ""
    content = _INNER.sub("", content)
    if "<|inner_prefix|>" in content and "<|inner_suffix|>" not in content:
        # Truncated thinking — drop the unfinished span.
        content = content.split("<|inner_prefix|>", 1)[0]
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    content = re.sub(r"^.*?</think>", "", content, flags=re.DOTALL)
    return content.strip()


def _strip_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([\]\}])", r"\1", text)


def _extract_json_from_response(content: str) -> Any:
    """Extract and parse JSON from LLM response (strips reasoning and markdown fences).

    Returns the parsed Python object, or raises json.JSONDecodeError if nothing found.
    """
    original = content
    content = strip_reasoning_spans(content)

    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if json_match:
        fence_content = json_match.group(1).strip()
        if fence_content:
            return json.loads(fence_content)

    def _balanced_json_slice(text: str, start: int) -> str | None:
        open_char = text[start]
        if open_char not in "[{":
            return None
        close_char = "}" if open_char == "{" else "]"
        stack: list[str] = [close_char]
        in_string = False
        escaped = False
        for i in range(start + 1, len(text)):
            ch = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
                continue
            if ch == "{":
                stack.append("}")
            elif ch == "[":
                stack.append("]")
            elif ch in "]}":
                if not stack or ch != stack[-1]:
                    return None
                stack.pop()
                if not stack:
                    return text[start : i + 1]
        return None

    def _scan(text: str) -> list[tuple[int, Any]]:
        results: list[tuple[int, Any]] = []
        for i, ch in enumerate(text):
            if ch not in "[{":
                continue
            candidate = _balanced_json_slice(text, i)
            if not candidate:
                continue
            try:
                results.append((i, json.loads(_strip_trailing_commas(candidate))))
            except json.JSONDecodeError:
                continue
        return results

    content = _strip_trailing_commas(content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    candidates = _scan(content)

    if not candidates:
        candidates = _scan(original)

    if candidates:
        dicts = [v for _, v in candidates if isinstance(v, dict) and v]
        if dicts:
            return max(dicts, key=lambda d: len(json.dumps(d)))
        return candidates[-1][1]

    raise json.JSONDecodeError("No JSON found", content, 0)


def _unwrap_single_object_array(parsed: Any) -> Any:
    """Some models wrap a single object in an array — return the first dict found."""
    if isinstance(parsed, list):
        return next((x for x in parsed if isinstance(x, dict)), {})
    return parsed


def _flatten_schema(schema: dict[str, Any]) -> dict[str, Any]:
    defs = schema.get("$defs", {})

    def _resolve(obj: Any) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_name = obj["$ref"].split("/")[-1]
                return _resolve(defs.get(ref_name, obj))
            return {k: _resolve(v) for k, v in obj.items() if k != "$defs"}
        if isinstance(obj, list):
            return [_resolve(item) for item in obj]
        return obj

    return _resolve({k: v for k, v in schema.items() if k != "$defs"})


def _schema_to_example(schema: dict[str, Any]) -> Any:
    """Build a concrete placeholder instance from a flattened JSON schema.

    Showing the model an example instance (with placeholder values) is far more
    reliable than showing it the schema definition.
    """
    t = schema.get("type")
    if t == "object":
        return {k: _schema_to_example(v) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        return [_schema_to_example(schema.get("items", {}))]
    if t == "string":
        if "enum" in schema:
            return schema["enum"][0]
        return "..."
    if t in ("integer", "number"):
        return 0
    if t == "boolean":
        return True
    if "anyOf" in schema:
        non_null = [s for s in schema["anyOf"] if s.get("type") != "null"]
        return _schema_to_example(non_null[0]) if non_null else None
    return None


def _status(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)


async def _ainvoke(llm: ChatOpenAI, prompt: str, json_mode: bool = True) -> Any:
    """One completion in json_object mode. 429 -> back off and retry the SAME model (never
    downgrade); the plain (non-json) call is only for endpoints that reject response_format."""
    lim = _limiter()
    for attempt in range(_RATE_RETRIES):
        try:
            async with lim:
                t0 = time.perf_counter()
                try:
                    response = await (llm.bind(response_format={"type": "json_object"}) if json_mode else llm).ainvoke(prompt)
                except Exception as exc:
                    overloaded = _status(exc) in (429, 500, 502, 503, 504) or "timeout" in type(exc).__name__.lower()
                    if overloaded:  # a second call would only add load exactly when the gateway is saturated
                        raise
                    if not json_mode:
                        raise
                    STATS["json_mode_rejected"] += 1
                    response = await llm.ainvoke(prompt)
            elapsed = time.perf_counter() - t0
            usage = getattr(response, "usage_metadata", None)
            out_tokens = usage.get("output_tokens") if isinstance(usage, dict) else None
            lim.ok(elapsed / out_tokens if out_tokens and out_tokens >= 50 else None)
            record_call(getattr(llm, "model_name", "?"), usage, elapsed)
            return response
        except Exception as exc:
            if _status(exc) == 429 and attempt < _RATE_RETRIES - 1:
                lim.pushback()
                STATS["rate_limited"] += 1
                note_event("rate_limited")
                await asyncio.sleep(min(20.0, 1.5 * 2**attempt))  # outside the limiter
                continue
            if _status(exc) in (502, 503, 504) and attempt < 2:
                # CSCS answers 504 "upstream request timeout" under mixed load instead of 429 (research E21/F64): retry the same model
                # twice before the caller considers a smaller one.
                lim.pushback()
                STATS["gateway_5xx_retried"] += 1
                note_event("gateway_5xx_retried")
                await asyncio.sleep(2.0 * 2**attempt)
                continue
            note_event("failed")
            raise
    raise RuntimeError("unreachable")


async def invoke_llm_structured(
    prompt: str,
    response_model: type[T],
    max_tokens: int = 4096,
    llm: ChatOpenAI | None = None,
    lang: str | None = None,
    **_kwargs: Any,
) -> T:
    """Invoke Apertus and parse the response into a Pydantic model.
    Retries up to 3 times — the model occasionally outputs reasoning text with no JSON.
    On validation error, the next attempt is an error-feedback repair (APO-lite).
    """
    if llm is None:
        llm = get_llm(max_tokens=max_tokens, enable_thinking=False)

    # A model may supply its own example: the example is the behaviour policy (research E2/F22),
    # so the generic placeholder ("...", 0, true) is only the default.
    custom = getattr(response_model, "prompt_example", None)
    example = (custom(lang) if lang else custom()) if callable(custom) else _schema_to_example(_flatten_schema(response_model.model_json_schema()))
    shown = json.dumps(example, indent=2, ensure_ascii=False)
    if callable(custom) and "events" in response_model.model_fields:  # wording validated in research E2b
        augmented_prompt = (
            f"{prompt}\n\nOutput ONLY a JSON object of this shape. Replace every <...> with your own content; "
            f"use 1-3 events of the types that fit you (not necessarily the ones shown):\n{shown}"
        )
    else:
        augmented_prompt = (
            f"{prompt}\n\n"
            f"Output ONLY the following JSON with the placeholder values filled in. "
            f"No explanation, no reasoning, no other text — just the completed JSON:\n"
            f"{shown}"
        )

    logger.info(
        "LLM structured call → %s (prompt %d chars)",
        response_model.__name__,
        len(augmented_prompt),
    )

    last_exc: Exception = RuntimeError("no attempts made")
    content = ""
    current_prompt = augmented_prompt
    for attempt in range(1, 4):  # up to 3 attempts
        try:
            response = await _ainvoke(llm, current_prompt)
            content = response.content  # type: ignore[assignment]
            content = strip_reasoning_spans(str(content))
            parsed = _unwrap_single_object_array(_extract_json_from_response(content))
            result = response_model.model_validate(parsed)
            logger.info("LLM structured call ← %s OK", response_model.__name__)
            return result

        except Exception as exc:
            last_exc = exc
            if attempt < 3:
                logger.warning(
                    "LLM structured call attempt %d/3 failed for %s: %s — retrying",
                    attempt,
                    response_model.__name__,
                    exc,
                )
                if isinstance(exc, ValidationError):
                    current_prompt = (
                        f"{augmented_prompt}\n\n"
                        f"Your previous JSON failed validation. Fix it. Do not add facts.\n"
                        f"Invalid JSON:\n{content[:2000]}\n"
                        f"Error:\n{exc}"
                    )
                elif isinstance(exc, json.JSONDecodeError):
                    # identical prompt at temperature 0 repeats the same mistake; say what was wrong
                    current_prompt = (
                        f"{augmented_prompt}\n\nYour previous answer was not a JSON object. "
                        f"Reply with the JSON object only, nothing before or after it."
                    )
                err = str(exc).lower()
                # Rate limits are handled (and retried on the same model) in _ainvoke; only a
                # slow/unavailable gateway justifies the smaller model, and we count it.
                if any(k in err for k in ("timeout", "timed out", "502", "503", "504", "overloaded")):
                    STATS["downgraded_to_fallback_model"] += 1
                    note_event("downgraded_to_fallback_model")
                    logger.warning("DOWNGRADE to %s after: %s", LLM_FALLBACK_NAME, exc)
                    llm = get_llm(
                        max_tokens=min(max_tokens, 2048),
                        enable_thinking=False,
                        model=LLM_FALLBACK_NAME,
                    )
            else:
                logger.warning(
                    "Failed to parse response for %s: %s\nContent: %s",
                    response_model.__name__,
                    exc,
                    content[:300],
                )

    raise last_exc


async def invoke_llm_json(
    prompt: str,
    max_tokens: int = 4096,
    llm: ChatOpenAI | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Invoke Apertus and return the parsed JSON response as a dict.
    Retries up to 3 times.
    """
    if llm is None:
        llm = get_llm(max_tokens=max_tokens, enable_thinking=False)

    last_exc: Exception = RuntimeError("no attempts made")
    content = ""
    for attempt in range(1, 4):
        try:
            response = await _ainvoke(llm, prompt)
            content = strip_reasoning_spans(str(response.content))
            result = _unwrap_single_object_array(_extract_json_from_response(content))
            if not isinstance(result, dict):
                result = {"value": result}
            return result

        except Exception as exc:
            last_exc = exc
            if attempt < 3:
                logger.warning(
                    "invoke_llm_json attempt %d/3 failed: %s — retrying",
                    attempt,
                    exc,
                )
            else:
                logger.warning(
                    "invoke_llm_json failed after 3 attempts: %s\nContent: %s",
                    exc,
                    content[:300],
                )

    raise last_exc


async def ainvoke_text(llm: ChatOpenAI, prompt: str) -> Any:
    """A free-text completion (the 1:1 chat) through the same limiter, retries and metrics as the JSON calls."""
    return await _ainvoke(llm, prompt, json_mode=False)


async def astream_text(llm: ChatOpenAI, prompt: str):
    """Stream a free-text completion piece by piece (the 1:1 chat). Same limiter and metrics as `_ainvoke`; a 429 / gateway timeout that arrives
    before the first piece is retried like there, one that arrives mid-stream is raised (the caller already showed text)."""
    lim = _limiter()
    for attempt in range(_RATE_RETRIES):
        started = False
        try:
            async with lim:
                t0 = time.perf_counter()
                usage = None
                async for chunk in llm.astream(prompt):
                    started = True
                    usage = getattr(chunk, "usage_metadata", None) or usage
                    if chunk.content:
                        yield str(chunk.content)
            lim.ok()
            record_call(getattr(llm, "model_name", "?"), usage, time.perf_counter() - t0)
            return
        except Exception as exc:
            status = _status(exc)
            if not started and status == 429 and attempt < _RATE_RETRIES - 1:
                lim.pushback()
                note_event("rate_limited")
                await asyncio.sleep(min(20.0, 1.5 * 2**attempt))
                continue
            if not started and status in (502, 503, 504) and attempt < 2:
                lim.pushback()
                note_event("gateway_5xx_retried")
                await asyncio.sleep(2.0 * 2**attempt)
                continue
            note_event("failed")
            raise


async def invoke_llm_think(prompt: str, max_tokens: int = 2048) -> str:
    """Thinking-mode call (no tools, no json_object). Returns visible answer only."""
    llm = get_llm(max_tokens=max_tokens, enable_thinking=True)
    t0 = time.perf_counter()
    async with _limiter():
        response = await llm.ainvoke(prompt)
    record_call(getattr(llm, "model_name", "?"), getattr(response, "usage_metadata", None), time.perf_counter() - t0)
    return strip_reasoning_spans(str(response.content))
