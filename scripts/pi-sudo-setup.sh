#!/usr/bin/env bash
# scripts/pi-sudo-setup.sh
#
# One-time setup on a fresh Raspberry Pi: passwordless sudo for commands ieOS uses
# (USB mount/umount/blkid, system time via timedatectl). Run from repo root:
#
#   sudo bash scripts/pi-sudo-setup.sh
#   sudo bash scripts/pi-sudo-setup.sh --user pi
#
# Requires root. Creates /etc/sudoers.d/ieos and /mnt/usb0.

set -euo pipefail

SUDOERS_FILE="/etc/sudoers.d/ieos"
MOUNT_POINT="/mnt/usb0"
TARGET_USER="${TARGET_USER:-}"

usage() {
    echo "Usage: sudo $0 [--user LOGIN]"
    echo "  Installs ${SUDOERS_FILE} for ieOS (NOPASSWD for timedatectl, blkid, mount, umount)."
    echo "  Default user: the account that invoked sudo (SUDO_USER), or ${USER}, or pi."
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --user)
            TARGET_USER="${2:?}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ "${EUID:-0}" -ne 0 ]]; then
    echo "Run as root, e.g.: sudo $0" >&2
    exit 1
fi

if [[ -z "${TARGET_USER}" ]]; then
    if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
        TARGET_USER="${SUDO_USER}"
    elif [[ -n "${USER:-}" && "${USER}" != "root" ]]; then
        TARGET_USER="${USER}"
    elif id -u pi &>/dev/null; then
        TARGET_USER="pi"
    else
        echo "Cannot infer login user (e.g. root shell). Use: sudo $0 --user YOUR_LOGIN" >&2
        exit 1
    fi
fi

if ! id -u "${TARGET_USER}" &>/dev/null; then
    echo "User does not exist: ${TARGET_USER}" >&2
    exit 1
fi

for bin in timedatectl blkid mount umount; do
    if ! command -v "${bin}" &>/dev/null; then
        echo "Required command not found: ${bin} (install systemd-utils / util-linux)" >&2
        exit 1
    fi
done

TIMEDATECTL="$(command -v timedatectl)"
BLKID="$(command -v blkid)"
MOUNT="$(command -v mount)"
UMOUNT="$(command -v umount)"

TMP="$(mktemp)"
trap 'rm -f "${TMP}"' EXIT

# Mount options must match gui/utils/usb/USBDriveManager.py (vfat/exfat branch).
# Sudoers treats commas as command separators unless escaped with backslash.
VFAT_OPTS_SUDOERS='uid=1000\,gid=1000\,fmask=0022\,dmask=0022'

cat >"${TMP}" <<EOF
# ieOS — passwordless sudo for USB + clock (installed by scripts/pi-sudo-setup.sh)
# Remove: sudo rm ${SUDOERS_FILE}

Defaults:${TARGET_USER} !requiretty

${TARGET_USER} ALL=(root) NOPASSWD: ${TIMEDATECTL} set-ntp false
${TARGET_USER} ALL=(root) NOPASSWD: ${TIMEDATECTL} set-time *

${TARGET_USER} ALL=(root) NOPASSWD: ${BLKID} -o value -s TYPE /dev/sd*
${TARGET_USER} ALL=(root) NOPASSWD: ${MOUNT} -o ${VFAT_OPTS_SUDOERS} /dev/sd* ${MOUNT_POINT}
${TARGET_USER} ALL=(root) NOPASSWD: ${MOUNT} /dev/sd* ${MOUNT_POINT}

# udisks may mount the same device elsewhere; allow unmount by path (any args).
${TARGET_USER} ALL=(root) NOPASSWD: ${UMOUNT}
EOF

if ! visudo -c -f "${TMP}"; then
    echo "Generated sudoers fragment failed visudo check." >&2
    exit 1
fi

install -m 0440 -o root -g root "${TMP}" "${SUDOERS_FILE}"
echo "Installed ${SUDOERS_FILE}"

if ! visudo -c; then
    echo "WARNING: global sudoers check reported an error; inspect /etc/sudoers.d/" >&2
fi

# App calls os.makedirs(/mnt/usb0); that requires the directory to exist (root-owned parent).
if [[ ! -d "${MOUNT_POINT}" ]]; then
    install -d -m 0755 -o root -g root "${MOUNT_POINT}"
    echo "Created ${MOUNT_POINT}"
else
    echo "${MOUNT_POINT} already exists"
fi

echo "Done. User ${TARGET_USER} can run timedatectl/mount/umount/blkid without a password."
echo "Log out and back in if your session cached sudo credentials."
