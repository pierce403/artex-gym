"""llm-logger: fail-open capture proxy between ARTEX and the model provider.

Endpoints, which the overlay and `artexctl up` are written against:

    GET  /api/health   liveness for compose and for `artexctl up`
    GET  /metrics      Prometheus text; collector_dropped_total is the alarm
    POST /v1/chat/completions   proxy + capture
    GET  /v1/models             proxy (the UI model picker calls it)
    *                           proxied verbatim

Design notes: adr/0002-collector-placement.md (placement, fail-open, drops)
and adr/0003-collector-contract.md (record shape, auth, redaction).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response, StreamingResponse

from artex_gym.collector import proxy as px
from artex_gym.collector.blobs import BlobStore
from artex_gym.collector.config import CollectorConfig
from artex_gym.collector.queue import CaptureQueue

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("llm-logger")

STATE: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = CollectorConfig.from_env()
    store = BlobStore(cfg.blob_dir)
    queue = CaptureQueue(store=store, maxsize=cfg.queue_max)
    queue.start()
    STATE.update(cfg=cfg, queue=queue, store=store, seq=_SeqCounter(store, cfg.run_id))
    log.info(
        "capturing to %s as run %s (queue %d, upstream %s)",
        cfg.blob_dir,
        cfg.run_id,
        cfg.queue_max,
        cfg.upstream_base_url,
    )
    try:
        yield
    finally:
        await queue.stop()


def _SeqCounter(store: BlobStore, run_id: str) -> Seq:  # noqa: N802 - reads as a constructor
    return Seq(start=len(store.list_run(run_id)))


class Seq:
    """Per-run capture sequence. Continues after a restart instead of colliding."""

    def __init__(self, start: int = 0) -> None:
        self._next = start

    def take(self) -> int:
        n = self._next
        self._next += 1
        return n


app = FastAPI(title="artex-gym llm-logger", version="0.1.0", lifespan=lifespan)


def _client() -> httpx.AsyncClient:
    cfg: CollectorConfig = STATE["cfg"]
    return httpx.AsyncClient(
        base_url=cfg.upstream_base_url,
        timeout=httpx.Timeout(cfg.request_timeout_s, connect=15.0),
        follow_redirects=False,
        # Tests inject a transport so the proxy path is exercised without a socket.
        transport=STATE.get("transport"),
    )


def _authorised(request: Request) -> bool:
    cfg: CollectorConfig = STATE["cfg"]
    if not cfg.inbound_auth or not cfg.collector_token:
        return True
    header = request.headers.get("authorization", "")
    return header == f"Bearer {cfg.collector_token}"


# ------------------------------------------------------------------ health & metrics


@app.get("/api/health")
def health() -> dict[str, Any]:
    cfg: CollectorConfig = STATE["cfg"]
    counters = STATE["queue"].counters
    return {
        "ok": True,
        "service": "llm-logger",
        "run_id": cfg.run_id,
        "blob_dir": str(cfg.blob_dir),
        "upstream": cfg.upstream_base_url,
        "dropped": counters.dropped,
        "written": counters.written,
        "queue_depth": counters.depth,
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    counters = STATE["queue"].counters
    series = {
        "collector_dropped_total": counters.dropped,
        "collector_written_total": counters.written,
        "collector_write_errors_total": counters.write_errors,
        "collector_queue_depth": counters.depth,
        "collector_capture_total": counters.accepted,
    }
    lines = [
        "# HELP collector_dropped_total Captures lost before reaching disk.",
        "# TYPE collector_dropped_total counter",
    ]
    lines += [f"{name} {value}" for name, value in series.items()]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------- proxy


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Response:
    cfg: CollectorConfig = STATE["cfg"]
    if not _authorised(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    body = await request.body()
    ctx = px.build_context(body, STATE["seq"].take(), cfg)
    headers = px._upstream_headers(dict(request.headers), cfg)

    client = _client()
    try:
        upstream = await client.send(
            client.build_request("POST", "/chat/completions", content=body, headers=headers),
            stream=True,
        )
    except httpx.HTTPError as exc:
        # Upstream is down: tell ARTEX, and still record the attempt so a failed
        # call is visible in the capture rather than missing from it.
        await client.aclose()
        record = px.build_record(
            ctx,
            response={"error": str(exc)},
            status=502,
            streaming=False,
            ttft_ms=None,
            error=str(exc),
            captured_bytes=0,
            cfg=cfg,
        )
        STATE["queue"].offer(record)
        return JSONResponse({"error": f"upstream unreachable: {exc}"}, status_code=502)

    streaming = "text/event-stream" in upstream.headers.get("content-type", "")
    if streaming:
        return await _stream_and_capture(ctx, upstream, client, cfg)
    return await _read_and_capture(ctx, upstream, client, cfg, body)


async def _stream_and_capture(
    ctx: px.CaptureContext,
    upstream: httpx.Response,
    client: httpx.AsyncClient,
    cfg: CollectorConfig,
) -> StreamingResponse:
    acc = px.SseAccumulator()
    out_headers = px._downstream_headers(upstream.headers)

    async def body_iterator():
        buffer = b""
        try:
            async for chunk in upstream.aiter_raw():
                yield chunk
                buffer += chunk
                *lines, buffer = buffer.split(b"\n")
                for line in lines:
                    acc.feed(line.strip())
        finally:
            await upstream.aclose()
            await client.aclose()
            # Capture happens here, after the client has every byte.
            try:
                record = px.build_record(
                    ctx,
                    response=acc.as_response(),
                    status=upstream.status_code,
                    streaming=True,
                    ttft_ms=acc.first_token_ms,
                    error=None,
                    captured_bytes=acc.chunks,
                    cfg=cfg,
                )
                STATE["queue"].offer(record)
            except Exception:  # fail-open: capture must never raise into the response
                log.exception("streaming capture failed for %s", ctx.req_id)

    return StreamingResponse(
        body_iterator(),
        status_code=upstream.status_code,
        headers=out_headers,
        media_type=upstream.headers.get("content-type", "text/event-stream"),
    )


async def _read_and_capture(
    ctx: px.CaptureContext,
    upstream: httpx.Response,
    client: httpx.AsyncClient,
    cfg: CollectorConfig,
    req_body: bytes,
) -> Response:
    try:
        raw = await upstream.aread()
    finally:
        await upstream.aclose()
        await client.aclose()

    truncated = len(raw) > cfg.max_capture_bytes
    response = px._non_streaming_response(raw[: cfg.max_capture_bytes] if truncated else raw)
    try:
        record = px.build_record(
            ctx,
            response=response,
            status=upstream.status_code,
            streaming=False,
            ttft_ms=None,
            error=None,
            captured_bytes=len(raw),
            cfg=cfg,
            truncated=truncated,
        )
        STATE["queue"].offer(record)
    except Exception:
        log.exception("capture failed for %s", ctx.req_id)

    return Response(
        content=raw,
        status_code=upstream.status_code,
        headers=px._downstream_headers(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )


@app.get("/v1/models")
async def list_models(request: Request) -> Response:
    cfg: CollectorConfig = STATE["cfg"]
    if not _authorised(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    client = _client()
    try:
        upstream = await client.get(
            "/models", headers=px._upstream_headers(dict(request.headers), cfg)
        )
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=px._downstream_headers(upstream.headers),
            media_type=upstream.headers.get("content-type"),
        )
    finally:
        await client.aclose()


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def passthrough(path: str, request: Request) -> Response:
    """Anything else goes up stream unchanged. Not captured: not a model call."""
    cfg: CollectorConfig = STATE["cfg"]
    if not _authorised(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    client = _client()
    try:
        upstream = await client.request(
            request.method,
            f"/{path}",
            content=await request.body(),
            headers=px._upstream_headers(dict(request.headers), cfg),
            params=dict(request.query_params),
        )
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=px._downstream_headers(upstream.headers),
            media_type=upstream.headers.get("content-type"),
        )
    finally:
        await client.aclose()


def _debug_state() -> dict[str, Any]:
    """Test hook: lets contract tests assert counters without HTTP."""
    return STATE


__all__ = ["app"]
