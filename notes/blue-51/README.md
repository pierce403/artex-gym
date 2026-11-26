# Blue (HTB machine 51)

- **Difficulty** 22 (Easy), Windows
- **Started** 2026-11-26T06:05:05Z, IP `10.129.137.105`
- **ArTeX task** 5
- **User flag** `7d37324ea2368ebb7c07e05199905876` — accepted
- **Root flag** `8bb3e0f52559463b88871f0abf7db831` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 171 blobs referencing `10.129.137.105`
- ArTeX task `5`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated (guest/empty-password) SMBv1 on 10.129.137.105:445 is vulnerable to MS17-010; exploiting it (sleepya/AutoBlue zzz_exploit matched-pair
