# UnderPass (HTB machine 641)

- **Difficulty** 32 (Easy), Linux
- **Started** 2026-11-26T10:54:43Z, IP `10.129.231.213`
- **ArTeX task** 28
- **User flag** `a6fed770e3751a75e485f12bc053eb13` — accepted
- **Root flag** `657a4bb12857ecc5befea583fc07e4ff` — accepted
- **Outcome** solved (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 146 blobs referencing `10.129.231.213`
- ArTeX task `28`; collector `dropped=0` for the run
- Findings:

  - **high** — Local user svcMosh can execute arbitrary commands as root via `sudo NOPASSWD /usr/bin/mosh-server`; a root mosh-server was started and connected to wi
  - **high** — daloRADIUS at /daloradius/ logs in with default administrator:radius and discloses RADIUS user svcMosh's MD5-Password 412DD4759978ACFCC81DEAB01B382403
