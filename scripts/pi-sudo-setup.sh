#!/usr/bin/env bash
# scripts/pi-sudo-setup.sh
#
# One-time setup on a fresh Raspberry Pi: passwordless sudo for commands ieOS uses
# (USB mount/umount/blkid, system time via timedatectl), /mnt/usb0, and an @reboot
# crontab for ie.sh (sleep before launch so the OLED comes up reliably).
#
#   sudo bash scripts/pi-sudo-setup.sh
#   sudo bash scripts/pi-sudo-setup.sh --user pi
#   sudo IEOS_ROOT=/opt/ieos bash scripts/pi-sudo-setup.sh --no-cron
#
# Requires root. Creates /etc/sudoers.d/ieos and /mnt/usb0.

set -euo pipefail

SUDOERS_FILE="/etc/sudoers.d/ieos"
MOUNT_POINT="/mnt/usb0"
TARGET_USER="${TARGET_USER:-}"
IEOS_ROOT_OVERRIDE=""
NO_CRON=0
# Delay before ie.sh at boot (display init); override: REBOOT_SLEEP_SEC=15 sudo ...
REBOOT_SLEEP_SEC="${REBOOT_SLEEP_SEC:-10}"

usage() {
    echo "Usage: sudo $0 [--user LOGIN] [--ieos-root DIR] [--no-cron]"
    echo "  Installs ${SUDOERS_FILE} for ieOS (NOPASSWD for timedatectl, blkid, mount, umount)."
    echo "  Adds @reboot sleep+ie.sh to ${TARGET_USER:-USER}'s crontab unless --no-cron."
    echo "  Repo path defaults to TARGET_USER's home/ieos from passwd (override: --ieos-root or IEOS_ROOT)."
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --user)
            TARGET_USER="${2:?}"
            shift 2
            ;;
        --ieos-root)
            IEOS_ROOT_OVERRIDE="${2:?}"
            shift 2
            ;;
        --no-cron)
            NO_CRON=1
            shift
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

# Resolve repo path: explicit --ieos-root / env IEOS_ROOT, else ~TARGET_USER/ieos via passwd (not hardcoded /home/pi).
if [[ -n "${IEOS_ROOT_OVERRIDE}" ]]; then
    IEOS_ROOT="${IEOS_ROOT_OVERRIDE}"
elif [[ -n "${IEOS_ROOT:-}" ]]; then
    :
else
    TARGET_HOME="$(getent passwd "${TARGET_USER}" | cut -d: -f6)"
    if [[ -z "${TARGET_HOME}" || ! -d "${TARGET_HOME}" ]]; then
        echo "Could not resolve home directory for ${TARGET_USER}; set IEOS_ROOT or use --ieos-root DIR." >&2
        exit 1
    fi
    IEOS_ROOT="${TARGET_HOME}/ieos"
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
# uid/gid 1000 = typical first user on Raspberry Pi OS; must match Python mount -o there.
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

if [[ "${NO_CRON}" -eq 0 ]]; then
    CRON_MARKER="# ieOS reboot launch (scripts/pi-sudo-setup.sh)"
    IE_SH="${IEOS_ROOT}/ie.sh"
    if [[ ! -f "${IE_SH}" ]]; then
        echo "WARNING: ${IE_SH} not found; skipping crontab @reboot (clone repo to ${IEOS_ROOT} or use --ieos-root)." >&2
    elif [[ ! -x "${IE_SH}" ]]; then
        echo "WARNING: ${IE_SH} is not executable (chmod +x); skipping crontab @reboot." >&2
    elif crontab -u "${TARGET_USER}" -l 2>/dev/null | grep -qF "${CRON_MARKER}"; then
        echo "Crontab @reboot entry already present for ${TARGET_USER}; skipping."
    else
        CRON_LINE="@reboot /bin/sleep ${REBOOT_SLEEP_SEC} && ${IE_SH}"
        (
            { crontab -u "${TARGET_USER}" -l 2>/dev/null || true; } \
                | grep -vF "${CRON_MARKER}" \
                | grep -vF "@reboot /bin/sleep ${REBOOT_SLEEP_SEC} && ${IE_SH}" \
                || true
            printf '%s\n%s\n' "${CRON_MARKER}" "${CRON_LINE}"
        ) | crontab -u "${TARGET_USER}" -
        echo "Installed @reboot crontab for ${TARGET_USER}: sleep ${REBOOT_SLEEP_SEC}s then ${IE_SH}"
    fi
else
    echo "Skipping crontab (--no-cron)."
fi

echo "Done. User ${TARGET_USER} can run timedatectl/mount/umount/blkid without a password."
echo "Log out and back in if your session cached sudo credentials."
