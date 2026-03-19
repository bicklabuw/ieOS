from __future__ import annotations

from enum import Enum

import Display
import Main
from SelectionManager import Direction
from ViewController import ViewController
from Views import CoordinateView, RectangleView, TextAnchor, TextView


class KeyboardAction(Enum):
    CHAR = 0
    SPACE = 1
    PREV_PAGE = 2
    NEXT_PAGE = 3
    DELETE = 4
    ENTER = 5
    SHIFT = 6


class KeyboardKeyView(CoordinateView):
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        label: str,
        action: KeyboardAction,
        value: str,
        callback,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height)
        self.action = action
        self.value = value
        self._callback = callback

        self.label_view = TextView(0, 0, text=label, anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.label_view.selectable = False
        self.add_subview(self.label_view)

    def _layout(self, parent_abs_x=0, parent_abs_y=0):
        super()._layout(parent_abs_x, parent_abs_y)
        text_w, text_h = self.label_view.get_text_size()
        self.label_view.x = (self.width - text_w) / 2
        self.label_view.y = (self.height - text_h) / 2

    def _render_self(self, draw):
        draw.rectangle(
            [0, 0, self.width - 1, self.height - 1],
            outline=Display.ON,
            fill=Display.ON if self.selected else Display.OFF,
            width=1,
        )
        self.label_view.fill = Display.OFF if self.selected else Display.ON

    def on_button_press(self) -> bool:
        self._callback(self)
        return True


class KeyboardViewController(ViewController[str]):
    # Base chars (lowercase); shift toggles case.
    BASE_CHARS = list("abcdefghijklmnopqrstuvwxyz") + list("0123456789") + list(".,!?-_/@")
    GRID_COLS = 4
    GRID_ROWS = 2

    def __init__(self, initial_text: str = "", prompt_text: str = "Enter text"):
        super().__init__()
        self.entered_text = initial_text
        self.page_index = 0
        self.shift_active = False

        self.title = TextView(0, 0, text=prompt_text[:9], anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.title.selectable = False

        self.input_panel = RectangleView(x=0, y=0, width=1, height=1, fill=Display.OFF, outline=Display.ON, stroke_width=1)
        self.input_panel.selectable = False

        self.input_value = TextView(0, 0, text="", anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.input_value.selectable = False

        self.view.add_subview(self.title)
        self.view.add_subview(self.input_panel)
        self.view.add_subview(self.input_value)

        self.char_keys: list[KeyboardKeyView] = []
        self._create_keys()
        self._rebuild_pages()
        self._refresh_text_display()
        self._refresh_key_page()

    def _create_keys(self) -> None:
        for _ in range(self.GRID_ROWS * self.GRID_COLS):
            key = KeyboardKeyView(
                x=0, y=0, width=1, height=1,
                label="",
                action=KeyboardAction.CHAR,
                value="",
                callback=self._handle_key_press,
            )
            self.char_keys.append(key)
            self.view.add_subview(key)

        self.right_arrow_key = KeyboardKeyView(
            x=0, y=0, width=1, height=1,
            label=">",
            action=KeyboardAction.NEXT_PAGE,
            value="",
            callback=self._handle_key_press,
        )
        self.left_arrow_key = KeyboardKeyView(
            x=0, y=0, width=1, height=1,
            label="<",
            action=KeyboardAction.PREV_PAGE,
            value="",
            callback=self._handle_key_press,
        )
        self.shift_key = KeyboardKeyView(
            x=0, y=0, width=1, height=1,
            label="SHF",
            action=KeyboardAction.SHIFT,
            value="",
            callback=self._handle_key_press,
        )
        self.space_key = KeyboardKeyView(
            x=0, y=0, width=1, height=1,
            label="SPC",
            action=KeyboardAction.SPACE,
            value=" ",
            callback=self._handle_key_press,
        )
        self.delete_key = KeyboardKeyView(
            x=0, y=0, width=1, height=1,
            label="DEL",
            action=KeyboardAction.DELETE,
            value="",
            callback=self._handle_key_press,
        )
        self.go_key = KeyboardKeyView(
            x=0, y=0, width=1, height=1,
            label="GO",
            action=KeyboardAction.ENTER,
            value="",
            callback=self._handle_key_press,
        )

        self.view.add_subview(self.right_arrow_key)
        self.view.add_subview(self.left_arrow_key)
        self.view.add_subview(self.shift_key)
        self.view.add_subview(self.space_key)
        self.view.add_subview(self.delete_key)
        self.view.add_subview(self.go_key)

    def _rebuild_pages(self) -> None:
        per_page = self.GRID_ROWS * self.GRID_COLS
        self.current_pages: list[list[str]] = []
        for i in range(0, len(self.BASE_CHARS), per_page):
            self.current_pages.append(self.BASE_CHARS[i:i + per_page])

    def _refresh_text_display(self) -> None:
        max_visible = 11
        shown = self.entered_text[-max_visible:] if len(self.entered_text) > max_visible else self.entered_text
        self.input_value.text = shown if shown else "_"

    def _refresh_key_page(self) -> None:
        chars = self.current_pages[self.page_index]
        for index, key in enumerate(self.char_keys):
            if index < len(chars):
                display = chars[index].upper() if self.shift_active else chars[index]
                key.value = display
                key.label_view.text = display
                key.visible = True
                key.selectable = True
            else:
                key.visible = False
                key.selectable = False
        self.shift_key.label_view.text = "SHF^" if self.shift_active else "SHF"

    def _change_page(self, delta: int) -> None:
        old_page = self.page_index
        self.page_index = (self.page_index + delta) % len(self.current_pages)
        if self.page_index == old_page:
            return

        selected = self.selection.current
        persistent_keys = self._bottom_controls() + self._right_col_keys()
        selected_index = self.char_keys.index(selected) if selected in self.char_keys else None

        self._refresh_key_page()

        if selected in persistent_keys:
            return
        if selected_index is not None and self.char_keys[selected_index].visible:
            self.select(self.char_keys[selected_index])
        elif self.char_keys[0].visible:
            self.select(self.char_keys[0])

    def _handle_key_press(self, key: KeyboardKeyView) -> None:
        if key.action == KeyboardAction.CHAR:
            self.entered_text += key.value
            self._refresh_text_display()
        elif key.action == KeyboardAction.SPACE:
            self.entered_text += " "
            self._refresh_text_display()
        elif key.action == KeyboardAction.PREV_PAGE:
            self._change_page(-1)
        elif key.action == KeyboardAction.NEXT_PAGE:
            self._change_page(1)
        elif key.action == KeyboardAction.DELETE:
            self.entered_text = self.entered_text[:-1]
            self._refresh_text_display()
        elif key.action == KeyboardAction.ENTER:
            self.pop_view_controller(self.entered_text)
        elif key.action == KeyboardAction.SHIFT:
            self.shift_active = not self.shift_active
            self._refresh_key_page()

    def on_key1_press(self):
        cur = self.selection.current
        if isinstance(cur, KeyboardKeyView):
            self._handle_key_press(cur)
        return True

    def on_key2_press(self):
        self.pop_view_controller(None)
        return True

    def on_key3_press(self):
        self._change_page(1)
        return True

    def _bottom_controls(self) -> list[KeyboardKeyView]:
        return [self.shift_key, self.space_key, self.delete_key, self.go_key]

    def _right_col_keys(self) -> list[KeyboardKeyView]:
        return [self.right_arrow_key, self.left_arrow_key]

    def _select_nearest_last_row_key(self) -> bool:
        current = self.selection.current
        if current is None:
            return False

        last_row = self.GRID_ROWS - 1
        visible_last_row = [
            key for idx, key in enumerate(self.char_keys)
            if key.visible and (idx // self.GRID_COLS) == last_row
        ]
        if not visible_last_row:
            return False

        cur_cx = current.abs_x + (current.width / 2)
        nearest = min(visible_last_row, key=lambda k: abs((k.abs_x + (k.width / 2)) - cur_cx))
        self.select(nearest)
        return True

    def on_down_press(self):
        current = self.selection.current
        if current in self.char_keys:
            idx = self.char_keys.index(current)
            if (idx // self.GRID_COLS) == (self.GRID_ROWS - 1):
                self.select(self.space_key)
                return True
        return self.selection.move(Direction.DOWN)

    def on_up_press(self):
        if self.selection.current in self._bottom_controls():
            return self._select_nearest_last_row_key()
        return self.selection.move(Direction.UP)

    def on_layout(self):
        col_w = Display.SCREEN_WIDTH / 5
        row_h = Display.SCREEN_HEIGHT / 4

        def cx(col): return round(col * col_w)
        def ry(row): return round(row * row_h)

        # Row 0: title (cols 0–1), input panel + value (cols 2–4)
        _, title_h = self.title.get_text_size()
        self.title.x = cx(0)
        self.title.y = ry(0) + (ry(1) - ry(0) - title_h) / 2

        self.input_panel.x = cx(2)
        self.input_panel.y = ry(0)
        self.input_panel.width = cx(5) - cx(2)
        self.input_panel.height = ry(1) - ry(0)

        _, val_h = self.input_value.get_text_size()
        self.input_value.x = cx(2) + 2
        self.input_value.y = ry(0) + (self.input_panel.height - val_h) / 2

        # Rows 1–2: char keys (cols 0–3)
        key_h = ry(1) - ry(0)
        for idx, key in enumerate(self.char_keys):
            row = idx // self.GRID_COLS
            col = idx % self.GRID_COLS
            key.x = cx(col)
            key.y = ry(1 + row)
            key.width = cx(col + 1) - cx(col)
            key.height = key_h

        # Col 4: right_arrow (row 1), left_arrow (row 2)
        arrow_x = cx(4)
        arrow_w = cx(5) - cx(4)
        self.right_arrow_key.x = arrow_x
        self.right_arrow_key.y = ry(1)
        self.right_arrow_key.width = arrow_w
        self.right_arrow_key.height = key_h

        self.left_arrow_key.x = arrow_x
        self.left_arrow_key.y = ry(2)
        self.left_arrow_key.width = arrow_w
        self.left_arrow_key.height = key_h

        # Row 3: shift (col 0), space (cols 1–2), del (col 3), go (col 4)
        bottom_y = ry(3)
        bottom_h = Display.SCREEN_HEIGHT - bottom_y

        self.shift_key.x = cx(0)
        self.shift_key.y = bottom_y
        self.shift_key.width = cx(1) - cx(0)
        self.shift_key.height = bottom_h

        self.space_key.x = cx(1)
        self.space_key.y = bottom_y
        self.space_key.width = cx(3) - cx(1)
        self.space_key.height = bottom_h

        self.delete_key.x = cx(3)
        self.delete_key.y = bottom_y
        self.delete_key.width = cx(4) - cx(3)
        self.delete_key.height = bottom_h

        self.go_key.x = cx(4)
        self.go_key.y = bottom_y
        self.go_key.width = cx(5) - cx(4)
        self.go_key.height = bottom_h


if __name__ == "__main__":
    Main.main(KeyboardViewController())
