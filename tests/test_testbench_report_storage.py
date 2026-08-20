from __future__ import annotations

import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ieos.testbench import report_storage


class TestbenchReportStorageTests(unittest.TestCase):
    def test_copy_report_to_usb_writes_timestamped_report(self) -> None:
        with TemporaryDirectory() as tmp, TemporaryDirectory() as usb_root:
            local_report = os.path.join(tmp, "report.json")
            with open(local_report, "w", encoding="utf-8") as f:
                f.write("{}")

            with patch("ieos.testbench.report_storage.USBDriveManager.mount_pendrive"), patch(
                "ieos.testbench.report_storage.USBDriveManager.get_active_mount_point",
                return_value=usb_root,
            ), patch("ieos.testbench.report_storage.USBDriveManager.unmount_pendrive") as unmount:
                result = report_storage.copy_report_to_usb(local_report, "quick")

            self.assertTrue(result.ok)
            self.assertEqual("SAVED", result.code)
            self.assertIsNotNone(result.usb_path)
            assert result.usb_path is not None
            self.assertTrue(result.usb_path.startswith(os.path.join(usb_root, "testbench-reports")))
            self.assertTrue(os.path.basename(result.usb_path).startswith("ieos-testbench-quick-"))
            self.assertTrue(os.path.isfile(result.usb_path))
            unmount.assert_called_once()

    def test_copy_report_to_usb_handles_mount_errors(self) -> None:
        with TemporaryDirectory() as tmp:
            local_report = os.path.join(tmp, "report.json")
            with open(local_report, "w", encoding="utf-8") as f:
                f.write("{}")

            with patch(
                "ieos.testbench.report_storage.USBDriveManager.mount_pendrive",
                side_effect=OSError("No USB drive found"),
            ):
                result = report_storage.copy_report_to_usb(local_report, "long")

            self.assertFalse(result.ok)
            self.assertEqual("USB_ERROR", result.code)


if __name__ == "__main__":
    unittest.main()
