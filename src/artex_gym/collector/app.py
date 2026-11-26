"""llm-logger: fail-open capture proxy between ARTEX and the model provider.

M0 stub: it serves health and metrics and forwards nothing yet. M1 fills in the
proxy path, the bounded queue and the gzip blob writer. The endpoint list here is
the contract the overlay and the CLI are written against:

    GET  /api/health   liveness for compose and for `artexctl up`
    GET  /metrics      Prometheus text; collector_dropped_total is the alarm
    POST /v1/chat/completions
    GET  /v1/models

Design notes live in adr/0002-collector-placement.md.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="artex-gym llm-logger", version="0.0.0")

# Counters are module-level until M1 wires the real queue; exposing them now keeps
# the alarm contract ("above 0") visible from the first milestone.
COUNTERS: dict[str, int] = {
    "collector_dropped_total": 0,
    "collector_written_total": 0,
    "collector_write_errors_total": 0,
    "collector_queue_depth": 0,
}


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "llm-logger"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    lines = [
        "# HELP collector_dropped_total Captures lost before reaching disk.",
        "# TYPE collector_dropped_total counter",
    ]
    lines += [f"{name} {value}" for name, value in COUNTERS.items()]
    return "\n".join(lines) + "\n"
