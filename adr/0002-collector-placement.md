# ADR 0002 — Collector is a separate service, not an ARTEX feature

- **Status:** accepted
- **Date:** 2026-11-26
- **Milestone:** M1
- **Deciders:** pierce

## Context

ARTEX already records LLM traffic twice, in two different shapes:

- `llm_records` (Postgres): `request_body` / `response_body` are *normalized*
  — `serializeRequest` keeps only `system`, `messages`, `max_tokens`, and the
  response body is `{text, stop_reason, usage, thinking?}`. Tool schemas and
  `tool_use` blocks are dropped.
- `raw_request` / `raw_response` columns: the untouched wire bodies, filled by
  `llmrec.Capture` through the HTTP transport. This is the useful one, but it
  lives in ARTEX's database, needs a `task_id` + worker binding we do not
  control, and gives us no control over what is stored or when it is dropped.

Neither is a stable capture format for training, and reading either requires
coupling to ARTEX's Postgres schema (which is "safe" — it is a public contract
— but ties capture to a database we do not own, and to ARTEX having written the
row before we read it).

The settled design is a logging reverse proxy between ARTEX and the provider:

```
ARTEX_LLM_PROVIDER=openai
ARTEX_LLM_BASE_URL=http://llm-logger:4000/v1
```

ARTEX appends `/chat/completions`, so the collector terminates
`POST /v1/chat/completions` (and `GET /v1/models`, which the UI model picker
calls) and forwards to the real provider.

## Decision

A FastAPI service, `llm-logger`, is the capture point:

- One endpoint family (`/v1/chat/completions`, `/v1/models`) plus `/metrics`
  and `/api/health`. Unrecognised paths are proxied verbatim.
- **Fail-open**: the request path never awaits a disk write. Capture goes to an
  in-process bounded queue; a worker task writes gzip blobs. Queue overflow,
  write error, or serialization error increments `collector_dropped_total` and
  the response still flows. A drop is never a 5xx to ARTEX.
- Streaming responses are teed: the client gets bytes as they arrive; the
  capture file is written only when the stream ends (or errors).
- Blobs are immutable and content-addressed by name order:
  `{run_id}/{turn:04d}-{req_id}.json.gz`, exactly as specified.
- `/metrics` exposes at least `collector_dropped_total`, `collector_written_total`,
  `collector_queue_depth`, `collector_write_errors_total`. The alarm rule is
  "above 0", per the constraint.

Ground truth is still ARTEX's recording proxy (`data/traffic/_blobs`, SQLite
index) and the Postgres exploration graph; the collector supplies the
per-turn model IO. Joining them is M3.

## Consequences

- Capture is independent of ARTEX internals, so it survives ARTEX upgrades that
  change `llm_records`.
- We add a hop and a failure domain. Fail-open is what makes that acceptable;
  the cost is that a blob may be missing, which is why the drop counter exists
  and why `/metrics` is part of the M1 Done gate.
- `turn:04d` implies the collector needs a turn notion. It does not have one:
  turn index comes from the *join* (see ADR for M3). The filename therefore
  uses a monotonic per-run sequence at write time, and the join rewrites the
  logical `turn_idx` into the capture record. Renaming blobs later would break
  immutability, so the sequence is only the sort key, never the authority.

## Alternatives considered

| Option | Why not |
| --- | --- |
| Read `llm_records.raw_request` from ARTEX's Postgres | Couples capture to ARTEX's schema and write timing; no drop control; misses calls that ARTEX fails to persist. |
| Patch ARTEX to emit capture events | Non-goal (no source patches). |
| MITM the provider TLS | Certificate and SNI problems; the base-URL override is a supported ARTEX feature. |
| Collector writes directly to Postgres | Adds a second writer and a migration dependency to the hot path; blobs are the contract. |

## Open questions

- **Q1 (owner):** the drop-counter alarm threshold. Constraint says "alert
  above 0". Does "alert" mean a non-zero exit from `artexctl collect`, a
  Prometheus rule, or both? Default plan: `/metrics` gauge plus `collect`
  printing a warning and returning non-zero only under `--strict`.
- **Q2:** retention. Blobs are immutable; does `down` delete them, or only
  `down --volumes`?
