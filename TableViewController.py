from __future__ import annotations

import threading
import time

import Display
import Main
from ViewController import ViewController
from Views import CoordinateView, RectangleView
from SelectionManager import SelectionManager
from InputArrowView import InputArrowView
from InputUtils import InputCode
from Display import SCREEN_WIDTH, SCREEN_HEIGHT
from PIL import ImageDraw, ImageFont
from typing import Callable

_VISIBLE_COUNT = 3
_ARROW_SIZE = 8
_CELL_HEIGHT = (SCREEN_HEIGHT - 2 * _ARROW_SIZE) // _VISIBLE_COUNT  # 16px


class _CellLabel(CoordinateView):
    _CHAR_HEIGHT: int = 9
    _SCROLL_DELAY: float = 1.2   # seconds before scrolling starts / restarts
    _SCROLL_SPEED: float = 25.0  # pixels per second
    _SCROLL_STEP: float = 0.1    # seconds between scroll updates

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        super().__init__(x, y, width, height)
        self.text: str = ""
        self.fill: int = Display.ON
        self.scroll_offset: float = 0
        self._font: ImageFont.ImageFont = ImageFont.load_default()
        self._scrolling: bool = False
        self.selectable = False

    def _text_width(self) -> float:
        return self._font.getlength(self.text)

    def start_scroll(self) -> None:
        self._scrolling = True
        self.scroll_offset = 0
        t = threading.Thread(target=self._scroll_loop, daemon=True)
        t.start()

    def stop_scroll(self) -> None:
        self._scrolling = False
        self.scroll_offset = 0

    def _scroll_loop(self) -> None:
        pixels_per_step = self._SCROLL_SPEED * self._SCROLL_STEP

        # Initial delay
        steps = int(self._SCROLL_DELAY / self._SCROLL_STEP)
        for _ in range(steps):
            if not self._scrolling:
                return
            time.sleep(self._SCROLL_STEP)

        max_offset = self._text_width() - self.width + TableViewCell._TEXT_PADDING_RIGHT
        if max_offset <= 0:
            return  # text fits, nothing to scroll

        while self._scrolling:
            # Scroll forward
            while self.scroll_offset < max_offset and self._scrolling:
                self.scroll_offset = min(self.scroll_offset + pixels_per_step, max_offset)
                time.sleep(self._SCROLL_STEP)

            # Pause at end
            for _ in range(steps):
                if not self._scrolling:
                    return
                time.sleep(self._SCROLL_STEP)

            # Reset to start
            self.scroll_offset = 0

            # Pause at start before next pass
            for _ in range(steps):
                if not self._scrolling:
                    return
                time.sleep(self._SCROLL_STEP)

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        if self.text:
            text_y = int((self.height - self._CHAR_HEIGHT) // 2)
            draw.text((-int(self.scroll_offset), text_y), self.text, fill=self.fill, font=self._font)


class TableViewCell(CoordinateView):
    _TEXT_PADDING_X: int = 4
    _TEXT_PADDING_RIGHT: int = 8

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        super().__init__(x, y, width, height)
        self._on_highlight: Callable[[], None] | None = None
        self._on_stop_highlight: Callable[[], None] | None = None
        self._on_confirm: Callable[[], None] | None = None
        self._label: _CellLabel | None = None

        self._bg = RectangleView(0, 0, width, height, fill=Display.OFF, outline=None)
        self._bg.selectable = False
        self.add_subview(self._bg)

    @property
    def text(self) -> str:
        return self._label.text if self._label else ""

    @text.setter
    def text(self, value: str) -> None:
        if not value:
            if self._label:
                self._label.stop_scroll()
                self._label.text = ""
            return
        if self._label is None:
            self._label = _CellLabel(
                self._TEXT_PADDING_X, 0,
                self.width - self._TEXT_PADDING_X - self._TEXT_PADDING_RIGHT, self.height,
            )
            if self.selected:
                self._label.fill = Display.OFF
            self.add_subview(self._label)
        self._label.text = value
        # Restart scroll if this cell is currently selected
        if self.selected and self._label:
            self._label.stop_scroll()
            self._label.start_scroll()

    def on_select(self) -> None:
        super().on_select()
        self._bg.fill = Display.ON
        if self._label:
            self._label.fill = Display.OFF
            self._label.start_scroll()
        if self._on_highlight:
            self._on_highlight()

    def on_deselect(self) -> None:
        super().on_deselect()
        self._bg.fill = Display.OFF
        if self._label:
            self._label.fill = Display.ON
            self._label.stop_scroll()
        if self._on_stop_highlight:
            self._on_stop_highlight()

    def on_button_press(self) -> bool:
        if self._on_confirm:
            self._on_confirm()
        return True


class TableViewController(ViewController[str]):
    def __init__(self, items: list[str], pop_on_confirm: bool = True) -> None:
        super().__init__()
        self._pop_on_confirm = pop_on_confirm

        self.selection = SelectionManager(self.view, wrap=False)

        self._items: list[str] = list(items)
        self._offset: int = 0

        arrow_x = (SCREEN_WIDTH - _ARROW_SIZE) // 2

        self._up_arrow = InputArrowView(
            arrow_x, 0, _ARROW_SIZE, InputCode.UP,
            outline=None, fill=Display.ON, stroke_width=1,
        )
        self._up_arrow.selectable = False
        self.view.add_subview(self._up_arrow)

        self._cells: list[TableViewCell] = []
        for i in range(_VISIBLE_COUNT):
            cell = TableViewCell(
                0,
                _ARROW_SIZE + i * _CELL_HEIGHT,
                SCREEN_WIDTH,
                _CELL_HEIGHT,
            )
            cell._on_highlight      = lambda pos=i: self.did_highlight_row_at(self._offset + pos)
            cell._on_stop_highlight = lambda pos=i: self.did_stop_highlighting_row_at(self._offset + pos)
            cell._on_confirm        = lambda pos=i: self._confirm_row(pos)
            self._cells.append(cell)
            self.view.add_subview(cell)

        self._down_arrow = InputArrowView(
            arrow_x,
            _ARROW_SIZE + _VISIBLE_COUNT * _CELL_HEIGHT,
            _ARROW_SIZE,
            InputCode.DOWN,
            outline=None, fill=Display.ON, stroke_width=1,
        )
        self._down_arrow.selectable = False
        self.view.add_subview(self._down_arrow)

        self._reload_cells()
        self._update_arrows()

    def _reload_cells(self) -> None:
        for i, cell in enumerate(self._cells):
            idx = self._offset + i
            if idx < len(self._items):
                cell.text = self._items[idx]
                cell.visible = True
                cell.selectable = True
            else:
                cell.text = ""
                cell.visible = False
                cell.selectable = False

    def _update_arrows(self) -> None:
        self._up_arrow.visible   = self._offset > 0
        self._down_arrow.visible = self._offset + _VISIBLE_COUNT < len(self._items)

    def _confirm_row(self, position: int) -> None:
        idx = self._offset + position
        if idx < len(self._items):
            item = self._items[idx]
            self.did_select_row_at(idx, item)
            if self._pop_on_confirm:
                self.pop_view_controller(item)

    def handle_wrap(self, code: InputCode) -> None:
        if code == InputCode.UP and self._offset > 0:
            self._offset -= 1
            self._reload_cells()
            self._update_arrows()
        elif code == InputCode.DOWN and self._offset + _VISIBLE_COUNT < len(self._items):
            self._offset += 1
            self._reload_cells()
            self._update_arrows()

    def did_highlight_row_at(self, index: int) -> None:
        pass

    def did_stop_highlighting_row_at(self, index: int) -> None:
        pass

    def did_select_row_at(self, index: int, item: str) -> None:
        pass


if __name__ == "__main__":
    vc = TableViewController([
        "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
        "Zeta", "Eta", "Theta",
    ])
    Main.main(vc)
