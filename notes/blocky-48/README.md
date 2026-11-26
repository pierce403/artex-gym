# Blocky (HTB machine 48)

- **Difficulty** 31 (Easy), Linux
- **Started** 2026-11-26T08:40:00Z, IP `10.129.137.127`
- **ArTeX task** 17
- **User flag** `f2bdb409303e8bf94cea6bc8434048a3` — accepted
- **Root flag** `b6122e6a6798339e0a8876a21ead000d` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 102 blobs referencing `10.129.137.127`
- ArTeX task `17`; collector `dropped=0` for the run
- Findings:

  - **high** — Unauthenticated users can download /plugins/files/BlockyCore.jar, whose BlockyCore.class contains hardcoded MySQL/root credentials root:8YsqfCTnvxAUed
  - **high** — User notch can run '(ALL : ALL) ALL' via sudo with the same password disclosed in BlockyCore.jar, allowing direct escalation to root and read of /root
