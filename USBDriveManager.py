PENDRIVE_MOUNT_POINT = "/mnt/usb0"
PENDRIVE_RECORDINGS_DIR = "/WAV"
PENDRIVE_RECORDINGS_PATH = PENDRIVE_MOUNT_POINT + PENDRIVE_RECORDINGS_DIR

def is_pendrive_connected():
    """Check if the pendrive is connected."""
    return os.path.isdir(PENDRIVE_MOUNT_POINT)

def create_recordings_dir():
    """Create the recordings directory if it does not exist."""
    
    if (is_pendrive_connected() and not os.path.isdir(PENDRIVE_RECORDINGS_PATH)):
        try:
            os.makedirs(PENDRIVE_RECORDINGS_PATH, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create recordings directory: {e}")


class MultipleUSBDrivesException(Exception):
    """Exception raised when multiple USB drives are detected."""
    pass
    