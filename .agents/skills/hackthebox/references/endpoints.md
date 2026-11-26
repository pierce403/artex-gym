# HTB Labs API v4 — endpoint record

Base: `https://labs.hackthebox.com/api/v4`

**Status of each row is evidence, not documentation.** Official HTB API docs are
not publicly reachable (checked 2026-11-26: `/api/v4/docs`, `/openapi.json`,
`api-documentation` repos all 404). So this file separates what was probed live
from what was inferred.

## Route existence — probed live 2026-11-26 (no token)

Method: `curl -H 'Accept: application/json'`, then read 401/405/404.

| route | GET | POST | conclusion |
|---|---|---|---|
| `/machine/paginated` | 401 | 405 | exists, GET |
| `/machine/active` | 401 | 405 | exists, GET |
| `/machine/profile/{id}` | 401 | — | exists, GET |
| `/season/machine/active` | — | — | (inferred, used by htb-cli) |
| `/user/info` | 401 | 405 | exists, GET |
| `/vm/spawn` | 405 | 401 | exists, POST only |
| `/vm/terminate` | 405 | 401 | exists, POST only |
| `/vm/reset` | 405 | 401 | exists, POST only |
| `/machine/submit` | 405 | 401 | exists, POST only |
| `/challenge/list` | 401 | — | exists, GET |
| `/machine/list` | 404 | 404 | **does not exist** |
| `/machine/own` | 404 | 404 | not as a bare path — see below |
| `/machine/own/{id}` | 404 | 404 | does not exist |
| `/machine/{id}` | 404 | 404 | does not exist |
| `/machine/play/{id}` | 404 | 404 | does not exist |
| `/machine/terminate/{id}` | 404 | 404 | does not exist |
| `/machine/extend`, `/machine/reset`, `/machine/todo`, `/machine/rank` | 404 | 404 | do not exist |
| `/user/api_token`, `/user/refresh`, `/user/logout` | 404 | — | do not exist |
| `/vpn/status`, `/connections`, `/access` | 404 | — | do not exist as bare paths |

## Contradiction to resolve with a live token

`POST /machine/own` probed **404**, but `GoToolSharing/htb-cli` uses
`{base}/machine/own` with `{"id": ..., "flag": ...}`. Most likely the route is
registered only for authenticated POSTs, or the probe's empty body was rejected
before routing. **Verify with a real token before relying on the flag path** —
this is the single most important unconfirmed route, because it is how a run
proves success.

## Inferred from a maintained client (not official docs)

Source: `github.com/GoToolSharing/htb-cli` (v1.7.0), `lib/`.

| route | shape | evidence |
|---|---|---|
| `GET /user/info` | — | `lib/utils/utils.go:267` |
| `GET /machine/active` | response `info.id`, `info.expires_at` | `utils.go:288,315` |
| `GET /machine/profile/{id}` | — | `utils.go:251,481` |
| `GET /machine/recommended/` | — | `utils.go:240` |
| `GET /search/fetch?query=` | — | `utils.go:73` |
| `POST /machine/own` | `{"id": int, "flag": string}` | `lib/submit/submit.go:79,133` |
| `POST /arena/own` | `{"id": int, "flag": string}` | `submit.go` (release-arena branch) |
| `GET /connection/status` | VPN state | `lib/vpn/vpn.go:255` |
| `GET /access/ovpnfile/{id}/0` | `.ovpn` bytes | `vpn.go:51` |
| `GET /connections/servers?product=` | — | `vpn.go:116` |

Auth in that client: `Authorization: Bearer <token>`, plus
`Accept: application/json, text/plain, */*` on POST.

## To confirm with a live token (checklist)

Run each once and paste the real status + a truncated body:

- [ ] `GET /machine/paginated?page=1&per_page=50` — pagination field names
      (`data`, `meta`, `links`?)
- [ ] `GET /machine/active` — exact shape when nothing is spawned vs. spawned
- [ ] `POST /vm/spawn {"id":1}` — does it return the machine or just `message`?
- [ ] `GET /machine/active` poll — how long until `ip` appears
- [ ] `POST /vm/terminate {"id":1}`
- [ ] `POST /vm/reset {"id":1}`
- [ ] `POST /machine/own {"id":1,"flag":"..."}` — **confirm the 404 above**
- [ ] `GET /search/fetch?query=Lame` — response shape for name→id
- [ ] rate-limit headers on a burst (`X-RateLimit-*`? `Retry-After`?)

## Notes on this project's use

- Free tier = 1 active machine; all spawns go through a single-slot queue.
- `expires_at` is the deadline for a run; exceeding it is `timeout`.
- Machine `id` is numeric and stable; `name` is not unique enough to key on.
