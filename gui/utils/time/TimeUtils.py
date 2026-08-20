# gui/utils/time/TimeUtils.py
import logging
import subprocess
import sys
import time

_log = logging.getLogger(__name__)


def get_duration_text(duration):
    """
    Converts a duration in seconds to a human-readable string format."
    """

    if duration <= 0:
        return "0s"

    secs = duration
    mins = secs // 60
    hours = mins // 60
    days = hours // 24
    
    time_str = f"{days}d " if days > 0 else ""
    time_str += f"{(hours % 24)}h " if hours > 0 else ""
    time_str += f"{mins % 60}m " if mins > 0 else ""
    time_str += f"{secs % 60}s " if mins == 0 else ""
    
    return time_str


def ntp_synchronized_linux() -> bool:
    """True if systemd reports NTP is currently synchronized (no sudo)."""
    if sys.platform != "linux":
        return False
    try:
        r = subprocess.run(
            ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and (r.stdout or "").strip().lower() == "yes"


def enable_ntp_linux(timeout_sec: float = 8.0) -> bool:
    """Turn network time sync on via timedatectl (passwordless sudo on configured Pi)."""
    if sys.platform != "linux":
        return False
    try:
        subprocess.run(
            ["sudo", "-n", "timedatectl", "set-ntp", "true"],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        _log.warning("enable NTP failed: %s", e)
        return False
    except subprocess.CalledProcessError as e:
        err = (e.stderr or "").strip()
        _log.warning("enable NTP failed: %s", err or e)
        return False


def wait_for_ntp_sync_linux(
    max_wait_sec: float = 8.0,
    poll_sec: float = 0.4,
) -> bool:
    """
    Ensure NTP is enabled, then poll until NTPSynchronized or timeout.

    Use on boot so DateTimeInputViewController seeds from a clock corrected
    by systemd-timesyncd when the network is available.
    """
    if sys.platform != "linux":
        return False
    enable_ntp_linux()
    deadline = time.monotonic() + max_wait_sec
    while time.monotonic() < deadline:
        if ntp_synchronized_linux():
            _log.info("NTP synchronized before time picker")
            return True
        time.sleep(poll_sec)
    _log.info("NTP not synchronized within %.1fs; showing picker with OS clock", max_wait_sec)
    return False


def set_system_time(datetime_str: str) -> tuple[bool, str]:
    """
    Set system time without interactive prompts.

    :param datetime_str: A string in 'YYYY-MM-DD HH:MM:SS' format
    :return: (success, message)
    """
    if sys.platform != "linux":
        return False, "Time setting only supported on Linux/Raspberry Pi"

    try:
        # Disable Time Sync First (non-interactive sudo to avoid password prompt hangs).
        subprocess.run(
            ["sudo", "-n", "timedatectl", "set-ntp", "false"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Set the System Time
        subprocess.run(
            ["sudo", "-n", "timedatectl", "set-time", datetime_str],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Leave NTP enabled so the next boot can pull correct time from the network
        # instead of staying on fake-hwclock with sync permanently off.
        try:
            subprocess.run(
                ["sudo", "-n", "timedatectl", "set-ntp", "true"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            _log.warning("set-time OK but re-enable NTP failed: %s", e)
        return True, "Time set successfully"
    except subprocess.TimeoutExpired:
        return False, "Timed out while setting time"
    except subprocess.CalledProcessError as e:
        err = (e.stderr or "").strip()
        if "a password is required" in err.lower():
            return False, "Sudo requires password (configure passwordless timedatectl)"
        return False, f"Failed to set time: {err or str(e)}"