# Bashed (HTB machine 118)

- **Difficulty** 30 (Easy), Linux
- **Started** 2026-11-26T07:13:57Z, IP `10.129.137.119`
- **ArTeX task** 11
- **User flag** `900ddb3e93deb8abb7746f9e02dcb4ca` — accepted
- **Root flag** `9c1568c9f0cde356e3646c60f38a7dca` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 124 blobs referencing `10.129.137.119`
- ArTeX task `11`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated phpbash web shell at http://10.129.137.119/dev/phpbash.php executes arbitrary OS commands as www-data.
  - **critical** — Local privesc from www-data to root: www-data can sudo to scriptmanager, scriptmanager owns the /scripts directory, and a root cron executes /scripts/
