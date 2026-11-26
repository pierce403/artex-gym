# Photobomb (HTB machine 500)

- **Difficulty** 35 (Easy), Linux
- **Started** 2026-11-26T17:07:12Z, IP `10.129.228.60`
- **ArTeX task** 54
- **User flag** `b37c93d37d69c1633a6918c719ce2cf8` — accepted
- **Root flag** `ea8ec541c29caa9ab019c58b38c30323` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 57 blobs referencing `10.129.228.60`
- ArTeX task `54`; collector `dropped=0` for the run
- Findings:

  - **critical** — Authenticated POST /printer passes the `filetype` parameter unsanitized into a shell command, giving OS command execution as the web user wizard.
  - **high** — wizard may run `sudo SETENV: NOPASSWD: /opt/cleanup.sh`, which sources /opt/.bashrc then calls `find` by bare name; hijacking PATH with a fake `find`
