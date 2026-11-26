# Conversor (HTB machine 787)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T13:24:43Z, IP `10.129.137.166`
- **ArTeX task** 39
- **User flag** `23678b2411b4fc70ca3e419aa68f6518` — accepted
- **Root flag** `eecd71fccc7e9da5872b2aca518ec6fa` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 126 blobs referencing `10.129.137.166`
- ArTeX task `39`; collector `dropped=0` for the run
- Findings:

  - **critical** — User fismathack can run `/usr/sbin/needrestart` (3.7) as root without a password; needrestart imports a Python sitecustomize.py from the PYTHONPATH of
  - **high** — POST /convert saves uploads with the raw client-supplied filename via os.path.join(UPLOAD_FOLDER, filename); an absolute filename lets an authenticate
