from SelectableView import SelectableView
from typing import Callable
from PIL import ImageDraw

class Button(SelectableView):
    def __init__(
        self, x: float, y: float,
        width: float, height: float,
        text: str, callback: Callable,
        enabled: bool = True
    ) -> None:
        super().__init__(x, y, width, height, enabled)
        self.text = text
        self.callback = callback

    def _render_self(
        self, draw: ImageDraw.ImageDraw
    ) -> None:
        bbox = [
            self.abs_x, self.abs_y,
            self.abs_x + self.width,
            self.abs_y + self.height
        ]
        outline = 1 if self.selected else 0
        draw.rectangle(bbox, outline=outline)
        tw, th = draw.textsize(self.text)
        tx = self.abs_x + (self.width - tw) / 2
        ty = self.abs_y + (self.height - th) / 2
        draw.text((tx, ty), self.text, fill=1)

    def on_button_press(self) -> bool:
        if self.callback:
            self.callback()
        return True