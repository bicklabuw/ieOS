from TableViewController import TableViewController
from RecordFlowViewController import RecordFlowViewController
from FileSelectViewController import FileSelectViewController
from MicTestViewController import MicTestViewController


class MainMenuViewController(TableViewController):
    def __init__(self) -> None:
        super().__init__(["Record", "Play", "Mic Test"], pop_on_confirm=False)

    def on_key2_press(self) -> bool:
        return True  # no-op: main menu has nothing to go back to

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == 0:
            self.push_view_controller(RecordFlowViewController())
        elif index == 1:
            self.push_view_controller(FileSelectViewController())
        else:
            self.push_view_controller(MicTestViewController())
