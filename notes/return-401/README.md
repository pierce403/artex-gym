# Return (HTB machine 401)

- **Difficulty** 30 (Easy), Windows
- **Started** 2026-11-26T07:58:45Z, IP `10.129.95.241`
- **ArTeX task** 14
- **User flag** `b810d57c2d3c9c317a2b5902cde2300d` — accepted
- **Root flag** `baa359b1c38eea51af5018393c9bf38c` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 160 blobs referencing `10.129.95.241`
- ArTeX task `14`; collector `dropped=0` for the run
- Findings:

  - **high** — Domain user svc-printer (member of Server Operators) authenticates over SMB and, using the SMB2 create option FILE_OPEN_FOR_BACKUP_INTENT (0x2000), op
