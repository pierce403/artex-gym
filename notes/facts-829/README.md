# Facts (HTB machine 829)

- **Difficulty** 33 (Easy), Linux
- **Started** 2026-11-26T12:04:39Z, IP `10.129.244.96`
- **ArTeX task** 33
- **User flag** `58d1a1e0c987d8724c194229c43462c4` — accepted
- **Root flag** `08610a98584997861723ae044b9599b0` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 199 blobs referencing `10.129.244.96`
- ArTeX task `33`; collector `dropped=0` for the run
- Findings:

  - **high** — CVE-2024-46987: authenticated path traversal in Camaleon CMS /admin/media/download_private_file?file= allows arbitrary file read; with a self-register
  - **high** — trivia may run "(ALL) NOPASSWD: /usr/bin/facter"; a custom fact loaded via --custom-dir executes Ruby, giving root and the root flag.
