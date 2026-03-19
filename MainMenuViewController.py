from TableViewController import TableViewController
from RecordFlowViewController import RecordFlowViewController
from FileSelectViewController import FileSelectViewController


class MainMenuViewController(TableViewController):
    def __init__(self) -> None:
        super().__init__(["Record", "Play"], pop_on_confirm=False)

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == 0:
            self.push_view_controller(RecordFlowViewController())
        else:
            self.push_view_controller(FileSelectViewController())
