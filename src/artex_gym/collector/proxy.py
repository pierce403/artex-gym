"""The transparent proxy path: forward, then capture out of the way.

Two rules decide the shape of this module:

1. The client gets bytes as the upstream sends them. Streaming is not
   buffered-and-forwarded, because ARTEX streams by default and a collector
   that buffers turns a live agent into a slow one.
2. Capture happens after forwarding, never on the critical path. A parse
   failure, a missing field, or a full queue degrades the record, not the call.

SSE is teed: each chunk goes to the client immediately and to a small parser
that accumulates text and the terminal metadata. That parser is deliberately
tolerant — an event it does not recognise is ignored, not fatal.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from artex_gym.collector.config import CollectorConfig
from artex_gym.collector.record import (
    CaptureRecord,
    prompt_sha256,
    tools_schema_sha256,
)

# Headers that must not be forwarded verbatim in either direction.
# Hop-by-hop ones are per-connection; the rest are recomputed.
_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
    "accept-encoding",
}


def _upstream_headers(incoming: dict[str, str], cfg: CollectorConfig) -> dict[str, str]:
    out = {k: v for k, v in incoming.items() if k.lower() not in _HOP_BY_HOP}
    # The provider key replaces whatever ARTEX sent (our local token).
    out["authorization"] = f"Bearer {cfg.upstream_api_key}"
    # Ask for an unencoded body: we need the plaintext to capture it.
    out["accept-encoding"] = "identity"
    return out


def _downstream_headers(upstream: httpx.Headers) -> dict[str, str]:
    return {k: v for k, v in upstream.items() if k.lower() not in _HOP_BY_HOP}


@dataclass
class SseAccumulator:
    """Collects what a streaming response said, without changing what it said."""

    text: list[str] = field(default_factory=list)
    thinking: list[str] = field(default_factory=list)
    tool_calls: dict[int, dict[str, Any]] = field(default_factory=dict)
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    model: str | None = None
    first_token_ms: int | None = None
    chunks: int = 0
    _start: float = field(default_factory=time.monotonic)

    def feed(self, line: bytes) -> None:
        """One SSE line. Tolerant by design: anything unexpected is skipped."""
        if not line.startswith(b"data:"):
            return
        payload = line[5:].strip()
        if not payload or payload == b"[DONE]":
            return
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return
        self.chunks += 1

        if isinstance(event.get("model"), str):
            self.model = event["model"]
        if event.get("usage"):
            self.usage = event["usage"]

        for choice in event.get("choices") or []:
            if not isinstance(choice, dict):
                continue
            if choice.get("finish_reason"):
                self.finish_reason = choice["finish_reason"]
            delta = choice.get("delta") or {}
            if isinstance(delta.get("content"), str) and delta["content"]:
                self._mark_first_token()
                self.text.append(delta["content"])
            if isinstance(delta.get("reasoning_content"), str) and delta["reasoning_content"]:
                self._mark_first_token()
                self.thinking.append(delta["reasoning_content"])
            for call in delta.get("tool_calls") or []:
                if not isinstance(call, dict):
                    continue
                idx = call.get("index", 0)
                slot = self.tool_calls.setdefault(
                    idx,
                    {"id": None, "type": "function", "function": {"name": None, "arguments": ""}},
                )
                self._mark_first_token()
                if call.get("id"):
                    slot["id"] = call["id"]
                fn = call.get("function") or {}
                if fn.get("name"):
                    slot["function"]["name"] = fn["name"]
                if fn.get("arguments"):
                    slot["function"]["arguments"] += fn["arguments"]

    def _mark_first_token(self) -> None:
        """TTFT is the first *content* token, not the first SSE frame.

        Providers open a stream with a role-only delta, so measuring at the
        first chunk reports ~0ms for every call — which would make the M6
        turns-to-flag and latency numbers meaningless.
        """
        if self.first_token_ms is None:
            self.first_token_ms = int((time.monotonic() - self._start) * 1000)

    def as_response(self) -> dict[str, Any]:
        message: dict[str, Any] = {"role": "assistant", "content": "".join(self.text) or None}
        if self.thinking:
            message["reasoning_content"] = "".join(self.thinking)
        calls = [self.tool_calls[i] for i in sorted(self.tool_calls)]
        if calls:
            message["tool_calls"] = calls
        return {
            "object": "chat.completion",
            "model": self.model,
            "choices": [{"index": 0, "message": message, "finish_reason": self.finish_reason}],
            "usage": self.usage,
        }


def _non_streaming_response(body: bytes) -> dict[str, Any]:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"raw": body.decode("utf-8", "replace")}


def _usage_from(response: dict[str, Any]) -> dict[str, Any] | None:
    usage = response.get("usage")
    return usage if isinstance(usage, dict) else None


def _finish_reason(response: dict[str, Any]) -> str | None:
    choices = response.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        return choices[0].get("finish_reason")
    return None


@dataclass
class CaptureContext:
    """Everything about one call that is known before the response arrives."""

    seq: int
    req_id: str
    ts_start: str
    started: float
    request: Any
    model: str
    temperature: float | None
    seed: int | None
    max_tokens: int | None
    provider: str


def build_context(body: bytes, seq: int, cfg: CollectorConfig) -> CaptureContext:
    """Parse the request defensively; never raise on a shape we did not expect."""
    try:
        parsed: Any = json.loads(body)
    except json.JSONDecodeError:
        parsed = {"raw": body.decode("utf-8", "replace")}
    fields = parsed if isinstance(parsed, dict) else {}
    return CaptureContext(
        seq=seq,
        req_id=uuid.uuid4().hex,
        ts_start=_utc_now(),
        started=time.monotonic(),
        request=parsed,
        model=str(fields.get("model") or ""),
        temperature=fields.get("temperature"),
        seed=fields.get("seed"),
        max_tokens=fields.get("max_tokens"),
        provider="openai",
    )


def build_record(
    ctx: CaptureContext,
    response: dict[str, Any],
    status: int,
    streaming: bool,
    ttft_ms: int | None,
    error: str | None,
    captured_bytes: int,
    cfg: CollectorConfig,
    truncated: bool = False,
) -> CaptureRecord:
    """Assemble the blob. Pure, so it can be tested without a socket."""
    request = ctx.request if isinstance(ctx.request, dict) else {}
    return CaptureRecord(
        req_id=ctx.req_id,
        run_id=cfg.run_id,
        capture_seq=ctx.seq,
        model=ctx.model or str(response.get("model") or ""),
        provider=ctx.provider,
        temperature=ctx.temperature,
        seed=ctx.seed,
        max_tokens=ctx.max_tokens,
        prompt_sha256=prompt_sha256(request),
        tools_schema_sha256=tools_schema_sha256(request),
        ts_start=ctx.ts_start,
        ts_end=_utc_now(),
        ttft_ms=ttft_ms,
        usage=_usage_from(response),
        finish_reason=_finish_reason(response),
        http_status=status,
        request=ctx.request,
        response=response,
        streaming=streaming,
        truncated=truncated,
        error=error,
    )


def _utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
