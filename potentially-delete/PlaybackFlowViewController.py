from __future__ import annotations

from TableViewController import TableViewController
from FileSelectViewController import FileSelectViewController


class PlaybackFlowViewController(TableViewController):
    def __init__(self) -> None:
        super().__init__(["Regular Playback", "Record + Play"], pop_on_confirm=False)

    def did_select_row_at(self, index: int, item: str) -> None:
        mode = "regular" if index == 0 else "record_and_play"
        self.push_view_controller(FileSelectViewController(mode))
