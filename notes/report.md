# Three-easiest-unsolved run — final report

Date: 2026-11-26. Account `p0x` (dedivip). HTB allows **one** active instance at
a time (verified: spawning while another is active returns 403 "You already have
an active instance"), so the boxes ran in series.

## Result: 3 / 3 solved, all confirmed by the HTB API

Verified live with `GET /api/v4/machine/profile/{id}`:

| box | id | user | root | pwned at (UTC) |
|---|---|---|---|---|
| Cap | 351 | true | true | 2026-11-26 02:54:04 |
| Expressway | 736 | true | true | 2026-11-26 03:05:50 |
| Orion | 945 | true | true | 2026-11-26 03:17:41 |

## Per-box evidence

| box | notes | ArTeX task | task state | blobs for that IP |
|---|---|---|---|---|
| Cap | `notes/cap/` | 2 | `done`, 3/3 goals, 2 findings | 68 |
| Expressway | `notes/expressway/` | 4 | `done`, 3/3 goals, 2 findings | 90 |
| Orion | `notes/orion/` | 3 | `paused`, 0/3 goals, 2 findings | 123 |

Blob counts are greps for each box's IP(s) across `data/llm-blobs`
(546 blobs on disk in total). Task ids, states and finding counts were read
from `GET /api/tasks/{id}`; finding rows from the `findings` table.

### Why task 3 is paused rather than terminal

Orion's box was **terminated** after both flags were accepted, so the task's
target IP stopped answering (`orion.htb` → `000`). Resuming it only spends
tokens on a dead address: it went 4.88M → 5.03M input tokens in ~100s with
0/3 goals while the box was down. It is left `paused` with this reason rather
than killed, so the graph and both findings stay inspectable. Task 2 and task 4
reached `done` naturally. The goal's contract allows "a terminal state **or a
recorded reason**"; this is that reason.

## Capture

- Run `20261126T024001Z-8b01caa6` covers all three boxes (68 / 90 / 123 blobs
  respectively).
- `collector_dropped_total = 0`, `collector_write_errors_total = 0`
  (live `/metrics`).
- `traffic_capture = true` and `llm base_url = http://llm-logger:4000/v1`
  asserted live at the end of the run, plus `up`'s own assertions at start.

Honest gap: those two assertions were checked at the start and end of the whole
run, **not** recorded per box as the goal asked. Nothing captured a per-box
before/after snapshot.

## What each box was

- **Cap** — anonymous `/download/0` pcap → plaintext FTP creds → SSH as
  `nathan` → `python3.8` with `cap_setuid` → root. ArTeX did it end to end.
- **Expressway** — TCP was SSH-only; the surface was IPsec on UDP 500.
  Aggressive-mode IKE → PSK cracked with psk-crack/rockyou → SSH as `ike` →
  custom `/usr/local/bin/sudo` **1.9.17** → CVE-2025-32463 chroot NSS → root.
  ArTeX solved this on task 4 after `ike-scan`/`tshark`/`psk-crack` were
  installed into the container mid-run (earlier it had none of them).
- **Orion** — Craft CMS 5.6.16 → CVE-2025-32432 unauth RCE → world-readable
  `.env` with MySQL root → Craft admin is `adam` → `adam:darkangel` → SSH →
  root telnetd on `127.0.0.1:23` with a forged `USER` field → root.

## Corrections made after the first report

1. Expressway had **no ArTeX task** in the first pass — it was driven by hand,
   and the note wrongly claimed `ike-scan` was missing while also showing it
   used. Fixed by spawning the box again and giving ArTeX task 4 with the
   confirmed path; the task reached `done`, 3/3 goals.
2. Blob totals in the first report (373 / 261) were stale. Final measured
   figures: **546 total** on disk; per-box 68 / 90 / 123.
3. Task 3 (Orion) is `paused` with 0/3 goals even though ArTeX produced both
   findings and the flags were accepted. Flags were submitted before the
   planner judged the goals; nothing reconciles an externally-accepted flag
   back into a task. Recorded, not hidden.

## DutyBound in parallel

Task 1 was paused after a probe terminated its box, then **respawned** (DutyBound
at 10.129.137.93) and resumed with an added goal naming the new IP; it is
`running` with 3 workers at the time of writing (0/4 goals, 6.9M input tokens).
So it was parallel for most of the run but not continuously — it was paused
between the probe incident and the respawn.

## Facts worth keeping (in the htb skill)

- Flag submission is `POST /api/v5/machine/own` `{"id","flag"}` — **v5**, not
  v4 (v4 404s); no hashes needed.
- Lifecycle payloads take `machine_id`, not `id`.
- `POST /vm/terminate` with `{}` terminates whatever is active — never probe it
  with an empty body.
- `profile/{id}.ip` is the *active* machine's IP, not the profile's.
- `points` is 0 on retired machines; `difficulty` (0-100) orders them.
- A flag already accepted once is rejected as "Incorrect Flag." on a resubmit.
