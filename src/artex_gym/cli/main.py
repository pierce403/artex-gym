"""Typer entry point for artexctl.

Every command is a stub in M0. Help text is the contract: options shown here
are the options the milestone implementation must accept, so `--help` doubles
as the interface spec.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from artex_gym import __version__

app = typer.Typer(
    name="artexctl",
    help="ARTEX capture → join → dataset → train → eval pipeline.",
    no_args_is_help=True,
    add_completion=False,
)
# NB: rich_markup_mode="plain" raises AssertionError inside rich with typer 0.29
# when a command help contains bracketed text like "[M1]". The default mode is
# used instead; keep bracket claims out of help strings if that changes.

NOT_IMPLEMENTED_STATUS = 3


def _todo(command: str, milestone: str) -> None:
    """Exit non-zero, naming the milestone that implements this command."""
    typer.secho(f"{command}: NotImplemented (planned in {milestone})", fg=typer.colors.YELLOW)
    raise typer.Exit(NOT_IMPLEMENTED_STATUS)


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Print version and exit.", is_eager=True),
    ] = False,
) -> None:
    if version:
        typer.echo(f"artexctl {__version__}")
        raise typer.Exit(0)


# --------------------------------------------------------------------- stack


@app.command(help="Provision the stack: ARTEX + collector + Postgres, from a compose overlay. [M1]")
def up(
    artex_source: Annotated[
        Path | None,
        typer.Option(help="ARTEX git checkout to build/reference. Defaults to $ARTEX_SOURCE."),
    ] = None,
    detach: Annotated[
        bool, typer.Option(help="Return once healthy instead of streaming logs.")
    ] = True,
) -> None:
    _todo("up", "M1")


@app.command(help="Tear down the stack. Keeps the data volumes unless --volumes. [M1]")
def down(
    volumes: Annotated[bool, typer.Option(help="Also delete Postgres and blob volumes.")] = False,
) -> None:
    _todo("down", "M1")


# ----------------------------------------------------------------------- run


@app.command(help="Queue a run for one room: N attempts, a fresh instance each. [M2]")
def run(
    room: Annotated[str, typer.Argument(help="Room slug, e.g. htb-lame or thm-blueprint.")],
    attempts: Annotated[int, typer.Option("--attempts", "-n", help="Attempts to queue.")] = 1,
    provider: Annotated[str, typer.Option(help="Provider adapter: htb | thm.")] = "htb",
    tier: Annotated[
        str, typer.Option(help="Difficulty tier, recorded on every training row.")
    ] = "easy",
    max_turns: Annotated[int | None, typer.Option(help="Turn budget passed to ARTEX.")] = None,
) -> None:
    _todo("run", "M2 (HTB) / M5 (THM)")


# ------------------------------------------------------------------- collect


@app.command(help="Drain the collector and join blobs + graph into trajectories. [M3]")
def collect(
    run_id: Annotated[
        str, typer.Option("--run-id", help="Only join one run. Default: all pending.")
    ] = "",
    dry_run: Annotated[
        bool, typer.Option(help="Report joins without writing trajectories.")
    ] = False,
) -> None:
    _todo("collect", "M3")


# ------------------------------------------------------------------- dataset


@app.command(help="Build SFT/DPO splits and the split manifest. [M4]")
def dataset(
    kind: Annotated[str, typer.Option(help="Output shape: sft | dpo | both.")] = "both",
    out: Annotated[Path, typer.Option(help="Directory for rows, splits and manifest.")] = Path(
        "artifacts/dataset"
    ),
    config: Annotated[
        Path | None, typer.Option(help="Dataset config; filters are mandatory either way.")
    ] = None,
) -> None:
    _todo("dataset", "M4")


# --------------------------------------------------------------------- train


@app.command(help="LoRA/QLoRA training run from a config file. [M6]")
def train(
    config: Annotated[Path, typer.Argument(help="Train config (schema in adr/).")],
    resume: Annotated[
        bool, typer.Option(help="Resume the last checkpoint for this config.")
    ] = False,
) -> None:
    _todo("train", "M6")


# ---------------------------------------------------------------------- eval


@app.command(help="Baseline or post-train eval over held-out rooms. [M6]")
def eval(  # noqa: A001 - the command name is part of the CLI contract
    run_id: Annotated[str, typer.Argument(help="Run id to evaluate, or 'baseline'.")],
    config: Annotated[
        Path | None, typer.Option(help="Eval config; defaults to the train config's eval block.")
    ] = None,
) -> None:
    _todo("eval", "M6")


if __name__ == "__main__":
    app()
