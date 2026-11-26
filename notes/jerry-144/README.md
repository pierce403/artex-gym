# Jerry (HTB machine 144)

- **Difficulty** 27 (Easy), Windows
- **Started** 2026-11-26T06:50:48Z, IP `10.129.137.117`
- **ArTeX task** 8
- **User flag** `7004dbcef0f854e0fb401875f26ebd00` — accepted
- **Root flag** `04a8b36e1545a455393d067e772fe90e` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 140 blobs referencing `10.129.137.117`
- ArTeX task `8`; collector `dropped=0` for the run
- Findings:

  - **critical** — Apache Tomcat 7.0.88 Manager on 10.129.137.117:8080 is protected only by the default credentials tomcat:s3cret; authenticating to /manager/html and up
