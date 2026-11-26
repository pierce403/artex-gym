# ADR 0001 — Pin ARTEX by image digest, build from a pinned checkout meanwhile

- **Status:** accepted
- **Date:** 2026-11-26
- **Milestone:** M0 (drives M1)
- **Deciders:** pierce

## Context

The project requires ARTEX to be "pinned by digest in a compose overlay, never
vendored" (hard constraint). Two facts constrain how we can honour that today:

1. `ghcr.io/baarai/artex` is **not anonymously pullable**. The release workflow
   publishes it and then verifies an anonymous pull, but the package is still
   private, so the verification step would fail:

   ```
   $ docker manifest inspect ghcr.io/baarai/artex:latest
   Head "https://ghcr.io/v2/baarai/artex/manifests/latest": denied
   $ TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:baarai/artex:pull&service=ghcr.io" ...)
   $ gh api /orgs/BaaRai/packages/container/artex
   gh: Not Found (HTTP 404)
   ```

   Pulling after `docker login ghcr.io` as the package owner works, but a
   digest that only the owner can resolve is not a pin we can hand to CI or a
   second machine.

2. The upstream compose file builds from the checkout (`build: context: .`),
   and the newest commit on `main` (`38c7477`) is ahead of the newest tag
   (`v0.7.0`, 2026-11-21), so "latest release" and "current source" differ.

A digest pin must be resolvable offline-ish (no registry auth) and reproducible.

## Decision

**Two-tier pin, one lock file.**

- `compose/artex.lock.json` is committed and records: `artex_git_sha`,
  `artex_version`, `image_ref`, and `image_digest` (the `sha256:...` of the
  local image manifest after build). The CLI reads it; nothing else does.
- While GHCR is private, the overlay builds ARTEX from `$ARTEX_SOURCE` at
  exactly `artex_git_sha`, then `artexctl up` resolves the built image digest
  and **refuses to start** if it differs from the lock. Building a different
  commit without updating the lock is an error, not a silent upgrade.
- When GHCR becomes public, the lock's `image_ref` flips to
  `ghcr.io/baarai/artex@sha256:...` and the `build:` block is dropped. No other
  overlay change is needed; the service name and env stay the same.

The overlay is `compose/overlay.yml`, merged with the upstream file:

```
docker compose -f "$ARTEX_SOURCE/docker-compose.yml" -f compose/overlay.yml ...
```

The overlay only **adds** services and **sets** environment; it never edits
upstream files (non-goal: no ARTEX source patches).

## Consequences

- Every run is traceable to `artex_git_sha`, which is also a field in the
  capture blob and the training row.
- A private registry does not block M1. The cost is a local build (~minutes,
  Node + Go) on first `up` per machine, cached afterwards by the layer cache.
- The digest in the lock is a **build-output** digest: identical inputs on a
  different Docker version can produce a different digest. It pins *what we
  ran*, not a bit-identical rebuild. The authoritative pin is `artex_git_sha`.
- Revisit when `docker manifest inspect ghcr.io/baarai/artex:<tag>` succeeds
  anonymously. That is the trigger; check it in the M1 smoke test.

## Alternatives considered

| Option | Why not (now) |
| --- | --- |
| `image: ghcr.io/baarai/artex@sha256:...` | Digest unresolvable without owner credentials; CI and other machines fail. |
| Pin the release zip (`artex-v0.7.0-linux-amd64`) | Not a container; we lose the upstream compose (Postgres wiring, /app/data layout) and gain a hand-rolled runtime. |
| Vendor or patch ARTEX | Explicit non-goal. |
| `:latest` tag | Movable; violates the constraint and breaks run-to-run comparability. |
| Fork-and-publish our own image | Adds a publishing pipeline and a second supply chain to trust, for no gain while we build from source anyway. |

## Evidence

```
$ cd ~/projects/ARTEX && git rev-parse HEAD
38c7477c51636c9221c78683f4aa9c4f08f65c19
$ git log -1 --format='%cd' 
Sun Nov 22 23:01:48 2026 +0100
$ gh release view --repo BaaRai/ARTEX --json tagName
v0.7.0
$ docker compose version
Docker Compose version 2.40.3+ds2-0ubuntu2
```

## Open questions

- **Q1 (owner):** can the GHCR package be set to public? If yes, M1 can pin a
  registry digest and skip the local build; the lock format already allows it.
- **Q2:** does the ARTEX image need the frontend (`-tags embedui`)? The compose
  file builds it in; we only need the HTTP API, so the overlay keeps the
  upstream build args as-is rather than optimising M1 for build time.
