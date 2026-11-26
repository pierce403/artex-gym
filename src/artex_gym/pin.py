"""The ARTEX pin: load the lock, verify a checkout against it.

This is the only place that decides "is this checkout the ARTEX we pinned?".
`artexctl up` calls it before building, so a drifted or detached-HEAD checkout
fails loudly instead of silently producing training data from a different agent.

See adr/0001-artex-pinning.md.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

# src/artex_gym/pin.py -> repo root. Overridable so an installed wheel can point
# at a checkout instead of failing on a path that does not exist.
_DEFAULT_LOCK = Path(__file__).resolve().parents[2] / "compose" / "artex.lock.json"
LOCK_PATH = Path(os.environ.get("ARTEX_GYM_PIN_FILE", _DEFAULT_LOCK))


class PinError(RuntimeError):
    """The checkout is not the pinned ARTEX, or the pin itself is unusable."""


@dataclass(frozen=True)
class ArtexPin:
    """What compose/artex.lock.json says we run."""

    git_sha: str
    git_describe: str | None
    nearest_tag: str | None
    source_repo: str
    image_repo: str
    image_ref: str
    image_digest: str | None
    commits_behind_upstream: int | None

    @classmethod
    def load(cls, path: Path = LOCK_PATH) -> ArtexPin:
        try:
            raw = json.loads(path.read_text())
        except FileNotFoundError as exc:
            raise PinError(f"pin file missing: {path}") from exc
        except json.JSONDecodeError as exc:
            raise PinError(f"pin file is not valid JSON: {path}: {exc}") from exc

        sha = raw.get("artex_git_sha") or ""
        if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            raise PinError(f"artex_git_sha is not a full 40-hex commit: {sha!r}")

        return cls(
            git_sha=sha,
            git_describe=raw.get("artex_git_describe"),
            nearest_tag=raw.get("artex_nearest_tag"),
            source_repo=raw.get("source_repo", ""),
            image_repo=raw.get("image_repo", ""),
            image_ref=raw.get("image_ref", ""),
            image_digest=raw.get("image_digest"),
            commits_behind_upstream=raw.get("artex_commits_behind_upstream"),
        )


@dataclass(frozen=True)
class CheckoutState:
    """What a checkout actually is, as reported by git."""

    path: Path
    head_sha: str
    describe: str
    dirty: bool

    def matches(self, pin: ArtexPin) -> bool:
        return self.head_sha == pin.git_sha


def _git(path: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise PinError(f"git {' '.join(args)} failed in {path}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def inspect_checkout(path: Path) -> CheckoutState:
    """Read a checkout without changing it (no fetch, no checkout)."""
    if not (path / ".git").exists():
        raise PinError(f"not a git checkout: {path}")
    head = _git(path, "rev-parse", "HEAD")
    try:
        describe = _git(path, "describe", "--tags", "--always")
    except PinError:
        describe = head[:7]
    dirty = bool(_git(path, "status", "--porcelain", "--untracked-files=no"))
    return CheckoutState(path=path, head_sha=head, describe=describe, dirty=dirty)


def verify(path: Path, pin: ArtexPin) -> CheckoutState:
    """Return the checkout state, or raise if it is not the pinned commit.

    A dirty checkout is allowed: the commit is what we pin, and local edits are
    visible in the error message so a surprising run is explainable. Set
    `strict_clean` in the caller if that ever stops being true.
    """
    state = inspect_checkout(path)
    if not state.matches(pin):
        raise PinError(
            f"{path} is at {state.head_sha[:12]} ({state.describe}), "
            f"but compose/artex.lock.json pins {pin.git_sha[:12]} ({pin.git_describe}).\n"
            f"  Fix: git -C {path} checkout {pin.git_sha}\n"
            f"  Or:  bump the pin in compose/artex.lock.json (and record why)."
        )
    return state
