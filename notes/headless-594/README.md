# Headless (HTB machine 594)

- **Difficulty** 32 (Easy), Linux
- **Started** 2026-11-26T10:25:50Z, IP `10.129.137.144`
- **ArTeX task** 26
- **User flag** `060eef1cf30dc4d042132e4658142c42` — accepted
- **Root flag** `bd86d11789236acae53f068c668635da` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 157 blobs referencing `10.129.137.144`
- ArTeX task `26`; collector `dropped=0` for the run
- Findings:

  - **high** — The is_admin cookie is signed with a static hardcoded itsdangerous key (b'PcBE2u6tBomJmDMwUbRzO18I07A', URLSafeSerializer defaults), so an unauthentic
  - **critical** — The /dashboard POST 'date' parameter is passed to a shell unsanitized (OS command injection) executing as dvir; combined with `sudo /usr/bin/syscheck`
