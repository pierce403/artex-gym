# Antique (HTB machine 400)

- **Difficulty** 32 (Easy), Linux
- **Started** 2026-11-26T09:16:58Z, IP `10.129.137.131`
- **ArTeX task** 20
- **User flag** `4b01c855424540f44c8fb063fb88dfbc` — accepted
- **Root flag** `e1ff0c60da26f57194fee980c60e1cc3` — accepted
- **Outcome** solved (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 106 blobs referencing `10.129.137.131`
- ArTeX task `20`; collector `dropped=0` for the run
- Findings:

  - **high** — Local privilege escalation from user lp to root on HTB Antique via CVE-2021-4034 (PwnKit) in SUID /usr/bin/pkexec, yielding /root/root.txt.
  - **high** — SNMP community 'public' on 10.129.137.131:161/udp discloses the HP JetDirect admin password (OID 1.3.6.1.4.1.11.2.3.9.1.1.13.0 = P@ssw0rd@123!!123); l
