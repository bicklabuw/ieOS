from __future__ import annotations

import threading

from gui.ui_kit.AlertViewController import AlertViewController
from gui.ui_kit.TitleViewController import TitleViewController
from ieos.updater_service import (
    RebootResult,
    UpdateInstallResult,
    UpdateValidationResult,
    install_update_from_usb,
    reboot_device,
    validate_update_from_usb,
)


def _build_status_message(result: UpdateValidationResult) -> str:
    if result.ok:
        return (
            "USB Update Ready\n"
            f"Current: {result.current_version}\n"
            f"Payload: {result.payload_version}\n"
            f"Files: {result.copy_targets_count}\n"
            "Validation only"
        )
    return (
        "USB Update Failed\n"
        f"{result.code}\n"
        f"{result.message}"
    )


class UpdateFromUSBViewController(TitleViewController[None]):
    def __init__(self) -> None:
        super().__init__("Checking USB update...")
        self._checked = False
        self._install_in_progress = False
        self._pop_scheduled = False

    def on_appear(self) -> None:
        super().on_appear()
        if self._checked:
            return
        self._checked = True
        result = validate_update_from_usb()
        if not result.ok:
            self.set_title(_build_status_message(result))
            self._schedule_pop_after_delay()
            return
        self.set_title(_build_status_message(result) + "\nPress button")
        self._show_confirm_apply_alert()

    def _show_confirm_apply_alert(self) -> None:
        alert = AlertViewController("Apply USB\nupdate now?")
        alert.add_option("Install", callback=self._apply_update)
        alert.add_option("Cancel")
        self.push_view_controller(alert)

    def _apply_update(self) -> None:
        if self._install_in_progress:
            return
        self._install_in_progress = True
        self.set_title("Installing\nupdate...")
        threading.Thread(target=self._run_install_update, daemon=True).start()

    def _run_install_update(self) -> None:
        try:
            result = install_update_from_usb()
            self.set_title(_build_install_message(result))
            if result.ok:
                self._show_reboot_alert()
            else:
                self._schedule_pop_after_delay()
        except Exception:
            # Keep UI responsive even on unexpected updater errors.
            self.set_title("Update Failed\nUNKNOWN_ERROR\nCheck logs")
            self._schedule_pop_after_delay()
        finally:
            self._install_in_progress = False

    def _schedule_pop_after_delay(self, delay: float = 2.0) -> None:
        if self._pop_scheduled:
            return
        self._pop_scheduled = True

        def _pop() -> None:
            import time

            time.sleep(delay)
            self.pop_view_controller(None)

        threading.Thread(target=_pop, daemon=True).start()

    def _show_reboot_alert(self) -> None:
        alert = AlertViewController("Update done.\nReboot now?")
        alert.add_option("Reboot", callback=self._request_reboot)
        alert.add_option("Later")
        self.push_view_controller(alert)

    def _request_reboot(self) -> None:
        result = reboot_device()
        self.set_title(_build_reboot_message(result))


def _build_install_message(result: UpdateInstallResult) -> str:
    if result.ok:
        return (
            "Update Applied\n"
            f"Payload: {result.payload_version}\n"
            f"Files: {result.files_copied}\n"
            "Reboot required"
        )
    return (
        "Update Failed\n"
        f"{result.code}\n"
        f"{result.message}"
    )


def _build_reboot_message(result: RebootResult) -> str:
    if result.ok:
        return "Rebooting..."
    return (
        "Reboot Failed\n"
        f"{result.code}\n"
        f"{result.message}"
    )

