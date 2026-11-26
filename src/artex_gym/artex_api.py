"""Talking to a running ARTEX: health, auth, settings.

Every call here is against a documented public endpoint (adr/0003). Nothing
reads ARTEX's database directly, so a lock bump cannot break this module —
it can only make a `GET /api/llm` answer differently, which is an assertion
failure, not an import error.

The one deliberate exception is the setup token, which ARTEX prints to stderr
rather than exposing over HTTP. Scraping it is log-format coupling; it is
confined to `scrape_setup_token` so a wording change breaks one function.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

import httpx

# ARTEX's login username is a hardcoded constant (server/auth.go), compared
# byte-for-byte and never normalised. Sending "artex" fails exactly like a wrong
# password, so this is pinned here and asserted by a test.
ARTEX_USERNAME = "ARTEX"

_SETUP_TOKEN_RE = re.compile(r"Setup token for the /setup page:\s*(\S+)")


class ArtexError(RuntimeError):
    """ARTEX answered, but not with what a healthy stack should answer."""


@dataclass
class ArtexClient:
    base_url: str = "http://127.0.0.1:8787"
    token: str | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def health(self) -> dict:
        resp = httpx.get(f"{self.base_url}/api/health", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def login(self, password: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/api/auth/login",
            json={"username": ARTEX_USERNAME, "password": password},
            timeout=15,
        )
        if resp.status_code == 403:
            raise ArtexError(
                "no password is set yet; run the init step "
                "(POST /api/auth/init with the setup token)"
            )
        if resp.status_code != 200:
            raise ArtexError(f"login failed ({resp.status_code}): {resp.text}")
        self.token = resp.json()["token"]
        return self.token

    def init_password(self, password: str, setup_token: str) -> None:
        """Set the first password. 403 "already set" is success, not failure."""
        resp = httpx.post(
            f"{self.base_url}/api/auth/init",
            json={"password": password, "setup_token": setup_token},
            timeout=15,
        )
        if resp.status_code == 200:
            self.token = resp.json()["token"]
            return
        if resp.status_code == 403 and "already set" in resp.text.lower():
            return
        raise ArtexError(f"password init failed ({resp.status_code}): {resp.text}")

    def auth_status(self) -> bool:
        resp = httpx.get(f"{self.base_url}/api/auth/status", timeout=10)
        resp.raise_for_status()
        return bool(resp.json().get("initialized"))

    def settings(self) -> dict:
        resp = httpx.get(f"{self.base_url}/api/settings", headers=self._headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def put_settings(self, payload: dict) -> None:
        resp = httpx.put(
            f"{self.base_url}/api/settings", json=payload, headers=self._headers(), timeout=10
        )
        if resp.status_code != 200:
            raise ArtexError(f"settings update failed ({resp.status_code}): {resp.text}")

    def llm(self) -> dict:
        resp = httpx.get(f"{self.base_url}/api/llm", headers=self._headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def profiles(self) -> list[dict]:
        resp = httpx.get(f"{self.base_url}/api/llm/profiles", headers=self._headers(), timeout=10)
        resp.raise_for_status()
        return resp.json().get("profiles", [])

    def activate_profile(self, profile_id: int) -> None:
        resp = httpx.post(
            f"{self.base_url}/api/llm/profiles/active",
            json={"id": profile_id},
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code != 200:
            raise ArtexError(f"activate profile failed ({resp.status_code}): {resp.text}")

    def delete_profile(self, profile_id: int) -> None:
        resp = httpx.delete(
            f"{self.base_url}/api/llm/profiles/{profile_id}", headers=self._headers(), timeout=10
        )
        if resp.status_code != 200:
            raise ArtexError(f"delete profile failed ({resp.status_code}): {resp.text}")


def scrape_setup_token(compose_argv: list[str], service: str = "artex") -> str | None:
    """Read the one-time setup token from the artex container's stderr.

    ARTEX prints it once at startup while no password is set. This is the only
    log-format dependency in the project.
    """
    proc = subprocess.run(
        [*compose_argv, "logs", "--no-color", service],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    matches = _SETUP_TOKEN_RE.findall(proc.stdout + proc.stderr)
    return matches[-1] if matches else None
