import subprocess
import sys
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
        return True, "Time set successfully"
    except subprocess.TimeoutExpired:
        return False, "Timed out while setting time"
    except subprocess.CalledProcessError as e:
        err = (e.stderr or "").strip()
        if "a password is required" in err.lower():
            return False, "Sudo requires password (configure passwordless timedatectl)"
        return False, f"Failed to set time: {err or str(e)}"