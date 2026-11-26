# BoardLight (HTB machine 603)

- **Difficulty** 32 (Easy), Linux
- **Started** 2026-11-26T09:39:04Z, IP `10.129.231.37`
- **ArTeX task** 21
- **User flag** `4ee88e423da40aff49b70d4ab9b606e0` — accepted
- **Root flag** `1dce3066b4d5186d79c7af5626b3d7c6` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 94 blobs referencing `10.129.231.37`
- ArTeX task `21`; collector `dropped=0` for the run
- Findings:

  - **critical** — Dolibarr 17.0.0 on crm.board.htb lets an authenticated admin execute arbitrary OS commands via the Website module page editor (CVE-2023-30253): inject
  - **high** — Local privilege escalation to root on BoardLight via SUID /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_sys (Enlightenment 0.23.1-4, CVE
  - **medium** — The exposed Dolibarr 17.0.0 instance at crm.board.htb accepts the default credentials admin:admin, giving full administrative access (the precondition
