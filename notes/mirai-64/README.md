# Mirai (HTB machine 64)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T14:50:59Z, IP `10.129.137.174`
- **ArTeX task** 44
- **User flag** `ff837707441b257a20e32199d7c8838d` — accepted
- **Root flag** `3d3e483143ff12ec505d026fa13e020b` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 56 blobs referencing `10.129.137.174`
- ArTeX task `44`; collector `dropped=0` for the run
- Findings:

  - **high** — SSH on 10.129.137.174 accepts the Raspberry Pi default credential pi:raspberry, yielding an interactive shell as uid 1000(pi) and read access to /home
  - **high** — The pi account is granted `(ALL : ALL) NOPASSWD: ALL` via sudoers, so an attacker holding pi:raspberry escalates to root with `sudo id` / `sudo cat`,
