#!/usr/bin/env bash
# Is ARTEX running AND capturing? Check, and optionally fix.
#
#   ./artex-status.sh                 # check only, exit 1 on any problem
#   ./artex-status.sh --fix           # start/repair, then assert capture
#   ./artex-status.sh --fix --reset-llm-profiles
#
# Read-only by default: --fix is the only mode that mutates anything.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO" || exit 1

ARTEX_URL="${ARTEX_URL:-http://127.0.0.1:8787}"
COLLECTOR_URL="${COLLECTOR_URL:-http://127.0.0.1:4000}"
FIX=0
RESET_PROFILES=0

for arg in "$@"; do
  case "$arg" in
    --fix) FIX=1 ;;
    --reset-llm-profiles) RESET_PROFILES=1; FIX=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

pass() { printf '  \033[32mPASS\033[0m %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$*"; FAILED=1; }
warn() { printf '  \033[33mWARN\033[0m %s\n' "$*"; }
FAILED=0

env_get() { grep -E "^$1=" .env 2>/dev/null | head -1 | cut -d= -f2-; }

echo "== ARTEX (${ARTEX_URL})"
health="$(curl -s --max-time 5 "${ARTEX_URL}/api/health" || true)"
if [ -z "$health" ]; then
  fail "no response — not running"
else
  pass "responds: $(echo "$health" | head -c 80)"
  iso="$(echo "$health" | python3 -c 'import sys,json;d=json.load(sys.stdin);print((d.get("isolation") or {}).get("mode","absent"))' 2>/dev/null || echo absent)"
  case "$iso" in
    degraded) fail "isolation=degraded: the agent can read its own secrets. Check -exec-uid and the self-test." ;;
    absent)   warn "isolation not reported (normal: the pinned build predates the self-test)" ;;
    *)        pass "isolation=${iso}" ;;
  esac
fi

echo "== collector (${COLLECTOR_URL})"
chealth="$(curl -s --max-time 5 "${COLLECTOR_URL}/api/health" || true)"
if [ -z "$chealth" ]; then
  fail "no response — collector not running (blobs are NOT being written)"
else
  pass "responds: $(echo "$chealth" | head -c 100)"
  dropped="$(curl -s --max-time 5 "${COLLECTOR_URL}/metrics" | awk '/^collector_dropped_total/{print $2}')"
  case "${dropped:-0}" in
    0) pass "dropped=0" ;;
    *) fail "dropped=${dropped}: blobs were lost. Check ARTEX_GYM_QUEUE_MAX and disk." ;;
  esac
fi

echo "== capture settings (database rows, not env)"
# Always authenticate: /api/health hides "isolation" from an anonymous caller,
# and the capture flags are only readable with a token. Login is read-only, so
# this does not make the default mode a mutating one.
token=""
pw="$(env_get ARTEX_GYM_ADMIN_PASSWORD)"; pw="${pw:-password1234}"
token="$(curl -s --max-time 10 -X POST "${ARTEX_URL}/api/auth/login" \
  -H 'content-type: application/json' \
  -d "$(python3 -c 'import json,sys;print(json.dumps({"username":"ARTEX","password":sys.argv[1]}))' "$pw")" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin).get("token",""))' 2>/dev/null)"
if [ -n "$token" ]; then
  pass "logged in as ARTEX"
  # Re-read health WITH the token: isolation is only reported to a signed-in caller.
  health="$(curl -s --max-time 5 "${ARTEX_URL}/api/health" -H "Authorization: Bearer ${token}" || true)"
  iso="$(echo "$health" | python3 -c 'import sys,json;print((json.load(sys.stdin).get("isolation") or {}).get("mode","absent"))' 2>/dev/null || echo absent)"
  case "$iso" in
    degraded) fail "isolation=degraded: the agent can read its own secrets" ;;
    absent)   warn "isolation not reported (normal: the pinned build predates the self-test)" ;;
    *)        pass "isolation=${iso}" ;;
  esac
else
  fail "login failed (username is ARTEX, password >=12 chars when first set)"
fi

if [ -n "$token" ]; then
  settings="$(curl -s --max-time 10 "${ARTEX_URL}/api/settings" -H "Authorization: Bearer ${token}")"
  capture="$(echo "$settings" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("traffic_capture"))' 2>/dev/null)"
  if [ "$FIX" = "1" ] && [ "$capture" != "True" ] && [ "$capture" != "true" ]; then
    curl -s --max-time 10 -X PUT "${ARTEX_URL}/api/settings" -H "Authorization: Bearer ${token}" \
      -H 'content-type: application/json' -d '{"traffic_capture": true}' >/dev/null
    capture="$(curl -s --max-time 10 "${ARTEX_URL}/api/settings" -H "Authorization: Bearer ${token}" \
      | python3 -c 'import sys,json;print(json.load(sys.stdin).get("traffic_capture"))' 2>/dev/null)"
    pass "traffic_capture turned on"
  fi
  case "$capture" in
    True|true) pass "traffic_capture=on" ;;
    *) fail "traffic_capture=${capture:-unknown}: agents get no proxy, nothing is recorded" ;;
  esac

  base="$(curl -s --max-time 10 "${ARTEX_URL}/api/llm" -H "Authorization: Bearer ${token}" \
    | python3 -c 'import sys,json;print(json.load(sys.stdin).get("base_url",""))' 2>/dev/null)"
  case "$base" in
    *llm-logger*) pass "LLM base_url=${base}" ;;
    "") fail "no LLM base_url: the engine is idle" ;;
    *) fail "LLM base_url=${base} — not the collector, so calls bypass capture. A saved profile is winning." ;
       [ "$RESET_PROFILES" = "1" ] && echo "       (--reset-llm-profiles requested: run: artexctl up --reset-llm-profiles)" ;;
  esac
else
  warn "skipping capture checks (no token; re-run with --fix to log in)"
fi

if [ "$FIX" = "1" ] && [ "$FAILED" != "0" ]; then
  echo "== starting the stack"
  fd=""
  [ "$RESET_PROFILES" = "1" ] && fd="--reset-llm-profiles"
  .venv/bin/artexctl up $fd || fail "artexctl up failed"
fi

echo
[ "$FAILED" = "0" ] && echo "OK: ARTEX is running with capture enabled" || echo "PROBLEMS: see FAIL lines above"
exit "$FAILED"
