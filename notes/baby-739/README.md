# Baby (HTB machine 739)

- **Difficulty** 33 (Easy), Windows
- **Started** 2026-11-26T11:16:30Z, IP `10.129.234.71`
- **ArTeX task** 29
- **User flag** `fcef2c93e17ed4b3b7719e8de7783fe8` — accepted
- **Root flag** `161e1f54def8490c7e1cada7340a0e37` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 109 blobs referencing `10.129.234.71`
- ArTeX task `29`; collector `dropped=0` for the run
- Findings:

  - **medium** — Anonymous LDAP bind lets an unauthenticated attacker read user descriptions; the it user's description disclosed the initial password 'BabyStart123!',
  - **high** — Backup Operators membership lets Caroline.Robinson read any file over SMB using FILE_OPEN_FOR_BACKUP_INTENT, including Administrator's root.txt (machi
