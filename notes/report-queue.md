# Box queue — progress report

Generated from `notes/queue.json` (543 retired boxes) and `.work/logs/queue-run.log`.

## Totals

- solved **72**
- timeout 6
- skipped (no spawn) 1
- partial (user only) 3
- pending 461

## By tier

| tier | solved | timeout | skipped | partial | pending |
|---|---|---|---|---|---|
| Easy | 72 | 6 | 1 | 3 | 78 |
| Medium | 0 | 0 | 0 | 0 | 193 |
| Hard | 0 | 0 | 0 | 0 | 122 |
| Insane | 0 | 0 | 0 | 0 | 68 |

## Speed (solved boxes only)

- n = 65
- median 11.7 min
- p90 21.4 min
- max 22.2 min
- took >12 min: 32 of 65
- time spent on non-solves: 206 min across 21 boxes

## Not solved

| id | name | tier | state | note |
|---|---|---|---|---|
| 578 | Broker | Easy | timeout | timeout after 20m |
| 569 | Analytics | Easy | timeout | timeout after 20m |
| 13 | Grandpa | Easy | timeout | timeout after 20m |
| 617 | GreenHorn | Easy | partial:user-only | timeout after 20m |
| 5 | Beep | Easy | skipped:no-spawn | error: spawn issued but no IP appeared within 120s; check th |
| 356 | Explore | Easy | partial:user-only | timeout after 20m |
| 678 | VulnEscape | Easy | timeout | timeout after 20m |
| 668 | Artificial | Easy | timeout | timeout after 20m |
| 587 | Crafty | Easy | timeout | timeout after 20m |
| 699 | Lock | Easy | partial:user-only | timeout after 20m |
