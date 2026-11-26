#!/usr/bin/env bash
# Install the pentest tooling the boxes actually need, into the running ARTEX
# container. Idempotent; safe to re-run.
#
# Why this exists: the image ships nmap/ffuf and little else. During the first
# run, Boxes needing SMB (37 of 153 Easy boxes are Windows) had no smbclient at
# all, and the IPsec box had no ike-scan -- both were installed by hand, which
# means a `docker compose up --build` silently loses them and the next box times
# out for a reason that is not the box's fault.
#
#   ./scripts/box-tools.sh            # install
#   ./scripts/box-tools.sh --check    # report only, exit 1 if anything missing
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1

ARTEX_SOURCE="${ARTEX_GYM_ARTEX_SOURCE:-$HOME/projects/ARTEX}"
COMPOSE=(docker compose -p artex-gym --project-directory "$REPO" --env-file "$REPO/.env"
         -f "$ARTEX_SOURCE/docker-compose.yml" -f "$REPO/compose/overlay.yml")

# name -> probe command. Keep probes cheap and free of network calls.
TOOLS=(
  "nmap:nmap --version"
  "ffuf:ffuf -V"
  "ike-scan:ike-scan --version"
  "psk-crack:psk-crack -h"
  "tshark:tshark --version"
  "tcpdump:tcpdump --version"
  "smbclient:smbclient --version"
  "smbmap:smbmap --help"
  "wmiexec.py:wmiexec.py -h"
  "secretsdump.py:secretsdump.py -h"
  "gcc:gcc --version"
  "paramiko:python3 -c 'import paramiko'"
)

missing=()
for entry in "${TOOLS[@]}"; do
  name="${entry%%:*}"; probe="${entry#*:}"
  if ! "${COMPOSE[@]}" exec -T artex sh -c "$probe" >/dev/null 2>&1; then
    missing+=("$name")
  fi
done

if [ "${1:-}" = "--check" ]; then
  if [ "${#missing[@]}" -eq 0 ]; then
    echo "all tools present"
    exit 0
  fi
  echo "missing: ${missing[*]}"
  exit 1
fi

echo "present: $(( ${#TOOLS[@]} - ${#missing[@]} ))/${#TOOLS[@]}"
if [ "${#missing[@]}" -eq 0 ]; then
  echo "nothing to install"
  exit 0
fi
echo "installing (missing: ${missing[*]})"

# apt covers the C tools; pip covers impacket (wmiexec/secretsdump/smbclient.py).
"${COMPOSE[@]}" exec -T artex sh -c '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq \
    ike-scan strongswan tshark tcpdump \
    smbclient smbmap \
    gcc make libssl-dev >/dev/null
  pip install --quiet --no-input impacket >/dev/null 2>&1 || pip install --quiet --break-system-packages impacket
  echo installed
' || { echo "install failed" >&2; exit 1; }

echo "re-checking"
"$0" --check
