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
# Machine ownership moved to v5: the web app posts /machine/own with
# enableV5Api for MACHINE only (common-api: `a = n === MACHINE`). On v4 the same
# path is 404, which is why every v4 probe looked like a missing route.
BASE_V5 = "https://labs.hackthebox.com/api/v5"
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


def call(
    method: str, path: str, body: dict | None = None, *, retry_429: bool = True, v5: bool = False
) -> dict:
    """One request. On 429, sleep Retry-After once and retry; then fail."""
    url = f"{BASE_V5 if v5 else BASE}{path}"
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
    """Active/all machines. Trailing slash and query are required by the route."""
    if args.retired:
        path = f"/machine/list/retired/paginated/?page={args.page}&per_page={args.per_page}"
        if args.sort_by:
            path += f"&sort_by={args.sort_by}"
    else:
        path = f"/machine/paginated/?page={args.page}&per_page={args.per_page}"
    return call("GET", path)


def _machines(payload: dict) -> list[dict]:
    """The list payload's machine array.

    `data` is the documented-in-practice key (htb-cli parses "data"). Pagination
    metadata sits alongside it; fall back to top-level lists so a shape change
    degrades to something printable instead of a crash.
    """
    for key in ("data", "machines", "info"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _is_easy(machine: dict) -> bool:
    """Easy per the list payload.

    `difficultyText` is the human label; `difficulty` is a 0-100 numeric score
    where lower is easier (Cap=28, DoubleTake=36, all labelled "Easy"). `points`
    is 0 on every retired machine, so it is useless as a difficulty proxy even
    though it looks like one.
    """
    text = machine.get("difficultyText") or machine.get("difficulty_text")
    if isinstance(text, str):
        return text.strip().lower() == "easy"
    score = machine.get("difficulty")
    return isinstance(score, int) and score <= 40


def _owned(machine: dict) -> bool:
    """True when the user already owns user and/or root, per the list payload."""
    return bool(machine.get("authUserInUserOwns") or machine.get("authUserInRootOwns"))


def _retired(machine: dict) -> bool:
    """There is no `retired` key: a machine is retired when `active` is null."""
    return machine.get("active") is None


def cmd_easy(args) -> dict:
    """Easiest unowned machines. Retired first, because that is what a benchmark wants."""
    rows: list[dict] = []
    errors: list[str] = []
    for label, path in (
        ("retired", "/machine/list/retired/paginated/?per_page=100&sort_by=release-date"),
        ("active", "/machine/paginated/?per_page=100"),
    ):
        if args.source not in ("both", label):
            continue
        try:
            payload = call("GET", path)
        except HtbError as exc:
            errors.append(f"{label}: {exc}")
            print(f"  ({label}: {exc})", file=sys.stderr)
            continue
        for machine in _machines(payload):
            if _is_easy(machine) and not _owned(machine):
                rows.append({**machine, "_source": label})

    # The numeric difficulty score orders them honestly; `points` is 0 on all
    # retired machines and would make the order alphabetical by accident.
    rows.sort(key=lambda m: (m.get("difficulty") or 0, m.get("name") or ""))
    shown = rows[: args.limit]
    if not shown:
        # Both sources failing is not "no machines" — it is a broken call, and
        # reporting it as an empty catalogue hides the real cause.
        if errors and len(errors) == (2 if args.source == "both" else 1):
            raise HtbError(errors[0])
        print("no easy unowned machines found")
        return {"machines": []}
    print(
        f"{'id':>5}  {'name':<18} {'os':<8} {'diff':>4} {'pts':>4}  "
        f"{'retired':<7} {'free':<5} source"
    )
    for m in shown:
        print(
            f"{m.get('id', '?'):>5}  {str(m.get('name', '?'))[:18]:<18} "
            f"{str(m.get('os', '?'))[:8]:<8} {str(m.get('difficulty', '?')):>4} "
            f"{str(m.get('static_points', '?')):>4}  "
            f"{str(_retired(m)):<7} {str(bool(m.get('free'))):<5} {m['_source']}"
        )
    return {"machines": shown}


QUEUE_PATH = "notes/queue.json"
TIER_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2, "Insane": 3}


def _all_retired() -> list[dict]:
    """Every retired machine, following meta.last_page rather than guessing."""
    rows: list[dict] = []
    page = 1
    last = 1
    while page <= last:
        payload = call(
            "GET",
            f"/machine/list/retired/paginated/?page={page}&per_page=100&sort_by=release-date",
        )
        rows.extend(_machines(payload))
        meta = payload.get("meta") or {}
        last = int(meta.get("last_page") or 1)
        page += 1
    return rows


def _slug(machine: dict) -> str:
    """Directory name for a box: lowercase name, id-suffixed to stay unique."""
    name = str(machine.get("name") or "unknown")
    keep = [c.lower() if (c.isalnum() or c in "-_") else "-" for c in name]
    return f"{''.join(keep).strip('-')}-{machine.get('id')}"


def _load_queue(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"boxes": []}


def _save_queue(path: str, queue: dict) -> None:
    import os

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(queue, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def cmd_queue(args) -> dict:
    """Build or refresh the working queue: unowned boxes, easiest first.

    Resumable by construction: each box keeps its recorded state across runs, so
    re-running never resets `solved`, `timeout` or `skipped`. A box that has
    since been owned on HTB is marked `solved` (that is the ground truth), which
    also picks up boxes solved outside this loop.
    """
    path = args.path
    previous = _load_queue(path)
    prev_by_id = {str(b["id"]): b for b in previous.get("boxes", [])}

    machines = _all_retired()
    rows = []
    for m in machines:
        mid = str(m.get("id"))
        owned = _owned(m)
        prior = prev_by_id.get(mid, {})
        state = prior.get("state") or "pending"
        if owned:
            state = "solved"
        rows.append(
            {
                "id": m.get("id"),
                "name": m.get("name"),
                "slug": _slug(m),
                "tier": m.get("difficultyText") or "Unknown",
                "difficulty": m.get("difficulty") or 0,
                "os": m.get("os"),
                "free": bool(m.get("free")),
                "retired": _retired(m),
                "state": state,
                "task_id": prior.get("task_id"),
                "ip": prior.get("ip"),
                "attempts": prior.get("attempts", 0),
                "note": prior.get("note", ""),
            }
        )

    # Difficulty order is the whole point: lowest numeric score first, then tier,
    # then name so the order is stable and reproducible.
    rows.sort(key=lambda r: (r["difficulty"], TIER_ORDER.get(r["tier"], 9), r["name"] or ""))

    pending = [r for r in rows if r["state"] == "pending"]
    queue = {
        "generated_from": "GET /machine/list/retired/paginated (all pages)",
        "total_retired": len(machines),
        "unowned": sum(1 for r in rows if not _owned_source(r)),
        "boxes": rows,
    }
    _save_queue(path, queue)

    from collections import Counter

    per_tier = Counter(r["tier"] for r in pending)
    print(f"queue: {path}")
    print(f"  retired seen : {len(machines)}")
    print(f"  solved       : {sum(1 for r in rows if r['state'] == 'solved')}")
    print(f"  timeout      : {sum(1 for r in rows if r['state'] == 'timeout')}")
    print(f"  skipped      : {sum(1 for r in rows if str(r['state']).startswith('skipped'))}")
    tiers = " ".join(f"{k}={v}" for k, v in sorted(per_tier.items()))
    print(f"  pending      : {len(pending)}  {tiers}")
    if pending:
        nxt = pending[0]
        print(
            f"  next up      : {nxt['id']} {nxt['name']} "
            f"({nxt['tier']}, diff {nxt['difficulty']})"
        )
    return {"pending": len(pending), "per_tier": dict(per_tier)}


def _owned_source(row: dict) -> bool:
    """A queue row came from a machine the API marked owned only if state says so."""
    return row.get("state") == "solved"


def cmd_find(args) -> dict:
    q = urllib.parse.quote(args.name)
    data = call("GET", f"/search/fetch?query={q}")
    # The response shape is not documented; show what came back rather than
    # guessing at a key name.
    print(json.dumps(data, indent=2))
    return data


def cmd_profile(args) -> dict:
    data = call("GET", f"/machine/profile/{args.id}")
    info = data.get("info", data)
    play = info.get("playInfo") or {}
    for key in ("id", "name", "os", "difficulty", "difficultyText", "points", "active", "retired"):
        if key in info:
            print(f"{key:14} {info[key]}")

    # TRAP: `ip` on a profile is the IP of whatever machine is spawned right now,
    # not of the machine you asked about. Verified 2026-11-26: profiles 351, 692
    # and 999 all returned 10.129.137.83. Trust playInfo, never `ip`.
    spawned = bool(play.get("isActive") or play.get("isSpawned"))
    print(f"{'spawned':14} {spawned}")
    if spawned:
        print(f"{'ip':14} {info.get('ip')}  (this machine is the active one)")
        print(f"{'expires_at':14} {play.get('expires_at')}")
    else:
        print(f"{'ip':14} —  (not spawned; profile.ip is the ACTIVE machine's, ignore it)")
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
            f"terminating id={current.get('id')} {current.get('name')!r} to free the free-tier slot"
        )
        call("POST", "/vm/terminate", {"machine_id": current.get("id")})
        # Wait for the slot to actually free; spawning immediately after a
        # terminate is the usual source of confusing errors.
        for _ in range(12):
            time.sleep(5)
            if not call("GET", "/machine/active").get("info"):
                break
        else:
            raise HtbError("the slot did not free within 60s of terminate")

    print(f"spawning id={args.id}")
    call("POST", "/vm/spawn", {"machine_id": args.id})

    for _ in range(24):
        time.sleep(5)
        info = call("GET", "/machine/active").get("info")
        if info and info.get("ip"):
            print(
                f"up: id={info.get('id')} ip={info.get('ip')} expires_at={info.get('expires_at')}"
            )
            return info
    raise HtbError("spawn issued but no IP appeared within 120s; check the HTB UI and the VPN")


def cmd_reset(args) -> dict:
    return call("POST", "/vm/reset", {"machine_id": args.id})


def cmd_stop(_args) -> dict:
    info = call("GET", "/machine/active").get("info")
    if not info:
        print("nothing to terminate")
        return {}
    print(f"terminating id={info.get('id')} {info.get('name')!r}")
    return call("POST", "/vm/terminate", {"machine_id": info.get("id")})


def cmd_own(args) -> dict:
    """Submit a flag. Route is v5, and needs only id + flag (no hashes).

    A wrong flag answers 400 {"message":"Incorrect Flag."}; that is a real
    answer, not a failure of the call, so it is reported distinctly.
    """
    flag = "".join(args.flag.split())  # a trailing space is the classic false negative
    try:
        result = call("POST", "/machine/own", {"id": args.id, "flag": flag}, v5=True)
    except HtbError as exc:
        text = str(exc)
        if "Incorrect Flag" in text:
            print(f"rejected: {args.id} did not accept that flag")
            return {"accepted": False, "machine": args.id}
        raise
    print(f"accepted: {args.id}")
    return result


def cmd_vpn(_args) -> dict:
    return call("GET", "/connection/status")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="HTB Labs v4 helper (single-slot aware)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("active").set_defaults(fn=cmd_active)
    sub.add_parser("stop").set_defaults(fn=cmd_stop)
    sub.add_parser("vpn").set_defaults(fn=cmd_vpn)

    q = sub.add_parser("queue", help="build/refresh the resumable box queue")
    q.add_argument("--path", default=QUEUE_PATH)
    q.set_defaults(fn=cmd_queue)

    easy = sub.add_parser("easy", help="easiest unowned machines")
    easy.add_argument("--limit", type=int, default=10)
    easy.add_argument("--source", choices=["retired", "active", "both"], default="both")
    easy.set_defaults(fn=cmd_easy)

    lst = sub.add_parser("list")
    lst.add_argument("--retired", action="store_true", help="retired catalogue instead")
    lst.add_argument("--sort-by", dest="sort_by", default="")
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
    if isinstance(result, dict) and args.cmd in {"list", "reset", "own", "vpn", "stop", "queue"}:
        # Full payload, not a truncated prefix: piping this into another tool must
        # not produce unparseable JSON.
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
