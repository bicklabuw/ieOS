import subprocess
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

def set_system_time(datetime_str):
    """
    Sets the system time using 'timedatectl'.

    :param datetime_str: A string in 'YYYY-MM-DD HH:MM:SS' format
    """
    try:
        # Disable Time Sync First
        subprocess.run(["timedatectl", "set-ntp", "false"], check=True)

        # Set the System Time
        subprocess.run(
            ["sudo", "timedatectl", "set-time", datetime_str],
            check=True
        )
        print("Time set successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set time: {e}")