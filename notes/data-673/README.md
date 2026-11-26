# Data (HTB machine 673)

- **Difficulty** 33 (Easy), Linux
- **Started** 2026-11-26T11:38:32Z, IP `10.129.234.47`
- **ArTeX task** 31
- **User flag** `25d8890a0c207557ff14bcf6a63ba0cb` — accepted
- **Root flag** `9432137681939deaa3baa5b057648072` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 63 blobs referencing `10.129.234.47`
- ArTeX task `31`; collector `dropped=0` for the run
- Findings:

  - **high** — Unauthenticated path traversal on Grafana 8.0.0 at http://10.129.234.47:3000/public/plugins/<plugin>/../../../../../../../../<path> reads arbitrary ho
  - **high** — User boris has '(root) NOPASSWD: /snap/bin/docker exec *'. Exec'ing as root into the running 'grafana' container (privileged, CapEff=0x3fffffffff) exp
