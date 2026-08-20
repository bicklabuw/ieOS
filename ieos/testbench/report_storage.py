from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from gui.utils.durable_io import copy_file_durable
from gui.utils.usb import USBDriveManager

REPORTS_DIR = "testbench-reports"


@dataclass(frozen=True)
class UsbReportResult:
    ok: bool
    code: str
    message: str
    usb_path: str | None = None


def _report_filename(mode: str) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return f"ieos-testbench-{mode}-{ts}.json"


def copy_report_to_usb(local_report_path: str, mode: str) -> UsbReportResult:
    local = Path(local_report_path)
    if not local.is_file():
        return UsbReportResult(False, "LOCAL_REPORT_MISSING", f"Missing report: {local}")

    mounted = False
    try:
        USBDriveManager.mount_pendrive()
        mounted = True
        root = USBDriveManager.get_active_mount_point()
        if not root:
            return UsbReportResult(False, "USB_NOT_MOUNTED", "USB mounted but no mount point was found")

        out_dir = Path(root) / REPORTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / _report_filename(mode)
        copy_file_durable(local, dest)
        return UsbReportResult(True, "SAVED", "Report saved to USB", str(dest))
    except OSError as e:
        return UsbReportResult(False, "USB_ERROR", str(e))
    finally:
        if mounted:
            try:
                USBDriveManager.unmount_pendrive()
            except OSError:
                pass
