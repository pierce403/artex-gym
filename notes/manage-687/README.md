# Manage (HTB machine 687)

- **Difficulty** 33 (Easy), Linux
- **Started** 2026-11-26T12:42:38Z, IP `10.129.234.57`
- **ArTeX task** 35
- **User flag** `a86d44c7243b65a9171cf7da3e0bc279` — accepted
- **Root flag** `b3645b7e6db6d5276ad33f0c75b8dc34` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 150 blobs referencing `10.129.234.57`
- ArTeX task `35`; collector `dropped=0` for the run
- Findings:

  - **critical** — The Java RMI/JMX endpoint on tcp/2222 accepts unauthenticated connections; beanshooter abused it (StandardMBean/TemplateImpl payload) to execute arbit
  - **high** — useradmin's sudoers rule allows '/usr/sbin/adduser' with a single alphanumeric argument; creating a local user named 'admin' grants that account full
  - **medium** — /home/useradmin/backups/backup.tar.gz is world-readable (rw-rw-r-- in a 775 dir); it contains useradmin's SSH ed25519 private key and the .google_auth
