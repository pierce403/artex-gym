"""Contract tests for the CLI surface. Offline: no docker, no network."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from artex_gym.cli.main import NOT_IMPLEMENTED_STATUS, app

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
    }.get(name, [name])
    result = runner.invoke(app, argv)
    assert result.exit_code == NOT_IMPLEMENTED_STATUS, result.output
    assert "NotImplemented" in result.output


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.startswith("artexctl ")
