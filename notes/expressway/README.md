# Expressway (HTB machine 736)

- **Difficulty** 31 (Easy), Linux, `free: false`, retired, released 2025-09-20
- **Spawned** 2026-11-26, IP `10.129.137.88`, expires 2026-11-27 02:54:34
- **User flag** `a126d80d35481a1a8a84ea88f28af199` — **accepted by HTB**
- **Root flag** `780a5799e4c3c9366685769900f12891` — **accepted by HTB**
- **Outcome** SOLVED (`machine_pwned: true`)
- **ArTeX task** 4 (`HTB Expressway (10.129.137.91)`), `done`, 3/3 goals, 2 findings
- **Note** the box was first solved by hand (task-less); it was then respawned
  and given to ArTeX as task 4, which solved it independently.

## Attack path (complete)

1. TCP was SSH-only; UDP 500/4500 = IPsec/IKE.
2. `ike-scan -M -A` aggressive mode → PSK hash, identity `ike@expressway.htb`.
3. `psk-crack -d rockyou` → PSK **`freakingrockstarontheroad`**.
4. SSH as `ike` with that PSK as the password → `user.txt`.
5. `/usr/local/bin/sudo` is **1.9.17** (a custom build, different md5 from
   `/usr/bin/sudo`) → **CVE-2025-32463** (chroot NSS load race).
6. Exploit: a no-libc shared object with `_nss_pwn_*` symbols and a
   `constructor`, `nsswitch.conf` pointing `passwd:`/`group:` at it, then
   `/usr/local/bin/sudo -R <dir> <static-exit-binary>`. The constructor runs as
   root inside the chroot; it double-chroots out (`chroot("esc")`, chdir `..`,
   `chroot(".")`) and reads `/root/root.txt`.
7. Result landed at `/tmp/escaped_root.txt` on the real host.

Exploit source and binaries: `.work/probes/` (`pwn5.c`, `libnss_pwn.so.2`, `t`,
`exp9.py`).

## Why there was no task the first time (corrected)

The first pass had no tools: `ike-scan`, `tshark`, `psk-crack` were **not
installed** at that moment, so the box was solved by hand. `hashcat` is still
absent, but `psk-crack` (ships with ike-scan) is enough for aggressive-mode
PSKs, so the gap was tooling, not protocol.

After `apt-get install ike-scan tshark tcpdump` the box was respawned
(`10.129.137.91`) and given to ArTeX as **task 4**, which reproduced the whole
path itself: IKE aggressive mode → `psk-crack` → SSH as `ike` → custom
`sudo 1.9.17` (CVE-2025-32463) → root. Task 4: `done`, 3/3 goals, 2 findings
(1 critical, 1 high).

Still true: the container has **no `CAP_NET_ADMIN`** and no `/dev/net/tun`, so
strongSwan cannot build an actual tunnel interface. That did not matter here —
the privesc is reachable over plain SSH — but it would for a box needing real
IPsec transport. Fix candidate: `cap_add: NET_ADMIN` + `/dev/net/tun`.

## Recon (verified from the container, 2026-11-26)

TCP (full 65535, `-p- --open`): **only 22/tcp** — `SSH-2.0-OpenSSH_10.0p2 Debian-8`.
26k ports returned *filtered* (no-response), which reads like a firewall, not a
slow boot: a second scan after 60s gave the same single port.

UDP (top 20): **500/udp open** (`isakmp`), 4500/udp `open|filtered` (nat-t-ike).

### What that means

`isakmp` on 500 + NAT-T on 4500 is **IPsec/IKE**. The machine name "Expressway"
is Cisco's VPN concentractor line, so this is a VPN box, not a web app. There is
no HTTP surface to enumerate — chasing port 80 here is wasted effort.

## Attack surface to try, in order

1. **IKE aggressive mode + PSK hash capture, then crack offline.**
   `ike-scan` / `strongswan`'s `ipsec` / `nmap` `ike-version` script.
   Aggressive mode leaks the PSK hash; crack with hashcat mode 5400
   (`-m 5400 hash.txt wordlist`).
2. **Known Cisco Expressway / default-credential issues** once a PSK or login is
   obtained (it may expose an admin interface on the VPN side).
3. SSH on 22 is the entry point *after* credentials — reuse anything cracked.

## Notes

- `ssh` is **not installed** in the ARTEX container; use `ncat`/`bash /dev/tcp`
  for banner grabbing and Python paramiko if a full client is needed.
- Always `--noproxy '*'`; the container's outbound proxy cannot reach HTB.

## Progress: IKE aggressive mode cracked (2026-11-26)

```
$ ike-scan -M -A --pskcrack=/tmp/psk.txt 10.129.137.88
10.129.137.88  Aggressive Mode Handshake returned
  SA=(Enc=3DES Hash=SHA1 Group=2:modp1024 Auth=PSK)
  ID(Type=ID_USER_FQDN, Value=ike@expressway.htb)
  VID=09002689dfd6b712 (XAUTH)
  VID=afcad71368a1f1c96b8696fc77570100 (Dead Peer Detection)

$ psk-crack -d rockyou.txt /tmp/psk.txt
key "freakingrockstarontheroad" matches SHA1 hash 8318d604...
```

- **PSK: `freakingrockstarontheroad`**
- Peer identity: `ike@expressway.htb`
- XAUTH vendor ID present → after IKE, expect **XAUTH username/password**.

### Tools

`ike-scan`, `tshark`, `tcpdump` installed via apt in the container.
`psk-crack` ships with ike-scan. Wordlist at `/app/data/wordlists/rockyou.txt.gz`
(134M, plain text despite the name).
Handshake saved at `/tmp/psk.txt` (perishable — recapture with the ike-scan line above).

## Capture assertions

Run `20261126T024001Z-8b01caa6`, blobs referencing this box's IP: **90**.
`collector_dropped_total = 0`, `collector_write_errors_total = 0`.
`traffic_capture = true`, `llm base_url = http://llm-logger:4000/v1`
(asserted at the start and end of the whole run — see notes/report.md for the
gap: this was not snapshotted per box).
