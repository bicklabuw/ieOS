from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ieos import updater_service


def _write_version_py(root_ieos: str, version: str) -> None:
    with open(os.path.join(root_ieos, "version.py"), "w", encoding="utf-8") as f:
        f.write(f'APP_VERSION = "{version}"\n')


def _proof_bytes_for_ascii(text: str) -> bytes:
    out = bytearray()
    for ch in text:
        b = ord(ch)
        out.extend((b, b & 0xFF))
    return bytes(out)


class UpdaterServiceTests(unittest.TestCase):
    def test_missing_usb_ieos_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            proof = os.path.join(tmp, updater_service.IEOS_PROOF)
            with open(proof, "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            result = updater_service.validate_update_payload(tmp, current_version="0.1")
            self.assertFalse(result.ok)
            self.assertEqual("MISSING_IEOS", result.code)

    def test_missing_proof_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "ieos"))
            _write_version_py(os.path.join(tmp, "ieos"), "9.9.9")
            with open(os.path.join(tmp, "ieos", "a.py"), "w", encoding="utf-8") as f:
                f.write("pass\n")
            result = updater_service.validate_update_payload(tmp, current_version="0.1")
            self.assertFalse(result.ok)
            self.assertEqual("MISSING_PROOF", result.code)

    def test_proof_odd_length_fails(self) -> None:
        ok, err = updater_service.validate_proof_file_binary(b"A")
        self.assertFalse(ok)
        self.assertIn("odd", err)

    def test_proof_bad_checksum_fails(self) -> None:
        ok, err = updater_service.validate_proof_file_binary(bytes((65, 0)))
        self.assertFalse(ok)
        self.assertIn("bad pair", err)

    def test_proof_valid(self) -> None:
        self.assertTrue(updater_service.validate_proof_file_binary(_proof_bytes_for_ascii("OK"))[0])

    def test_missing_version_py_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            ie = os.path.join(tmp, "ieos")
            os.makedirs(ie)
            with open(os.path.join(tmp, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            with open(os.path.join(ie, "a.py"), "w", encoding="utf-8") as f:
                f.write("pass\n")
            result = updater_service.validate_update_payload(tmp, current_version="0.1")
            self.assertFalse(result.ok)
            self.assertEqual("MISSING_VERSION", result.code)

    def test_invalid_version_body_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            ie = os.path.join(tmp, "ieos")
            os.makedirs(ie)
            with open(os.path.join(tmp, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            with open(os.path.join(ie, "version.py"), "w", encoding="utf-8") as f:
                f.write("not a version line\n")
            with open(os.path.join(ie, "a.py"), "w", encoding="utf-8") as f:
                f.write("pass\n")
            result = updater_service.validate_update_payload(tmp, current_version="0.1")
            self.assertFalse(result.ok)
            self.assertEqual("INVALID_VERSION", result.code)

    def test_version_too_old_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            ie = os.path.join(tmp, "ieos")
            os.makedirs(ie)
            with open(os.path.join(tmp, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            _write_version_py(ie, "0.1")
            with open(os.path.join(ie, "a.py"), "w", encoding="utf-8") as f:
                f.write("pass\n")
            result = updater_service.validate_update_payload(tmp, current_version="0.3")
            self.assertFalse(result.ok)
            self.assertEqual("VERSION_TOO_OLD", result.code)

    def test_same_version_passes_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            ie = os.path.join(tmp, "ieos")
            os.makedirs(ie)
            with open(os.path.join(tmp, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            _write_version_py(ie, "0.3")
            with open(os.path.join(ie, "a.py"), "w", encoding="utf-8") as f:
                f.write("pass\n")
            result = updater_service.validate_update_payload(tmp, current_version="0.3")
            self.assertTrue(result.ok)
            self.assertEqual("READY", result.code)

    def test_newer_version_passes_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            ie = os.path.join(tmp, "ieos")
            os.makedirs(ie)
            with open(os.path.join(tmp, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            _write_version_py(ie, "1.0")
            with open(os.path.join(ie, "a.py"), "w", encoding="utf-8") as f:
                f.write("pass\n")
            result = updater_service.validate_update_payload(tmp, current_version="0.3")
            self.assertTrue(result.ok)

    def test_parse_app_version_from_version_py(self) -> None:
        self.assertEqual(
            "0.42",
            updater_service.parse_app_version_from_version_py('APP_VERSION = "0.42"\n'),
        )
        self.assertIsNone(updater_service.parse_app_version_from_version_py(""))

    def test_usb_mount_error_returns_usb_error(self) -> None:
        with patch("ieos.updater_service.USBDriveManager.mount_pendrive", side_effect=OSError("No USB drive found")):
            result = updater_service.validate_update_from_usb()
            self.assertFalse(result.ok)
            self.assertEqual("USB_ERROR", result.code)

    def test_validate_update_from_usb_ignores_unmount_error(self) -> None:
        with TemporaryDirectory() as usb_root:
            ie = os.path.join(usb_root, "ieos")
            os.makedirs(ie)
            with open(os.path.join(usb_root, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            _write_version_py(ie, "9.9.9")
            with open(os.path.join(ie, "a.py"), "w", encoding="utf-8") as f:
                f.write("pass\n")
            with patch("ieos.updater_service.USBDriveManager.mount_pendrive"), patch(
                "ieos.updater_service.USBDriveManager.get_active_mount_point", return_value=usb_root
            ), patch("ieos.updater_service.USBDriveManager.unmount_pendrive", side_effect=OSError("busy")):
                result = updater_service.validate_update_from_usb()
            self.assertTrue(result.ok)

    def test_install_replaces_ieos_only(self) -> None:
        with TemporaryDirectory() as usb_root, TemporaryDirectory() as app_root:
            usb_ie = os.path.join(usb_root, "ieos")
            os.makedirs(usb_ie)
            with open(os.path.join(usb_root, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            _write_version_py(usb_ie, "0.3")
            with open(os.path.join(usb_ie, "new_file.py"), "w", encoding="utf-8") as f:
                f.write("new\n")

            dest_ieos = os.path.join(app_root, "ieos")
            os.makedirs(dest_ieos)
            with open(os.path.join(dest_ieos, "old.py"), "w", encoding="utf-8") as f:
                f.write("old\n")

            gui_dir = os.path.join(app_root, "gui")
            os.makedirs(gui_dir)
            with open(os.path.join(gui_dir, "keep_gui.py"), "w", encoding="utf-8") as f:
                f.write("keep\n")

            with patch.object(updater_service, "APP_ROOT", app_root), patch.object(
                updater_service, "DEST_IEOS_ROOT", dest_ieos
            ), patch("ieos.updater_service.USBDriveManager.mount_pendrive"), patch(
                "ieos.updater_service.USBDriveManager.get_active_mount_point", return_value=usb_root
            ), patch("ieos.updater_service.USBDriveManager.unmount_pendrive"), patch(
                "ieos.updater_service.BACKUP_ROOT", os.path.join(app_root, "backups")
            ):
                result = updater_service.install_update_from_usb()

            self.assertTrue(result.ok)
            self.assertEqual("UPDATED", result.code)
            self.assertTrue(os.path.isfile(os.path.join(dest_ieos, "new_file.py")))
            self.assertFalse(os.path.exists(os.path.join(dest_ieos, "old.py")))
            self.assertTrue(os.path.isfile(os.path.join(gui_dir, "keep_gui.py")))

    def test_install_failure_restores_ieos(self) -> None:
        with TemporaryDirectory() as usb_root, TemporaryDirectory() as app_root:
            usb_ie = os.path.join(usb_root, "ieos")
            os.makedirs(usb_ie)
            with open(os.path.join(usb_root, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            _write_version_py(usb_ie, "0.3")
            with open(os.path.join(usb_ie, "new_file.py"), "w", encoding="utf-8") as f:
                f.write("new\n")

            dest_ieos = os.path.join(app_root, "ieos")
            os.makedirs(dest_ieos)
            with open(os.path.join(dest_ieos, "old.py"), "w", encoding="utf-8") as f:
                f.write("old content\n")

            orig_copytree = shutil.copytree
            def flaky_copytree(src: str, dst: str, **kwargs: object) -> str:
                if os.path.abspath(src) == os.path.abspath(usb_ie):
                    raise OSError("simulated copy failure")
                return orig_copytree(src, dst, **kwargs)

            with patch.object(updater_service, "APP_ROOT", app_root), patch.object(
                updater_service, "DEST_IEOS_ROOT", dest_ieos
            ), patch("ieos.updater_service.USBDriveManager.mount_pendrive"), patch(
                "ieos.updater_service.USBDriveManager.get_active_mount_point", return_value=usb_root
            ), patch("ieos.updater_service.USBDriveManager.unmount_pendrive"), patch(
                "ieos.updater_service.BACKUP_ROOT", os.path.join(app_root, "backups")
            ), patch("ieos.updater_service.shutil.copytree", side_effect=flaky_copytree):
                result = updater_service.install_update_from_usb()

            self.assertFalse(result.ok)
            self.assertEqual("UPDATE_FAILED", result.code)
            with open(os.path.join(dest_ieos, "old.py"), encoding="utf-8") as f:
                self.assertEqual("old content\n", f.read())
            self.assertFalse(os.path.exists(os.path.join(dest_ieos, "new_file.py")))

    def test_install_update_from_usb_ignores_unmount_error(self) -> None:
        with TemporaryDirectory() as usb_root, TemporaryDirectory() as app_root:
            usb_ie = os.path.join(usb_root, "ieos")
            os.makedirs(usb_ie)
            with open(os.path.join(usb_root, updater_service.IEOS_PROOF), "wb") as f:
                f.write(_proof_bytes_for_ascii("x"))
            _write_version_py(usb_ie, "0.3")
            with open(os.path.join(usb_ie, "x.py"), "w", encoding="utf-8") as f:
                f.write("x\n")
            dest_ieos = os.path.join(app_root, "ieos")
            os.makedirs(dest_ieos)
            _write_version_py(dest_ieos, "0.3")
            with patch.object(updater_service, "APP_ROOT", app_root), patch.object(
                updater_service, "DEST_IEOS_ROOT", dest_ieos
            ), patch("ieos.updater_service.USBDriveManager.mount_pendrive"), patch(
                "ieos.updater_service.USBDriveManager.get_active_mount_point", return_value=usb_root
            ), patch("ieos.updater_service.USBDriveManager.unmount_pendrive", side_effect=OSError("busy")), patch(
                "ieos.updater_service.BACKUP_ROOT", os.path.join(app_root, "backups")
            ):
                result = updater_service.install_update_from_usb()
            self.assertTrue(result.ok)

    def test_reboot_device_success(self) -> None:
        with patch(
            "ieos.updater_service.subprocess.run",
            return_value=subprocess.CompletedProcess(args=["sudo", "reboot"], returncode=0, stdout="", stderr=""),
        ):
            result = updater_service.reboot_device()
            self.assertTrue(result.ok)
            self.assertEqual("REBOOTING", result.code)

    def test_reboot_device_rejected(self) -> None:
        with patch(
            "ieos.updater_service.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["sudo", "reboot"], returncode=1, stdout="", stderr="permission denied"
            ),
        ):
            result = updater_service.reboot_device()
            self.assertFalse(result.ok)
            self.assertEqual("REBOOT_FAILED", result.code)


if __name__ == "__main__":
    unittest.main()
