import os
import subprocess
from typing import List

# Import the function from previous code block
# from usb_drives import find_usb_drives_full

def format_usb_drives(drives: List[dict], format_script_path=None) -> bool:
    """
    Given a list of drive info dicts (see find_usb_drives_full()),
    call format.sh for each device.
    """
    if format_script_path is None:
        script_dir = os.path.dirname(__file__)
        format_script_path = os.path.join(script_dir, "format.sh")
    
    for drive in drives:
        device = drive['device']
        label = drive['label'] or ""
        print(f"Formatting {device} (label: {label}) ...")
        try:
            # If format.sh expects both device and label:
            subprocess.run([format_script_path, device, "-y"], check=True)
            print(f"Formatted {device} successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error formatting {device}: {e}")
            return False

if __name__ == "__main__":
    # --- FIND ALL USB DRIVES ---
    from gui.utils.usb.USBDriveFinder import find_usb_drives  # or just paste the function above
    drives = find_usb_drives()

    # --- SELECT WHICH TO FORMAT (Your GUI Here) ---
    # For demo: format ALL drives
    print("Connected USB drives:")
    for i, d in enumerate(drives):
        print(f"{i}: {d['device']} (label: {d['label']}, id: {d['id_path']})")

    # You'd get 'selected_drives' from your GUI, e.g. all of them:
    selected_drives = drives  # or filter by label/id/etc

    # --- FORMAT ---
    format_usb_drives(selected_drives, "./format.sh")
