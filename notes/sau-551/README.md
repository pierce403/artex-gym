# Sau (HTB machine 551)

- **Difficulty** 30 (Easy), Linux
- **Started** 2026-11-26T08:07:45Z, IP `10.129.229.26`
- **ArTeX task** 15
- **User flag** `edffc53802bf3a26c4abd3c70bbbc1cc` — accepted
- **Root flag** `9f36662a3f93ea803e567e71c84fa276` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 277 blobs referencing `10.129.229.26`
- ArTeX task `15`; collector `dropped=0` for the run
- Findings:

  - **high** — Request Baskets on 10.129.229.26:55555 proxies attacker-controlled requests to arbitrary URLs (forward_url + expand_path), enabling SSRF into services
  - **critical** — Maltrail 0.53's /login handler interpolates the username into a shell command (logger), giving unauthenticated RCE as uid 1001 (puma); reached via the
  - **high** — User puma may run `/usr/bin/systemctl status trail.service` as root without a password; the less pager's `!command` escape yields root command executi
