# Legacy (HTB machine 2)

- **Difficulty** 23 (Easy), Windows
- **Started** 2026-11-26T06:19:42Z, IP `10.129.137.108`
- **ArTeX task** 6
- **User flag** `e69af0e4f443de7e36876fda4ec7644f` — accepted
- **Root flag** `993442d258b0e0ec917cae9e695d5713` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 209 blobs referencing `10.129.137.108`
- ArTeX task `6`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated anonymous SMB access to \\10.129.137.108\pipe\spoolss allowed the MS17-010 EternalChampion exploit (CVE-2017-0143 family) to corrupt t
