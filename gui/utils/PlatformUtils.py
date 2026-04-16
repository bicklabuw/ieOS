import platform


def get_device_serial() -> str:
    """
    Raspberry Pi SoC serial (hex string), or a human-readable placeholder
    when unavailable (e.g. desktop dev).
    """
    try:
        with open("/sys/firmware/devicetree/base/serial-number", "rb") as f:
            raw = f.read().strip(b"\x00").decode("ascii", errors="replace").strip()
            if raw:
                return raw
    except OSError:
        pass
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("Serial"):
                    _, _, rest = line.partition(":")
                    s = rest.strip()
                    if s:
                        return s
    except OSError:
        pass
    return "unknown"


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