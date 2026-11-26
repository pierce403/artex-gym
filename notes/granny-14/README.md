# Granny (HTB machine 14)

- **Difficulty** 32 (Easy), Windows
- **Started** 2026-11-26T10:19:51Z, IP `10.129.95.234`
- **ArTeX task** 25
- **User flag** `700c5dc163014e22b3e408f8703f67d1` — accepted
- **Root flag** `aa4beed1c0584445ab463a6747bd06e9` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 85 blobs referencing `10.129.95.234`
- ArTeX task `25`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated IIS 6.0 WebDAV accepts PUT of arbitrary files and MOVE to .aspx, giving remote code execution as NT AUTHORITY\\NETWORK SERVICE on 10.1
  - **high** — Churrasco token-kidnapping on Windows Server 2003 escalates the IIS 6 NETWORK SERVICE worker to NT AUTHORITY\\SYSTEM, allowing root.txt to be read.
