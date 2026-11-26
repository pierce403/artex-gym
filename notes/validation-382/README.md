# Validation (HTB machine 382)

- **Difficulty** 33 (Easy), Linux
- **Started** 2026-11-26T13:02:28Z, IP `10.129.95.235`
- **ArTeX task** 37
- **User flag** `dcfa10abf889c545f5b28f14a26e9c58` — accepted
- **Root flag** `4b9b9688a62bd14f70dfea91b6c58f8c` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 96 blobs referencing `10.129.95.235`
- ArTeX task `37`; collector `dropped=0` for the run
- Findings:

  - **critical** — The POST / registration form stores the 'country' value and /account.php later concatenates it into a SELECT, giving second-order UNION SQL injection
  - **high** — The MySQL/app password uhc-9qual-global-pw found in /var/www/html/config.php is also the system root account password, so any web-shell foothold (www-
