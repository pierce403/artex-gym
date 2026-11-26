# HTB Labs API v4 — endpoint record

Base: `https://labs.hackthebox.com/api/v4`

**Status of each row is evidence, not documentation.** Official HTB API docs are
not publicly reachable (checked 2026-11-26: `/api/v4/docs`, `/openapi.json`,
`api-documentation` repos all 404). So this file separates what was probed live
from what was inferred.

> Reference checkout: `.work/vendor/htb-cli` (run `scripts/vendor.sh`), at
> commit `35a970d`. Paths below are quoted from it, not from memory.

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
| `/machine/paginated/` (trailing slash) | 401 | — | exists; the bare path 404s on some hosts |
| `/machine/list/retired/paginated/` | 401 | — | exists, retired catalogue |
| `/machine/unreleased/` | 404 | — | not on labs; `htb-cli` cites it |
| `/machine/own` (v4) | 404 | 404 | **exists on v5 only** |
| `/machine/own` (v5) | — | 400 | correct route: `{"id","flag"}` |
| `/machine/own/{id}` | 404 | 404 | does not exist |
| `/machine/{id}` | 404 | 404 | does not exist |
| `/machine/play/{id}` | 404 | 404 | does not exist |
| `/machine/terminate/{id}` | 404 | 404 | does not exist |
| `/machine/extend`, `/machine/reset`, `/machine/todo`, `/machine/rank` | 404 | 404 | do not exist |
| `/user/api_token`, `/user/refresh`, `/user/logout` | 404 | — | do not exist |
| `/vpn/status`, `/connections`, `/access` | 404 | — | do not exist as bare paths |

## List routes, corrected from the reference client

The catalogue routes need a **trailing slash and a query**, which is why the
first probe pass reported them missing:

```
GET /machine/paginated/?per_page=100                    # active + retired, mixed
GET /machine/list/retired/paginated/?per_page=100&sort_by=release-date
```

Source: `.work/vendor/htb-cli/cmd/machines.go` (`machineURL`, `retiredURL`).

## Verified lifecycle payloads (live, 2026-11-26)

`vm/spawn`, `vm/reset`, `vm/terminate` all take **`machine_id`**, not `id`.
Body `{}` on spawn/reset answers:

```
422 {"message":"The machine id field is required.",
     "errors":{"machine_id":["The machine id field is required."]}}
```

`htb-cli` and my first draft both used `{"id":...}`; that silently means "no
machine id" and is easy to misread as an auth problem.

### Side effect to know before probing

`POST /vm/terminate` with `{}` **succeeds and terminates whatever is active**
(200 {"message":"Machine terminated.","success":true}) — it does not need a
machine id at all. So a `{}` "does this field exist?" probe on terminate kills
the running box. Verified the hard way: DutyBound was terminated mid-run.

Probe spawn/reset with `{}` (harmless 422), never terminate.

### Concurrency: exactly ONE active instance, even on dedivip

```
GET  /machine/active                  -> DutyBound (999), ip 10.129.137.83
POST /vm/spawn {"machine_id":351}     -> 403 {"message":"You already have an active instance"}
.. terminate DutyBound ..
POST /vm/spawn {"machine_id":351}     -> 200 {"message":"Machine deployed to lab.","success":true}
```

So the account is `dedivip` (`lab_server: dedivip_lab`) and still holds one
instance at a time. The single-slot queue is correct and required, not a
free-tier-only assumption. Boxes run in SERIES.

Spawn is also slow: `isSpawning: true` with `ip: null` for ~90-100s before an
IP appears. Poll `/machine/active` until `ip` is non-null.

## RESOLVED: flag submission is on v5, not v4

`POST /api/v4/machine/own` is **404 with a valid token** — so `htb-cli`'s path
is stale, and this was not an auth artifact.

`POST /api/v5/machine/own` is the real route:

```
$ curl -X POST -H 'Accept: application/json' -H "Authorization: Bearer $TOK" \
    -d '{"id":999,"flag":"HTB{probe}"}' \
    https://labs.hackthebox.com/api/v5/machine/own
400 {"message":"Incorrect Flag."}
```

Payload is just `{"id": <machine id>, "flag": "<flag>"}` — **no hashes, no
links, no accept_terms**. A wrong flag answers `400 {"message":"Incorrect
Flag."}`, which is a real answer, not a call failure.

Why every v4 probe missed it: the web app's own bundle decides the API version
per content type. From `assets/common-api-*.js`:

```js
a = (n, r, i) => { let a = n === e.MACHINE;
  return t.post(`/${n}/own`, r, {enableV5Api: a, signal: i}) }
```

`enableV5Api` is true **only for MACHINE**, so machines use `/api/v5/machine/own`
while challenges and fortresses stay on v4.

Do **not** confuse this with two other routes found in the bundles:

- `POST /api/v4/machine/submit` — the **machine creator** form (submit a NEW
  machine for review). It demands `name`, `user`, `admin`, both 32-char hashes,
  `download_link`, `writeup_link`, `hypervisor`, `accept_terms`, and answers
  "The name has already been taken" for an existing box. Wrong tool for a flag.
- `POST /api/v4/machines/{contentId}/tasks/{taskId}/flag` — per-task flags
  (Starting Point), not machine ownership.

Evidence bundle, kept in `.work/probes/htb-web/`: `common-api-JS`,
`machines-api-JS`, `MachineSubmission.js`, `MachineProfile.js`, `http-client.js`
(base URLs v4 + v5).

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
- [x] `POST /api/v5/machine/own {"id":999,"flag":"..."}` -> 400 Incorrect Flag
      (route confirmed; needs a real flag to confirm a 200)
- [ ] `GET /search/fetch?query=Lame` — response shape for name→id
- [ ] rate-limit headers on a burst (`X-RateLimit-*`? `Retry-After`?)

## Verified against the live API, 2026-11-26 (real token)

Three things the reference client's field list did **not** tell us:

1. **`profile/{id}.ip` is a lie.** It returns the IP of whichever machine is
   spawned *right now*, not the machine you asked about. Profiles 351 (Cap),
   692 (CodePartTwo) and 999 (DutyBound) all returned `10.129.137.83`; only 999
   was actually running. The per-machine truth is `playInfo`:

   ```
   playInfo.isActive / isSpawned  -> is THIS machine the spawned one
   playInfo.expires_at             -> when it dies
   ```

   Never read `ip` off a profile without checking `playInfo` first.

2. **`points` is 0 on every retired machine.** It is not a difficulty proxy.
   `static_points` (20/30/40) is the score. Use `difficulty` (0-100, lower is
   easier) to order, and `difficultyText` to filter.

3. **There is no `retired` key in list payloads.** A machine is retired when
   `active` is `null`. Profiles *do* carry `retired`.

Actual list row (trimmed, `GET /machine/list/retired/paginated/`):

```json
{"id":351,"name":"Cap","os":"Linux","static_points":20,"points":0,
 "difficulty":28,"difficultyText":"Easy","star":4.6,"free":true,
 "authUserInUserOwns":false,"authUserInRootOwns":false,
 "active":null,"playInfo":{"isActive":null,"expires_at":null}}
```

Sample size for the counts below: 300 retired machines across 3 pages ->
89 Easy, 88 Easy+unowned, 1 owned by this account (Titanic).

## List payload fields (from `cmd/machines.go`)

The list response array is read by `htb-cli` as `data`, with per-machine keys:

| field | use |
|---|---|
| `id` | numeric machine id, the stable key |
| `name` | display name |
| `os` | `Linux` / `Windows` |
| `difficultyText` | `Easy` / `Medium` / `Hard` / `Insane` (list) |
| `difficulty` | same idea on `machine/profile/{id}` |
| `points` | **0 on retired machines** — not usable for ordering |
| `static_points` | the score: 20/30/40/50 by tier |
| `difficulty` | 0-100 numeric score; lower is easier |
| `active` | non-null only for the current season's machines |
| `free` | playable without a subscription |
| `release` | RFC3339 timestamp |
| `star` | star count |
| `retired` | retired flag |
| `authUserInUserOwns` | bool, nullable — user flag owned |
| `authUserInRootOwns` | bool, nullable — root flag owned |

Note the two spellings: `difficultyText` (camelCase) in list payloads vs
`difficulty` in a profile. Code that assumes one will silently match nothing.

## Notes on this project's use

- Free tier = 1 active machine; all spawns go through a single-slot queue.
- `expires_at` is the deadline for a run; exceeding it is `timeout`.
- Machine `id` is numeric and stable; `name` is not unique enough to key on.
- "Unsolved" = `authUserInUserOwns` **and** `authUserInRootOwns` both false.
  A box where user is owned but not root is still worth training on (the run is
  a partial-success label), so it is reported, not silently dropped.
- Retired easy boxes are the default training target, but retired boxes have
  public writeups: a model that memorised them scores higher than its skill
  warrants. Record `retired` on the dataset row so an eval can split on it.
