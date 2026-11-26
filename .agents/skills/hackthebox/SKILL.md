---
name: hackthebox
description: Enumerate, search, start, reset, stop, and submit flags on HackTheBox Labs machines through the v4 API (labs.hackthebox.com), plus VPN/tunnel status and the one-active-machine constraint of free tier. Use when asked what HTB boxes exist or are retired, to find a box by name or difficulty, to spawn/play/terminate/reset a machine, to check what is active or expiring, to submit a flag, or when an HTB API call fails with 401/404/429.
---

# HackTheBox Labs API (v4)

Base URL: `https://labs.hackthebox.com/api/v4`

    Authorization: Bearer $HTB_TOKEN
    Accept: application/json        # REQUIRED — see the trap below

`HTB_TOKEN` is an **App Token**, not a password and not the session cookie:
app.hackthebox.com → profile → Settings → App Tokens.

## The trap that costs the most time

**Without `Accept: application/json`, every endpoint returns a 302 redirect to
HTML instead of JSON.** That reads like "endpoint missing" and sends you hunting
for the wrong bug. With it, you get a real `401 {"error":"Unauthenticated."}`.

Status code decoding on this API:

| code | means |
|---|---|
| 401 | route exists, token missing/invalid |
| 405 | route exists, wrong HTTP method (e.g. GET on a POST-only route) |
| 404 | route does not exist — trust this, it is accurate |
| 429 | rate limited; honour `Retry-After` |

## Verified endpoints

Route existence verified 2026-11-26 by status-code probing against the live API
(no token). Payload shapes are inferred from a maintained client
(`GoToolSharing/htb-cli`) plus the API's own conventions, not from official
docs — official docs are not publicly reachable. Re-verify before trusting a
payload shape.

### Enumerate / search

    GET  /machine/paginated/?per_page=100          # catalogue (trailing slash!)
    GET  /machine/list/retired/paginated/?per_page=100&sort_by=release-date
    GET  /machine/profile/{id}                     # one machine by numeric id
    GET  /machine/active                           # currently spawned machine
    GET  /season/machine/active                    # season-active machine
    GET  /machine/recommended/                     # suggested next box
    GET  /search/fetch?query={name}                # resolve a NAME to an id
    GET  /user/info                                # who the token is
    GET  /connection/status                        # VPN/tunnel up?
    GET  /access/ovpnfile/{id}/0                   # download .ovpn
    GET  /challenge/list                           # challenges (not machines)

**`GET /machine/list` does not exist** (404) — but
`/machine/list/retired/paginated/` does. The catalogue routes need a trailing
slash; without it some hosts 404, which reads as "wrong endpoint" when the only
problem is the missing slash.

Name → id needs `/search/fetch`; profiles are keyed by numeric id only.

### Lifecycle (all POST)

    POST /vm/spawn        # start a machine        {"id": <machine_id>}
    POST /vm/terminate    # stop the active machine {"id": <machine_id>}
    POST /vm/reset        # revert to clean state  {"id": <machine_id>}
    POST /machine/own     # submit the user flag    {"id": <machine_id>, "flag": "..."}
    POST /arena/own       # release-arena machines use this instead of machine/own
    POST /machine/submit  # machine questions/answers

`vm/spawn`, `vm/terminate`, `vm/reset` are **POST only** (GET → 405).
`machine/own` is **POST only** and needs both `id` and `flag`.

There is **no** `/machine/own/{id}`, `/machine/play/{id}`, or
`/machine/{id}` route (all 404). Do not construct them.

### Flag submission

    POST /machine/own   {"id": 123, "flag": "deadbeef..."}

Strip whitespace from a pasted flag before sending; a trailing space is the
usual false "wrong flag".

## Free tier: exactly one active machine

Free accounts may have **one** machine spawned at a time. Every workflow here
must assume a single slot:

1. `GET /machine/active` — if one is up and it is not the target, `POST
   /vm/terminate` first.
2. `POST /vm/spawn`.
3. Poll `/machine/active` until `ip` is present and stable; spawn is not
   instant.
4. Work.
5. `POST /vm/terminate` — free the slot even on failure, or the next spawn
   fails.

Machines have an **expiry** (`expires_at` on `/machine/active`); a box can die
mid-run. Check it before long runs, and treat a mid-run death as
`timeout`/`crashed`, not as a failed attempt.

Serialize every spawn through a single-slot queue with backoff. Concurrent
spawn attempts on free tier produce confusing errors, not a queue.

## Enumerate → pick → spawn

    # what is up right now?
    curl -s -H "Accept: application/json" -H "Authorization: Bearer $HTB_TOKEN" \
      https://labs.hackthebox.com/api/v4/machine/active | jq .

    # catalogue page 1 (name, id, difficulty, os, points)
    curl -s -H "Accept: application/json" -H "Authorization: Bearer $HTB_TOKEN" \
      "https://labs.hackthebox.com/api/v4/machine/paginated?page=1&per_page=50" | jq .

    # resolve a name to an id
    curl -s -H "Accept: application/json" -H "Authorization: Bearer $HTB_TOKEN" \
      "https://labs.hackthebox.com/api/v4/search/fetch?query=Lame" | jq .

    # profile of one machine
    curl -s -H "Accept: application/json" -H "Authorization: Bearer $HTB_TOKEN" \
      https://labs.hackthebox.com/api/v4/machine/profile/1 | jq .

## Local evidence, not /tmp

Two places, both in-tree, both gitignored:

    .work/vendor/htb-cli     # the reference client (scripts/vendor.sh)
    .work/probes/             # ad-hoc request payloads used while probing

`references/endpoints.md` cites line-level paths into the vendored checkout, so
a claim can be re-read instead of trusted. Re-vendor with `scripts/vendor.sh
--update` and diff the reference file if the API moved.

## Scripts

    scripts/htb.py active
    scripts/htb.py easy                       # easiest unowned (the default question)
    scripts/htb.py easy --limit 3 --source retired
    scripts/htb.py list --page 1 --per-page 50
    scripts/htb.py list --retired --sort-by release-date
    scripts/htb.py find Lame
    scripts/htb.py profile 1
    scripts/htb.py spawn 1        # terminates the current machine first
    scripts/htb.py reset 1
    scripts/htb.py stop
    scripts/htb.py own 1 <flag>
    scripts/htb.py vpn

The script enforces the single slot, prints what it terminated, and never
retries a spawn blindly.

## Rate limits and etiquette

The API rate-limits but does not publish numbers. Treat these as hard rules:

- Do not poll `/machine/active` faster than every 5s while spawning.
- On 429, sleep `Retry-After` (or 30s) and retry once; then give up loudly.
- Never spawn in a loop. One attempt, then report.
- Enumeration pages are cheap; lifecycle calls are not. Cache the catalogue for
  the duration of a task instead of re-fetching per lookup.

## Gotchas

- **`profile/{id}.ip` is the ACTIVE machine's IP**, not the profile's. Three
  different profiles returned the same IP. Use `playInfo.isActive` to decide
  whether the machine you asked about is the spawned one.
- **`points` is 0 on retired machines**; `static_points` is the score and
  `difficulty` (0-100) orders them. `difficultyText` is the label.
- **No `retired` key in list rows** — retired means `active` is `null`.
- **Difficulty tiers** are `easy`/`medium`/`hard`/`insane` in the UI; the list
  gives `difficultyText` (string) *and* `difficulty` (int). Never assume one.
- **Retired vs active**: retired machines are still in `/machine/paginated`;
  keeping them out of a training split set is a filtering concern, not an API one.
- **Release arena** machines take `/arena/own`, not `/machine/own`. Submitting
  to the wrong one returns a rejection that looks like a wrong flag.
- **A 401 with a valid-looking token** is usually the token being an API key from
  a different product, or an unset `HTB_TOKEN` that expanded to empty.
- Flags are machine-specific and rotate on reset. Never cache a flag across
  spawns.

## Recording what you learned

This API has no public docs, so the file at `references/endpoints.md` is the
authoritative record for this project. When you confirm a route or payload
shape, add it there with the date and the exact command, and note whether it
came from a live call or from inference.
