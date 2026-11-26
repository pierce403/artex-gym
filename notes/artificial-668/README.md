# Artificial (HTB machine 668)

- **Difficulty** 36 (Easy), Linux
- **Started** 2026-11-26T18:36:07Z, IP `10.129.232.51`
- **ArTeX task** 59
- **User flag** `not found` — not accepted
- **Root flag** `not found` — not accepted
- **Outcome** timeout (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 185 blobs referencing `10.129.232.51`
- ArTeX task `59`; collector `dropped=0` for the run
- Findings:

  - **high** — Unauthenticated-model RCE via malicious Keras .h5 Lambda layer: uploading a crafted model to artificial.htb and hitting /run_model/<uuid> executes arb
