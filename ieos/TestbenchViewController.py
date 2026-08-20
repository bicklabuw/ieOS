# ieos/TestbenchViewController.py
from __future__ import annotations

import threading
import time

from gui.core.OSGlobals import get_current_view_controller
from gui.ui_kit.AlertViewController import AlertViewController
from gui.ui_kit.TableViewController import TableViewController
from gui.ui_kit.TitleViewController import TitleViewController
from ieos.testbench.runner import SettingsTestbenchResult, start_settings_run
from ieos.updater_service import reboot_device


class TestbenchMenuViewController(TableViewController):
    _ROW_QUICK = 0
    _ROW_LONG = 1

    def __init__(self) -> None:
        super().__init__(["Quick testbench", "Long testbench"], pop_on_confirm=False)

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == self._ROW_QUICK:
            self._confirm_run("quick", "Quick")
        elif index == self._ROW_LONG:
            self._confirm_run("long", "Long")

    def _confirm_run(self, mode: str, label: str) -> None:
        alert = AlertViewController(f"{label} testbench\nNeeds USB+mics\nReboots after")
        alert.pop_after_callback = False
        alert.add_option("Run", callback=lambda: self._start_run(mode))
        alert.add_option("Cancel")
        self.push_view_controller(alert)

    def _start_run(self, mode: str) -> None:
        from ieos.MainMenuViewController import MainMenuViewController

        self.replace_root_view_controller(MainMenuViewController())
        start_settings_run(mode, self._show_result)

    def _show_result(self, result: SettingsTestbenchResult) -> None:
        current = get_current_view_controller()
        if current is not None:
            current.push_view_controller(TestbenchResultViewController(result))


class TestbenchResultViewController(TitleViewController[None]):
    _REBOOT_DELAY_SEC = 4.0

    def __init__(self, result: SettingsTestbenchResult) -> None:
        super().__init__(_build_result_message(result))
        self._result = result
        self._reboot_started = False

    def on_appear(self) -> None:
        super().on_appear()
        if self._reboot_started:
            return
        self._reboot_started = True
        threading.Thread(target=self._reboot_after_delay, daemon=True).start()

    def _reboot_after_delay(self) -> None:
        time.sleep(self._REBOOT_DELAY_SEC)
        result = reboot_device()
        if result.ok:
            self.set_title("Rebooting...")
        else:
            self.set_title(f"Reboot Failed\n{result.code}\n{result.message}")


def _build_result_message(result: SettingsTestbenchResult) -> str:
    mode = result.mode.capitalize()
    run = result.run_result
    usb = result.usb_report_result
    status = "PASS" if run.success else "FAIL"
    if usb.ok:
        report_line = "Report saved"
    else:
        report_line = f"Report failed\n{usb.code}"
    return f"{mode} {status}\n{run.message}\n{report_line}\nRebooting soon"
