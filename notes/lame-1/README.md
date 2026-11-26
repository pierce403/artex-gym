# Lame (HTB machine 1)

- **Difficulty** 25 (Easy), Linux
- **Started** 2026-11-26T06:37:14Z, IP `10.129.137.112`
- **ArTeX task** 7
- **User flag** `1edc5326e4577256056fccb630cc8880` — accepted
- **Root flag** `ead743804be7f933182fc93a5f6efd96` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 132 blobs referencing `10.129.137.112`
- ArTeX task `7`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated root command execution on Samba 3.0.20 (HTB Lame) via username map script injection (CVE-2007-2447); arbitrary commands ran as root an
