import os
import subprocess

_DEFAULT_MOUNT_POINT = "/mnt/usb0"
PENDRIVE_RECORDINGS_DIR = "/WAV"

# Set by mount_pendrive(), cleared by unmount_pendrive()
_active_mount_point: str | None = None


def _find_usb_block_device() -> str | None:
    """Return the device path (e.g. /dev/sda1) of the first USB block device, mounted or not."""
    try:
        block_devs = sorted(os.listdir('/sys/block'))
    except OSError:
        return None

    for dev in block_devs:
        if not dev.startswith('sd'):
            continue
        try:
            real_path = os.path.realpath(f'/sys/block/{dev}')
            if 'usb' not in real_path:
                continue
        except OSError:
            continue

        try:
            partitions = sorted([
                p for p in os.listdir(f'/sys/block/{dev}')
                if p.startswith(dev)
            ])
        except OSError:
            partitions = []

        if partitions:
            return f'/dev/{partitions[0]}'
        return f'/dev/{dev}'

    return None


def _get_mount_point(device: str) -> str | None:
    """Return the current mount point of device, or None if not mounted."""
    try:
        with open('/proc/mounts') as f:
            for line in f:
                parts = line.split()
                if parts and parts[0] == device:
                    return parts[1]
    except OSError:
        pass
    return None


def get_recordings_path() -> str:
    """Return the path to the recordings directory on the mounted USB drive."""
    if _active_mount_point is None:
        raise OSError("USB drive not mounted")
    return _active_mount_point + PENDRIVE_RECORDINGS_DIR


def mount_pendrive() -> None:
    """
    Mount the USB drive. If already mounted (e.g. by udisks2), uses the existing
    mount point. Raises OSError if no USB drive is found or mount fails.
    """
    global _active_mount_point

    device = _find_usb_block_device()
    if not device:
        raise OSError("No USB drive found")

    # Already mounted somewhere (e.g. udisks2 auto-mounted it)
    existing = _get_mount_point(device)
    if existing:
        _active_mount_point = existing
        return

    # Mount it ourselves
    os.makedirs(_DEFAULT_MOUNT_POINT, exist_ok=True)

    fstype_result = subprocess.run(
        ['sudo', 'blkid', '-o', 'value', '-s', 'TYPE', device],
        capture_output=True, text=True,
    )
    fstype = fstype_result.stdout.strip()

    if fstype in ('vfat', 'exfat'):
        cmd = ['sudo', 'mount', '-o', 'uid=1000,gid=1000,fmask=0022,dmask=0022', device, _DEFAULT_MOUNT_POINT]
    else:
        cmd = ['sudo', 'mount', device, _DEFAULT_MOUNT_POINT]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise OSError(f"mount failed: {result.stderr.strip()}")

    _active_mount_point = _DEFAULT_MOUNT_POINT


def unmount_pendrive() -> None:
    """Unmount the USB drive. No-op if not mounted."""
    global _active_mount_point
    if _active_mount_point is None:
        return
    subprocess.run(['sudo', 'umount', _active_mount_point], capture_output=True)
    _active_mount_point = None


def is_pendrive_mounted() -> bool:
    device = _find_usb_block_device()
    if not device:
        return False
    return _get_mount_point(device) is not None

# Alias for any remaining callers
is_pendrive_connected = is_pendrive_mounted


def create_recordings_dir() -> None:
    """Create the recordings directory on the USB drive if it does not exist."""
    path = get_recordings_path()
    if not os.path.isdir(path):
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create recordings directory: {e}")


class MultipleUSBDrivesException(Exception):
    pass
