"""`artexctl up` and `artexctl down`: bring the stack to a usable state.

`up` is not "containers started". A stack that runs but does not capture is
worse than one that is down, because it looks fine. So `up` ends on assertions:

    pin → compose → health → password → capture flags → effective LLM config

The last check is the interesting one. ARTEX resolves its LLM config as
"persisted profile, else env", so a profile saved from the UI silently shadows
ARTEX_LLM_BASE_URL and every model call bypasses the collector. See adr/0003.
"""

from __future__ import annotations

from pathlib import Path

from artex_gym import artex_api, stack
from artex_gym.artex_api import ArtexClient
from artex_gym.pin import ArtexPin, verify

# Defaults chosen in conversation; both are overridable from .env.
DEFAULT_PASSWORD = "password1234"
DEFAULT_UPSTREAM = "http://llm-logger:4000/v1"


def load_environment(required: bool = True) -> tuple[Path, dict[str, str]]:
    env_file = stack.REPO / ".env"
    return env_file, stack.read_env_file(env_file, required=required)


def resolve_source(env: dict[str, str], cli_value: Path | None = None) -> Path:
    """ARTEX checkout: --artex-source, then $ARTEX_GYM_ARTEX_SOURCE, then .env."""
    if cli_value is not None:
        return cli_value.expanduser()
    return Path(stack.require_source(env)).expanduser()


def resolve_password(env: dict[str, str]) -> str:
    """The admin password. .env wins, then the documented default.

    ARTEX requires 12 runes for a new password; a shorter value fails at
    /api/auth/init with a 400, which is a clear enough error to leave alone.
    """
    return stack.env_or_file(env, "ARTEX_GYM_ADMIN_PASSWORD", DEFAULT_PASSWORD)


def check_pin(artex_source: Path | None) -> tuple[ArtexPin, object, Path]:
    """Resolve the checkout from .env and verify it against the lock.

    Raises PinError, which the CLI maps to its own exit code so "wrong
    checkout" is never confused with "stack did not come up".
    """
    # Optional env: a pin check may be fully specified by --artex-source or the
    # process environment, and must not fail merely because .env is absent.
    _, env = load_environment(required=False)
    source = resolve_source(env, artex_source)
    pin = ArtexPin.load()
    return pin, verify(source, pin), source


def bring_up(
    artex_source: Path | None,
    detach: bool,
    skip_pin_check: bool,
    reset_llm_profiles: bool,
) -> dict:
    """Run the whole sequence and return a summary for the caller to print."""
    env_file, env = load_environment()
    source = resolve_source(env, artex_source)

    pin = ArtexPin.load()
    if not skip_pin_check:
        verify(source, pin)

    bind = stack.env_or_file(env, "ARTEX_BIND_ADDR", "127.0.0.1")
    stack.assert_loopback(bind, bind)

    st = stack.Stack(artex_source=source, env_file=env_file)
    st.up(build=True, detach=detach)

    collector = stack.wait_healthy(
        stack.COLLECTOR_HEALTH, "collector", expect=lambda b: b.get("ok") is True
    )
    artex = stack.wait_healthy(stack.ARTEX_HEALTH, "ARTEX")

    # Isolation is reported only by builds that have the startup self-test. Our
    # pin predates it, so "absent" is the normal answer — but "degraded" means
    # the agent can read its own secrets and must not be trusted. Never conflate
    # absent with isolated: that is exactly the false-green this gate exists for.
    isolation = (artex.get("isolation") or {}).get(
        "mode"
    ) or "not reported (build predates the self-test)"
    if isolation == "degraded":
        raise stack.StackError(
            "ARTEX started degraded: the agent can read jwt.key/secret.key/the MITM CA key "
            "and open the database without a password. Trajectories from this stack are not "
            "trustworthy. Check -exec-uid and the isolation self-test output."
        )

    client = ArtexClient()
    password = resolve_password(env)

    if not client.auth_status():
        token = artex_api.scrape_setup_token(st.compose_argv())
        if not token:
            raise stack.StackError(
                "ARTEX has no password set and the setup token was not found in its logs.\n"
                f"  Check: docker compose -p {stack.PROJECT} logs artex"
            )
        client.init_password(password, token)

    client.login(password)

    # Capture must be on. This one is a DB setting, not env, and defaults to off.
    client.put_settings({"traffic_capture": True})
    settings = client.settings()
    if not settings.get("traffic_capture"):
        raise stack.StackError("traffic_capture did not stick after PUT /api/settings")

    effective = client.llm()
    expected = stack.env_or_file(env, "ARTEX_GYM_BASE_URL", DEFAULT_UPSTREAM)
    if (effective.get("base_url") or "").rstrip("/") != expected.rstrip("/"):
        _enforce_collector_base_url(client, effective, expected, reset_llm_profiles)

    return {
        "artex_git_sha": pin.git_sha,
        "artex_image_digest": st.image_digest("artex"),
        "run_id": collector.get("run_id"),
        "blob_dir": collector.get("blob_dir"),
        "collector": stack.COLLECTOR_HEALTH,
        "artex": stack.ARTEX_HEALTH,
        "password": password,
        "username": artex_api.ARTEX_USERNAME,
        "isolation": isolation,
        "traffic_capture": settings.get("traffic_capture"),
        "llm_base_url": expected,
    }


def _enforce_collector_base_url(
    client: ArtexClient, effective: dict, expected: str, reset: bool
) -> None:
    """A saved profile is winning. Warn, or clear it when asked to."""
    profiles = client.profiles()
    default = [p for p in profiles if p.get("is_default")]
    if reset:
        _reset_profiles(client, profiles)
        return
    detail = "\n".join(
        f"      id={p.get('id')} name={p.get('name')!r} base_url={p.get('base_url')}"
        for p in default
    )
    raise stack.StackError(
        "a saved LLM profile shadows the collector, so model calls bypass capture.\n"
        f"      expected base_url: {expected}\n"
        f"      actual:            {effective.get('base_url')}\n"
        + (f"      default profile(s):\n{detail}\n" if default else "")
        + "      fix: artexctl up --reset-llm-profiles   (activates then deletes them)"
    )


def _reset_profiles(client: ArtexClient, profiles: list[dict]) -> None:
    """Activate a survivor, then delete the rest.

    ARTEX refuses to delete the active profile, so one must be activated first.
    With a single profile there is no survivor, and ARTEX offers no way to have
    zero profiles, so we say so rather than half-doing it.
    """
    if len(profiles) <= 1:
        raise stack.StackError(
            "only one LLM profile exists and it is active; ARTEX will not delete it.\n"
            "      Create a second profile in the UI (pointing at the collector), then re-run."
        )
    survivor = next((p for p in profiles if not p.get("is_default")), profiles[0])
    client.activate_profile(int(survivor["id"]))
    for profile in profiles:
        if profile.get("id") == survivor.get("id"):
            continue
        client.delete_profile(int(profile["id"]))


def teardown(volumes: bool) -> None:
    env_file, env = load_environment()
    source = resolve_source(env)
    stack.Stack(artex_source=source, env_file=env_file).down(volumes=volumes)


__all__ = [
    "bring_up",
    "teardown",
    "check_pin",
    "load_environment",
    "resolve_source",
    "resolve_password",
    "DEFAULT_PASSWORD",
]
