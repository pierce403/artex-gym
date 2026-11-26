# Explore (HTB machine 356)

- **Difficulty** 35 (Easy), Android
- **Started** 2026-11-26T15:51:10Z, IP `10.129.238.59`
- **ArTeX task** 50
- **User flag** `f32017174c7c7e8f50c6da52891ae250` — accepted
- **Root flag** `not found` — not accepted
- **Outcome** partial:user-only (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 111 blobs referencing `10.129.238.59`
- ArTeX task `50`; collector `dropped=0` for the run
- Findings:

  - **high** — The ES File Explorer HTTP server on 10.129.238.59:59777 accepts unauthenticated GET requests with arbitrary absolute filesystem paths and returns the
