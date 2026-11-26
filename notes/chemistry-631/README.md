# Chemistry (HTB machine 631)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T13:12:31Z, IP `10.129.231.170`
- **ArTeX task** 38
- **User flag** `2a095106ff5a03c5b6e8971d084eb1db` — accepted
- **Root flag** `41a136e86475438f71d635a70167569e` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 109 blobs referencing `10.129.231.170`
- ArTeX task `38`; collector `dropped=0` for the run
- Findings:

  - **critical** — Authenticated users of the Flask CIF analyzer can upload a crafted .cif whose _space_group_magn.transform_BNS_Pp_abc value is eval()'d by pymatgen's J
  - **critical** — The root-owned monitoring app /opt/monitoring_site/app.py (aiohttp 3.9.1) on 127.0.0.1:8080 serves /assets with follow_symlinks and is vulnerable to C
