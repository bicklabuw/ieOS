from gui.ui_kit.Views import CoordinateView
from PIL import ImageDraw
from typing import Optional, Callable
from gui.utils.InputUtils import InputCode

class InputArrowView(CoordinateView):
    """
    Reusable icon for joystick directions or button press.
    """
    def __init__(
        self,
        x: float,
        y: float,
        size: float,
        code: InputCode,
        outline: Optional[int] = 1,
        fill: Optional[int] = None,
        stroke_width: int = 1
    ) -> None:
        super().__init__(x, y, size, size)
        self.code = code
        self.outline = outline
        self.fill = fill
        self.size = size
        self.stroke_width = stroke_width
        self.selectable = False

    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)

        true_size = self.size + (self.stroke_width if self.outline == 0 else 0)
        self.width = true_size
        self.height = true_size

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        cx = self.size / 2
        cy = self.size / 2
        half = self.size / 2
        if self.code == InputCode.BUTTON:
            draw.ellipse(
                [0, 0,
                  self.size, self.size],
                outline=self.outline,
                fill=self.fill,
                width=self.stroke_width
            )
            return
        if self.code == InputCode.UP:
            pts = [(cx, cy - half), (cx - half, cy + half), (cx + half, cy + half)]
        elif self.code == InputCode.DOWN:
            pts = [(cx, cy + half), (cx - half, cy - half), (cx + half, cy - half)]
        elif self.code == InputCode.LEFT:
            pts = [(cx - half, cy), (cx + half, cy - half), (cx + half, cy + half)]
        elif self.code == InputCode.RIGHT:
            pts = [(cx + half, cy), (cx - half, cy - half), (cx - half, cy + half)]
        else:
            return
        draw.polygon(pts, outline=self.outline, fill=self.fill, width=self.stroke_width)