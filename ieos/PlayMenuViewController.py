# ieos/PlayMenuViewController.py
from __future__ import annotations

from gui.ui_kit.TableViewController import TableViewController

from ieos.LiveListenViewController import LiveListenViewController
from ieos.PlayAndRecordViewController import PlayAndRecordViewController
from ieos.PlaybackFileSelectViewController import PlaybackFileSelectViewController
from ieos.PlayRecordFileSelectViewController import PlayRecordFileSelectViewController


class PlayMenuViewController(TableViewController):
    """Choose listen-only vs play+record before opening the WAV list."""

    def __init__(self) -> None:
        super().__init__(["Listen", "Live listen", "Play + record"], pop_on_confirm=False)

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == 0:
            self.push_view_controller(PlaybackFileSelectViewController())
        elif index == 1:
            self.push_view_controller(LiveListenViewController())
        else:
            self.push_view_controller(
                PlayRecordFileSelectViewController(PlayAndRecordViewController),
            )
