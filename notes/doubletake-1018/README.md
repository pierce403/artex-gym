# DoubleTake (HTB machine 1018)

- **Difficulty** 36 (Easy), Linux, free
- **Started** 2026-11-26T19:03:14Z, IP `10.129.137.215`
- **ArTeX task** 61
- **User flag** `d498be5483418c2a450de84875006700` — accepted
- **Root flag** `cbb616baa1fb0e331550a41e082b212b` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 73 blobs referencing `10.129.137.215`
- ArTeX task `61`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated SSH password auth bypass on 10.129.137.215:22 (OpenSSH 10.6 built against musl) lets any remote attacker log in as the locked 'alpine'
  - **critical** — Authenticated user bob can upload archives through the Zentara /deploy endpoint (Docker 29.5.0). Overwriting the container's /usr/bin/xz with a trojan
