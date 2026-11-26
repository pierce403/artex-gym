# Editor (HTB machine 684)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T14:17:21Z, IP `10.129.137.171`
- **ArTeX task** 42
- **User flag** `0082a8daf624e50a857fc1fc8e8873c2` — accepted
- **Root flag** `392e5f2d5a95aa1ec8dbe66d16305f9d` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 118 blobs referencing `10.129.137.171`
- ArTeX task `42`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated GET to /xwiki/bin/get/Main/SolrSearch?media=rss with a crafted text parameter breaks out of the Velocity context into a Groovy macro (
  - **high** — The setuid-root, group-netdata helper /opt/netdata/usr/libexec/netdata/plugins.d/ndsudo resolves allowed executables (e.g. nvme) via the caller's PATH
