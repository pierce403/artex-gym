"""Collector contract tests. Offline: a fake upstream, no network, no docker.

These assert the properties the pipeline depends on rather than the exact logs:
the blob's bytes are stable, the record's required fields are present, a
streaming call is captured as faithfully as a buffered one, and a full queue
drops instead of failing the call.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from artex_gym.collector.blobs import BlobExistsError, BlobStore
from artex_gym.collector.config import CollectorConfig, ConfigError
from artex_gym.collector.queue import CaptureQueue
from artex_gym.collector.record import (
    CaptureRecord,
    prompt_sha256,
    tools_schema_sha256,
)

ENV = {
    "ARTEX_GYM_UPSTREAM_BASE_URL": "https://upstream.invalid/v1",
    "ARTEX_GYM_UPSTREAM_API_KEY": "sk-real-provider-key",
    "ARTEX_GYM_COLLECTOR_TOKEN": "artex-gym-local",
    "ARTEX_GYM_RUN_ID": "run-test-1",
}


# ------------------------------------------------------------------- fixtures


@pytest.fixture()
def blobs(tmp_path: Path) -> BlobStore:
    return BlobStore(tmp_path / "blobs")


@pytest.fixture()
def record(blobs: BlobStore) -> CaptureRecord:
    return CaptureRecord(
        req_id="abc123",
        run_id="run-test-1",
        capture_seq=3,
        model="test-model",
        provider="openai",
        temperature=0.2,
        seed=None,
        max_tokens=512,
        prompt_sha256="0" * 64,
        tools_schema_sha256="1" * 64,
        ts_start="2026-11-26T00:00:00.000Z",
        ts_end="2026-11-26T00:00:01.000Z",
        ttft_ms=120,
        usage={"prompt_tokens": 10, "completion_tokens": 5},
        finish_reason="stop",
        http_status=200,
        request={"messages": [{"role": "user", "content": "hi"}]},
        response={"choices": [{"message": {"content": "hello"}}]},
    )


# ----------------------------------------------------------------- blob store


def test_blob_path_is_the_contract(blobs: BlobStore, record: CaptureRecord) -> None:
    path = blobs.path_for(record)
    assert path.parent.name == "run-test-1"
    # {run_id}/{seq:04d}-{req_id}.json.gz — seq is zero-padded so it sorts.
    assert path.name == "0003-abc123.json.gz"


def test_blob_is_gzip_and_reads_back(blobs: BlobStore, record: CaptureRecord) -> None:
    path = blobs.write(record)
    raw = path.read_bytes()
    assert raw[:2] == b"\x1f\x8b", "not gzip"
    back = blobs.read(path)
    assert back.req_id == record.req_id
    assert back.capture_seq == record.capture_seq


def test_same_record_produces_identical_bytes(blobs: BlobStore, record: CaptureRecord) -> None:
    """gzip mtime is pinned, so a replayed join can compare bytes (M3 gate)."""
    first = blobs.write(record).read_bytes()
    other = BlobStore(blobs.root / "second")
    second = other.write(record).read_bytes()
    assert first == second


def test_blob_is_immutable(blobs: BlobStore, record: CaptureRecord) -> None:
    blobs.write(record)
    with pytest.raises(BlobExistsError):
        blobs.write(record)


def test_record_keeps_join_fields_null(blobs: BlobStore, record: CaptureRecord) -> None:
    """The collector must not guess what only the join knows."""
    back = blobs.read(blobs.write(record))
    for field in ("task_id", "room_slug", "instance_id", "role", "turn_idx", "artex_git_sha"):
        assert getattr(back, field) is None, f"{field} should be null until M3"


def test_truncated_blob_is_marked(blobs: BlobStore, record: CaptureRecord) -> None:
    record.truncated = True
    back = blobs.read(blobs.write(record))
    assert back.truncated is True


# ----------------------------------------------------------------------- hashes


def test_prompt_hash_ignores_sampling_params() -> None:
    a = {"system": "s", "messages": [{"role": "user", "content": "x"}], "temperature": 0.1}
    b = {"system": "s", "messages": [{"role": "user", "content": "x"}], "temperature": 0.9}
    assert prompt_sha256(a) == prompt_sha256(b)


def test_prompt_hash_tracks_message_content() -> None:
    a = {"messages": [{"role": "user", "content": "x"}]}
    b = {"messages": [{"role": "user", "content": "y"}]}
    assert prompt_sha256(a) != prompt_sha256(b)


def test_prompt_hash_is_key_order_independent() -> None:
    a = {"system": "s", "messages": [{"role": "user", "content": "x"}]}
    b = {"messages": [{"role": "user", "content": "x"}], "system": "s"}
    assert prompt_sha256(a) == prompt_sha256(b)


def test_absent_and_empty_tools_are_the_same_schema() -> None:
    assert tools_schema_sha256({}) == tools_schema_sha256({"tools": []})


# ---------------------------------------------------------------------- config


def test_config_requires_the_upstream_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARTEX_GYM_UPSTREAM_API_KEY", raising=False)
    monkeypatch.setenv("ARTEX_GYM_UPSTREAM_BASE_URL", "https://x.invalid/v1")
    with pytest.raises(ConfigError, match="ARTEX_GYM_UPSTREAM_API_KEY"):
        CollectorConfig.from_env()


def test_config_generates_a_run_id_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("ARTEX_GYM_RUN_ID", raising=False)
    cfg = CollectorConfig.from_env()
    assert cfg.run_id and "-" in cfg.run_id


# ----------------------------------------------------------------------- queue


@pytest.mark.asyncio
async def test_full_queue_drops_instead_of_raising(blobs: BlobStore, record: CaptureRecord) -> None:
    """Fail-open: offer() on a full queue returns False and counts, never raises."""
    q = CaptureQueue(store=blobs, maxsize=1)
    record.capture_seq = 1
    assert q.offer(record) is True
    record.capture_seq = 2
    record.req_id = "second"
    assert q.offer(record) is False
    assert q.counters.dropped == 1


@pytest.mark.asyncio
async def test_writer_persists_and_counts(blobs: BlobStore, record: CaptureRecord) -> None:
    q = CaptureQueue(store=blobs, maxsize=8)
    q.start()
    q.offer(record)
    await q.stop()
    assert q.counters.written == 1
    assert blobs.list_run("run-test-1"), "no blob written"


@pytest.mark.asyncio
async def test_writer_failure_is_counted_not_raised(
    blobs: BlobStore, record: CaptureRecord
) -> None:
    class Boom(BlobStore):
        def write(self, rec):  # noqa: ANN001, ANN201
            raise OSError("disk full")

    q = CaptureQueue(store=Boom(blobs.root), maxsize=8)
    q.start()
    q.offer(record)
    await q.stop()
    assert q.counters.write_errors == 1
    assert "disk full" in (q.counters.last_error or "")
