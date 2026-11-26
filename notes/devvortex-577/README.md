# Devvortex (HTB machine 577)

- **Difficulty** 32 (Easy), Linux
- **Started** 2026-11-26T10:07:42Z, IP `10.129.229.146`
- **ArTeX task** 24
- **User flag** `b86eafd23917444a26ae400a0f7f9691` — accepted
- **Root flag** `95e20918b8b8b64a41eb3155092e4e06` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 150 blobs referencing `10.129.229.146`
- ArTeX task `24`; collector `dropped=0` for the run
- Findings:

  - **critical** — logan (uid 1000) may run `sudo /usr/bin/apport-cli` as any user; apport-cli 2.20.11 opens the crash report in a root pager with `!sh` available, yield
  - **critical** — dev.devvortex.htb Joomla exposes /api/index.php/v1/config/application?public=true to unauthenticated users, leaking DB/admin credentials (lewis:P4nthe
