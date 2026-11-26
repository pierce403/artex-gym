"""Contract test for the collector's health/metrics surface. Uses the ASGI app.

Replaces the M0 stub assertion (a module-level COUNTERS dict) with the real
contract: the endpoints answer, and /metrics always carries the drop counter
the alarm rule is written against.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from artex_gym.collector import app as app_module

REQUIRED_SERIES = [
    "collector_dropped_total",
    "collector_written_total",
    "collector_write_errors_total",
    "collector_queue_depth",
]


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ARTEX_GYM_UPSTREAM_BASE_URL", "https://upstream.invalid/v1")
    monkeypatch.setenv("ARTEX_GYM_UPSTREAM_API_KEY", "sk-test")
    monkeypatch.setenv("ARTEX_GYM_BLOB_DIR", str(tmp_path / "blobs"))
    monkeypatch.setenv("ARTEX_GYM_RUN_ID", "run-surface-1")
    with TestClient(app_module.app) as c:
        yield c


def test_health_is_green(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["service"] == "llm-logger"
    assert body["run_id"] == "run-surface-1"


def test_metrics_exposes_the_drop_counter(client: TestClient) -> None:
    resp = client.get("/metrics")
    assert resp.status_code == 200
    for name in REQUIRED_SERIES:
        assert name in resp.text, f"{name} missing from /metrics"


def test_drop_counter_starts_at_zero(client: TestClient) -> None:
    """The alarm rule is "above 0", so a fresh collector must read exactly 0."""
    text = client.get("/metrics").text
    line = next(ln for ln in text.splitlines() if ln.startswith("collector_dropped_total "))
    assert line.split()[1] == "0"
