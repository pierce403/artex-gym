# Code (HTB machine 653)

- **Difficulty** 35 (Easy), Linux
- **Started** 2026-11-26T15:28:32Z, IP `10.129.231.240`
- **ArTeX task** 48
- **User flag** `c7bf35e43c8851cc0a5d9e4df8d59c54` — accepted
- **Root flag** `224d88a81c86a7d4fe8808de56d4073b` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 151 blobs referencing `10.129.231.240`
- ArTeX task `48`; collector `dropped=0` for the run
- Findings:

  - **critical** — Remote code execution in the Code web app: /run_code's substring keyword blacklist is trivially bypassed (string concatenation + globals()), giving ar
  - **high** — sudo-allowed /usr/bin/backy.sh (martin NOPASSWD) validates directories with a prefix check after a single non-recursive '../' strip, so '....//....//r
