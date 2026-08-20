# ieos/RecordingsFilesViewController.py
from __future__ import annotations

import os

from gui.ui_kit.AlertViewController import AlertViewController
from gui.ui_kit.TableViewController import TableViewController
from gui.utils.usb.USBDriveManager import ensure_recordings_ready, get_recordings_path


class RecordingsFilesViewController(TableViewController):
    """List WAV files on the pendrive /WAV folder with per-file delete."""

    def __init__(self) -> None:
        super().__init__(["Loading..."], pop_on_confirm=False)
        self._loaded = False
        self._pending_delete_error: str | None = None

    def on_appear(self) -> None:
        super().on_appear()
        if self._loaded:
            return
        self._loaded = True
        try:
            ensure_recordings_ready()
        except OSError:
            alert = AlertViewController("No pendrive\nconnected")
            alert.add_option("OK")
            self.push_view_controller(alert, return_callback=lambda _: self.pop_view_controller())
            return
        self._reload_list()

    def _reload_list(self) -> None:
        try:
            names = sorted(
                f for f in os.listdir(get_recordings_path()) if f.lower().endswith(".wav")
            )
        except OSError:
            names = []
        if not names:
            alert = AlertViewController("No WAV files")
            alert.add_option("OK")
            self.push_view_controller(alert, return_callback=lambda _: self.pop_view_controller())
            return
        self.set_items(names)

    def did_select_row_at(self, index: int, item: str) -> None:
        full = os.path.join(get_recordings_path(), item)
        short = item if len(item) <= 16 else item[:15] + "…"
        self._pending_delete_error = None

        def delete_file() -> None:
            try:
                os.remove(full)
            except OSError as e:
                self._pending_delete_error = str(e)[:48]

        alert = AlertViewController(f"Delete\n{short}?")
        alert.add_option("OK", callback=delete_file)
        alert.add_option("Cancel")
        self.push_view_controller(alert, return_callback=lambda _: self._after_delete_confirm())

    def _after_delete_confirm(self) -> None:
        err = self._pending_delete_error
        self._pending_delete_error = None
        if err is not None:
            err_alert = AlertViewController(f"Delete failed:\n{err}")
            err_alert.add_option("OK")
            self.push_view_controller(err_alert, return_callback=lambda _: self._reload_list_after_error())
            return
        self._after_delete_success()

    def _reload_list_after_error(self) -> None:
        try:
            ensure_recordings_ready()
        except OSError:
            self.pop_view_controller()
            return
        self._reload_list_or_pop()

    def _after_delete_success(self) -> None:
        try:
            ensure_recordings_ready()
        except OSError:
            self.pop_view_controller()
            return
        self._reload_list_or_pop()

    def _reload_list_or_pop(self) -> None:
        try:
            names = sorted(
                f for f in os.listdir(get_recordings_path()) if f.lower().endswith(".wav")
            )
        except OSError:
            names = []
        if not names:
            self.pop_view_controller()
            return
        self.set_items(names)
