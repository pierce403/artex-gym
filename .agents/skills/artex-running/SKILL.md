---
name: artex-running
description: Check, start, and verify a local ARTEX stack with capture enabled — the artex-gym compose overlay, the llm-logger collector, Postgres, health/isolation gates, admin login, traffic_capture and llm_record settings, and proving an LLM call is actually being captured. Use when asked whether ARTEX is up, to start or restart it, to turn logging/capture on, to find where blobs land, or when a run must be shown to be capturable before trusting it.
---

# ARTEX running with capture enabled

A stack that is *running* but not *capturing* looks identical to a healthy one
and silently produces untrainable data. Every check here answers "is it
capturing?", not "is it up?".

## The three containers

| service | port | role |
|---|---|---|
| `artex` | 8787 (API/UI), 8788 (traffic proxy) | the agent |
| `llm-logger` | 4000 (host-local) | capture proxy between ARTEX and the provider |
| `postgres` | internal | ARTEX state |

ARTEX talks to the *collector*, not the provider:
`ARTEX_LLM_BASE_URL=http://llm-logger:4000/v1`. Trailing `/v1` is required —
ARTEX appends `/chat/completions`.

## Fast check (read-only, no mutation)

    curl -s localhost:8787/api/health          # ARTEX: ok + isolation
    curl -s localhost:4000/api/health          # collector: ok + run_id + dropped
    curl -s localhost:4000/metrics | grep dropped

`/api/health` on ARTEX is unauthenticated and returns `{"ok":true}` only. With a
token, *newer* builds also return `isolation`.

**`isolation.mode == "degraded"` is a failure**: a degraded agent can read its
own secrets (`jwt.key`, `secret.key`, MITM CA key) and open the DB without a
password, which poisons trajectories.

**`isolation` absent is not the same as isolated.** The startup self-test landed
after our pinned commit (`38c7477`), so on this stack the field is simply not
reported. Never treat "absent" as a pass — say what it is.

Capture settings are **database rows, not env vars**, and both default to off:

    traffic_capture   # gates whether agents get the proxy wired in at all
    llm_record        # ARTEX's own duplicate copy of calls (leave OFF; the collector is the record)

## Full control script

    scripts/artex-status.sh              # check only
    scripts/artex-status.sh --fix        # start the stack, then assert capture
    scripts/artex-status.sh --fix --password-env ARTEX_GYM_ADMIN_PASSWORD

Everything is env-driven from `.env` in the repo root (copy `.env.example`):

    ARTEX_GYM_ARTEX_SOURCE=/path/to/ARTEX     # pinned checkout (required)
    ARTEX_GYM_MODEL=...
    ARTEX_GYM_UPSTREAM_BASE_URL=https://.../v1
    ARTEX_GYM_UPSTREAM_API_KEY=sk-...         # real provider key: collector only
    ARTEX_GYM_COLLECTOR_TOKEN=artex-gym-local # ARTEX gets this, not the real key
    ARTEX_GYM_ADMIN_PASSWORD=password1234      # >=12 chars (ARTEX's minimum)

## Rules that bite

1. **Username is `ARTEX`**, uppercase, byte-compared, not configurable. `artex`
   fails exactly like a wrong password.
2. **Password must be ≥12 runes** on *first set* (`/api/auth/init`). Login never
   checks length, so a shorter password works only if seeded directly into
   Postgres. Default `password1234` is 12.
3. **First boot needs the setup token**, printed to container stderr:
   `Setup token for the /setup page: <token>`. Then
   `POST /api/auth/init {"password":..., "setup_token":...}`. A later run gets
   403 "Password is already set" — treat that as success, so `up` is re-runnable.
4. **A saved LLM profile shadows the env.** ARTEX resolves config as
   "persisted default profile, else env". A profile saved in the UI silently
   bypasses the collector. Verify with
   `GET /api/llm` → `base_url` must be `http://llm-logger:4000/v1`.
   `artexctl up` fails on a mismatch; `--reset-llm-profiles` clears them
   (ARTEX refuses to delete the *active* one, so activate a survivor first).
5. **Loopback only.** `ARTEX_BIND_ADDR` defaults to `127.0.0.1` and 8788 is
   hardcoded to loopback. Never widen it.
6. **The agent shares the container network namespace**, so it can reach
   `127.0.0.1:8787` and `PUT /api/settings` to turn capture off mid-run. Check
   the flags at `collect` time, not only at `up`.

## Prove a call is captured

    curl -s localhost:4000/v1/chat/completions \
      -H 'content-type: application/json' \
      -H 'authorization: Bearer artex-gym-local' \
      -d '{"model":"<ARTEX_GYM_MODEL>","messages":[{"role":"user","content":"Say OK."}],"max_tokens":8}'

    find data/llm-blobs -name '*.json.gz' | sort | tail -1
    gunzip -c <blob> | python3 -m json.tool | head -30
    curl -s localhost:4000/metrics | grep -E 'dropped|written'

A valid blob has `http_status`, `prompt_sha256`, `tools_schema_sha256`,
`usage`, `finish_reason`, and `null` for `task_id`/`role`/`turn_idx` — those
belong to the join (M3), and the collector must never guess them.

## Known gap on the pinned build

The pin predates the agent-isolation self-test and the allowlisted executor
environment (both arrived in later upstream commits). So on this stack the agent
process inherits the container environment more broadly than a newer ARTEX would
allow. Do not report "isolated" for this stack.

`collector_dropped_total` above 0 is the alarm: fail-open means a full queue
loses blobs without failing the call.

## Restart collector after env changes

The collector reads env once at startup:

    docker compose -p artex-gym --project-directory . --env-file .env \
      -f "$ARTEX_GYM_ARTEX_SOURCE/docker-compose.yml" -f compose/overlay.yml \
      up -d --build llm-logger

## Blob layout

    data/llm-blobs/{run_id}/{capture_seq:04d}-{req_id}.json.gz

Gzipped, immutable (never overwritten; a collision raises), atomic
temp+rename. `capture_seq` is the collector's ordering within a run; the
logical `turn_idx` is written by the join. `run_id` is per collector process
in M1 and becomes a real per-run id in M2.
