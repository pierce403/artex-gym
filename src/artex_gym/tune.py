"""Make a stack benchmark-ready, and record why.

Two settings decide how much of the box a run actually explores in parallel, and
both were wrong for this use:

1. **workers** — ARTEX defaults to 3 worker agents per task.
2. **the planner's intent batch cap** — the seeded planner prompt says "at most
   4 highest-value ones" and calls 2-3 parallel routes "the ideal". That cap,
   not the worker count, is what limits parallelism: with 2-3 intents open, a
   3-worker (or 8-worker) task still runs mostly serial. Measured on a real run:
   Cap produced 2 intents, Expressway 3, Orion 4, so extra workers idled.

Raising the prompt cap is a versioned, reversible edit (`POST
/api/agents/planner/prompt/reset` restores the built-in default), so it is safe
to apply from `up`.

Every change here is idempotent: re-running finds the text already present and
does nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_WORKERS = 8

# The two sentences in the shipped planner prompt that throttle breadth.
_CAP_OLD = "at most 4 highest-value ones"
_CAP_NEW = "at most 8 highest-value ones"
_ROUTES_OLD = "The ideal is 2–3 routes with different mechanisms in parallel"
_ROUTES_NEW = "The ideal is 4–6 routes with different mechanisms in parallel"

_NOTE = (
    "Benchmark breadth: intent batch cap 4 -> 8 and the ideal route count "
    "2-3 -> 4-6, so more workers can be fed in parallel. Revert with "
    "POST /api/agents/planner/prompt/reset."
)


def _current_version(agent: dict) -> int | None:
    """The live prompt version.

    `GET /api/agents/{key}` carries the text but not a top-level version; the
    version list is newest-first, so its head is the current one.
    """
    versions = agent.get("versions") or []
    if versions and isinstance(versions[0], dict):
        return versions[0].get("version")
    return agent.get("version")


@dataclass
class TuneResult:
    workers: int
    workers_changed: bool
    prompt_version: int | None
    prompt_changed: bool
    detail: str


def apply(artex, workers: int = DEFAULT_WORKERS) -> TuneResult:
    """Set worker count and planner breadth. Idempotent."""
    before = artex.settings()
    changed_workers = before.get("workers") != workers
    if changed_workers:
        artex.put_settings({"workers": workers})

    agent = artex.agent("planner")
    template: str = agent["prompt"]
    version = _current_version(agent)
    detail = "prompt already broad enough"

    if _CAP_NEW in template and _ROUTES_NEW in template:
        return TuneResult(workers, changed_workers, version, False, detail)

    if _CAP_OLD in template:
        template = template.replace(_CAP_OLD, _CAP_NEW)
    if _ROUTES_OLD in template:
        template = template.replace(_ROUTES_OLD, _ROUTES_NEW)

    if template == agent["prompt"]:
        return TuneResult(
            workers,
            changed_workers,
            agent.get("version"),
            False,
            "no known cap sentence found; leaving the prompt alone",
        )

    version = artex.save_agent_prompt("planner", template, _NOTE)
    return TuneResult(workers, changed_workers, version, True, "planner breadth raised")


def revert_prompt(artex) -> None:
    """Restore the built-in planner prompt. Kept next to apply() so the
    reversibility in the docstring is executable, not just a claim."""
    artex.reset_agent_prompt("planner")
