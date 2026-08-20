from __future__ import annotations

from datetime import datetime

import gui.core.Main as Main
from gui.ui_kit.DateTimeViewController import DateTimeInputViewController
from gui.ui_kit.KeyboardViewController import KeyboardViewController
from gui.ui_kit.TableViewController import TableViewController


class DemoMenuViewController(TableViewController):
    """Root menu that lets the user launch each demo in turn."""

    ITEMS = ["DateTime", "Table View", "Keyboard"]

    def __init__(self) -> None:
        super().__init__(self.ITEMS)

    # Override _confirm_row so we PUSH a child VC instead of popping.
    def _confirm_row(self, position: int) -> None:
        idx = self._offset + position
        if idx == 0:
            self.push_view_controller(
                DateTimeInputViewController(),
                return_callback=self._on_datetime_return,
            )
        elif idx == 1:
            sample = ["Alpha", "Beta", "Gamma", "Delta",
                      "Epsilon", "Zeta", "Eta", "Theta"]
            self.push_view_controller(TableViewController(sample))
        elif idx == 2:
            self.push_view_controller(
                KeyboardViewController(),
                return_callback=self._on_keyboard_return,
            )

    def _on_datetime_return(self, dt: datetime) -> None:
        pass  # Back to menu

    def _on_keyboard_return(self, text: str) -> None:
        pass  # Back to menu


if __name__ == "__main__":
    Main.main(DemoMenuViewController())
