# Retro (HTB machine 671)

- **Difficulty** 31 (Easy), Windows
- **Started** 2026-11-26T08:43:18Z, IP `10.129.234.44`
- **ArTeX task** 18
- **User flag** `cbda362cff2099072c5e96c51712ff33` — accepted
- **Root flag** `40fce9c3f09024bcab29d377ee1ed071` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 161 blobs referencing `10.129.234.44`
- ArTeX task `18`; collector `dropped=0` for the run
- Findings:

  - **critical** — AD CS certificate template 'RetroClients' on retro-DC-CA is ESC1-vulnerable (enrollee supplies subject + Client Authentication, enrollable by Domain C
