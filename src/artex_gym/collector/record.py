"""Capture records: the schema of one blob, and the hashes that identify it.

The blob is the unit the rest of the pipeline reads, so its shape is pinned
here rather than in the proxy. Two hashes are computed at write time because the
information only exists in the request: prompt_sha256 and
tools_schema_sha256. They are what M4 dedupes training rows on.

Fields the collector cannot know — task_id, room_slug, instance_id, role,
turn_idx — are null here and filled by the M3 join. capture_seq is the
collector's own ordering within a run, which is what the filename sorts by.
See adr/0002-collector-placement.md.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

# Roles ARTEX uses for LLM lanes, from llmrec.parseSession and WithWorker.
ROLES = ("planner", "worker", "oneshot")


def canonical_json(value: Any) -> bytes:
    """Stable bytes for hashing: key order and separators fixed, no spaces."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prompt_sha256(request: dict[str, Any]) -> str:
    """Hash of the prompt as sent.

    Covers the system prompt and the message list, which is what determines the
    model's output for a fixed request. Deliberately excludes sampling params:
    temperature changes a sample, not the prompt.
    """
    system = request.get("system")
    messages = request.get("messages") or []
    return sha256_hex(canonical_json({"system": system, "messages": messages}))


def tools_schema_sha256(request: dict[str, Any]) -> str:
    """Hash of the tool schema block. Absent and empty are the same schema."""
    return sha256_hex(canonical_json(request.get("tools") or []))


@dataclass
class CaptureRecord:
    # --- identity, known at write time -------------------------------------
    req_id: str
    run_id: str
    capture_seq: int
    model: str
    provider: str
    temperature: float | None
    seed: int | None
    max_tokens: int | None
    prompt_sha256: str
    tools_schema_sha256: str
    ts_start: str
    ts_end: str
    ttft_ms: int | None
    usage: dict[str, Any] | None
    finish_reason: str | None
    http_status: int
    request: Any
    response: Any

    # --- filled by the join (M3) ------------------------------------------
    # Null here and now, so a reader never mistakes a guess for ground truth.
    task_id: str | None = None
    room_slug: str | None = None
    instance_id: str | None = None
    role: str | None = None
    turn_idx: int | None = None
    artex_git_sha: str | None = None

    # --- provenance and honesty -------------------------------------------
    streaming: bool = False
    truncated: bool = False
    error: str | None = None
    redaction: dict[str, Any] = field(default_factory=lambda: {"applied": False})
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_bytes(self) -> bytes:
        return canonical_json(self.to_dict())


def response_sha256(record: CaptureRecord) -> str:
    """Hash of the model output. Dedupe key together with prompt_sha256."""
    return sha256_hex(canonical_json(record.response))
