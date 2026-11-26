"""Contract tests for the CLI surface. Offline: no docker, no network, no pulls.

The pin tests read the local ARTEX checkout (git only) and skip when absent;
the drift test clones it from a local file:// URL, so nothing is fetched.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from artex_gym.cli.main import NOT_IMPLEMENTED_STATUS, app

HOME_ARTEX = Path.home() / "projects" / "ARTEX"

COMMANDS = ["up", "down", "run", "collect", "dataset", "train", "eval"]

# The Done gate for M0: `artexctl --help` lists every command.
EXPECTED = [
    "up",
    "down",
    "run",
    "collect",
    "dataset",
    "train",
    "eval",
]


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_help_lists_every_command(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    # Rich draws a table: continuation lines start with the box glyph too, so
    # match on the rendered row prefix instead of parsing the column layout.
    body = result.output
    missing = [n for n in EXPECTED if f"│ {n} " not in body]
    assert not missing, f"missing from --help: {missing}\n{body}"
    assert set(COMMANDS) == set(EXPECTED)


def test_help_renders_every_subcommand(runner: CliRunner) -> None:
    for name in COMMANDS:
        result = runner.invoke(app, [name, "--help"])
        assert result.exit_code == 0, f"{name} --help failed: {result.output}"


@pytest.mark.parametrize("name", COMMANDS)
def test_commands_are_not_implemented(runner: CliRunner, name: str) -> None:
    argv = {
        "run": [name, "htb-lame"],
        "train": [name, "train.toml"],
        "eval": [name, "baseline"],
        # `up` checks the pin first, so it needs the checkout it should build.
        "up": [name, "--artex-source", str(HOME_ARTEX)],
    }.get(name, [name])
    if name == "up" and not (HOME_ARTEX / ".git").exists():
        pytest.skip("no ARTEX checkout for the pin check")
    result = runner.invoke(app, argv)
    assert result.exit_code == NOT_IMPLEMENTED_STATUS, result.output
    assert "NotImplemented" in result.output


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.startswith("artexctl ")


# --------------------------------------------------------------- pin enforcement

from artex_gym.cli.main import PIN_MISMATCH_STATUS  # noqa: E402


def test_up_refuses_a_drifted_checkout(runner: CliRunner, tmp_path) -> None:
    """The pin is enforced on the real command path, not only in pin.py's tests.

    Uses a clone of the real checkout one commit behind, so the mismatch is a
    real git state rather than a mocked return value.
    """
    src = HOME_ARTEX
    if not (src / ".git").exists():
        pytest.skip("no ARTEX checkout")
    drift = tmp_path / "drift"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "2", f"file://{src}", str(drift)],
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "-C", str(drift), "checkout", "-q", "HEAD~1"], check=True)
    result = runner.invoke(app, ["up", "--artex-source", str(drift)])
    assert result.exit_code == PIN_MISMATCH_STATUS, result.output
    assert "pins" in result.output and "checkout" in result.output


def test_up_accepts_the_pinned_checkout(runner: CliRunner) -> None:
    if not (HOME_ARTEX / ".git").exists():
        pytest.skip("no ARTEX checkout")
    result = runner.invoke(app, ["up", "--artex-source", str(HOME_ARTEX)])
    # M0: the command still stops at NotImplemented, but only after the pin check.
    assert "NotImplemented" in result.output
    assert "ARTEX pinned:" in result.output
