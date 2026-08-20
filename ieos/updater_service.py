from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from dataclasses import dataclass

from gui.utils.durable_io import fsync_directory, fsync_tree
from gui.utils.usb import USBDriveManager
from ieos.version import APP_VERSION

_log = logging.getLogger(__name__)

# USB root proof file: even-length sequence of pairs (ASCII byte, checksum byte).
# For each ASCII character byte c at an even offset, byte c+1 must equal (c & 0xFF).
IEOS_PROOF = "IEOS_PROOF"

# Only the app package folder is shipped via USB updater (not gui/).
# APP_ROOT holds both ieos and gui alongside each other after install paths.
DEST_IEOS_SEG = "ieos"

EXCLUDED_COPY_DIR_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
EXCLUDED_COPY_FILE_SUFFIXES = {".pyc", ".pyo"}

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEST_IEOS_ROOT = os.path.join(APP_ROOT, DEST_IEOS_SEG)
BACKUP_ROOT = os.path.join(os.path.expanduser("~"), ".config", "ieos", "update_backups")


@dataclass(frozen=True)
class UpdateValidationResult:
    ok: bool
    code: str
    message: str
    details: list[str]
    source_root: str | None = None
    payload_version: str | None = None
    current_version: str = APP_VERSION
    copy_targets_count: int = 0


@dataclass(frozen=True)
class UpdateInstallResult:
    ok: bool
    code: str
    message: str
    details: list[str]
    payload_version: str | None = None
    backup_path: str | None = None
    files_copied: int = 0


@dataclass(frozen=True)
class RebootResult:
    ok: bool
    code: str
    message: str
    details: list[str]


_APP_VERSION_RE = re.compile(
    r"""^\s*APP_VERSION\s*=\s*(?:["']([^"']+)["']|([^\s#]+))\s*(?:#.*)?$""",
    re.MULTILINE,
)


def _parse_version(value: str) -> tuple[int, ...] | None:
    parts = value.strip().split(".")
    if not parts:
        return None
    parsed: list[int] = []
    for part in parts:
        if not part.isdigit():
            return None
        parsed.append(int(part))
    return tuple(parsed)


def _payload_at_least_installed(payload_version: str, current_version: str) -> bool:
    payload = _parse_version(payload_version)
    current = _parse_version(current_version)
    if payload is None or current is None:
        return False
    max_len = max(len(payload), len(current))
    payload_pad = payload + (0,) * (max_len - len(payload))
    current_pad = current + (0,) * (max_len - len(current))
    return payload_pad >= current_pad


def _should_skip_dir(name: str) -> bool:
    return name in EXCLUDED_COPY_DIR_NAMES


def _should_skip_file(name: str) -> bool:
    for suffix in EXCLUDED_COPY_FILE_SUFFIXES:
        if name.endswith(suffix):
            return True
    return False


def _copytree_ignore(dirpath: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        full = os.path.join(dirpath, name)
        try:
            is_dir = os.path.isdir(full)
        except OSError:
            continue
        if is_dir:
            if _should_skip_dir(name):
                ignored.add(name)
        else:
            if _should_skip_file(name):
                ignored.add(name)
    return ignored


def _count_installable_files(under_ieos_usb: str) -> int:
    n = 0
    for base, dir_names, file_names in os.walk(under_ieos_usb):
        dir_names[:] = [d for d in dir_names if not _should_skip_dir(d)]
        for file_name in file_names:
            if _should_skip_file(file_name):
                continue
            n += 1
    return n


def parse_app_version_from_version_py(contents: str) -> str | None:
    """Return APP_VERSION literal from ieos/version.py body, or None."""
    match = _APP_VERSION_RE.search(contents)
    if not match:
        return None
    return (match.group(1) or match.group(2) or "").strip() or None


def validate_proof_file_binary(data: bytes) -> tuple[bool, str]:
    """True if IEOS_PROOF pairing rules hold."""
    if not data:
        return False, "proof file empty"
    if len(data) % 2 != 0:
        return False, "proof file odd length"
    for i in range(0, len(data), 2):
        char_b = data[i]
        chk = data[i + 1]
        if chk != (char_b & 0xFF):
            return False, f"bad pair at offset {i}"
        try:
            c = chr(char_b)
        except ValueError:
            return False, f"bad char at offset {i}"
        if not c.isascii():
            return False, f"non-ASCII pair at offset {i}"
    return True, ""


def validate_update_payload(source_root: str, current_version: str = APP_VERSION) -> UpdateValidationResult:
    if not os.path.isdir(source_root):
        return UpdateValidationResult(
            ok=False,
            code="INVALID_SOURCE",
            message="Update source is not a directory",
            details=[f"source_root={source_root}"],
        )

    usb_ieos = os.path.join(source_root, DEST_IEOS_SEG)
    if not os.path.isdir(usb_ieos):
        return UpdateValidationResult(
            ok=False,
            code="MISSING_IEOS",
            message="USB has no ieos folder",
            details=[f"expected {DEST_IEOS_SEG}/ at USB root"],
            source_root=source_root,
        )

    proof_path = os.path.join(source_root, IEOS_PROOF)
    if not os.path.isfile(proof_path):
        return UpdateValidationResult(
            ok=False,
            code="MISSING_PROOF",
            message=f"Proof file missing ({IEOS_PROOF})",
            details=[f"expected {proof_path}"],
            source_root=source_root,
        )
    try:
        with open(proof_path, "rb") as f:
            proof_data = f.read()
    except OSError as exc:
        return UpdateValidationResult(
            ok=False,
            code="INVALID_PROOF",
            message="Proof file unreadable",
            details=[str(exc)],
            source_root=source_root,
        )
    proof_ok, proof_err = validate_proof_file_binary(proof_data)
    if not proof_ok:
        return UpdateValidationResult(
            ok=False,
            code="INVALID_PROOF",
            message="Proof verification failed",
            details=[proof_err],
            source_root=source_root,
        )

    version_py = os.path.join(usb_ieos, "version.py")
    if not os.path.isfile(version_py):
        return UpdateValidationResult(
            ok=False,
            code="MISSING_VERSION",
            message="Missing ieos/version.py on USB",
            details=[version_py],
            source_root=source_root,
        )
    try:
        with open(version_py, encoding="utf-8") as f:
            vbody = f.read()
    except OSError as exc:
        return UpdateValidationResult(
            ok=False,
            code="INVALID_VERSION",
            message="Unable to read version.py on USB",
            details=[str(exc)],
            source_root=source_root,
        )
    payload_version = parse_app_version_from_version_py(vbody)
    if not payload_version:
        return UpdateValidationResult(
            ok=False,
            code="INVALID_VERSION",
            message="Could not parse APP_VERSION in ieos/version.py",
            details=[version_py],
            source_root=source_root,
        )
    if _parse_version(payload_version) is None:
        return UpdateValidationResult(
            ok=False,
            code="INVALID_VERSION",
            message="Payload version uses unsupported format",
            details=[payload_version],
            source_root=source_root,
            payload_version=payload_version,
        )

    if not _payload_at_least_installed(payload_version, current_version):
        return UpdateValidationResult(
            ok=False,
            code="VERSION_TOO_OLD",
            message="Installed version is newer than USB",
            details=[f"current={current_version}", f"payload={payload_version}"],
            source_root=source_root,
            payload_version=payload_version,
        )

    files_n = _count_installable_files(usb_ieos)
    if files_n == 0:
        return UpdateValidationResult(
            ok=False,
            code="NO_COPY_TARGETS",
            message="No installable files under USB ieos/",
            details=["Nothing to copy after exclusions"],
            source_root=source_root,
            payload_version=payload_version,
        )

    return UpdateValidationResult(
        ok=True,
        code="READY",
        message="Update package is valid",
        details=[
            f"usb_ieos={usb_ieos}",
            f"target={DEST_IEOS_ROOT}",
            f"files_to_copy={files_n}",
        ],
        source_root=source_root,
        payload_version=payload_version,
        copy_targets_count=files_n,
    )


def validate_update_from_usb() -> UpdateValidationResult:
    mounted = False
    try:
        USBDriveManager.mount_pendrive()
        mounted = True
        source_root = USBDriveManager.get_active_mount_point()
        if not source_root:
            return UpdateValidationResult(
                ok=False,
                code="USB_NOT_MOUNTED",
                message="USB drive is not mounted",
                details=["mount_pendrive returned without active mount point"],
            )
        return validate_update_payload(source_root=source_root)
    except OSError as exc:
        _log.warning("USB validation failed: %s", exc)
        return UpdateValidationResult(
            ok=False,
            code="USB_ERROR",
            message="Unable to access USB drive",
            details=[str(exc)],
        )
    finally:
        if mounted:
            try:
                USBDriveManager.unmount_pendrive()
            except OSError as exc:
                _log.warning("USB unmount after validation failed: %s", exc)


def _build_backup_path(payload_version: str | None) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_text = payload_version or "unknown"
    return os.path.join(BACKUP_ROOT, f"backup-v{version_text}-{stamp}")


def _replace_ieos_from_usb(usb_ieos: str, payload_version: str | None, backup_root: str) -> tuple[bool, UpdateInstallResult | None]:
    """
    Bulk-replace DEST_IEOS_ROOT with usb_ieos. Backup existing tree to backup_root/ieos if present.
    Returns (success, error_result_if_failed).
    """
    os.makedirs(backup_root, exist_ok=True)
    backup_ieos = os.path.join(backup_root, DEST_IEOS_SEG)
    had_existing = os.path.isdir(DEST_IEOS_ROOT)

    if had_existing:
        try:
            shutil.copytree(DEST_IEOS_ROOT, backup_ieos, ignore=_copytree_ignore, dirs_exist_ok=False)
            fsync_tree(backup_ieos)
            fsync_directory(backup_root)
        except OSError as exc:
            return False, UpdateInstallResult(
                ok=False,
                code="BACKUP_FAILED",
                message="Could not backup current ieos",
                details=[str(exc)],
                payload_version=payload_version,
                backup_path=backup_root,
                files_copied=0,
            )

    try:
        if os.path.isdir(DEST_IEOS_ROOT):
            shutil.rmtree(DEST_IEOS_ROOT)
            fsync_directory(os.path.dirname(DEST_IEOS_ROOT))
        shutil.copytree(usb_ieos, DEST_IEOS_ROOT, ignore=_copytree_ignore, dirs_exist_ok=False)
        fsync_tree(DEST_IEOS_ROOT)
        fsync_directory(os.path.dirname(DEST_IEOS_ROOT))
    except OSError as exc:
        _log.exception("ieOS tree replace failed: %s", exc)
        try:
            if os.path.isdir(DEST_IEOS_ROOT):
                shutil.rmtree(DEST_IEOS_ROOT)
                fsync_directory(os.path.dirname(DEST_IEOS_ROOT))
            if had_existing and os.path.isdir(backup_ieos):
                shutil.copytree(backup_ieos, DEST_IEOS_ROOT, ignore=_copytree_ignore, dirs_exist_ok=False)
                fsync_tree(DEST_IEOS_ROOT)
                fsync_directory(os.path.dirname(DEST_IEOS_ROOT))
        except OSError as rollback_exc:
            _log.exception("Rollback after replace failure failed: %s", rollback_exc)
            return False, UpdateInstallResult(
                ok=False,
                code="ROLLBACK_FAILED",
                message="Update failed and rollback failed",
                details=[str(exc), str(rollback_exc)],
                payload_version=payload_version,
                backup_path=backup_root,
                files_copied=0,
            )
        return False, UpdateInstallResult(
            ok=False,
            code="UPDATE_FAILED",
            message="Update failed; rollback completed",
            details=[str(exc)],
            payload_version=payload_version,
            backup_path=backup_root if had_existing else None,
            files_copied=0,
        )

    return True, None


def install_update_from_usb() -> UpdateInstallResult:
    mounted = False
    backup_root: str | None = None
    payload_version: str | None = None
    try:
        USBDriveManager.mount_pendrive()
        mounted = True
        source_root = USBDriveManager.get_active_mount_point()
        if not source_root:
            return UpdateInstallResult(
                ok=False,
                code="USB_NOT_MOUNTED",
                message="USB drive is not mounted",
                details=["mount_pendrive returned without active mount point"],
            )

        validation = validate_update_payload(source_root=source_root)
        payload_version = validation.payload_version
        if not validation.ok:
            return UpdateInstallResult(
                ok=False,
                code=validation.code,
                message=validation.message,
                details=validation.details,
                payload_version=validation.payload_version,
            )

        usb_ieos = os.path.join(source_root, DEST_IEOS_SEG)
        backup_root = _build_backup_path(payload_version)
        ok, err = _replace_ieos_from_usb(usb_ieos, payload_version, backup_root)
        if not ok:
            assert err is not None
            return err

        files_n = validation.copy_targets_count

        return UpdateInstallResult(
            ok=True,
            code="UPDATED",
            message="Update applied successfully",
            details=[
                f"payload={payload_version}",
                f"files_copied={files_n}",
                "Reboot device to run the new version",
            ],
            payload_version=payload_version,
            backup_path=backup_root,
            files_copied=files_n,
        )
    except OSError as exc:
        _log.exception("Update install failed: %s", exc)
        return UpdateInstallResult(
            ok=False,
            code="UPDATE_FAILED",
            message="Update failed unexpectedly",
            details=[str(exc)],
            payload_version=payload_version,
            backup_path=backup_root,
            files_copied=0,
        )
    finally:
        if mounted:
            try:
                USBDriveManager.unmount_pendrive()
            except OSError as exc:
                _log.warning("USB unmount after install failed: %s", exc)


def reboot_device() -> RebootResult:
    try:
        result = subprocess.run(
            ["sudo", "reboot"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RebootResult(
            ok=False,
            code="REBOOT_ERROR",
            message="Failed to request reboot",
            details=[str(exc)],
        )
    if result.returncode != 0:
        err = result.stderr.strip() or "sudo reboot returned non-zero"
        return RebootResult(
            ok=False,
            code="REBOOT_FAILED",
            message="Reboot command was rejected",
            details=[err],
        )
    return RebootResult(
        ok=True,
        code="REBOOTING",
        message="Device reboot initiated",
        details=[],
    )
