#!/usr/bin/env python3
"""HTB Labs v4 helper. Enforces the one-machine free-tier rule.

    htb.py active
    htb.py list [--page N] [--per-page N]
    htb.py find NAME
    htb.py profile ID
    htb.py spawn ID [--yes]
    htb.py reset ID
    htb.py stop
    htb.py own ID FLAG
    htb.py vpn

Reads HTB_TOKEN from the environment. Never prints the token.

Design notes:
  - `Accept: application/json` is mandatory: without it every route returns a
    302 to HTML, which looks exactly like a missing endpoint.
  - Spawning frees the single slot first, and says what it terminated.
  - No spawn retry loop: one attempt, then a clear error. A blind retry on free
    tier makes the failure harder to read, not easier.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://labs.hackthebox.com/api/v4"
UA = "artex-gym-htb/0.1"


class HtbError(RuntimeError):
    pass


def token() -> str:
    """The app token: $HTB_TOKEN, else $HTB_TOKEN_FILE, else ./htb.txt.

    A file is read and whitespace-stripped, because a pasted token usually
    carries a trailing newline and often a literal "..." from a truncated copy.
    Validated here so a bad token fails with a readable reason instead of a
    generic 401 that looks like a permissions problem.
    """
    tok = os.environ.get("HTB_TOKEN", "").strip()
    source = "$HTB_TOKEN"
    if not tok:
        path = os.environ.get("HTB_TOKEN_FILE", "").strip()
        if not path and os.path.isfile("htb.txt"):
            path = "htb.txt"
        if path:
            try:
                tok = "".join(Path(path).read_text().split())
                source = path
            except OSError as exc:
                raise HtbError(f"cannot read token file {path}: {exc}") from None
    if not tok:
        raise HtbError(
            "no token: set HTB_TOKEN, or put the app token in htb.txt "
            "(app.hackthebox.com -> profile -> Settings -> App Tokens)"
        )
    validate_token(tok, source)
    return tok


def validate_token(tok: str, source: str) -> None:
    """Reject a token that clearly cannot work, naming why.

    Three checks, each of which has a distinct real cause:
      - a literal "...": copied from a UI that truncated the display
      - wrong segment count: not a JWT at all (a password, or a cookie)
      - a short signature: complete-looking but cut off
    """
    if tok.endswith("..."):
        raise HtbError(
            f"token from {source} is truncated (ends with '...'). "
            "Copy the full value — the UI truncates long tokens on screen."
        )
    parts = tok.split(".")
    if len(parts) != 3:
        raise HtbError(
            f"token from {source} is not a JWT ({len(parts)} segments, expected 3). "
            "An app token is a long eyJ... string, not a password or a cookie."
        )
    # Base64url of a 256-byte RS256 signature is ~342 chars. Anything much
    # shorter means the copy stopped early.
    if len(parts[2]) < 300:
        raise HtbError(
            f"token from {source} looks truncated: signature is {len(parts[2])} chars, "
            "expected ~342 for RS256. Copy the whole token again."
        )


def call(method: str, path: str, body: dict | None = None, *, retry_429: bool = True) -> dict:
    """One request. On 429, sleep Retry-After once and retry; then fail."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token()}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", UA)
    if data:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        if exc.code == 429 and retry_429:
            wait = int(exc.headers.get("Retry-After") or 30)
            print(f"  rate limited; sleeping {wait}s", file=sys.stderr)
            time.sleep(wait)
            return call(method, path, body, retry_429=False)
        detail = exc.read().decode("utf-8", "replace")[:300]
        hint = {
            401: "token missing/invalid, or the request lacked Accept: application/json",
            404: "route does not exist (this API's 404s are accurate)",
            405: "wrong HTTP method for this route",
        }.get(exc.code, "")
        raise HtbError(f"{method} {path} -> {exc.code} {detail} {hint}".strip()) from None
    except urllib.error.URLError as exc:
        raise HtbError(f"{method} {path} -> network error: {exc.reason}") from None


# ------------------------------------------------------------------ commands


def cmd_active(_args) -> dict:
    data = call("GET", "/machine/active")
    info = data.get("info")
    if not info:
        print("no machine is active")
        return data
    print(
        f"active: id={info.get('id')} name={info.get('name')!r} "
        f"ip={info.get('ip')} expires_at={info.get('expires_at')}"
    )
    if not info.get("ip"):
        print("  warning: no IP yet — still spawning, or the tunnel is down")
    return data


def cmd_list(args) -> dict:
    return call("GET", f"/machine/paginated?page={args.page}&per_page={args.per_page}")


def cmd_find(args) -> dict:
    q = urllib.parse.quote(args.name)
    data = call("GET", f"/search/fetch?query={q}")
    # The response shape is not documented; show what came back rather than
    # guessing at a key name.
    print(json.dumps(data, indent=2)[:4000])
    return data


def cmd_profile(args) -> dict:
    data = call("GET", f"/machine/profile/{args.id}")
    info = data.get("info", data)
    for key in ("id", "name", "os", "difficulty", "points", "retired", "ip"):
        if key in info:
            print(f"{key:12} {info[key]}")
    return data


def cmd_spawn(args) -> dict:
    try:
        current = call("GET", "/machine/active").get("info")
    except HtbError as exc:
        raise HtbError(f"cannot check the active slot before spawning: {exc}") from None

    if current:
        if current.get("id") == args.id:
            print(f"machine {args.id} is already active at {current.get('ip')}")
            return current
        print(
            f"terminating id={current.get('id')} {current.get('name')!r} "
            "to free the free-tier slot"
        )
        call("POST", "/vm/terminate", {"id": current.get("id")})
        # Wait for the slot to actually free; spawning immediately after a
        # terminate is the usual source of confusing errors.
        for _ in range(12):
            time.sleep(5)
            if not call("GET", "/machine/active").get("info"):
                break
        else:
            raise HtbError("the slot did not free within 60s of terminate")

    print(f"spawning id={args.id}")
    call("POST", "/vm/spawn", {"id": args.id})

    for _ in range(24):
        time.sleep(5)
        info = call("GET", "/machine/active").get("info")
        if info and info.get("ip"):
            print(
                f"up: id={info.get('id')} ip={info.get('ip')} "
                f"expires_at={info.get('expires_at')}"
            )
            return info
    raise HtbError("spawn issued but no IP appeared within 120s; check the HTB UI and the VPN")


def cmd_reset(args) -> dict:
    return call("POST", "/vm/reset", {"id": args.id})


def cmd_stop(_args) -> dict:
    info = call("GET", "/machine/active").get("info")
    if not info:
        print("nothing to terminate")
        return {}
    print(f"terminating id={info.get('id')} {info.get('name')!r}")
    return call("POST", "/vm/terminate", {"id": info.get("id")})


def cmd_own(args) -> dict:
    flag = "".join(args.flag.split())  # a trailing space is the classic false negative
    return call("POST", "/machine/own", {"id": args.id, "flag": flag})


def cmd_vpn(_args) -> dict:
    return call("GET", "/connection/status")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="HTB Labs v4 helper (single-slot aware)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("active").set_defaults(fn=cmd_active)
    sub.add_parser("stop").set_defaults(fn=cmd_stop)
    sub.add_parser("vpn").set_defaults(fn=cmd_vpn)

    lst = sub.add_parser("list")
    lst.add_argument("--page", type=int, default=1)
    lst.add_argument("--per-page", type=int, default=50, dest="per_page")
    lst.set_defaults(fn=cmd_list)

    find = sub.add_parser("find")
    find.add_argument("name")
    find.set_defaults(fn=cmd_find)

    prof = sub.add_parser("profile")
    prof.add_argument("id", type=int)
    prof.set_defaults(fn=cmd_profile)

    spawn = sub.add_parser("spawn")
    spawn.add_argument("id", type=int)
    spawn.set_defaults(fn=cmd_spawn)

    reset = sub.add_parser("reset")
    reset.add_argument("id", type=int)
    reset.set_defaults(fn=cmd_reset)

    own = sub.add_parser("own")
    own.add_argument("id", type=int)
    own.add_argument("flag")
    own.set_defaults(fn=cmd_own)

    args = p.parse_args(argv)
    try:
        result = args.fn(args)
    except HtbError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if isinstance(result, dict) and args.cmd in {"list", "reset", "own", "vpn", "stop"}:
        print(json.dumps(result, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
