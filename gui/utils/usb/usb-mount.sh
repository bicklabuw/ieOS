#!/bin/bash

# Auto-mount/unmount USB drives with write access for pi user (uid/gid 1000)
# Triggered by udev: /usr/local/bin/usb-mount.sh [remove] <kernel_device>

MOUNT_BASE="/mnt"
UID_GID="uid=1000,gid=1000"

if [ "$1" = "remove" ]; then
    DEV="/dev/$2"
    MOUNT_POINT=$(grep "^$DEV " /proc/mounts | awk '{print $2}')
    if [ -n "$MOUNT_POINT" ]; then
        umount "$MOUNT_POINT"
        rmdir "$MOUNT_POINT"
    fi
    exit 0
fi

DEV="/dev/$1"
FSTYPE=$(blkid -o value -s TYPE "$DEV" 2>/dev/null)

[ -z "$FSTYPE" ] && exit 0

# Find an available mount point (usb0, usb1, ...)
i=0
while [ -d "$MOUNT_BASE/usb$i" ]; do
    i=$((i + 1))
done
MOUNT_POINT="$MOUNT_BASE/usb$i"
mkdir -p "$MOUNT_POINT"

case "$FSTYPE" in
    vfat|fat32|exfat)
        mount -o "$UID_GID,fmask=0022,dmask=0022" "$DEV" "$MOUNT_POINT"
        ;;
    *)
        mount "$DEV" "$MOUNT_POINT"
        ;;
esac
