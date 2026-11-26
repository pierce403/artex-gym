# Keeper (HTB machine 556)

- **Difficulty** 29 (Easy), Linux
- **Started** 2026-11-26T06:57:46Z, IP `10.129.229.41`
- **ArTeX task** 9
- **User flag** `ab0569bb0c6aa84554749e28ff61efdc` — accepted
- **Root flag** `9124edd912212370a7cead5eb3833402` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 145 blobs referencing `10.129.229.41`
- ArTeX task `9`; collector `dropped=0` for the run
- Findings:

  - **high** — Request Tracker 4.4.4 at http://tickets.keeper.htb/rt/ accepts the default administrator credentials root:password, giving full admin access to the ti
  - **critical** — A world-readable KeePass crash dump in user lnorgaard's home leaks the master password (CVE-2023-32784), which opens passcodes.kdbx containing root's
