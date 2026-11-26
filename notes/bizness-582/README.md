# Bizness (HTB machine 582)

- **Difficulty** 36 (Easy), Linux
- **Started** 2026-11-26T18:57:45Z, IP `10.129.137.213`
- **ArTeX task** 60
- **User flag** `f1d336f3d9eb779def691a6011fd1f43` — accepted
- **Root flag** `be0036bd7a7f043764deaf82f1ed9b7f` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 57 blobs referencing `10.129.137.213`
- ArTeX task `60`; collector `dropped=0` for the run
- Findings:

  - **critical** — Apache OFBiz 18.12 at https://bizness.htb is vulnerable to CVE-2023-51467: an unauthenticated POST to /webtools/control/ProgramExport with empty USERN
  - **high** — The OFBiz admin password hash is stored in the world-readable Derby DB as a single-iteration salted SHA1 ($SHA$d$uP0_QaVBpDWFeo8-dRzDqRwXQ2I), cracks
