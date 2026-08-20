#!/usr/bin/env bash
# scripts/pi-bootstrap.sh
#
# Fresh Raspberry Pi: install apt deps, create .venv, pip install -e ".[rpi]".
# Run as a normal user (not root) from the repo after git clone.
#
#   cd ~/ieos && bash scripts/pi-bootstrap.sh
#   IEOS=/opt/ieos bash scripts/pi-bootstrap.sh
#
# Next: sudo bash scripts/pi-sudo-setup.sh

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
IEOS="${IEOS:-$(cd "${_SCRIPT_DIR}/.." && pwd)}"
cd "$IEOS" || exit 1

usage() {
    echo "Usage: bash scripts/pi-bootstrap.sh"
    echo "  Installs Python deps under ${IEOS}/.venv (editable install with [rpi] extras)."
    echo "  Run from repo root or set IEOS to the repository root directory."
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ "${EUID:-0}" -eq 0 ]]; then
    echo "Do not run as root. Use your login user so ~/.venv ownership is correct." >&2
    echo "Example: cd ~/ieos && bash scripts/pi-bootstrap.sh" >&2
    exit 1
fi

if [[ ! -f "${IEOS}/pyproject.toml" ]]; then
    echo "Expected pyproject.toml in ${IEOS}; set IEOS to the ieos repo root." >&2
    exit 1
fi

spi_warning() {
    local status=""
    if command -v raspi-config &>/dev/null; then
        status="$(raspi-config nonint get_spi 2>/dev/null || true)"
    fi
    if [[ "$status" == "1" ]]; then
        echo "WARNING: SPI appears disabled (raspi-config). Enable: sudo raspi-config → Interface Options → SPI → Yes, then reboot." >&2
        return
    fi
    local f
    for f in /boot/firmware/config.txt /boot/config.txt; do
        if [[ -f "$f" ]] && grep -qE '^[[:space:]]*dtparam=spi=off' "$f" 2>/dev/null; then
            echo "WARNING: SPI may be off (${f} has dtparam=spi=off). Enable SPI and reboot if the OLED does not work." >&2
            return
        fi
    done
}

spi_warning

echo "Installing system packages (apt)..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git

if [[ ! -d "${IEOS}/.venv" ]]; then
    echo "Creating virtual environment at ${IEOS}/.venv ..."
    python3 -m venv "${IEOS}/.venv"
else
    echo "Using existing ${IEOS}/.venv"
fi

# shellcheck source=/dev/null
source "${IEOS}/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e ".[rpi]"

if [[ -f "${IEOS}/ie.sh" ]]; then
    chmod +x "${IEOS}/ie.sh" 2>/dev/null || true
fi

echo ""
echo "Python install finished."
echo "Next steps:"
echo "  1. sudo bash scripts/pi-sudo-setup.sh"
echo "     (passwordless sudo for USB mount/time; optional @reboot cron for ./ie.sh)"
echo "  2. If you enabled SPI or changed boot config: reboot"
echo "  3. From repo root: ./ie.sh   (or wait for cron after reboot)"
echo ""
echo "If pip fails building sounddevice, try: sudo apt-get install -y portaudio19-dev && re-run this script."
