# ieos/PlaybackFileSelectViewController.py
from __future__ import annotations

import os

from gui.ui_kit.FileSelectViewController import FileSelectViewController
from gui.utils.usb.USBDriveManager import get_recordings_path

from ieos.PlaybackViewController import PlaybackViewController


class PlaybackFileSelectViewController(FileSelectViewController):
    """WAV picker for listen-only playback (no keyboard, no mic test)."""

    def __init__(self) -> None:
        super().__init__(PlaybackViewController)

    def did_select_row_at(self, index: int, item: str) -> None:
        if item in self._sentinel_paths:
            file_path = self._sentinel_paths[item]
        else:
            file_path = os.path.join(get_recordings_path(), item)
        self.push_view_controller(PlaybackViewController(file_path))
