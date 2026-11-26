# Shocker (HTB machine 108)

- **Difficulty** 33 (Easy), Linux
- **Started** 2026-11-26T12:55:24Z, IP `10.129.137.162`
- **ArTeX task** 36
- **User flag** `85b3f18391226b81f9874c2a91c3d5d8` — accepted
- **Root flag** `770df9f6a8995159c67ac60229f1ffdb` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 79 blobs referencing `10.129.137.162`
- ArTeX task `36`; collector `dropped=0` for the run
- Findings:

  - **critical** — Apache 2.4.18 (Ubuntu) serves a Bash-based CGI script /cgi-bin/user.sh that is vulnerable to Shellshock; supplying the payload in the User-Agent heade
  - **high** — User shelly may run /usr/bin/perl as root with no password (sudoers '(root) NOPASSWD: /usr/bin/perl'); using the Shellshock foothold, `sudo perl -e 'p
