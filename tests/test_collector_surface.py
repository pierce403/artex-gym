"""Contract test for the collector's health/metrics surface. Uses the ASGI app."""

from __future__ import annotations

from fastapi.testclient import TestClient

from artex_gym.collector.app import COUNTERS, app


def test_health_is_green() -> None:
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "service": "llm-logger"}


def test_metrics_exposes_the_drop_counter() -> None:
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "collector_dropped_total" in resp.text
    for name in COUNTERS:
        assert name in resp.text
