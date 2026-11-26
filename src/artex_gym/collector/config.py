"""Collector settings, from the environment only.

Every value here is read once at process start. Credentials never get a default
that could be mistaken for a real key: the upstream key is required, and a
missing one fails at startup rather than sending "Bearer None" to a provider.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """The collector cannot start with this environment."""


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required")
    return value


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


@dataclass(frozen=True)
class CollectorConfig:
    upstream_base_url: str
    upstream_api_key: str
    blob_dir: Path
    queue_max: int
    run_id: str
    collector_token: str
    inbound_auth: bool
    """When true, require our local token and replace it with the provider key."""
    max_capture_bytes: int
    request_timeout_s: float

    @classmethod
    def from_env(cls) -> CollectorConfig:
        base = _required("ARTEX_GYM_UPSTREAM_BASE_URL").rstrip("/")
        return cls(
            upstream_base_url=base,
            upstream_api_key=_required("ARTEX_GYM_UPSTREAM_API_KEY"),
            blob_dir=Path(os.environ.get("ARTEX_GYM_BLOB_DIR", "/data/llm-blobs")),
            queue_max=_int("ARTEX_GYM_QUEUE_MAX", 1024),
            # A run id per collector process: M2 replaces this with a real
            # per-run id minted when a run is queued.
            run_id=os.environ.get("ARTEX_GYM_RUN_ID", "").strip() or _generated_run_id(),
            collector_token=os.environ.get("ARTEX_GYM_COLLECTOR_TOKEN", "").strip(),
            inbound_auth=os.environ.get("ARTEX_GYM_INBOUND_AUTH", "1").strip()
            not in ("0", "false", "off", "no", ""),
            # A bound on one capture. A body past this is still forwarded in full;
            # only the stored copy is truncated, and the record says so.
            max_capture_bytes=_int("ARTEX_GYM_MAX_CAPTURE_BYTES", 16 * 1024 * 1024),
            request_timeout_s=float(os.environ.get("ARTEX_GYM_REQUEST_TIMEOUT_S", "600")),
        )


def _generated_run_id() -> str:
    """A sortable, collision-resistant id for an ad-hoc collector start.

    Time-prefixed so blobs sort chronologically across runs. Not a ULID: no
    dependency, and the alphabet only needs to be filename-safe.
    """
    import time
    import uuid

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"{stamp}-{uuid.uuid4().hex[:8]}"
