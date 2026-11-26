"""Proxy path: forward + capture, with a fake upstream.

The properties under test are the ones ARTEX depends on:
  - the client receives the upstream bytes and status,
  - the provider key replaces the local token going up stream,
  - a streaming call is captured with its text, tool calls and finish_reason,
  - a buffered call is captured whole,
  - an upstream failure still produces a record,
  - a bad local token is refused.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from artex_gym.collector import app as app_module

ENV = {
    "ARTEX_GYM_UPSTREAM_BASE_URL": "https://upstream.invalid/v1",
    "ARTEX_GYM_UPSTREAM_API_KEY": "sk-real-provider-key",
    "ARTEX_GYM_COLLECTOR_TOKEN": "artex-gym-local",
    "ARTEX_GYM_RUN_ID": "run-proxy-1",
    "ARTEX_GYM_BLOB_DIR": "",  # set per-test
}

REQUEST = {
    "model": "test-model",
    "temperature": 0.3,
    "max_tokens": 128,
    "messages": [{"role": "user", "content": "whoami"}],
    "tools": [{"type": "function", "function": {"name": "bash", "parameters": {"type": "object"}}}],
}

BUFFERED = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "model": "test-model",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "root"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 11, "completion_tokens": 2},
}

SSE_LINES = [
    b'data: {"model":"test-model","choices":[{"index":0,"delta":{"role":"assistant","content":""}}]}',
    b'data: {"model":"test-model","choices":[{"index":0,"delta":{"content":"ro"}}]}',
    b'data: {"model":"test-model","choices":[{"index":0,"delta":{"content":"ot"}}]}',
    b'data: {"model":"test-model","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"id":"call_1","function":{"name":"bash"}}]}}]}',
    b'data: {"model":"test-model","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\\"cmd\\""}}]}}]}',
    b'data: {"model":"test-model","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":":\\"id\\"}"}}]}}]}',
    b'data: {"model":"test-model","choices":[{"index":0,"delta":{},"finish_reason":"tool_calls"}],"usage":{"prompt_tokens":20,"completion_tokens":9}}',
    b"data: [DONE]",
]


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("ARTEX_GYM_BLOB_DIR", str(tmp_path / "blobs"))
    with TestClient(app_module.app) as c:
        yield c


def _sse_response(lines: list[bytes]) -> httpx.Response:
    """A streaming response, as a real transport delivers it.

    MockTransport with `content=bytes` hands back an already-consumed stream, so
    aiter_raw() raises StreamConsumed — an artifact of the fake, not of the
    proxy. An AsyncByteStream keeps the body lazy, which is what we are testing.
    """

    class _Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for line in lines:
                yield line + b"\n"

    return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=_Stream())


def _blobs(tmp_path: Path) -> list[Path]:
    """Blobs on disk, after giving the async writer a moment.

    Capture is deliberately off the response path, so a test must not assume the
    file exists the instant the response returns. Polling states that honestly
    instead of hiding a race behind a sleep.
    """
    import time

    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        found = sorted((tmp_path / "blobs").rglob("*.json.gz"))
        if found:
            return found
        time.sleep(0.01)
    return []


def _record(path: Path) -> dict:
    import gzip

    return json.loads(gzip.decompress(path.read_bytes()))


@pytest.fixture()
def upstream(monkeypatch: pytest.MonkeyPatch):
    """Install a fake upstream; the returned list collects the requests it saw."""

    def install(handler):
        seen: list[httpx.Request] = []

        def wrapper(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return handler(request)

        app_module.STATE["transport"] = httpx.MockTransport(wrapper)
        return seen

    yield install
    app_module.STATE.pop("transport", None)


# ------------------------------------------------------------------ buffered


def test_buffered_call_is_forwarded_and_captured(client, upstream, tmp_path: Path) -> None:
    upstream(lambda req: httpx.Response(200, json=BUFFERED))
    resp = client.post(
        "/v1/chat/completions",
        json=REQUEST,
        headers={"Authorization": "Bearer artex-gym-local"},
    )
    assert resp.status_code == 200
    assert resp.json()["choices"][0]["message"]["content"] == "root"

    blobs = _blobs(tmp_path)
    assert len(blobs) == 1
    rec = _record(blobs[0])
    assert rec["http_status"] == 200
    assert rec["model"] == "test-model"
    assert rec["finish_reason"] == "stop"
    assert rec["temperature"] == 0.3
    assert rec["max_tokens"] == 128
    assert rec["usage"]["prompt_tokens"] == 11
    assert rec["streaming"] is False
    # The join's fields stay null.
    assert rec["task_id"] is None and rec["turn_idx"] is None


def test_provider_key_replaces_the_local_token(client, upstream) -> None:
    seen = upstream(lambda req: httpx.Response(200, json=BUFFERED))
    client.post(
        "/v1/chat/completions",
        json=REQUEST,
        headers={"Authorization": "Bearer artex-gym-local"},
    )
    assert len(seen) == 1
    assert seen[0].headers["authorization"] == "Bearer sk-real-provider-key"
    # The local token must never leak up stream.
    assert "artex-gym-local" not in str(seen[0].headers)


def test_prompt_and_tools_hashes_are_recorded(client, upstream, tmp_path: Path) -> None:
    upstream(lambda req: httpx.Response(200, json=BUFFERED))
    client.post(
        "/v1/chat/completions", json=REQUEST, headers={"Authorization": "Bearer artex-gym-local"}
    )
    rec = _record(_blobs(tmp_path)[0])
    assert len(rec["prompt_sha256"]) == 64
    assert len(rec["tools_schema_sha256"]) == 64
    # A different tool schema must hash differently.
    assert rec["tools_schema_sha256"] != "0" * 64


# ----------------------------------------------------------------- streaming


def test_streaming_call_is_forwarded_byte_for_byte(client, upstream, tmp_path: Path) -> None:
    upstream(lambda req: _sse_response(SSE_LINES))
    # Starlette's TestClient has no `stream=True`; `client.stream(...)` is the
    # context-manager form and still exercises the chunked path.
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json=REQUEST,
        headers={"Authorization": "Bearer artex-gym-local"},
    ) as resp:
        received = b"".join(resp.iter_bytes())
    assert b"data: [DONE]" in received

    rec = _record(_blobs(tmp_path)[0])
    assert rec["streaming"] is True
    assert rec["finish_reason"] == "tool_calls"
    assert rec["usage"]["completion_tokens"] == 9
    message = rec["response"]["choices"][0]["message"]
    assert message["content"] == "root"
    assert message["tool_calls"][0]["function"]["name"] == "bash"
    # Arguments arrive split across deltas and must be re-joined.
    assert json.loads(message["tool_calls"][0]["function"]["arguments"]) == {"cmd": "id"}


def test_ttft_ignores_the_role_only_first_frame() -> None:
    """TTFT must be the first content token; a role delta arrives at ~0ms."""
    from artex_gym.collector.proxy import SseAccumulator

    acc = SseAccumulator()
    acc.feed(b'data: {"choices":[{"index":0,"delta":{"role":"assistant","content":""}}]}')
    assert acc.first_token_ms is None, "role-only delta must not count as a token"
    acc.feed(b'data: {"choices":[{"index":0,"delta":{"content":"hi"}}]}')
    assert acc.first_token_ms is not None


def test_streaming_ttft_is_measured(client, upstream, tmp_path: Path) -> None:
    upstream(lambda req: _sse_response(SSE_LINES))
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json=REQUEST,
        headers={"Authorization": "Bearer artex-gym-local"},
    ) as resp:
        b"".join(resp.iter_bytes())
    rec = _record(_blobs(tmp_path)[0])
    assert rec["ttft_ms"] is not None and rec["ttft_ms"] >= 0


# ----------------------------------------------------------------- fail-open


def test_upstream_failure_still_records(client, upstream, tmp_path: Path) -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    upstream(handler)
    resp = client.post(
        "/v1/chat/completions", json=REQUEST, headers={"Authorization": "Bearer artex-gym-local"}
    )
    assert resp.status_code == 502
    rec = _record(_blobs(tmp_path)[0])
    assert rec["http_status"] == 502
    assert "connection refused" in (rec["error"] or "")


def test_malformed_request_body_is_still_captured(client, upstream, tmp_path: Path) -> None:
    upstream(lambda req: httpx.Response(200, json=BUFFERED))
    resp = client.post(
        "/v1/chat/completions",
        content=b"{not json",
        headers={"content-type": "application/json", "Authorization": "Bearer artex-gym-local"},
    )
    assert resp.status_code == 200
    rec = _record(_blobs(tmp_path)[0])
    assert rec["request"]["raw"] == "{not json"


# ---------------------------------------------------------------------- auth


def test_wrong_local_token_is_refused(client, upstream) -> None:
    seen = upstream(lambda req: httpx.Response(200, json=BUFFERED))
    resp = client.post(
        "/v1/chat/completions", json=REQUEST, headers={"Authorization": "Bearer wrong"}
    )
    assert resp.status_code == 401
    assert seen == [], "refused request must not reach the provider"


def test_health_reports_run_and_counters(client) -> None:
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["run_id"] == "run-proxy-1"
    assert "dropped" in body
