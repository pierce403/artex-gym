"""The ARTEX pin is enforced, not documented.

These tests are hermetic: they build throwaway git repos, so they assert the
verifier's logic without depending on the developer's ARTEX checkout. One test
does check the real lock file against the real checkout, and skips if absent.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from artex_gym.pin import LOCK_PATH, ArtexPin, PinError, inspect_checkout, verify

REPO = Path(__file__).resolve().parents[1]
ARTEX_SOURCE = Path.home() / "projects" / "ARTEX"


def _git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A tiny repo with two commits, standing in for the ARTEX checkout."""
    path = tmp_path / "artex-fake"
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "t@example.com")
    _git(path, "config", "user.name", "t")
    (path / "Dockerfile").write_text("FROM scratch\n")
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "one")
    (path / "Dockerfile").write_text("FROM scratch\n# two\n")
    _git(path, "commit", "-qam", "two")
    return path


def _pin_for(path: Path) -> ArtexPin:
    return ArtexPin(
        git_sha=_git(path, "rev-parse", "HEAD"),
        git_describe=None,
        nearest_tag=None,
        source_repo="https://example.invalid/artex",
        image_repo="ghcr.io/example/artex",
        image_ref="artex:local",
        image_digest=None,
        commits_behind_upstream=None,
    )


def test_matching_checkout_verifies(repo: Path) -> None:
    pin = _pin_for(repo)
    state = verify(repo, pin)
    assert state.head_sha == pin.git_sha


def test_one_commit_off_fails_with_the_fix(repo: Path) -> None:
    pin = _pin_for(repo)
    _git(repo, "checkout", "-q", "HEAD~1")
    with pytest.raises(PinError) as exc:
        verify(repo, pin)
    message = str(exc.value)
    # The error must name the drift and the remedy, or an operator cannot act.
    assert pin.git_sha[:12] in message
    assert "git -C" in message and "checkout" in message


def test_dirty_checkout_is_allowed_but_reported(repo: Path) -> None:
    pin = _pin_for(repo)
    (repo / "Dockerfile").write_text("FROM scratch\n# local edit\n")
    state = verify(repo, pin)
    assert state.dirty is True


def test_not_a_checkout(tmp_path: Path) -> None:
    with pytest.raises(PinError, match="not a git checkout"):
        inspect_checkout(tmp_path)


def test_lock_file_is_well_formed() -> None:
    pin = ArtexPin.load(REPO / "compose" / "artex.lock.json")
    assert len(pin.git_sha) == 40
    assert pin.source_repo.endswith("pierce403/ARTEX")
    assert pin.image_repo.startswith("ghcr.io/")
    # Until the first tagged publish there is no digest to pin; the lock says so
    # rather than lying with a made-up value.
    assert pin.image_digest is None or pin.image_digest.startswith("sha256:")


def test_lock_rejects_a_short_sha(tmp_path: Path) -> None:
    bad = tmp_path / "lock.json"
    bad.write_text(json.dumps({"artex_git_sha": "38c7477"}))
    with pytest.raises(PinError, match="40-hex"):
        ArtexPin.load(bad)


@pytest.mark.skipif(not (ARTEX_SOURCE / ".git").exists(), reason="no ARTEX checkout")
def test_real_checkout_matches_the_committed_pin() -> None:
    """The developer's checkout must be the pinned commit, or `up` will refuse."""
    pin = ArtexPin.load(LOCK_PATH)
    state = verify(ARTEX_SOURCE, pin)
    assert state.head_sha == pin.git_sha
