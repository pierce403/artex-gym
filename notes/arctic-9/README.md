# Arctic (HTB machine 9)

- **Difficulty** 36 (Easy), Windows
- **Started** 2026-11-26T18:14:40Z, IP `10.129.137.209`
- **ArTeX task** 58
- **User flag** `b2842a29e4eb22ff79cc3e234508d591` — accepted
- **Root flag** `f0fc0317d7ba2a8d0bc0f5e41387467a` — accepted
- **Outcome** solved (timeout after 20m)

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 118 blobs referencing `10.129.137.209`
- ArTeX task `58`; collector `dropped=0` for the run
- Findings:

  - **high** — The locale parameter of /CFIDE/administrator/enter.cfm is used in a file path without sanitisation; a null-byte-terminated traversal payload makes the
  - **medium** — The ColdFusion 8 administrator account uses the weak password "happyday" (its SHA1 2F635F6D20E3FDE0C53075A84B68FB07DCEC9B03 was recovered from passwor
  - **medium** — The bundled FCKeditor connector upload.cfm accepts unauthenticated multipart uploads and writes them into the web-accessible /userfiles/file/ director
  - **critical** — With admin console access, a scheduled "HTTPRequest" task can fetch a target-local URL and publish the response body to an arbitrary file path, includ
  - **high** — The ColdFusion service account arctic\tolis has SeImpersonatePrivilege enabled; uploading JuicyPotato.exe and abusing the BITS COM CLSID executes cmd.
