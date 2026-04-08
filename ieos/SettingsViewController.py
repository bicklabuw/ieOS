from gui.ui_kit.TableViewController import TableViewController
from ieos.version import APP_VERSION


class SettingsViewController(TableViewController):
    def __init__(self) -> None:
        super().__init__([f"Version {APP_VERSION}"], pop_on_confirm=False)

    def did_select_row_at(self, index: int, item: str) -> None:
        # Read-only settings row for now.
        return
