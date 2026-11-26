#!/usr/bin/env bash
# Vendor the reference HTB client we read endpoint shapes from.
#
# Everything we learn about the HTB API comes from one of two places: a live
# probe, or this checkout. Keeping it in .work/vendor means the evidence behind
# .agents/skills/hackthebox/references/endpoints.md is local and re-readable,
# instead of a /tmp directory that vanishes between sessions.
#
#   ./scripts/vendor.sh            # clone if absent
#   ./scripts/vendor.sh --update   # fetch latest, report the new commit
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$REPO/.work/vendor/htb-cli"
UPSTREAM="https://github.com/GoToolSharing/htb-cli"

if [ -d "$DEST/.git" ]; then
  if [ "${1:-}" = "--update" ]; then
    git -C "$DEST" fetch -q --depth 1 origin
    git -C "$DEST" reset -q --hard origin/HEAD
  fi
else
  mkdir -p "$(dirname "$DEST")"
  git clone -q --depth 1 "$UPSTREAM" "$DEST"
fi

sha="$(git -C "$DEST" rev-parse --short HEAD)"
echo "htb-cli at $sha ($DEST)"

# The two files the endpoint record cites; fail loudly if they move.
for f in cmd/machines.go lib/utils/utils.go lib/submit/submit.go config/config.go; do
  [ -f "$DEST/$f" ] || { echo "MISSING: $f -- references/endpoints.md cites it" >&2; exit 1; }
done
echo "cited files present: cmd/machines.go, lib/utils/utils.go, lib/submit/submit.go, config/config.go"
