# Perfection (HTB machine 590)

- **Difficulty** 35 (Easy), Linux
- **Started** 2026-11-26T16:55:02Z, IP `10.129.229.121`
- **ArTeX task** 53
- **User flag** `4436efc42ea66ff324883a14b62c9722` — accepted
- **Root flag** `51a31971bbb592a11c98edbed334ccf9` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 155 blobs referencing `10.129.229.121`
- ArTeX task `53`; collector `dropped=0` for the run
- Findings:

  - **high** — The POST /weighted-grade-calc handler concatenates user-controlled category1..5 values into an ERB template (ERB.new(...).result). The validation /^[a
  - **high** — /home/susan/Migration/pupilpath_credentials.db is readable by the low-privilege web user susan and stores unsalted SHA-256 password hashes. susan's ha
