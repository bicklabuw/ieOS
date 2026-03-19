import os

from TableViewController import TableViewController
from USBDriveManager import mount_pendrive, get_recordings_path
from AlertViewController import AlertViewController
from PlayAndRecordViewController import PlayAndRecordViewController
from KeyboardViewController import KeyboardViewController

_HOME_DIR = os.path.expanduser("~")


class FileSelectViewController(TableViewController):
    """Shows a list of WAV files from the pendrive for play+record.
    WAV files found in ~ are pinned as sentinels at the top of the list
    and played from ~ rather than from the USB drive.
    """

    def __init__(self) -> None:
        home_wavs = sorted(
            f for f in os.listdir(_HOME_DIR) if f.lower().endswith('.wav')
        )
        self._sentinel_paths: dict[str, str] = {
            f: os.path.join(_HOME_DIR, f) for f in home_wavs
        }
        super().__init__(["Loading..."], pop_on_confirm=False, sentinel_items=home_wavs)
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

        if not all_files and not self._sentinel_paths:
            alert = AlertViewController("No WAV files\nfound")
            alert.add_option("OK")
            self.push_view_controller(alert, return_callback=lambda _: self.pop_view_controller())
            return

        self.set_items(all_files)

    def did_select_row_at(self, index: int, item: str) -> None:
        if item in self._sentinel_paths:
            file_path = self._sentinel_paths[item]
        else:
            file_path = os.path.join(get_recordings_path(), item)
        self.push_view_controller(
            KeyboardViewController(prompt_text="Name?"),
            return_callback=lambda name: self._got_name(name, file_path),
        )

    def _got_name(self, name: str | None, file_path: str) -> None:
        if not name:
            return
        self.push_view_controller(PlayAndRecordViewController(file_path, name))
