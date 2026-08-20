import os
import sounddevice as sd

# USB Microphones
print("=== USB Microphones ===")
devices = sd.query_devices()
mics_found = 0
for d in devices:
    name = d['name']
    if name.startswith("USB") and d['max_input_channels'] > 0:
        print(f"  [{d['index']}] {name}  (channels: {d['max_input_channels']})")
        mics_found += 1
if mics_found == 0:
    print("  (none found)")

# Pendrive
print("\n=== Pendrive ===")
mount = "/mnt/usb0"
if os.path.isdir(mount):
    print(f"  Connected at {mount}")
    try:
        total, used, free = os.statvfs(mount).f_blocks, os.statvfs(mount).f_bsize, os.statvfs(mount).f_bavail
        fs = os.statvfs(mount)
        total_mb = fs.f_blocks * fs.f_frsize // (1024 * 1024)
        free_mb  = fs.f_bavail * fs.f_frsize // (1024 * 1024)
        print(f"  {free_mb} MB free / {total_mb} MB total")
    except OSError:
        pass
else:
    print(f"  (not found at {mount})")
