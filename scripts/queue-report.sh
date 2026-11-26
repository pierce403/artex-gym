#!/usr/bin/env bash
# Regenerate notes/report-queue.md from the queue file and the run log.
# Cheap, idempotent, and the only place the tally is computed.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
python3 - <<'PY'
import json, re, datetime, statistics
from collections import Counter, defaultdict
from pathlib import Path

q = json.load(open("notes/queue.json"))
boxes = q["boxes"]
c = Counter(b["state"] for b in boxes)

# Durations, from the run log (one line per box start/finish).
starts, durs = {}, []
log = Path(".work/logs/queue-run.log")
if log.exists():
    for ln in log.read_text().splitlines():
        m = re.match(r"\[([^\]]+)\] ---- box (\d+) \((\w+)", ln)
        if m:
            starts[m.group(2)] = (datetime.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ"), m.group(3))
            continue
        m = re.match(r"\[([^\]]+)\] box (\d+) -> (\S+)", ln)
        if m and m.group(2) in starts:
            t, tier = starts[m.group(2)]
            end = datetime.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ")
            durs.append(((end - t).total_seconds() / 60, m.group(2), m.group(3), tier))

solved = [d for d in durs if d[2] == "solved"]
by_tier = defaultdict(lambda: Counter())
for b in boxes:
    by_tier[b["tier"]][b["state"]] += 1

out = ["# Box queue — progress report", "",
       f"Generated from `notes/queue.json` ({len(boxes)} retired boxes) and `.work/logs/queue-run.log`.", "",
       "## Totals", "",
       f"- solved **{c['solved']}**",
       f"- timeout {c['timeout']}",
       f"- skipped (no spawn) {c['skipped:no-spawn']}",
       f"- partial (user only) {c['partial:user-only']}",
       f"- pending {c['pending']}", "",
       "## By tier", "",
       "| tier | solved | timeout | skipped | partial | pending |", "|---|---|---|---|---|---|"]
for tier in ("Easy", "Medium", "Hard", "Insane", "Unknown"):
    if tier not in by_tier:
        continue
    t = by_tier[tier]
    out.append(f"| {tier} | {t['solved']} | {t['timeout']} | {t['skipped:no-spawn']} | "
               f"{t['partial:user-only']} | {t['pending']} |")

if solved:
    mins = sorted(d[0] for d in solved)
    out += ["", "## Speed (solved boxes only)", "",
            f"- n = {len(mins)}",
            f"- median {statistics.median(mins):.1f} min",
            f"- p90 {mins[int(len(mins) * 0.9)]:.1f} min",
            f"- max {max(mins):.1f} min",
            f"- took >12 min: {sum(1 for m in mins if m > 12)} of {len(mins)}"]
    waste = sum(d[0] for d in durs if d[2] != "solved")
    out.append(f"- time spent on non-solves: {waste:.0f} min across {len(durs) - len(solved)} boxes")

fails = [b for b in boxes if b["state"] not in ("solved", "pending")]
if fails:
    out += ["", "## Not solved", "", "| id | name | tier | state | note |", "|---|---|---|---|---|"]
    for b in fails:
        out.append(f"| {b['id']} | {b['name']} | {b['tier']} | {b['state']} | {b['note'][:60]} |")

Path("notes/report-queue.md").write_text("\n".join(out) + "\n")
print(f"wrote notes/report-queue.md ({len(boxes)} boxes, {c['solved']} solved)")
PY
