# Cap (HTB machine 351)

- **Difficulty** 28 (Easy), Linux, `free: true`, retired
- **ArTeX task** 2 (`HTB Cap (10.129.137.86)`), status `done`, 3/3 goals
- **Spawned** 2026-11-26, IP `10.129.137.86`, expires 2026-11-27 02:47:11
- **Blob run** `20261126T024001Z-8b01caa6` (165 captured calls, 0 dropped)
- **User flag** `c43f174928cfb0e06fb5c16b19a21094` — **accepted by HTB**
- **Root flag** `48afe25f4e7c5e80500ed6c516e57e9a` — **accepted by HTB**
- **Outcome** SOLVED (`machine_pwned: true`), tokens 1.22M in / 40k out

## Attack path

1. Anonymous FTP on 21 — `vsFTPd 3.0.3`, but the win was the web app.
2. `GET /download/0` on the dashboard served a **packet capture** with no auth.
3. The pcap contained `nathan:Buck3tH4TF0RM3!` in plaintext FTP traffic.
4. SSH as `nathan` → user.txt.
5. `/usr/bin/python3.8` has `cap_setuid` → `os.setuid(0)` → root.txt.

Full command transcript with PoC: `poc.md`. Flags: `flags.txt`.

## Notes on how it was solved

The recon in the task goal (ports, `/download`, pcap) came from an earlier
*chat* session, whose artifacts live in `/app/data/sessions/conv-1/`. ARTeX's
task 2 reused them and finished in ~3 minutes for 1.22M input tokens.

Two findings recorded by ARTeX (both `high`):
- `1` — Unauthenticated packet-capture download at `/download/0` exposing plaintext FTP credentials.
- `2` — `python3.8` carries `cap_setuid` → local privesc to root.

## Environment

The ARTEX container cannot resolve HTB vhost names; `/etc/hosts` **is** writable
inside the container. Prefer `--noproxy '*' --resolve <name>:<port>:<ip>`.
Verified: `curl -sk --noproxy '*' --resolve cap.htb:80:10.129.137.86 http://cap.htb/` -> 200.

## Log


## Capture assertions

Run `20261126T024001Z-8b01caa6`, blobs referencing this box's IP: **67**.
`collector_dropped_total = 0`, `collector_write_errors_total = 0`.
`traffic_capture = true`, `llm base_url = http://llm-logger:4000/v1`
(asserted at the start and end of the whole run — see notes/report.md for the
gap: this was not snapshotted per box).
