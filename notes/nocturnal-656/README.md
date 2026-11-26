# Nocturnal (HTB machine 656)

- **Difficulty** 36 (Easy), Linux
- **Started** 2026-11-26T19:11:24Z, IP `10.129.232.23`
- **ArTeX task** 62
- **User flag** `a5c3f4f3805f2edf5d72951538984273` — accepted
- **Root flag** `5ee4762001859d0e32d3ddce924fb688` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 102 blobs referencing `10.129.232.23`
- ArTeX task `62`; collector `dropped=0` for the run
- Findings:

  - **high** — view.php takes an arbitrary `username` and returns that user's uploaded files, allowing any registered user to read amanda's privacy.odt which disclos
  - **critical** — Internal ISPConfig 3.2.2 on 127.0.0.1:8080 (reachable via SSH tunnel as tobias) is vulnerable to CVE-2023-46818: after login as admin (admin/slowmotio
