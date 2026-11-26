# Optimum (HTB machine 6)

- **Difficulty** 30 (Easy), Windows
- **Started** 2026-11-26T07:39:47Z, IP `10.129.137.122`
- **ArTeX task** 13
- **User flag** `35af7177920b82ebfc28087b7b1d9b5e` — accepted
- **Root flag** `ca24e7d38919d80649bec78c1f9de4ff` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 243 blobs referencing `10.129.137.122`
- ArTeX task `13`; collector `dropped=0` for the run
- Findings:

  - **critical** — HttpFileServer 2.3 on 10.129.137.122:80 is vulnerable to CVE-2014-6287: the `search` parameter is parsed by the HFS template macro engine, allowing ar
  - **critical** — MS16-032 / CVE-2016-0099 (Secondary Logon handle leak) on 10.129.137.122 (Server 2012 R2, patch level 11/2014): from the low-priv HFS process account
