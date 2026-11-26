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
    POST /api/v5/machine/own   # submit a flag  {"id": <machine_id>, "flag": "..."}
    POST /arena/own       # release-arena machines use this instead of machine/own
    POST /machine/submit  # machine questions/answers

`vm/spawn`, `vm/terminate`, `vm/reset` are **POST only** (GET → 405).
`machine/own` is **POST only** and needs both `id` and `flag`.

There is **no** `/machine/own/{id}`, `/machine/play/{id}`, or
`/machine/{id}` route (all 404). Do not construct them.

### Flag submission — v5, not v4

    POST /api/v5/machine/own   {"id": 123, "flag": "HTB{...}"}

**Machines own on v5.** `POST /api/v4/machine/own` is 404 with a valid token;
the web app sets `enableV5Api` only for MACHINE. No hashes, links or
accept_terms are needed — that is `POST /api/v4/machine/submit`, which is the
*creator* form for submitting a new machine.

A wrong flag answers `400 {"message":"Incorrect Flag."}` — a real answer, not a
broken call.

Beware the lookalikes:

| route | what it actually is |
|---|---|
| `POST /api/v5/machine/own` | **flag submission** (what you want) |
| `POST /api/v4/machine/submit` | submit a NEW machine for review (creator form) |
| `POST /api/v4/machines/{cid}/tasks/{tid}/flag` | Starting Point per-task flags |

Strip whitespace from a pasted flag before sending; a trailing space is the
usual false "wrong flag".

## Always shut the box down once the flags are accepted

**The last step of every box is `terminate`, not "flags recorded".** A solved box
left running:

- holds the single instance slot, so the next box cannot be spawned;
- silently expires (~8h) and then answers nothing, so any task still pointed at
  its IP burns model tokens against a dead address;
- costs nothing in HTB credit but costs real money in LLM calls.

Order of operations, every time:

    1. read the flags off the box
    2. POST /api/v5/machine/own  (submit)   <- until accepted, the box is NOT done
    3. verify: profile/{id}.authUserInRootOwns == true
    4. POST /vm/terminate                    <- do not skip
    5. GET /machine/active  -> expect "no machine is active"

If step 2 is rejected, **do not terminate yet** — flags rotate on respawn, so a
rejected flag plus a terminated box means the work is lost and must be redone.

A "solved" claim with `authUserInRootOwns: false` is not solved. This happened
for real: ARTeX finished a task with `done`, 4/4 goals and both flags in its
report, but nobody submitted them, so HTB still showed the box unowned. See
`notes/report.md`.

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
spawn attempts produce confusing errors, not a queue — and this is **not** a
free-tier limitation: a `dedivip` account is refused identically
(`403 "You already have an active instance"`), and there is no plural endpoint
(`/api/v5/virtual_machine/active` returns one object, not a list).

**The box is the bottleneck, so breadth has to come from elsewhere.** The real
limit is planner breadth, not worker count: the planner prompt caps a round at a
few intents, so extra workers sit idle (measured: Cap got 2 intents, Expressway
3, Orion 4, with 3 workers each). `artexctl up` raises both — see
`adr/0003-parallelism.md`.

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
