import platform

def is_raspberry_pi():
    if platform.system() == "Linux":  # Check if running on Linux
        try:
            with open("/proc/cpuinfo") as f:
                cpuinfo = f.read()
            if "Raspberry Pi" in cpuinfo:
                return True
        except FileNotFoundError:
            pass  # File not found, likely not a Raspberry Pi
    return False