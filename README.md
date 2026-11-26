# artex-gym

One CLI that takes an ARTEX checkout to a trained, evaluated model:
provision → capture → join → dataset → train → eval.

ARTEX (AGPL-3.0) is never vendored and never patched. We drive it through
environment variables, a compose overlay and HTTP only.

Source of truth: our fork `pierce403/ARTEX` (upstream's history at an older
point), pinned by commit in `compose/artex.lock.json`. `artexctl up` verifies
the checkout is that commit before building — see `adr/0001-artex-pinning.md`.

## Status

M0 — skeleton only. Every command exits with `NotImplemented`; `up` also
verifies the ARTEX pin first.

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

## Documents

- `adr/` — decisions, in order. Start with `adr/0001-artex-pinning.md`.
- `docs/` — milestone notes and open questions.
