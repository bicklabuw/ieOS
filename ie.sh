#!/usr/bin/env bash
# ie.sh — launch ieOS (stderr appended to log; paths work for any login)

set -euo pipefail

# Repo root: this script’s directory by default, or set IEOS before running.
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
IEOS="${IEOS:-$_SCRIPT_DIR}"
cd "$IEOS" || exit 1

# Log under the invoking user’s home (cron sets HOME correctly for that user).
LOG_FILE="${IEOS_LOG:-$HOME/log.txt}"

if ! "$IEOS/.venv/bin/python3" -m ieos.ieOSMain 2> >(tee -a "$LOG_FILE"); then
  echo "ie.sh: an error occurred" | tee -a "$LOG_FILE" >&2
  exit 1
fi
