"""The blob store: gzipped, immutable, atomic.

Path is {blob_dir}/{run_id}/{capture_seq:04d}-{req_id}.json.gz — exactly the
contract, with the sequence where the spec puts the turn index. The logical
turn lives in the record and is written by the join (adr/0002).

Immutability is enforced, not assumed: an existing file is never overwritten.
A collision means either a duplicate capture or a sequence bug, and both are
worth a loud failure rather than a silent clobber.
"""

from __future__ import annotations

import gzip
import os
from pathlib import Path

from artex_gym.collector.record import CaptureRecord


class BlobExistsError(RuntimeError):
    """A blob for this (run_id, seq, req_id) is already on disk."""


class BlobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path_for(self, record: CaptureRecord) -> Path:
        return self.root / record.run_id / f"{record.capture_seq:04d}-{record.req_id}.json.gz"

    def write(self, record: CaptureRecord) -> Path:
        """Write one blob atomically. Never overwrites.

        gzip mtime is pinned to 0 and the filename is omitted from the header,
        so the same record always produces the same bytes. That is what makes
        "replaying the join reproduces byte-identical trajectories" (M3)
        checkable at the blob layer too.
        """
        target = self.path_for(record)
        target.parent.mkdir(parents=True, exist_ok=True)

        # temp file in the same directory, so rename is atomic on one filesystem
        tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        payload = record.to_bytes()
        try:
            with open(tmp, "wb") as raw:
                with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=6, mtime=0) as gz:
                    gz.write(payload)
            if target.exists():
                raise BlobExistsError(str(target))
            os.replace(tmp, target)
        finally:
            if tmp.exists():
                tmp.unlink()
        return target

    def read(self, path: Path) -> CaptureRecord:
        raw = gzip.decompress(Path(path).read_bytes())
        import json

        return CaptureRecord(**json.loads(raw))

    def list_run(self, run_id: str) -> list[Path]:
        run_dir = self.root / run_id
        if not run_dir.is_dir():
            return []
        return sorted(run_dir.glob("*.json.gz"))
