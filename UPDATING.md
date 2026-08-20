# Updating ieOS from USB

This document describes how to build a valid USB update payload and apply it on the device. The updater replaces only the `**ieos/**` application package on the Pi (`APP_ROOT/ieos`). The `**gui/**` tree is **not** modified by this flow; if a release needs both packages, use another mechanism or extend the updater separately.

## Prerequisites

- A USB drive the Pi can mount (see `gui/utils/usb/USBDriveManager.py` for mount behavior).
- A working copy of the `**ieos`** Python package you intend to ship (full directory tree, excluding build junk as noted below).

## USB filesystem layout

Everything below is relative to the **root of the mounted USB volume** (the top level you see when you open the stick on a computer).

```
USB_ROOT/
  IEOS_PROOF          # binary proof file (see below)
  ieos/               # complete app package to install
    version.py        # must contain APP_VERSION = "x.y.z…"
    …                 # rest of package mirroring repo layout
```

### 1. Folder `ieos/`

- There must be a directory named `**ieos**` at the USB root.
- It must contain a file `**ieos/version.py**` with a line the updater can parse, for example:

```python
APP_VERSION = "0.4"
```

Version strings must be dotted non-negative integers only (e.g. `0`, `0.3`, `1.2.0`). Values with letters or pre-release tags are rejected.

### 2. Version check

- The payload version is taken **only** from `ieos/version.py` on the USB stick.
- The update is accepted only if **payload version &ge; installed version** on the device.  
Matching versions are allowed (reinstall/same release).

Installed version comes from `ieos.version.APP_VERSION` in the currently running installation.

### 3. Proof file `IEOS_PROOF`

Filename is fixed: `**IEOS_PROOF`** (no extension), at USB root next to `**ieos/**`.

The file is **binary**, with an **even** number of bytes. It is interpreted as adjacent pairs `(c, checksum)`:

- For each pair, `checksum` must equal `c & 0xFF`.
- Each first byte `c` must decode to an ASCII character (`chr(c).isascii()`).
- Minimum useful length: treat an **empty** file as invalid.

For a short ASCII message, each character `ch` expands to two bytes `(ord(ch), ord(ch) & 0xFF)` (which is `(ord(ch), ord(ch))` for normal ASCII).

**Example:** generate `IEOS_PROOF` containing `OK`:

```bash
python3 -c 's=b"OK"; open("IEOS_PROOF","wb").write(bytes([b for o in map(ord,s) for b in (o, o & 255)]))'
```

Place the resulting `**IEOS_PROOF**` alongside your `**ieos/**` folder on the USB stick.

## Files omitted from install

Under `ieos/` on USB, these are **skipped** during copy (they are never installed):

| Skipped directories | `.git`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.venv`, `venv` |
| Skipped file suffixes | `.pyc`, `.pyo` |

## On the device

1. Copy the payload to the USB drive with the layout above.
2. Insert the USB drive into the Raspberry Pi.
3. Open **Settings**.
4. Select **Update from USB**.
5. If validation succeeds, confirm **Install** when prompted.
6. After a successful apply, reboot when prompted so the new code loads cleanly.

Validation runs briefly (drive is mounted then unmounted). Install mounts again, backs up the current `ieos` tree, replaces it entirely, then unmounts.

## Backups and rollback

- Before replacing `ieos/`, the updater copies the current installation to  
`**~/.config/ieos/update_backups/`** under a stamped directory (`backup-v<version>-<timestamp>/ieos`).
- If the replacement step fails, the updater attempts to restore the previous `ieos` tree from that backup.

## Troubleshooting


| Message / symptom                      | Typical cause                                         |
| -------------------------------------- | ----------------------------------------------------- |
| USB has no `ieos` folder               | Wrong layout; folder must be named `ieos` at USB root |
| Proof file missing (`IEOS_PROOF`)      | Missing `IEOS_PROOF` at USB root                      |
| Proof verification failed              | Odd length, wrong pair bytes, or non-ASCII first byte |
| Missing / invalid `ieos/version.py`    | No file, or line not matching `APP_VERSION = "…"`     |
| Installed version is newer than USB    | USB version is strictly lower than the device         |
| No installable files under USB `ieos/` | Only skipped paths present, or directory empty        |


The on-screen titles may shorten error text; fuller detail is logged where applicable (`ieos/updater_service.py`).

## Reference implementation

Canonical behavior lives in:

- `**ieos/updater_service.py**` — validation (`validate_update_*`), install (`install_update_from_usb`), proof and version parsing constants.
- `**ieos/UpdateFromUSBViewController.py**` — UI flow from **Settings → Update from USB**.

