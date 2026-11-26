# Box queue — progress report

Generated from `notes/queue.json` (543 retired boxes) and `.work/logs/queue-run.log`.

## Totals

- solved **57**
- timeout 5
- skipped (no spawn) 3
- partial (user only) 2
- pending 476

## By tier

| tier | solved | timeout | skipped | partial | pending |
|---|---|---|---|---|---|
| Easy | 57 | 5 | 3 | 2 | 93 |
| Medium | 0 | 0 | 0 | 0 | 193 |
| Hard | 0 | 0 | 0 | 0 | 122 |
| Insane | 0 | 0 | 0 | 0 | 68 |

## Speed (solved boxes only)

- n = 50
- median 11.6 min
- p90 21.3 min
- max 22.1 min
- took >12 min: 24 of 50
- time spent on non-solves: 157 min across 10 boxes

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
| 356 | Explore | Easy | partial:user-only | timeout after 20m |
| 678 | VulnEscape | Easy | timeout | timeout after 20m |
| 668 | Artificial | Easy | timeout | timeout after 20m |
