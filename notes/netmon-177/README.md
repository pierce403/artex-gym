# Netmon (HTB machine 177)

- **Difficulty** 29 (Easy), Windows
- **Started** 2026-11-26T07:04:09Z, IP `10.129.230.176`
- **ArTeX task** 10
- **User flag** `4c8ae28f45934551c67a0516528c4be2` — accepted
- **Root flag** `06290f4dc9c5c128d55e66a2fc618341` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 168 blobs referencing `10.129.230.176`
- ArTeX task `10`; collector `dropped=0` for the run
- Findings:

  - **critical** — Authenticated PRTG Network Monitor 18.1.37 'Execute Program' notification parameter injection (CVE-2018-9276) executes arbitrary OS commands as NT AUT
  - **high** — Anonymous FTP on Netmon exposes the Windows C: drive, including the user flag and the PRTG configuration backup containing the prtgadmin DB password
