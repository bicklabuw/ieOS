from __future__ import annotations

import gui.core.Main as Main
from gui.ui_kit.Button import Button
from gui.ui_kit.KeyboardViewController import KeyboardViewController
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import MultilineTextView, TextAlignment, TextAnchor


class KeyboardInputSample(ViewController[str]):
    def __init__(self):
        super().__init__()
        self.entered = ""

        self.title = MultilineTextView(
            0,
            0,
            text="Netflix-style\nkeyboard demo",
            anchor=TextAnchor.LEFT_ASCENDER,
            align=TextAlignment.CENTER,
        )
        self.title.selectable = False
        self.view.add_subview(self.title)

        self.input_button = Button(
            x=0,
            y=0,
            width=20,
            height=12,
            text="Input",
            callback=self._start_input,
        )
        self.input_button.set_size_from_text()

        self.clear_button = Button(
            x=0,
            y=0,
            width=20,
            height=12,
            text="Clear",
            callback=self._clear_text,
        )
        self.clear_button.set_size_from_text()

        self.view.add_subview(self.input_button)
        self.view.add_subview(self.clear_button)

    def _start_input(self) -> None:
        self.push_view_controller(
            KeyboardViewController(initial_text=self.entered, prompt_text="Enter search"),
            return_callback=self._process_text,
        )

    def _clear_text(self) -> None:
        self.entered = ""
        self.title.text = "Cleared\nPress Input"

    def _process_text(self, value: str | None) -> None:
        if value is None:
            self.title.text = "Input cancelled"
            return

        self.entered = value
        preview = self.entered if self.entered else "(empty)"
        self.title.text = f"Result:\n{preview}"

    def on_layout(self):
        title_w, title_h = self.title.get_text_size()
        self.title.x = (self.view.width - title_w) / 2
        self.title.y = 3

        spacing = 7
        total_width = self.input_button.width + self.clear_button.width + spacing
        start_x = (self.view.width - total_width) / 2
        y = title_h + 14

        self.input_button.x = start_x
        self.input_button.y = y

        self.clear_button.x = self.input_button.x + self.input_button.width + spacing
        self.clear_button.y = y


if __name__ == "__main__":
    my_view_controller = KeyboardInputSample()
    Main.main(my_view_controller)
