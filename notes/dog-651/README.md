# Dog (HTB machine 651)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T13:55:58Z, IP `10.129.231.223`
- **ArTeX task** 41
- **User flag** `48ba719e99448085ae05c56f172fa291` — accepted
- **Root flag** `a356067c7ec56eb22b2888133537bea4` — accepted
- **Outcome** solved (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 97 blobs referencing `10.129.231.223`
- ArTeX task `41`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated exposure of the Backdrop CMS .git repository (including Apache directory listing of .git/objects/) leaks an untracked settings.php blo
  - **high** — Authenticated Backdrop CMS administrator can upload an arbitrary module archive via /?q=admin/installer/manual; enabling it executes attacker PHP on t
  - **high** — User johncusack has NOPASSWD sudo rights on /usr/local/bin/bee, a PHP CLI exposing an 'eval' command; 'sudo bee eval' executes arbitrary PHP as root (
