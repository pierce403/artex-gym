#!/usr/bin/env bash
# One-line-per-fact status for the queue run. Cheap enough to call often.
cd "$(dirname "$0")/.." || exit 1
python3 - <<'PY'
import json
from collections import Counter
q = json.load(open("notes/queue.json"))
c = Counter(b["state"] for b in q["boxes"])
easy = sum(1 for b in q["boxes"] if b["state"] == "pending" and b["tier"] == "Easy")
print(f"solved={c['solved']} timeout={c['timeout']} skipped={c['skipped:no-spawn']} "
      f"pending={c['pending']} easy_left={easy}")
PY
tail -1 "$(ls -t .work/logs/box-*.log | head -1)" 2>/dev/null | sed 's/^/current: /'
