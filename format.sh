#!/bin/bash

# Usage: ./format.sh /dev/sdX [-y|--yes]

DEVICE="$1"
AUTO_YES=false

# Check for auto-yes flag
if [[ "$2" == "-y" || "$2" == "--yes" ]]; then
    AUTO_YES=true
fi

# Ensure device path is provided
if [[ -z "$DEVICE" ]]; then
    echo "Usage: $0 /dev/sdX [-y|--yes]"
    exit 1
fi

# Confirm before proceeding unless auto-yes is set
if [ "$AUTO_YES" = false ]; then
    echo "WARNING: This will completely erase $DEVICE"
    read -rp "Are you sure you want to continue? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Unmount all partitions of the device
echo "Unmounting partitions on $DEVICE..."
for part in $(ls ${DEVICE}?* 2>/dev/null); do
    sudo umount "$part" 2>/dev/null || true
done

# Wipe partition table
echo "Wiping partition table..."
sudo wipefs -a "$DEVICE"

# Create a single FAT32 partition
echo "Creating new FAT32 partition..."
sudo parted -s "$DEVICE" mklabel msdos
sudo parted -s "$DEVICE" mkpart primary fat32 1MiB 100%
sudo mkfs.vfat -F 32 "${DEVICE}1"

# Wait for kernel to register the new partition
sudo partprobe "$DEVICE"
sudo udevadm settle

# Set the label
echo "Setting label to 'Pendrive'..."
sudo fatlabel "${DEVICE}1" Pendrive

# Mount the new partition
MOUNT_POINT="/mnt/pendrive"
sudo mkdir -p "$MOUNT_POINT"
sudo mount "${DEVICE}1" "$MOUNT_POINT"

# Create the WAV directory
echo "Creating 'WAV' folder..."
sudo mkdir -p "$MOUNT_POINT/WAV"


# Sync and unmount
echo "Syncing and Unmounting"
sudo sync
sudo umount "$MOUNT_POINT"
sudo rmdir "$MOUNT_POINT"

# Eject
echo "Ejecting device..."
sudo eject "$DEVICE"

echo "Done. '$DEVICE' has been formatted and labeled 'Pendrive'."

