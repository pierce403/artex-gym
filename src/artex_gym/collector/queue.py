"""Fail-open capture queue.

A logging failure must never kill a run. So the request path does exactly one
thing here: offer the record to a bounded queue and return. Nothing awaits a
disk write, and nothing on the request path can raise from the writer.

The three outcomes, all counted:

  accepted   the writer will persist it
  dropped    the queue was full (bounded, so memory cannot grow without bound)
  failed     the writer raised; the record is lost, the run is not

Drops are the alarm. adr/0002 fixes that the metric is always exported and the
CLI warns; a non-zero exit needs --strict.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from artex_gym.collector.blobs import BlobExistsError, BlobStore
from artex_gym.collector.record import CaptureRecord

log = logging.getLogger("llm-logger.queue")


@dataclass
class Counters:
    accepted: int = 0
    written: int = 0
    dropped: int = 0
    write_errors: int = 0
    depth: int = 0
    last_error: str | None = None


@dataclass
class CaptureQueue:
    """Bounded, single-writer capture queue."""

    store: BlobStore
    maxsize: int = 1024
    counters: Counters = field(default_factory=Counters)
    _queue: asyncio.Queue[CaptureRecord] = field(init=False, repr=False)
    _task: asyncio.Task[None] | None = field(default=None, init=False, repr=False)
    _stopping: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._queue = asyncio.Queue(maxsize=self.maxsize)

    # ------------------------------------------------------------ request path

    def offer(self, record: CaptureRecord) -> bool:
        """Enqueue without blocking. Returns False when the record was dropped.

        This is called from the response path, so it must never raise and never
        await. put_nowait on a bounded queue is exactly that.
        """
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull:
            self.counters.dropped += 1
            log.warning(
                "capture queue full (%d): dropped %s for run %s",
                self.maxsize,
                record.req_id,
                record.run_id,
            )
            return False
        self.counters.accepted += 1
        self.counters.depth = self._queue.qsize()
        return True

    # ------------------------------------------------------------- writer side

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="capture-writer")

    async def stop(self, timeout: float = 10.0) -> None:
        """Drain what is queued, then stop. A hung writer is abandoned, not fatal."""
        self._stopping = True
        if self._task is None:
            return
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
        except TimeoutError:
            log.warning(
                "capture queue did not drain within %.1fs; %d left", timeout, self._queue.qsize()
            )
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        while True:
            record = await self._queue.get()
            try:
                self.store.write(record)
                self.counters.written += 1
            except BlobExistsError as exc:
                # Not a drop: the bytes are on disk, just under a name we expected
                # to be free. Counted separately so it is never silently ignored.
                self.counters.write_errors += 1
                self.counters.last_error = f"blob exists: {exc}"
                log.error("blob already present, not overwritten: %s", exc)
            except Exception as exc:  # fail-open: the run must not care
                self.counters.write_errors += 1
                self.counters.last_error = str(exc)
                log.exception("capture write failed for %s: %s", record.req_id, exc)
            finally:
                self.counters.depth = self._queue.qsize()
                self._queue.task_done()
