# Down (HTB machine 666)

- **Difficulty** 33 (Easy), Linux
- **Started** 2026-11-26T11:47:20Z, IP `10.129.234.87`
- **ArTeX task** 32
- **User flag** `d4bc94b386ef7c8113698a8c4951cacd` — accepted
- **Root flag** `87bb9869a311b8abb5fb4d3c7248fdcb` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 161 blobs referencing `10.129.234.87`
- ArTeX task `32`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated OS command execution as www-data on HTB Down (10.129.234.87:80): the expertmode=tcp `port` POST parameter is intval()-validated but th
  - **high** — HTB Down local privilege escalation: /home/aleks/.local/share/pswm/pswm is world-readable and its pswm master password is the dictionary word 'flower'
  - **high** — Aleks's pswm password vault (world-readable /home/aleks/.local/share/pswm/pswm, mode 664) is protected only by the weak master password 'flower'; decr
