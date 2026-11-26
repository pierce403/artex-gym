# Reactor (HTB machine 900)

- **Difficulty** 32 (Easy), Linux
- **Started** 2026-11-26T10:45:29Z, IP `10.129.245.214`
- **ArTeX task** 27
- **User flag** `9d59521856987eb9a85f118f88a30c4f` — accepted
- **Root flag** `52deb39bc4b1c56565bcbb926792bdb1` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 105 blobs referencing `10.129.245.214`
- ArTeX task `27`; collector `dropped=0` for the run
- Findings:

  - **critical** — Unauthenticated remote command execution on http://10.129.245.214:3000/ via the React Flight deserialization flaw CVE-2025-55182: a POST with header '
  - **high** — The systemd unit /etc/systemd/system/uptime-monitor.service runs 'User=root /usr/bin/node --inspect=127.0.0.1:9229 /opt/uptime-monitor/worker.js'; fro
