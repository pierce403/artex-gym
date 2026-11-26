# CodePartTwo (HTB machine 692)

- **Difficulty** 32 (Easy), Linux
- **Started** 2026-11-26T09:55:47Z, IP `10.129.137.136`
- **ArTeX task** 23
- **User flag** `480d8fc02e5989ee6b8c5ed90fb2c8e9` — accepted
- **Root flag** `58e4929ad556a9e9954d86126bce7ff9` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 93 blobs referencing `10.129.137.136`
- ArTeX task `23`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated POST /run_code passes user JavaScript to js2py.eval_js (js2py==0.74 with disable_pyimport); CVE-2024-28397 payload walks Python object
  - **high** — User marco (password sweetangelbabylove, groups marco,backups) may run /usr/local/bin/npbackup-cli as ALL NOPASSWD; npbackup 3.0.1 config is fully use
