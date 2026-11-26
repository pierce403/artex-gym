"""The compose invocation, and the stack lifecycle built on it.

PROJECT_DIRECTORY is this repo, so every relative path in the *upstream* compose
file resolves here; the overlay re-points the two that must not (build context,
skills). adr/0001 explains why we merge rather than copy.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
OVERLAY = REPO / "compose" / "overlay.yml"
PROJECT = "artex-gym"
COLLECTOR_HEALTH = "http://127.0.0.1:4000/api/health"
ARTEX_HEALTH = "http://127.0.0.1:8787/api/health"


class StackError(RuntimeError):
    """The stack did not reach the state the milestone requires."""


@dataclass
class Stack:
    artex_source: Path
    env_file: Path

    def compose_argv(self) -> list[str]:
        return [
            "docker",
            "compose",
            "-p",
            PROJECT,
            "--project-directory",
            str(REPO),
            "--env-file",
            str(self.env_file),
            "-f",
            str(self.artex_source / "docker-compose.yml"),
            "-f",
            str(OVERLAY),
        ]

    def up(self, build: bool = True, detach: bool = True) -> None:
        argv = [*self.compose_argv(), "up", "-d" if detach else "--abort-on-container-exit"]
        if build:
            argv.append("--build")
        _run(argv)

    def down(self, volumes: bool = False) -> None:
        argv = [*self.compose_argv(), "down"]
        if volumes:
            argv.append("--volumes")
        _run(argv)

    def logs(self, service: str, tail: int = 30) -> str:
        proc = subprocess.run(
            [*self.compose_argv(), "logs", "--no-color", "--tail", str(tail), service],
            capture_output=True,
            text=True,
            check=False,
        )
        return (proc.stdout + proc.stderr).strip()

    def image_digest(self, service: str = "artex") -> str | None:
        """The local image ID for a service, so the lock can record what ran.

        `docker compose images --format json` emits a JSON *array* (one object
        per container), not JSONL — and it carries `ID`, not `Digest`, because a
        locally built image has no registry manifest digest. ID is the honest
        local answer; a registry digest appears once the tag is published.
        """
        proc = subprocess.run(
            [*self.compose_argv(), "images", "--format", "json", service],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        try:
            rows = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            return None
        if isinstance(rows, dict):
            rows = [rows]
        for row in rows:
            if isinstance(row, dict) and row.get("ID"):
                return str(row["ID"])
        return None


def _run(argv: list[str]) -> None:
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise StackError(f"{' '.join(argv[:6])}... failed:\n{proc.stderr.strip()}")


def wait_healthy(url: str, what: str, timeout_s: float = 180.0, expect=None) -> dict:
    """Poll a health endpoint until it answers, or fail with the reason."""
    deadline = time.monotonic() + timeout_s
    last = ""
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(url, timeout=5)
            if resp.status_code == 200:
                body = resp.json()
                if expect is None or expect(body):
                    return body
                last = f"answered but not ready: {body}"
            else:
                last = f"HTTP {resp.status_code}"
        except httpx.HTTPError as exc:
            last = str(exc)
        time.sleep(1.0)
    raise StackError(f"{what} not healthy within {timeout_s:.0f}s at {url} ({last})")


_LABEL_RE = re.compile(r"^localhost-only: (.*)$", re.MULTILINE)


def assert_loopback(bind_addr: str, published: str) -> None:
    """The stack must not be reachable off-host (adr/0003).

    Two independent gates are checked because either alone is a claim we would be
    trusting: the ARTEX bind address, and the docker port publishing.
    """
    allowed = {"127.0.0.1", "::1", "localhost"}
    if bind_addr not in allowed:
        raise StackError(
            f"ARTEX_BIND_ADDR is {bind_addr!r}; only loopback is allowed so the "
            f"stack is not reachable off-host. Unset it or set 127.0.0.1."
        )
    host = published.split(":")[0]
    if host not in allowed:
        raise StackError(f"port published on {host!r}, not loopback")


def read_env_file(path: Path, required: bool = True) -> dict[str, str]:
    """Minimal .env reader: KEY=VALUE, '#' comments, no interpolation.

    `required=False` is for read-only steps (the pin check) that may be fully
    specified by a flag or the process environment; `up` itself requires it.
    """
    out: dict[str, str] = {}
    if not path.is_file():
        if not required:
            return out
        raise StackError(f"env file not found: {path} (copy .env.example to .env)")
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def env_or_file(env: dict[str, str], key: str, default: str = "") -> str:
    """Process env wins over .env, which wins over the default."""
    return os.environ.get(key) or env.get(key) or default


def require_source(env: dict[str, str]) -> str:
    """ARTEX_GYM_ARTEX_SOURCE must be configured; there is no guessed default.

    Guessing a path is how a benchmark silently runs a different checkout than
    the operator thinks, so a missing value is an error naming the file to fix.
    """
    value = env_or_file(env, "ARTEX_GYM_ARTEX_SOURCE")
    if not value:
        raise StackError(
            "ARTEX_GYM_ARTEX_SOURCE is not set (in the environment or .env).\n"
            "  Add e.g. ARTEX_GYM_ARTEX_SOURCE=/path/to/ARTEX to .env"
        )
    return value
