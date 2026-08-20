# ieos/TutorialViewController.py
"""Fixed-layout key legend (no scrolling table) before first-run flows."""

from __future__ import annotations

import threading
import time

import gui.core.Display as Display
from gui.core.Display import SCREEN_HEIGHT, SCREEN_WIDTH
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Button import Button
from gui.ui_kit.Views import RectangleView, TextAlignment, TextAnchor, TextView

TUTORIAL_AUTO_ADVANCE_SEC = 15.0

_TITLE = "Keys"
_MARGIN_X = 4
_TITLE_BAR_H = 9
_TITLE_BAR_Y = 0
_BODY_TOP_Y = 3
_BTN_BOTTOM_INSET = 2
_BTN_PAD = 1

_BODY_LINE_1 = "K1 +/GO   K2 back"
_BODY_LINE_2 = "K3 -      BTN GO"
_BODY_LINE_GAP = 2
_TEXT_BOTTOM_PAD = 2


class TutorialViewController(ViewController[bool | None]):
    """Returns True to hide tips next boot, False after Continue/auto, None on KEY2."""

    def __init__(self) -> None:
        super().__init__()
        self._finished = False
        self._auto_thread: threading.Thread | None = None

        self._title_bar = RectangleView(
            _MARGIN_X,
            _TITLE_BAR_Y,
            SCREEN_WIDTH - 2 * _MARGIN_X,
            _TITLE_BAR_H,
            fill=Display.ON,
            outline=None,
            stroke_width=0,
        )
        self._title_bar.selectable = False
        self.view.add_subview(self._title_bar)

        self._title_v = TextView(
            0,
            0,
            text=_TITLE,
            anchor=TextAnchor.LEFT_TOP,
            align=TextAlignment.CENTER,
            fill=Display.OFF,
        )
        self._title_v.selectable = False
        self.view.add_subview(self._title_v)

        self._body_line_1 = TextView(
            0,
            0,
            text=_BODY_LINE_1,
            anchor=TextAnchor.LEFT_TOP,
            align=TextAlignment.CENTER,
            fill=Display.ON,
        )
        self._body_line_1.selectable = False
        self._body_line_1.height += _TEXT_BOTTOM_PAD
        self.view.add_subview(self._body_line_1)
        self._body_line_2 = TextView(
            0,
            0,
            text=_BODY_LINE_2,
            anchor=TextAnchor.LEFT_TOP,
            align=TextAlignment.CENTER,
            fill=Display.ON,
        )
        self._body_line_2.selectable = False
        self._body_line_2.height += _TEXT_BOTTOM_PAD
        self.view.add_subview(self._body_line_2)

        self._btn_continue = Button(
            0,
            0,
            28,
            11,
            "OK",
            callback=lambda: self._finish(False),
            outline_width=1,
        )
        self._btn_no_tips = Button(
            0,
            0,
            36,
            11,
            "Hide",
            callback=lambda: self._finish(True),
            outline_width=1,
        )
        self.view.add_subview(self._btn_continue)
        self.view.add_subview(self._btn_no_tips)

    def on_appear(self) -> None:
        super().on_appear()
        self.on_layout()
        self.selection.select(self._btn_continue)
        self._auto_thread = threading.Thread(target=self._auto_advance, daemon=True, name="tutorial-auto")
        self._auto_thread.start()

    def on_layout(self) -> None:
        self._title_bar.x = _MARGIN_X
        self._title_bar.y = _TITLE_BAR_Y
        self._title_bar.width = SCREEN_WIDTH - 2 * _MARGIN_X
        self._title_bar.height = _TITLE_BAR_H

        tw, th = self._title_v.get_text_size()
        self._title_v.x = int((SCREEN_WIDTH - tw) / 2)
        self._title_v.y = int(_TITLE_BAR_Y + max(0, (_TITLE_BAR_H - th) / 2))

        self._btn_continue.set_size_from_text(space_between_outline_and_text=_BTN_PAD)
        self._btn_no_tips.set_size_from_text(space_between_outline_and_text=_BTN_PAD)
        btn_h = max(self._btn_continue.height, self._btn_no_tips.height)
        btn_y = SCREEN_HEIGHT - btn_h - _BTN_BOTTOM_INSET

        l1w, l1h = self._body_line_1.get_text_size()
        l2w, l2h = self._body_line_2.get_text_size()
        block_h = l1h + _BODY_LINE_GAP + l2h
        body_y = _TITLE_BAR_Y + _TITLE_BAR_H + _BODY_TOP_Y
        if body_y + block_h > btn_y - 2:
            body_y = max(_BODY_TOP_Y, btn_y - 2 - block_h)
        self._body_line_1.x = int((SCREEN_WIDTH - l1w) / 2)
        self._body_line_1.y = int(body_y)
        self._body_line_2.x = int((SCREEN_WIDTH - l2w) / 2)
        self._body_line_2.y = int(body_y + l1h + _BODY_LINE_GAP)

        gap = 4.0
        total_w = self._btn_continue.width + gap + self._btn_no_tips.width
        btn_x0 = (SCREEN_WIDTH - total_w) / 2
        self._btn_continue.x = btn_x0
        self._btn_continue.y = btn_y
        self._btn_no_tips.x = btn_x0 + self._btn_continue.width + gap
        self._btn_no_tips.y = btn_y

    def _auto_advance(self) -> None:
        time.sleep(TUTORIAL_AUTO_ADVANCE_SEC)
        if self._finished:
            return
        self._finished = True
        self.pop_view_controller(False)

    def _finish(self, hide_next_boot: bool) -> None:
        if self._finished:
            return
        self._finished = True
        self.pop_view_controller(hide_next_boot)

    def on_key2_press(self) -> bool:
        if self._finished:
            return True
        self._finished = True
        self.pop_view_controller(None)
        return True
