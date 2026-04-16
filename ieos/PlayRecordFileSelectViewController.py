# ieos/PlayRecordFileSelectViewController.py
from __future__ import annotations

from gui.ui_kit.FileSelectViewController import FileSelectViewController

from ieos.MicTestViewController import MicTestViewController
from ieos.PlayAndRecordViewController import PlayAndRecordViewController


class PlayRecordFileSelectViewController(FileSelectViewController):
    """WAV picker for play+record, then mic test (selection + levels), then PlayAndRecordViewController."""

    def _got_name(self, name: str | None, file_path: str) -> None:
        if not name:
            return

        def on_mic_step(ok: bool | None) -> None:
            if not ok:
                return
            self.push_view_controller(PlayAndRecordViewController(file_path, name))

        self.push_view_controller(
            MicTestViewController(show_go=True),
            return_callback=on_mic_step,
        )
