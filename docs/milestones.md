# Milestone log

## M0 — Skeleton

Branch `m0-skeleton`.

Done gate: `artexctl --help` lists every command, each exits NotImplemented.

- `up / down / run / collect / dataset / train / eval` present; every one
  prints `NotImplemented (planned in M<n>)` and exits 3 (`up` additionally
  verifies the ARTEX pin first and exits 4 if it drifted).
- `tests/test_cli_surface.py` asserts the surface and the exit codes offline.
- `tests/test_pin.py` proves the verifier with throwaway git repos, so the
  pin cannot rot into documentation.
- `adr/0000-template.md`, `adr/0001-artex-pinning.md`,
  `adr/0002-collector-placement.md`.
- `src/artex_gym/pin.py` loads `compose/artex.lock.json` and verifies a
  checkout against it; `artexctl up` calls it before doing anything, and exits
  4 with the exact fix on a mismatch.
- `compose/overlay.yml` + `compose/artex.lock.json` (pin) and the
  `compose/llm-logger/Dockerfile`.

Findings that change later milestones:

1. **We build ARTEX from our fork `pierce403/ARTEX`**, which is upstream's
   history at an older point: 0 commits of its own, 82 behind `BaaRai/ARTEX`
   `main`, at `38c7477` (`v0.7.0-109-g38c7477`). The pin is the commit, and
   `artexctl up` verifies it before building.
2. **The GHCR package does not exist yet.** The fork's release workflow
   publishes to `ghcr.io/pierce403/artex` on a `v*` tag push, and no tag has
   been pushed, so a registry digest pin is not yet available and the overlay
   builds from the pinned checkout. ADR-0001 records the exact commands and
   the flip condition.
3. **ARTEX already stores the raw wire bodies** in
   `llm_records.raw_request` / `raw_response`; `request_body` is normalized
   and drops tool schemas entirely. A useful cross-check for the collector,
   not a replacement for it.
4. **`ARTEX_LLM_BASE_URL` must end in `/v1`** for OpenAI-shaped providers,
   since ARTEX appends `/chat/completions`. The overlay does this and adds
   `llm-logger:4000` to `ARTEX_LLM_PRIVATE_ENDPOINTS`, without which the
   model-list fetch refuses a private address.
5. **Typer 0.29 + rich**: `rich_markup_mode="plain"` raises `AssertionError`
   on bracketed help text, so the app uses the default mode.

Open questions carried into M1:

- Q1: push a `v*` tag from `pierce403/ARTEX` to publish the image? That is the
  only thing between this design and a true registry digest pin.
- Q2: what "alert" means for the drop counter (metric only, or also a non-zero
  CLI exit).
- Q3: blob naming — `{turn:04d}` vs the collector's monotonic per-run sequence,
  with the logical `turn_idx` written by the join.
- Q4: redaction rules and where the manifests live (blocks ADR-0003).
- Q5: when the pin moves, must we re-capture, or can rows from two
  `artex_git_sha` values coexist in one dataset?
