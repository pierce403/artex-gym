# Box queue — progress report

Generated from `notes/queue.json` (543 retired boxes) and `.work/logs/queue-run.log`.

## Totals

- solved **47**
- timeout 3
- skipped (no spawn) 3
- partial (user only) 1
- pending 489

## By tier

| tier | solved | timeout | skipped | partial | pending |
|---|---|---|---|---|---|
| Easy | 47 | 3 | 3 | 1 | 106 |
| Medium | 0 | 0 | 0 | 0 | 193 |
| Hard | 0 | 0 | 0 | 0 | 122 |
| Insane | 0 | 0 | 0 | 0 | 68 |

## Speed (solved boxes only)

- n = 40
- median 11.3 min
- p90 21.3 min
- max 22.1 min
- took >12 min: 18 of 40
- time spent on non-solves: 92 min across 7 boxes

## Not solved

| id | name | tier | state | note |
|---|---|---|---|---|
| 578 | Broker | Easy | timeout | timeout after 20m |
| 569 | Analytics | Easy | timeout | timeout after 20m |
| 559 | CozyHosting | Easy | skipped:no-spawn | error: spawn issued but no IP appeared within 120s; check th |
| 13 | Grandpa | Easy | timeout | timeout after 20m |
| 617 | GreenHorn | Easy | partial:user-only | timeout after 20m |
| 111 | Sense | Easy | skipped:no-spawn | error: spawn issued but no IP appeared within 120s; check th |
| 5 | Beep | Easy | skipped:no-spawn | error: spawn issued but no IP appeared within 120s; check th |
