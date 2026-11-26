# Nibbles (HTB machine 121)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T14:56:34Z, IP `10.129.137.175`
- **ArTeX task** 45
- **User flag** `a68c482dad932452941aad7e04a6c32c` — accepted
- **Root flag** `5410ec355b6e2d79d0dcc2663a6e15cb` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 47 blobs referencing `10.129.137.175`
- ArTeX task `45`; collector `dropped=0` for the run
- Findings:

  - **critical** — Nibbleblog 4.0.3 admin panel (default creds admin:nibbles) lets an authenticated user upload a .php file through the 'My Image' plugin; the file is st
  - **high** — User nibbler may run /home/nibbler/personal/stuff/monitor.sh as root with NOPASSWD, but the script path is inside nibbler's own home; nibbler created
