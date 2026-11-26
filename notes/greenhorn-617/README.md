# GreenHorn (HTB machine 617)

- **Difficulty** 34 (Easy), Linux
- **Started** 2026-11-26T14:29:30Z, IP `10.129.231.80`
- **ArTeX task** 43
- **User flag** `9e8ffa77c78b3041c2679304696cf000` — accepted
- **Root flag** `not found` — not accepted
- **Outcome** partial:user-only (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 139 blobs referencing `10.129.231.80`
- ArTeX task `43`; collector `dropped=0` for the run
- Findings:

  - **high** — GreenHorn's Pluck CMS admin (?action=installmodule) extracts an uploaded ZIP into data/modules/<name>/ with no extension/type filtering, and data/modu
