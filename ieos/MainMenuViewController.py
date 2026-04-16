from gui.ui_kit.TableViewController import TableViewController
from ieos.FilesMenuViewController import FilesMenuViewController
from ieos.RecordFlowViewController import RecordFlowViewController
from ieos.MicTestViewController import MicTestViewController
from ieos.PlayAndRecordViewController import PlayAndRecordViewController
from ieos.SettingsViewController import SettingsViewController
from ieos.PlayRecordFileSelectViewController import PlayRecordFileSelectViewController


class MainMenuViewController(TableViewController):
    def __init__(self) -> None:
        super().__init__(["Record", "Play", "Mic Test", "Files", "Settings"], pop_on_confirm=False)

    def on_key2_press(self) -> bool:
        return True  # no-op: main menu has nothing to go back to

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == 0:
            self.push_view_controller(RecordFlowViewController())
        elif index == 1:
            self.push_view_controller(
                PlayRecordFileSelectViewController(PlayAndRecordViewController),
            )
        elif index == 2:
            self.push_view_controller(MicTestViewController())
        elif index == 3:
            self.push_view_controller(FilesMenuViewController())
        else:
            self.push_view_controller(SettingsViewController())
