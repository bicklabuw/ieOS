# ieos/FilesMenuViewController.py
from __future__ import annotations

import os

from gui.ui_kit.AlertViewController import AlertViewController
from gui.ui_kit.TableViewController import TableViewController
from gui.utils.recording_format import (
    count_usb_input_mics,
    estimate_record_seconds_remaining,
    format_compact_duration_h_m,
)
from gui.utils.usb.USBDriveManager import (
    ensure_recordings_ready,
    get_recordings_filesystem_free_bytes,
    get_recordings_path,
)
from ieos.RecordingsFilesViewController import RecordingsFilesViewController

_ROW_STATS = 0
_ROW_BROWSE = 1
_ROW_DELETE_ALL = 2


class FilesMenuViewController(TableViewController):
    """Pendrive free space (as time) and WAV file management."""

    def __init__(self) -> None:
        super().__init__(
            ["…", "Browse", "Delete all WAVs"],
            pop_on_confirm=False,
        )
        self._opened = False

    def on_appear(self) -> None:
        super().on_appear()
        if self._opened:
            self._refresh_stats_row()
            return
        self._opened = True
        try:
            ensure_recordings_ready()
        except OSError:
            alert = AlertViewController("No pendrive\nconnected")
            alert.add_option("OK")
            self.push_view_controller(alert, return_callback=lambda _: self.pop_view_controller())
            return
        self._refresh_stats_row()

    def _stats_label(self) -> str:
        free_b = get_recordings_filesystem_free_bytes()
        if free_b is None:
            return "Free: ?"
        mics = count_usb_input_mics()
        if mics <= 0:
            return "Free: (no mics)"
        sec = estimate_record_seconds_remaining(free_b, mics)
        mic_lbl = "mic" if mics == 1 else "mics"
        return f"~{format_compact_duration_h_m(sec)} ({mics} {mic_lbl})"

    def _refresh_stats_row(self) -> None:
        items = [self._stats_label(), "Browse", "Delete all WAVs"]
        self.set_items(items)

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == _ROW_STATS:
            self._refresh_stats_row()
            return
        if index == _ROW_BROWSE:
            self.push_view_controller(
                RecordingsFilesViewController(),
                return_callback=lambda _: self._refresh_stats_row(),
            )
            return
        if index == _ROW_DELETE_ALL:

            def delete_all_wavs() -> None:
                path = get_recordings_path()
                try:
                    for name in os.listdir(path):
                        if name.lower().endswith(".wav"):
                            try:
                                os.remove(os.path.join(path, name))
                            except OSError:
                                pass
                except OSError:
                    pass

            alert = AlertViewController("Delete ALL\nWAV on USB?")
            alert.add_option("OK", callback=delete_all_wavs)
            alert.add_option("Cancel")
            self.push_view_controller(alert, return_callback=lambda _: self._refresh_stats_row())
            return
