# Devel (HTB machine 3)

- **Difficulty** 34 (Easy), Windows
- **Started** 2026-11-26T13:42:49Z, IP `10.129.137.168`
- **ArTeX task** 40
- **User flag** `1f316a878b7cb320dfce9b9ebe6c58e6` — accepted
- **Root flag** `1dc7482a0c84138ba6e44e63df395ea9` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 125 blobs referencing `10.129.137.168`
- ArTeX task `40`; collector `dropped=0` for the run
- Findings:

  - **critical** — The Microsoft FTP service on 10.129.137.168 allows anonymous login with write permission to the IIS document root C:\inetpub\wwwroot, so any unauthent
  - **high** — The target runs Windows 7 Enterprise 6.1.7600 (x86 RTM) without the afd.sys fix; running the MS11-046 (CVE-2011-1249) x86 exploit from the webshell es
