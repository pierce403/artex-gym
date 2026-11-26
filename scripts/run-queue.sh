#!/usr/bin/env bash
# Run the queue to exhaustion, one box at a time.
#
#   ./scripts/run-queue.sh                 # all pending, easiest first
#   ./scripts/run-queue.sh --tier Easy     # only one tier
#   ./scripts/run-queue.sh --max 5         # stop after N boxes
#   ./scripts/run-queue.sh --budget 20     # minutes per box
#
# Each box goes through scripts/run-box.py, which spawns, runs ARTeX, submits,
# verifies, terminates, writes notes and commits+pushes. This loop only decides
# *which* box is next and guarantees the loop survives a single bad box.
#
# Design notes:
#   - `--next` re-reads notes/queue.json every iteration, so a solved box is
#     never retried and the queue file is the source of truth (restartable).
#   - A failure in one box does not stop the run: run-box.py records the state
#     and moves on. Only three consecutive *spawn* failures stop the loop, which
#     is the "tunnel is down" signal from the goal's blocker rule.
#   - After every box the collector's dropped counter is checked; capture loss is
#     silent otherwise.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1

BUDGET=20
TIER=""
MAX_BOXES=0
LOGDIR=".work/logs"
RUNLOG="$LOGDIR/queue-run.log"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --budget) BUDGET="$2"; shift 2 ;;
    --tier)   TIER="$2"; shift 2 ;;
    --max)    MAX_BOXES="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$LOGDIR"
say() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$RUNLOG"; }

next_box() {
  python3 - "$TIER" <<'PY'
import json, sys
tier = sys.argv[1]
q = json.load(open("notes/queue.json"))
pending = [b for b in q["boxes"] if b["state"] == "pending"]
if tier:
    pending = [b for b in pending if b["tier"] == tier]
if pending:
    b = pending[0]
    print(f'{b["id"]}\t{b["name"]}\t{b["tier"]}')
PY
}

count_pending() {
  python3 - "$TIER" <<'PY'
import json, sys
tier = sys.argv[1]
q = json.load(open("notes/queue.json"))
p = [b for b in q["boxes"] if b["state"] == "pending" and (not tier or b["tier"] == tier)]
print(len(p))
PY
}

dropped() {
  curl -s --max-time 5 http://127.0.0.1:4000/metrics 2>/dev/null \
    | awk '/^collector_dropped_total/{print $2}' || echo "?"
}

say "queue run start: budget=${BUDGET}m tier=${TIER:-all} max=${MAX_BOXES:-unlimited} pending=$(count_pending)"
consecutive_spawn_failures=0
done_count=0

while :; do
  if [ "$MAX_BOXES" -gt 0 ] && [ "$done_count" -ge "$MAX_BOXES" ]; then
    say "reached --max $MAX_BOXES; stopping"
    break
  fi

  line="$(next_box)"
  if [ -z "$line" ]; then
    say "no pending boxes${TIER:+ in tier $TIER}; done"
    break
  fi
  id="$(printf '%s' "$line" | cut -f1)"
  name="$(printf '%s' "$line" | cut -f2)"
  tier="$(printf '%s' "$line" | cut -f3)"

  say "---- box $id ($name, $tier) ; pending=$(count_pending) ; dropped=$(dropped)"

  out="$LOGDIR/box-$id.log"
  ./scripts/run-box.py "$id" --budget "$BUDGET" >> "$out" 2>&1
  rc=$?
  state="$(python3 -c "
import json
q=json.load(open('notes/queue.json'))
print(next(b['state'] for b in q['boxes'] if b['id']==$id))")"

  say "box $id -> $state (exit $rc) ; dropped=$(dropped)"
  done_count=$((done_count+1))

  case "$state" in
    skipped:no-spawn) consecutive_spawn_failures=$((consecutive_spawn_failures+1)) ;;
    *)                consecutive_spawn_failures=0 ;;
  esac
  if [ "$consecutive_spawn_failures" -ge 3 ]; then
    say "3 consecutive spawn failures; the tunnel or the slot is broken. stopping."
    break
  fi

  # Capture is fail-open by design, so a non-zero drop counter is the only
  # signal that blobs were lost. Report it loudly rather than hiding it.
  d="$(dropped)"
  if [ "$d" != "0" ] && [ "$d" != "?" ]; then
    say "WARNING: collector_dropped_total=$d -- capture loss on this run"
  fi
done

say "queue run end: processed=$done_count pending=$(count_pending) dropped=$(dropped)"
