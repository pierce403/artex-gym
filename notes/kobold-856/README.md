# Kobold (HTB machine 856)

- **Difficulty** 35 (Easy), Linux
- **Started** 2026-11-26T16:33:43Z, IP `10.129.245.50`
- **ArTeX task** 52
- **User flag** `59e9ea24ad1ca195159e42cf654a01ac` — accepted
- **Root flag** `8c4512360361de0f0b2bc39b2a9259a1` — accepted
- **Outcome** solved (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 223 blobs referencing `10.129.245.50`
- ArTeX task `52`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated RCE in MCPJam Inspector (CVE-2026-23744) on https://mcp.kobold.htb: POST /api/mcp/connect spawns an attacker-supplied stdio command; e
  - **medium** — Arcane v1.13.0 on 10.129.245.50:3552 exposes GET /api/templates/fetch?url= with no authentication and follows arbitrary http(s) URLs from the server,
