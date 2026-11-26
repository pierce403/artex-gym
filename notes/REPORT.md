# Three-easiest-unsolved run — final report

Date: 2026-11-26. Account `p0x` (dedivip). HTB gives **one** active instance at a
time, verified live, so the three boxes ran in series.

## Result: 3 / 3 solved

| box | id | flags (both accepted by HTB) | notes | ArTeX task | outcome |
|---|---|---|---|---|---|
| Cap | 351 | user `c43f1749…`, root `48afe25f…` | `notes/cap/` | 2 — `done`, 3/3 goals | solved by ArTeX |
| Expressway | 736 | user `a126d80d…`, root `780a5799…` | `notes/expressway/` | none — solved manually | solved by hand |
| Orion | 945 | user `ccdad380…`, root `26c5e341…` | `notes/orion/` | 3 — still `running` | solved by ArTeX (flags submitted by hand) |

HTB confirms `user_owned=True root_owned=True` for all three.

## Capture

- Collector run covering the whole session: `20261126T024001Z-8b01caa6`
- **373 blobs** on disk across all runs; 261 in the session run.
- **`collector_dropped_total = 0`** — no capture lost at any point.
- Earlier run `20261126T020227Z-15ec7ffd` holds 108 blobs including the 16
  `402` responses from the unfunded-key window (recorded, not dropped).

## What each box actually was

- **Cap** — anonymous `/download/0` pcap → plaintext FTP creds `nathan:…` →
  SSH → `python3.8` with `cap_setuid` → root. ArTeX did the whole thing:
  1.22M input tokens, ~3 minutes, both findings recorded.
- **Expressway** — TCP was SSH-only; UDP 500/4500 = IPsec. Aggressive-mode IKE
  → PSK cracked (`freakingrockstarontheroad`) → SSH as `ike` → custom
  `sudo 1.9.17` → **CVE-2025-32463** chroot NSS → root.
- **Orion** — Craft CMS 5.6.16 → **CVE-2025-32432** unauth RCE → world-readable
  `.env` with MySQL root → Craft admin is `adam` → `adam:darkangel` → SSH →
  root telnetd on `127.0.0.1:23` with a forged `USER` field → root.

## Bookkeeping gaps this run exposed

1. **Task 3 still says `running`, 0/3 goals**, although ArTeX produced both
   findings and the flags were submitted. ArTeX judged goals only when the
   planner got to it; flags were obtained manually before that happened. The
   task is idle-but-unfinished, and nothing reconciles "flag already accepted
   externally" back into the task.
2. **Task 1 (DutyBound) is `paused`, 0/3, 6.79M input tokens** — it was left
   paused after a probe terminated its box. The 3.8M tokens of task 3 plus
   these are the bulk of the spend.
3. **Expressway had no ArTeX task at all.** The container lacked `ike-scan`,
   `hashcat`, `tshark`, and has no `CAP_NET_ADMIN`/`/dev/net/tun`, so IPsec was
   untouchable from inside. That is a real capability gap, not laziness:
   fixing it needs image + `cap_add` changes.

## Facts worth keeping (added to the htb skill)

- Flag submission is `POST /api/v5/machine/own` `{"id","flag"}` — **v5**, not
  v4 (v4 404s), and no hashes needed.
- Lifecycle payloads take `machine_id`, not `id`.
- `POST /vm/terminate` with `{}` terminates whatever is active — never probe it.
- `profile/{id}.ip` is the *active* machine's IP, not the profile's.
- `points` is 0 on retired machines; `difficulty` (0-100) is what orders them.
