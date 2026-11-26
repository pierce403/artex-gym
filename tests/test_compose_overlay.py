"""The compose overlay must merge onto upstream ARTEX without touching it.

Runs `docker compose config`, which is local-only (no pull, no build), so this
stays inside the offline-CI rule. Skips when docker is unavailable.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ENV = {
    "POSTGRES_PASSWORD": "x",
    "ARTEX_GYM_MODEL": "test-model",
    "ARTEX_GYM_UPSTREAM_BASE_URL": "https://api.example.com/v1",
    "ARTEX_GYM_UPSTREAM_API_KEY": "sk-test",
    "ARTEX_GYM_ARTEX_SOURCE": str(Path.home() / "projects" / "ARTEX"),
}


def _artex_source() -> Path:
    src = Path(ENV["ARTEX_GYM_ARTEX_SOURCE"])
    if not (src / "docker-compose.yml").is_file():
        pytest.skip(f"ARTEX checkout not found at {src}")
    return src


@pytest.fixture(scope="module")
def merged() -> dict:
    if shutil.which("docker") is None:
        pytest.skip("docker not installed")
    src = _artex_source()
    argv = [
        "docker",
        "compose",
        "-p",
        "artex-gym",
        "--project-directory",
        str(REPO),
        "-f",
        str(src / "docker-compose.yml"),
        "-f",
        str(REPO / "compose" / "overlay.yml"),
        "--env-file",
        "/dev/null",
        "config",
        "--format",
        "json",
    ]
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", **ENV}
    proc = subprocess.run(argv, capture_output=True, text=True, env=env, check=False)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_upstream_services_are_kept(merged: dict) -> None:
    assert {"postgres", "artex", "llm-logger"} <= set(merged["services"])


def test_artex_is_pointed_at_the_collector(merged: dict) -> None:
    env = merged["services"]["artex"]["environment"]
    assert env["ARTEX_LLM_PROVIDER"] == "openai"
    assert env["ARTEX_LLM_BASE_URL"] == "http://llm-logger:4000/v1"
    # ARTEX must not receive the provider key.
    assert env["OPENAI_API_KEY"] == "artex-gym-local"


def test_artex_builds_from_the_pinned_checkout(merged: dict) -> None:
    build = merged["services"]["artex"]["build"]
    assert Path(build["context"]).resolve() == _artex_source().resolve()


def test_runtime_data_stays_in_this_repo(merged: dict) -> None:
    targets = {
        v["target"]: Path(v["source"]).resolve()
        for v in merged["services"]["artex"]["volumes"]
        if v["type"] == "bind"
    }
    assert targets["/app/data"] == (REPO / "data").resolve()
    assert targets["/app/keys"] == (REPO / "keys").resolve()
    # Skills come from the checkout, not from an empty ./skills here.
    assert targets["/app/skills"].parent == _artex_source().resolve()


def test_collector_is_health_gated(merged: dict) -> None:
    depends = merged["services"]["artex"]["depends_on"]
    assert depends["llm-logger"]["condition"] == "service_healthy"
    assert "api/health" in " ".join(merged["services"]["llm-logger"]["healthcheck"]["test"])
