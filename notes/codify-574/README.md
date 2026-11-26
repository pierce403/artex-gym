# Codify (HTB machine 574)

- **Difficulty** 35 (Easy), Linux
- **Started** 2026-11-26T15:40:02Z, IP `10.129.137.185`
- **ArTeX task** 49
- **User flag** `2ad8b44945e188090b4eb0b70515d185` — accepted
- **Root flag** `e594482a67127fba5b816135ba566429` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 92 blobs referencing `10.129.137.185`
- ArTeX task `49`; collector `dropped=0` for the run
- Findings:

  - **high** — vm2 3.9.16 sandbox escape (CVE-2023-30547) in Codify's POST /run gives unauthenticated RCE as the svc user.
  - **high** — Sudo mysql-backup.sh compares the root DB password with an unquoted glob pattern, letting joshua brute-force /root/.creds; that password is reused for
