from typing import Callable
from PIL import ImageDraw
from View import View
from Label import CenteredLabel

class Button(View):
    def __init__(
        self, x: float, y: float,
        width: float, height: float,
        text: str, callback: Callable,
        outline_width: int = 1,
        enabled: bool = True
    ) -> None:
        super().__init__(x, y, width, height, selectable=enabled)
        self._label = CenteredLabel(text=text)
        self._label.selectable = False
        self.add_subview(self._label)

        self.callback = callback
        self.outline_width = outline_width

    def _render_self(
        self, draw: ImageDraw.ImageDraw
    ) -> None:
        
        rect_outline_width = self.outline_width
        bbox = [
            0, 0,
            self.width-1,
            self.height-1
        ]
        outline = 0
        fill = 0 if self.selected else 1
        text_fill = 1 if self.selected else 0
        draw.rectangle(bbox, outline=outline, fill=fill, width=rect_outline_width)

        self._label.fill = text_fill
        # left, top, right, bottom = draw.textbbox((0, 0), text=self._label.text)
        # tw, th = right - left, bottom - top
        # print(f"Button text size: {tw}x{th}")
        # print(f"Button position: {self.abs_x}, {self.abs_y}")
        # print(f"Button size: {self.width}x{self.height}")
        # print(f"Button text: {self._label.text}")
        # tx = (self.width - tw) / 2
        # ty = (self.height - th) / 2
        # print(f"Button text position: {tx}, {ty}")
        # print()
        # draw.text((tx, ty), self._label.text, fill=text_fill, anchor="lt")

    @property
    def text(self) -> str:
        return self._label.text
    
    @text.setter
    def text(self, value: str) -> None:
        if not value:
            print("Button text cannot be empty.")
            return
        self._label.text = value

    def set_size_from_text(self, space_between_outline_and_text: int = 1) -> None:
        """
        Adjust the button size based on the text size.
        """
        if not self._label.text:
            print("Button text is empty, cannot set size.")
            return
        width, height = self._label.get_text_size()

        self.width = width + 2 * (self.outline_width + space_between_outline_and_text)
        self.height = height + 2 * (self.outline_width + space_between_outline_and_text)
        print(f"Button size set to: {self.width}x{self.height}")
        print(f"Button text: {self._label.text}")
        print(f"Button position: {self.abs_x}, {self.abs_y}")

        return self.width, self.height


    def on_button_press(self) -> bool:
        if self.callback:
            self.callback()
        return True