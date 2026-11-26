# Grandpa (HTB machine 13)

- **Difficulty** 33 (Easy), Windows
- **Started** 2026-11-26T12:21:27Z, IP `10.129.95.233`
- **ArTeX task** 34
- **User flag** `not found` — not accepted
- **Root flag** `not found` — not accepted
- **Outcome** timeout (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 193 blobs referencing `10.129.95.233`
- ArTeX task `34`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated remote code execution on 10.129.95.233 (Microsoft-IIS/6.0, WebDAV) via CVE-2017-7269: a PROPFIND with a crafted 'If:' header + alphanu
