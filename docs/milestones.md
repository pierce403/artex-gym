# Milestone log

## M0 — Skeleton

Branch `m0-skeleton`.

Done gate: `artexctl --help` lists every command, each exits NotImplemented.

- `up / down / run / collect / dataset / train / eval` present; every one
  prints `NotImplemented (planned in M<n>)` and exits 3.
- `tests/test_cli_surface.py` asserts the surface and the exit code, offline.
- `adr/0000-template.md`, `adr/0001-artex-pinning.md`,
  `adr/0002-collector-placement.md`.
- `compose/overlay.yml` + `compose/artex.lock.json` (pin) and the
  `compose/llm-logger/Dockerfile`.

Findings that change later milestones:

1. **GHCR image is private.** `ghcr.io/baarai/artex` denies anonymous pulls,
   so ADR-0001 pins a source SHA and builds locally, with the lock recording
   the resulting image digest. Needs an owner decision before M1's Done gate can
   claim "pinned by digest" in the registry sense.
2. **`llm_records.raw_request`** exists in ARTEX and holds the untouched wire
   bodies. It is a useful cross-check for the collector, not a replacement
   (normalized `request_body` drops tool schemas entirely).
3. **Typer 0.29 + rich**: `rich_markup_mode="plain"` crashes on bracketed help
   text. Left at default mode; noted in the source.

Open questions carried into M1:

- Q1: can the GHCR package be made public?
- Q2: what "alert" means for the drop counter (metric only, or also a non-zero
  CLI exit).
