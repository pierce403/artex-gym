# ADR 0003 — One box at a time; parallelism comes from planner breadth

- **Status:** accepted
- **Date:** 2026-11-26
- **Milestone:** M2 (shapes the provider queue)
- **Deciders:** pierce

## Context

The plan was "swarm three boxes at once". Three facts, each verified against
the live API, say that is not possible and that worker count is the wrong dial.

**1. HTB gives one active instance per account.** Probed twice, on a `dedivip`
subscription (`lab_server: dedivip_lab`), so this is not a free-tier artifact:

```
POST /api/v4/vm/spawn {"machine_id":736}            while Cap(351) active
  -> 403 {"message":"You already have an active instance"}
POST /api/v4/vm/spawn {"machine_id":736,
                       "lab_server":"dedivip_lab"}  same
  -> 403 {"message":"You already have an active instance"}
```

There is no plural endpoint either. The frontend bundle uses
`GET /api/v5/virtual_machine/active`, which exists (v4 404s) but returns
`{"info": {...}}` — one object, not a list.

**2. Running several tasks without boxes wastes real money.** Task concurrency is
uncapped (`task_concurrency_enabled: false`), so N tasks can run. But a task
whose box has gone away does not idle — it keeps planning and calling the model
against a dead IP. Measured: task 1 (DutyBound) spent 6.9M input tokens after
its box was terminated, for 0 progress.

**3. Worker count is not the limit — planner breadth is.** The seeded planner
prompt caps a round at "at most 4 highest-value ones" intents and calls
"2–3 routes" the ideal. Measured intent counts for the whole run:

| task | box | intents created | workers available |
|---|---|---|---|
| 1 | DutyBound | 18 | 3 |
| 2 | Cap | 2 | 3 |
| 3 | Orion | 4 | 3 |
| 4 | Expressway | 3 | 3 |

Cap finished in ~3 minutes with 2 intents: two of three workers had nothing to
claim for most of the run. Raising workers to 8 on a 2-intent frontier would
still leave six idle.

## Decision

- **Serial boxes.** One spawn at a time through a single-slot queue; each box
  is terminated once its flags are accepted (ADR-level rule, see the
  `hackthebox` skill).
- **Raise planner breadth, not worker count.** `workers = 8` is set, but the
  change that matters is the planner prompt: intent batch cap 4 → 8 and the
  ideal route count 2–3 → 4–6. Applied as a versioned prompt edit
  (`PUT /api/agents/planner/prompt`), reversible with
  `POST /api/agents/planner/prompt/reset`.
- **Codified, not manual.** `src/artex_gym/tune.py` applies both, idempotently,
  from `artexctl up`. A fresh stack gets the same settings; a second `up`
  changes nothing (asserted by `tests/test_tune.py`).

## Consequences

- A run gets more *breadth on one box* rather than more boxes. For a benchmark
  that is the right axis: the target, not the account, is the scarce resource.
- More workers multiplies token spend per minute. The unfunded-key incident
  showed how fast that bites; `collector_dropped_total` and the provider's 402
  are the signals to watch.
- The planner is now tuned away from upstream defaults, so `artex_git_sha` alone
  no longer fully describes a run's behaviour. The prompt version is reported in
  `up`'s summary (`planner v2 (breadth raised)`) and should be recorded on
  training rows.
- Revisit if HTB ever exposes multi-instance spawn, or if upstream raises its own
  intent cap (then the edit becomes a no-op and `tune` reports "already broad
  enough").

## Alternatives considered

| Option | Why not |
| --- | --- |
| Spawn 3 boxes in parallel | API refuses; 403 "You already have an active instance". |
| Run 3 tasks and accept the waste | Task 1 burned 6.9M input tokens on a dead IP. |
| Only raise `workers` | Frontier of 2–4 intents leaves most workers idle. |
| Patch `agent/planner.go` | Non-goal (no ARTEX source patches); the prompt is a DB row with versioning. |
| Auto-scale workers to open intents | Would need ARTEX changes; `workers` is a static setting. |

## Evidence

```
$ curl -X POST .../api/v4/vm/spawn -d '{"machine_id":736}'   # Cap active
403 {"message":"You already have an active instance"}

$ curl .../api/v5/virtual_machine/active
{"info": {"id":351,"name":"Cap","ip":"10.129.137.104",...}}   # singular

$ psql -c "select count(*) filter (where kind='intent') from exploration_nodes ..."
task 1: 18   task 2: 2   task 3: 4   task 4: 3
```
