# Busqueda (HTB machine 537)

- **Difficulty** 33 (Easy), Linux
- **Started** 2026-11-26T11:26:49Z, IP `10.129.228.217`
- **ArTeX task** 30
- **User flag** `a493fef2a3ff1b2658da2e4752997f34` — accepted
- **Root flag** `ca61e833d684b5cd90f4e53f86d43216` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 122 blobs referencing `10.129.228.217`
- ArTeX task `30`; collector `dropped=0` for the run
- Findings:

  - **critical** — Searchor 2.4.0 eval injection in the Searcher Flask app's /search endpoint (query parameter) allows unauthenticated remote command execution as user s
  - **critical** — User svc can run `sudo /usr/bin/python3 /opt/scripts/system-checkup.py full-checkup` (password = leaked Gitea/Git credential jh1usoih2bkjaspwe92), and
