# Orion (HTB machine 945)

- **Difficulty** 32 (Easy), Linux, retired
- **Spawned** 2026-11-26, IP `10.129.244.146`
- **ArTeX task** 3 (`HTB Orion (10.129.244.146)`, Craft CMS 5.6.16)
- **Blob run** `20261126T024001Z-8b01caa6`
- **User flag** `ccdad380f82da2e01f7b9e0be0804066` — **accepted by HTB**
- **Root flag** `26c5e3416666576eef4f71a2633eee14` — **accepted by HTB**
- **Outcome** SOLVED (`machine_pwned: true`)
- **Task state** `paused`, 0/3 goals — record: the box was terminated once both
  flags were accepted, so the target IP stopped answering; resuming only spent
  tokens on a dead address. Findings 3 (critical) and 4 (high) are preserved.

## Recon

- Full TCP: only **22/tcp** (OpenSSH 8.9p1 Ubuntu) and **80/tcp** (nginx 1.18.0).
- `GET /` → 302 → `http://orion.htb/`. `/etc/hosts` in the container is
  writable, so `10.129.244.146 orion.htb` was added there.
- `/` is a static "Orion Telecom" marketing site.
- `/admin` → `/admin/login` → **Craft CMS 5.6.16** (`X-Powered-By: Craft CMS`,
  `CraftSessionId`, `CRAFT_CSRF_TOKEN`, `cpresources/`).

## Attack path

1. **CVE-2025-32432** — unauth RCE in Craft CMS ≤ 5.6.16 (fixed `[CRITICAL]` in
   5.6.17). ArTeX found it independently and dropped a PHP webshell at
   `/s.php`, confirmed `uid=33(www-data)`.
   The CSRF gate is bypassable: fetch `/admin/login`, take the
   `CRAFT_CSRF_TOKEN` value out of the returned HTML form, and send it as
   `X-CSRF-Token`. Without it the action returns 400 "Unable to verify your
   data submission"; with it, 500 "Image transform cannot be created" — i.e.
   the action is reached with no login.
2. `/var/www/html/craft/.env` is world-readable → MySQL root:
   `root:SuperSecureCraft123Pass!` on `127.0.0.1:3306`, schema `orion`.
3. `users` table: one row — `admin` / `adam@orion.htb`, admin=1. So the Craft
   admin **is** the system user `adam`.
4. `adam:darkangel` (recovered during the run) → SSH → `~/user.txt`.
5. **Privesc**: `/etc/inetd.conf` runs a **root telnetd on 127.0.0.1:23**:
   `127.0.0.1:telnet stream tcp nowait root /usr/local/sbin/telnetd telnetd`
   As adam, telnet to localhost passing a forged user field:

       ( sleep 2; printf 'id\r'; sleep 1; printf 'cat /root/root.txt\r'; sleep 1; printf 'exit\r'; sleep 3 ) \
         | USER="-f root" telnet -a 127.0.0.1 23

   → `uid=0(root)` and `root.txt`.

## ArTeX findings recorded (task 3)

- `3` **critical** — unauthenticated OS command execution as www-data via CVE-2025-32432.
- `4` **high** — root-run, localhost-only telnetd reachable as adam → root.

Both were produced by ArTeX itself, with live evidence. Task 3 still shows
`running` / 0 of 3 goals because goal completion was never asserted before the
flags were submitted manually — a bookkeeping gap, not a solving gap.

## Capture

Blobs for this box are in run `20261126T024001Z-8b01caa6`; `collector_dropped_total`
stayed **0** throughout the whole session.

## Capture assertions

Run `20261126T024001Z-8b01caa6`, blobs referencing this box's IP: **106**.
`collector_dropped_total = 0`, `collector_write_errors_total = 0`.
`traffic_capture = true`, `llm base_url = http://llm-logger:4000/v1`
(asserted at the start and end of the whole run — see notes/report.md for the
gap: this was not snapshotted per box).
