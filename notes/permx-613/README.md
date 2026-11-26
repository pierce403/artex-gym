# PermX (HTB machine 613)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T15:00:33Z, IP `10.129.137.176`
- **ArTeX task** 46
- **User flag** `869fed918c34af905ab874ae0f96dec4` — accepted
- **Root flag** `fafdfc8b57c5b05d53568ac1bf6f4277` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 75 blobs referencing `10.129.137.176`
- ArTeX task `46`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated file upload in Chamilo bigUpload.php on lms.permx.htb leads to remote code execution as www-data
  - **high** — User mtz can run /opt/acl.sh via NOPASSWD sudo; symlink to /etc/passwd grants mtz rwx on the file, allowing a uid-0 account and root compromise
  - **high** — Chamilo configuration.php exposes DB password that is reused as system user mtz's password, giving SSH access and user.txt
