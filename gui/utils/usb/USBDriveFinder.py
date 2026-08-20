import os
import re
import subprocess
from enum import Enum

class USBDriveType(Enum):
    PARTITION = 'partition'
    DISK = 'disk'
    SUPERFLOPPY = 'superfloppy'

def _get_usb_symlink_map():
    """
    Returns a mapping:
      { '/dev/sdb1': '/dev/disk/by-id/usb-Whatever-part1', ... }
    Only includes USB drives.
    """
    by_id_path = '/dev/disk/by-id/'
    device_map = {}
    if not os.path.exists(by_id_path):
        return device_map
    for entry in os.listdir(by_id_path):
        if entry.startswith('usb-'):
            symlink = os.path.join(by_id_path, entry)
            if os.path.islink(symlink):
                device = os.path.realpath(symlink)
                if os.path.exists(device) and '/dev/sd' in device:
                    device_map[symlink] = device
    return device_map  # key: id_path, value: device

def _get_mount_points():
    mounts = {}
    with open('/proc/mounts', 'r') as f:
        for line in f:
            parts = line.split()
            device, mountpoint = parts[0], parts[1]
            mounts[device] = mountpoint
    return mounts

def _get_labels(devices):
    labels = {}
    if not devices:
        return labels
    try:
        cmd = ["lsblk", "-nro", "NAME,LABEL"]
        result = subprocess.check_output(cmd, universal_newlines=True)
        for line in result.strip().split('\n'):
            parts = line.strip().split(None, 1)
            if len(parts) == 1:
                name, label = parts[0], ""
            else:
                name, label = parts
            dev_path = '/dev/' + name
            labels[dev_path] = label if label else None
    except Exception:
        labels = {dev: None for dev in devices}
    return labels

def _determine_type(id_path, device, label) -> USBDriveType:
    if re.search(r'-part\d+$', id_path):
        return USBDriveType.PARTITION
    elif label:
        return USBDriveType.SUPERFLOPPY
    else:
        return USBDriveType.DISK

def find_usb_drives():
    """
    Returns a dictionary:
    {
        disk_id_path: {
            'id_path': disk_id_path,
            'device': /dev/sdX,
            'mountpoint': ...,
            'label': ...,
            'type': USBDriveType.DISK or USBDriveType.SUPERFLOPPY,
            'partitions': [
                {
                    'id_path': ...,
                    'device': ...,
                    'mountpoint': ...,
                    'label': ...,
                    'type': USBDriveType.PARTITION
                },
                ...
            ]
        },
        ...
    }
    """
    symlink_map = _get_usb_symlink_map()  # id_path -> device
    mount_points = _get_mount_points()
    labels = _get_labels(list(symlink_map.values()))

    # Organize by base disks
    disks = {}
    partitions = []

    # First, collect disk and partition entries
    for id_path, device in symlink_map.items():
        label = labels.get(device, None)
        typ = _determine_type(id_path, device, label)
        entry = {
            "id_path": id_path,
            "device": device,
            "mountpoint": mount_points.get(device, None),
            "label": label,
            "type": typ
        }
        if typ == USBDriveType.PARTITION:
            partitions.append(entry)
        else:
            disks[id_path] = entry
            disks[id_path]['partitions'] = []

    # Next, associate partitions with their parent disk
    for part in partitions:
        # Remove "-partN" from id_path to get parent id_path
        parent_id_path = re.sub(r'-part\d+$', '', part['id_path'])
        if parent_id_path in disks:
            disks[parent_id_path]['partitions'].append(part)
        else:
            # Orphan partition? If so, create a minimal disk entry
            disks[parent_id_path] = {
                "id_path": parent_id_path,
                "device": None,
                "mountpoint": None,
                "label": None,
                "type": USBDriveType.DISK,
                "partitions": [part]
            }

    return disks

# Example usage:
if __name__ == "__main__":
    drives = find_usb_drives()
    import pprint
    pprint.pprint(drives)