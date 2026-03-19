from __future__ import annotations

import Display
import Main
from ViewController import ViewController
from TableViewController import TableViewController, _CELL_HEIGHT
from Views import MultilineTextView, TextAnchor, TextAlignment, RectangleView
from Display import SCREEN_WIDTH, SCREEN_HEIGHT
from Button import Button


_ITEMS     = ["1 min", "5 min", "10 min"]
_DURATIONS = [60,      300,     600]

_BAR_MAX_W = 28
_BAR_H     = 6
_BAR_X     = SCREEN_WIDTH - _BAR_MAX_W - 4


class DurationTableViewController(TableViewController):
    def __init__(self, items: list[str], durations: list[int]) -> None:
        self._durations = durations
        self._max_duration = max(durations)
        super().__init__(items)

        for cell in self._cells:
            bar = RectangleView(
                _BAR_X, (_CELL_HEIGHT - _BAR_H) // 2,
                2, _BAR_H,
                fill=Display.ON, outline=None,
            )
            bar.selectable = False
            cell.add_subview(bar)
            cell._dur_bar = bar

        self._reload_cells()

    def _reload_cells(self) -> None:
        super()._reload_cells()
        for i, cell in enumerate(self._cells):
            if not hasattr(cell, '_dur_bar'):
                continue
            idx = self._offset + i
            if idx < len(self._items):
                bar_w = max(2, int(self._durations[idx] / self._max_duration * _BAR_MAX_W))
                cell._dur_bar.width = bar_w
                cell._dur_bar.visible = True
            else:
                cell._dur_bar.visible = False


class CustomTableViewSample(ViewController):
    def __init__(self) -> None:
        super().__init__()

        self.status = MultilineTextView(
            0, 0,
            text="No duration\nchosen.",
            anchor=TextAnchor.LEFT_ASCENDER,
            align=TextAlignment.CENTER,
        )
        self.status.selectable = False
        self.view.add_subview(self.status)

        self.pick_button = Button(
            x=0, y=40,
            width=20, height=12,
            text="Pick",
            callback=self._open_picker,
        )
        self.pick_button.set_size_from_text()
        self.view.add_subview(self.pick_button)

    def _open_picker(self) -> None:
        self.push_view_controller(
            DurationTableViewController(_ITEMS, _DURATIONS),
            return_callback=self._handle_selection,
        )

    def _handle_selection(self, item: str | None) -> None:
        if item is None:
            self.status.text = "Cancelled."
            return
        self.status.text = f"Chosen:\n{item}"

    def on_layout(self) -> None:
        label_w, label_h = self.status.get_text_size()
        self.status.x = (self.view.width - label_w) / 2
        self.status.y = 3

        self.pick_button.x = (self.view.width - self.pick_button.width) / 2
        self.pick_button.y = self.status.y + label_h + 8


if __name__ == "__main__":
    Main.main(CustomTableViewSample())
