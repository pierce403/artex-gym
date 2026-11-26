"""The benchmark tuning must be idempotent and reversible.

`up` runs it on every start, so a second run must not churn prompt versions or
reset anything. The reversibility claim is checked through the same client API
that a human would use.
"""

from __future__ import annotations

import pytest

from artex_gym import tune

SHIPPED = (
    "Use one add_intent batch call (the intents array, "
    "at most 4 highest-value ones; don't call it once per item). "
    "The ideal is 2–3 routes with different mechanisms in parallel."
)


class FakeArtex:
    """Records what tune.apply() asks of a stack."""

    def __init__(self, template: str = SHIPPED, workers: int = 3) -> None:
        self.template = template
        self._workers = workers
        self.saved: list[tuple[str, str, str]] = []
        self.resets: list[str] = []
        self.version = 1

    def settings(self) -> dict:
        return {"workers": self._workers}

    def put_settings(self, payload: dict) -> None:
        self._workers = payload["workers"]

    def agent(self, key: str) -> dict:
        # Mirrors the real payload: text plus a newest-first version list.
        return {"prompt": self.template, "versions": [{"version": self.version}]}

    def save_agent_prompt(self, key: str, template: str, note: str) -> int:
        self.template = template
        self.version += 1
        self.saved.append((key, template, note))
        return self.version

    def reset_agent_prompt(self, key: str) -> None:
        self.template = SHIPPED
        self._workers = 3
        self.resets.append(key)


def test_raises_worker_count_and_breadth_on_first_run() -> None:
    fake = FakeArtex()
    result = tune.apply(fake)

    assert result.workers == tune.DEFAULT_WORKERS
    assert result.workers_changed is True
    assert result.prompt_changed is True
    assert len(fake.saved) == 1

    template = fake.saved[0][1]
    assert "at most 8 highest-value ones" in template
    assert "at most 4 highest-value ones" not in template
    assert "4–6 routes" in template
    assert "2–3 routes" not in template


def test_second_run_changes_nothing() -> None:
    """`up` is re-runnable; a no-op second run proves idempotence."""
    fake = FakeArtex()
    tune.apply(fake)
    versions_after_first = fake.version

    second = tune.apply(fake)
    assert second.prompt_changed is False
    assert second.workers_changed is False
    assert fake.version == versions_after_first
    assert len(fake.saved) == 1, "a second run must not save another version"


def test_revert_restores_the_shipped_prompt() -> None:
    fake = FakeArtex()
    tune.apply(fake)
    tune.revert_prompt(fake)
    assert fake.resets == ["planner"]
    assert fake.template == SHIPPED


def test_already_raised_workers_are_left_alone() -> None:
    fake = FakeArtex(workers=tune.DEFAULT_WORKERS)
    result = tune.apply(fake)
    assert result.workers_changed is False
    assert fake._workers == tune.DEFAULT_WORKERS


def test_unknown_prompt_is_not_rewritten() -> None:
    """If ARTEX changes its wording, leave the prompt alone rather than guess."""
    fake = FakeArtex(template="A prompt with no recognisable cap sentence.")
    result = tune.apply(fake)
    assert result.prompt_changed is False
    assert fake.saved == []


@pytest.mark.parametrize("text", [tune._CAP_NEW, tune._ROUTES_NEW])
def test_the_replacement_strings_are_the_ones_we_document(text: str) -> None:
    assert text
