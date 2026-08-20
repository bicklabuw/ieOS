import os
import shutil
import subprocess
import time

_DEFAULT_MOUNT_POINT = "/mnt/usb0"
PENDRIVE_RECORDINGS_DIR = "/WAV"

# Set by mount_pendrive(), cleared by unmount_pendrive()
_active_mount_point: str | None = None

# Mount / write retries (USB may appear a moment after plug-in)
_DEFAULT_MOUNT_ATTEMPTS = 4
_MOUNT_RETRY_DELAY_SEC = 0.45


def _path_is_mounted(path: str) -> bool:
    """True if path appears as a mount point in /proc/mounts."""
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == path:
                    return True
    except OSError:
        pass
    return False


def refresh_mount_state() -> None:
    """
    Clear cached mount if the path is no longer mounted (e.g. drive unplugged).
    Safe to call often.
    """
    global _active_mount_point
    if _active_mount_point is None:
        return
    if not _path_is_mounted(_active_mount_point):
        _active_mount_point = None


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


def _mount_source_is_device(src: str, device: str) -> bool:
    """
    True if src names the same block device as device.

    Desktop udisks2 often records mounts as /dev/disk/by-uuid/... in /proc/mounts
    while we discover the stick as /dev/sda1; a plain string compare misses that
    and triggers a second mount (EBUSY / mount failed).
    """
    if src == device:
        return True
    try:
        return bool(
            os.path.exists(src)
            and os.path.exists(device)
            and os.path.samefile(src, device)
        )
    except OSError:
        return False


def _get_mount_point(device: str) -> str | None:
    """Return the current mount point of device, or None if not mounted."""
    try:
        with open('/proc/mounts') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and _mount_source_is_device(parts[0], device):
                    return parts[1]
    except OSError:
        pass
    return None


def get_recordings_path() -> str:
    """Return the path to the recordings directory on the mounted USB drive."""
    refresh_mount_state()
    if _active_mount_point is None:
        raise OSError("USB drive not mounted")
    return _active_mount_point + PENDRIVE_RECORDINGS_DIR


def get_active_mount_point() -> str | None:
    """Return current active mount point if mounted, else None."""
    refresh_mount_state()
    return _active_mount_point


def get_recordings_filesystem_free_bytes() -> int | None:
    """
    Free space on the filesystem that holds /WAV, if the drive is mounted and path exists.
    Returns None if not mounted or usage cannot be read.
    """
    refresh_mount_state()
    if _active_mount_point is None:
        return None
    try:
        path = get_recordings_path()
        if not os.path.isdir(path):
            return None
        return shutil.disk_usage(path).free
    except OSError:
        return None


def _verify_dir_writable(dir_path: str) -> None:
    """Raise OSError if we cannot create and delete a tiny test file."""
    test = os.path.join(dir_path, ".ieos_write_test")
    try:
        with open(test, "wb") as f:
            f.write(b"\x00")
        os.remove(test)
    except OSError as e:
        raise OSError(f"USB storage not writable: {e}") from e


def ensure_recordings_ready(
    attempts: int = _DEFAULT_MOUNT_ATTEMPTS,
    delay_sec: float = _MOUNT_RETRY_DELAY_SEC,
) -> str:
    """
    Ensure USB is mounted and /WAV exists and is writable.

    Retries on transient failures (drive just inserted, auto-mount racing).
    Returns the full path to the recordings directory.
    """
    last_err: OSError | None = None
    for i in range(attempts):
        refresh_mount_state()
        try:
            mount_pendrive()
            path = get_recordings_path()
            create_recordings_dir()
            _verify_dir_writable(path)
            return path
        except OSError as e:
            last_err = e
            if i + 1 < attempts:
                time.sleep(delay_sec * (i + 1))
    assert last_err is not None
    raise last_err


def assert_recordings_still_ready() -> str:
    """
    After refresh, confirm cached mount is still valid and folder is usable.
    Call between long recording segments or after suspected unplug.
    """
    refresh_mount_state()
    path = get_recordings_path()
    if not os.path.isdir(path):
        raise OSError("Recordings folder missing (USB may have been removed)")
    _verify_dir_writable(path)
    return path


def mount_pendrive() -> None:
    """
    Mount the USB drive. If already mounted (e.g. by udisks2), uses the existing
    mount point. Raises OSError if no USB drive is found or mount fails.
    """
    global _active_mount_point

    refresh_mount_state()

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
        # udisks may have auto-mounted after our first check (common on desktop Pi OS).
        time.sleep(_MOUNT_RETRY_DELAY_SEC)
        existing_after = _get_mount_point(device)
        if existing_after:
            _active_mount_point = existing_after
            return
        raise OSError(f"mount failed: {result.stderr.strip()}")

    _active_mount_point = _DEFAULT_MOUNT_POINT


def unmount_pendrive() -> None:
    """Flush buffers and unmount the USB drive. No-op if not mounted."""
    global _active_mount_point
    if _active_mount_point is None:
        return
    mp = _active_mount_point
    try:
        subprocess.run(["sync"], check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        pass
    subprocess.run(["sudo", "umount", mp], capture_output=True)
    _active_mount_point = None


def is_pendrive_mounted() -> bool:
    refresh_mount_state()
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
