import os
import time

from TableViewController import TableViewController
from USBDriveManager import mount_pendrive, get_recordings_path
from AlertViewController import AlertViewController
from PlayAndRecordViewController import PlayAndRecordViewController


class FileSelectViewController(TableViewController):
    """Shows a list of WAV files from the pendrive for play+record."""

    def __init__(self) -> None:
        super().__init__(["Loading..."], pop_on_confirm=False)
        self._files_loaded = False

    def on_appear(self) -> None:
        super().on_appear()
        if self._files_loaded:
            return
        self._files_loaded = True

        try:
            mount_pendrive()
        except OSError:
            alert = AlertViewController("No pendrive\nconnected")
            alert.add_option("OK")
            self.push_view_controller(alert, return_callback=lambda _: self.pop_view_controller())
            return

        try:
            all_files = sorted([
                f for f in os.listdir(get_recordings_path())
                if f.lower().endswith('.wav')
            ])
        except OSError:
            all_files = []

        if not all_files:
            alert = AlertViewController("No WAV files\nfound")
            alert.add_option("OK")
            self.push_view_controller(alert, return_callback=lambda _: self.pop_view_controller())
            return

        # Update the table with actual files
        self._items = all_files
        self._offset = 0
        self._reload_cells()
        self._update_arrows()

    def did_select_row_at(self, index: int, item: str) -> None:
        file_path = os.path.join(get_recordings_path(), item)
        self.push_view_controller(PlayAndRecordViewController(file_path))
