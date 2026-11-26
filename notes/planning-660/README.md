# Planning (HTB machine 660)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T15:06:45Z, IP `10.129.237.241`
- **ArTeX task** 47
- **User flag** `5ef523471da1129e7a675e80527fcf03` — accepted
- **Root flag** `fbe61199ad5b4fb0298cf041a73e21ad` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 154 blobs referencing `10.129.237.241`
- ArTeX task `47`; collector `dropped=0` for the run
- Findings:

  - **critical** — World-readable /opt/crontabs/crontab.db on the Planning host leaks the password of the root-run Crontab UI (127.0.0.1:8000); authenticated job creatio
  - **medium** — The Grafana container's GF_SECURITY_ADMIN_PASSWORD (RioTecRANDEntANT!) is reused as the host SSH password for user enzo, giving a shell and the user f
  - **critical** — Grafana 11.0.0 on grafana.planning.htb: the experimental SQL Expressions endpoint (/api/ds/query?ds_type=__expr__&expression=true) passes user-control
