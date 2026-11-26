# Resuming the box run

The loop is autonomous; this file is what a fresh context needs.

## Is it running?

    tmux ls                                  # session "htb"
    tmux capture-pane -pt htb -S -20         # live output
    ./scripts/queue-status.sh                 # one-line tally + current box

## Current state

- Queue: `notes/queue.json` (543 retired boxes, difficulty-ordered). It is the
  source of truth — `state` per box is `solved` / `timeout` /
  `skipped:no-spawn` / `partial:user-only` / `pending`.
- Every box: one commit, pushed. `git log --oneline` is the run history.
- Capture: `curl -s localhost:4000/metrics | grep dropped` must read 0.

## Restart it (after a reboot or a crash)

    ./scripts/box-tools.sh                     # re-install nmap/ike-scan/smbclient/impacket
    tmux new-session -d -s htb -c "$PWD" './scripts/run-queue.sh --tier Easy --budget 20'

`run-queue.sh` re-reads the queue each iteration, so it resumes where it stopped
and never retries a solved box. Swap `--tier` for Medium/Hard/Insane, or drop it
for all pending in difficulty order.

## Budget is 20 minutes, and that is measured, not guessed

Of the first 40 solves: median 11.3m, p90 21.3m, and **18 of 40 solved boxes
needed more than 12 minutes** (Antique 22.1m, UnderPass 21.8m, Dog 21.4m).
A 12-minute cap would have discarded ~45% of the wins to save 92 minutes of
timeout waste. Do not lower it without re-measuring.

## Known failure modes

- `skipped:no-spawn` ("no IP appeared within 120s"). Three consecutive stops
  the loop on purpose. In practice (2026-11-26 22:11) this was **transient**:
  a manual spawn two minutes later succeeded, so the slot was still releasing
  after a timeout. Recovery: reset the skipped boxes to pending, then restart:
  `python3 -c "import json;p='notes/queue.json';q=json.load(open(p));[b.update(state='pending',note='') for b in q['boxes'] if b['state']=='skipped:no-spawn'];json.dump(q,open(p,'w'),indent=1,sort_keys=True)"`
- `timeout` — 20 minutes elapsed. Left as-is; a re-attempt costs another 20m.
- `partial:user-only` — user flag accepted, root not. Worth a manual re-run.
- The reset one-liner above is the documented procedure; it was used once.
  Restart with the same `tmux new-session` line; the loop resumes from pending.
