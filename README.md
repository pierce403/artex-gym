# artex-gym

One CLI that takes an ARTEX checkout to a trained, evaluated model:
provision → capture → join → dataset → train → eval.

ARTEX (AGPL-3.0) is never vendored and never patched. We drive it through
environment variables, a compose overlay and HTTP only.

Source of truth: our fork `pierce403/ARTEX` (upstream's history at an older
point), pinned by commit in `compose/artex.lock.json`. `artexctl up` verifies
the checkout is that commit before building — see `adr/0001-artex-pinning.md`.

## Status

**M0 and M1 done; M2–M6 are stubs.** `up` / `down` work end to end and the
collector captures real calls; `run`, `collect`, `dataset`, `train` and `eval`
still exit `NotImplemented`.

M1 proves the pipe holds water: `artexctl up` pins the ARTEX commit, builds and
starts ARTEX + `llm-logger` + Postgres, authenticates, turns capture on, and
**asserts** it — a stack that runs without capturing is treated as a failure.
Calls with `curl` through `localhost:4000/v1/chat/completions` produce
immutable gzipped blobs under `data/llm-blobs/{run_id}/`.

`up` also tunes the stack for benchmark work — see `adr/0003-parallelism.md`:
`workers=8`, and the planner's intent-batch cap raised from 4 to 8 with the
ideal route count 2–3 → 4–6. Both are idempotent and the prompt edit is
reversible (`POST /api/agents/planner/prompt/reset`). HTB allows **one** active
box per account, so parallelism comes from breadth on one box, not from more
boxes.

See `notes/report.md` for a real run: four HackTheBox machines driven to
HTB-accepted flags with ARTeX, with capture held at 0 drops throughout, plus the
per-box write-ups in `notes/{cap,expressway,orion,dutybound}/`.

## Install

    uv sync --all-groups            # CLI + tests
    uv sync --extra collector       # + the llm-logger sidecar deps

## Commands

    artexctl up / down           provision or tear down the stack
    artexctl run ROOM            queue a run, N attempts, fresh instance each
    artexctl collect             drain + join into trajectories
    artexctl dataset             build SFT/DPO splits
    artexctl train CONFIG        LoRA/QLoRA run
    artexctl eval RUN_ID         baseline or post-train eval

## Layout

    src/artex_gym/{cli,collector,providers,join,dataset,train,eval}
    adr/          one file per decision, including every API contract
    compose/      overlay + collector image
    fixtures/     recorded API + LLM payloads for CI
    tests/        contract tests, offline

## Skills

Project-local agent skills in `.agents/skills/`, usable by any agent that reads
that convention:

- `artex-running` — tell a *capturing* stack from a merely running one, with
  `scripts/artex-status.sh` (read-only by default, `--fix` to repair).
- `hackthebox` — HTB Labs v4/v5 client (`scripts/htb.py`) with a verified
  route inventory in `references/endpoints.md`, including the traps that cost
  the most time.

## Documents

- `adr/` — decisions, in order. Start with `adr/0001-artex-pinning.md`
  (why we pin a commit, not a tag) and `adr/0002-collector-placement.md`
  (why capture lives in a sidecar and what "fail-open" means).
- `docs/milestones.md` — what each milestone delivered and what it left open.
- `notes/` — per-box write-ups from the first real run (`notes/report.md`).
