# Cicada (HTB machine 627)

- **Difficulty** 32 (Easy), Windows
- **Started** 2026-11-26T09:45:32Z, IP `10.129.231.149`
- **ArTeX task** 22
- **User flag** `6644a6e0760768a0ac29cb3eb858c777` — accepted
- **Root flag** `2b993c1a89d823e4d3a1a11f1e3df8fc` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 141 blobs referencing `10.129.231.149`
- ArTeX task `22`; collector `dropped=0` for the run
- Findings:

  - **high** — Unauthenticated guest SMB access to \\\\10.129.231.149\\HR exposes 'Notice from HR.txt' containing the domain default password Cicada$M6Corpb*@Lp#nZp!
  - **medium** — The AD user object david.orelious has description 'Just in case I forget my password is aRt$Lp#7t*VQ!3', which any authenticated domain user can read
  - **medium** — The DEV share (readable by david.orelious) contains Backup_script.ps1 with hardcoded emily.oscars credentials (Q!3@Lp#M6b*7t*Vt), valid for SMB; emily
  - **critical** — emily.oscars is a member of Backup Operators; using an SMB2/3 create with CreateOptions FILE_OPEN_FOR_BACKUP_INTENT over C$, she reads the ACL-protect
