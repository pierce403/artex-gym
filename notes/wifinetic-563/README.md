# Wifinetic (HTB machine 563)

- **Difficulty** 30 (Easy), Linux
- **Started** 2026-11-26T08:29:02Z, IP `10.129.229.90`
- **ArTeX task** 16
- **User flag** `1cfc731462d51cf9a982124ba7d2b53d` — accepted
- **Root flag** `18fa9ea4a3fb73040d587beaba005b34` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 117 blobs referencing `10.129.229.90`
- ArTeX task `16`; collector `dropped=0` for the run
- Findings:

  - **high** — vsftpd allows anonymous login and serves backup-OpenWrt-2023-07-26.tar, which contains etc/config/wireless with the plaintext WiFi PSK 'VeRyUniUqWiFIP
  - **high** — The OpenWrt AP (BSSID 02:00:00:00:00:00) accepts the default WPS PIN 12345670; reaver on the pre-created mon0 monitor interface recovers the live WPA
