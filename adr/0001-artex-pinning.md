# ADR 0001 — Pin ARTEX by commit from our fork; digest when the registry allows

- **Status:** accepted (revised 2026-11-26: source is now `pierce403/ARTEX`)
- **Date:** 2026-11-26
- **Milestone:** M0 (drives M1)
- **Deciders:** pierce

## Context

The project requires ARTEX to be "pinned by digest in a compose overlay, never
vendored". Three facts decide how that can be honoured today.

1. **Upstream's image is not anonymously pullable.** `ghcr.io/baarai/artex`
   denies anonymous pulls, and the package does not exist under the org either:

   ```
   $ docker manifest inspect ghcr.io/baarai/artex:latest
   Head "https://ghcr.io/v2/baarai/artex/manifests/latest": denied
   $ gh api /orgs/BaaRai/packages/container/artex
   gh: Not Found (HTTP 404)
   ```

   Upstream's own release workflow pushes the image and then verifies an
   anonymous pull; that verification would fail on the current package state.

2. **We work against our own fork.** `pierce403/ARTEX` is the checkout in use.
   It is a strict ancestor of upstream `main` — 0 commits of its own, 82 commits
   behind — so it is upstream's history at an older point, not a divergent fork
   we have to trust differently:

   ```
   $ git rev-list --left-right --count origin/main...upstream/main
   0	82
   $ git merge-base --is-ancestor origin/main upstream/main && echo yes
   yes
   $ git describe --tags
   v0.7.0-109-g38c7477
   ```

   Its release workflow (inherited from upstream) publishes to
   `ghcr.io/${{ github.repository }}`, i.e. `ghcr.io/pierce403/artex`, on a `v*`
   tag push, with `packages: write`. No tag has been pushed, so no package
   exists yet.

3. The upstream compose file builds from the checkout (`build: context: .`), so
   "the image" is whatever source tree we hand it.

A pin must be resolvable without registry credentials and must be reproducible
on a second machine.

## Decision

**The commit is the pin. The digest is an accelerator, recorded when available.**

- `compose/artex.lock.json` is committed and holds `artex_git_sha` (full
  40-hex), what that commit describes (`v0.7.0-109-g38c7477`), how far it is
  behind upstream at pin time, `source_repo`, `image_repo` and — once one
  exists — `image_digest`.
- `src/artex_gym/pin.py` is the only code that answers "is this our ARTEX?".
  `artexctl up` calls `verify()` **before** building and refuses on mismatch,
  naming the fix:

  ```
  ~/projects/ARTEX is at 1d24407a (v0.7.0-107-g1d24407), but
  compose/artex.lock.json pins 38c7477c51 (v0.7.0-109-g38c7477).
    Fix: git -C ~/projects/ARTEX checkout 38c7477c51636c9221c78683f4aa9c4f08f65c19
    Or:  bump the pin in compose/artex.lock.json (and record why).
  ```

  A dirty tree is allowed and reported; the commit is what was pinned.
- While no registry digest exists, the overlay builds from `$ARTEX_GYM_ARTEX_SOURCE`
  at the pinned commit. When the first `v*` tag publishes a public package,
  `image_ref` becomes `ghcr.io/pierce403/artex@sha256:...` and the `build:`
  block is dropped. Nothing else in the overlay changes.

## Consequences

- A changed ARTEX checkout can no longer silently change the data. This is the
  main reason the pin is enforced in code and not just written in an ADR.
- `artex_git_sha` flows into the capture blob and the training row, so every
  row is attributable to an exact agent source.
- The fork being 82 commits behind is a deliberate, recorded position, not
  drift: we can read the gap (`artex_commits_behind_upstream`) and decide when
  to move. Moving the pin is a one-line lock change plus a re-run of the
  contract tests.
- Local build cost on first `up` per machine (Node + Go, layer-cached after).
- Revisit: when a `v*` tag is pushed from `pierce403/ARTEX` and the package is
  public. Verify with `docker manifest inspect ghcr.io/pierce403/artex:<tag>`
  logged out. That is the trigger to flip `image_ref` to a digest.

## Alternatives considered

| Option | Why not (now) |
| --- | --- |
| `ghcr.io/baarai/artex@sha256:...` | Package not anonymously resolvable; not the repo we work against. |
| Tag (`:v0.7.0`) rather than a commit | Movable, and our checkout is 109 commits past that tag anyway. |
| Track upstream `main` | 82 commits of unreviewed change under a benchmark we are trying to hold constant. |
| Push our own image now and pin its digest | Requires a `v*` tag push and a package-visibility change; adds a publish step before M1 needs one. The lock format already accommodates the later swap. |
| Vendor or patch ARTEX | Explicit non-goal. |
| A local `docker save` blob committed to the repo | Hundreds of MB of binary in git for a pin the commit already gives. |

## Evidence

```
$ git -C ~/projects/ARTEX remote get-url origin
git@github.com:pierce403/ARTEX.git
$ git -C ~/projects/ARTEX rev-parse HEAD
38c7477c51636c9221c78683f4aa9c4f08f65c19
$ git -C ~/projects/ARTEX describe --tags
v0.7.0-109-g38c7477
$ curl -s -u pierce403:$TOKEN "https://ghcr.io/token?scope=repository:pierce403/artex:pull&service=ghcr.io"
$ curl -s -H "Authorization: Bearer $TOK" https://ghcr.io/v2/pierce403/artex/tags/list
{"errors":[{"code":"NAME_UNKNOWN","message":"repository name not known to registry"}]}
$ docker push ghcr.io/pierce403/artex-gym:pin-probe   # current gh token lacks write:packages
denied: permission_denied: The token provided does not match expected scopes.
```

## Open questions

- **Q1 (owner):** push a `v*` tag from `pierce403/ARTEX` to publish the
  package? That is the only thing standing between this design and a true
  registry digest pin. If yes, the `gh` token used locally also needs
  `write:packages` for manual pushes (CI already has it).
- **Q2:** when the pin moves, is a re-capture required (new `artex_git_sha` ⇒
  rows from two agent versions in one dataset), or is `artex_git_sha` on the
  training row enough to let both coexist?
