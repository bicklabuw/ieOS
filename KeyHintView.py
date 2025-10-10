from View import View
from Views import LineView
from Label import Label
from typing import Optional
from PIL import ImageFont
import Display

class KeyHintView(View):
    def __init__(self, key1_hint: Optional[str] = None, key2_hint: Optional[str] = None, key3_hint: Optional[str] = None, 
                 font: Optional[ImageFont.ImageFont] = None, 
                 border_line_enabled: bool = True, border_line_width: int = 2, 
                 border_line_padding_x: int = 3, border_line_padding_y: int = 5) -> None:
        super().__init__(x=0, y=0)

        self.selectable = False

        self.key1_label = Label(0, 0, key1_hint or "")
        self.key2_label = Label(0, 0, key2_hint or "")
        self.key3_label = Label(0, 0, key3_hint or "")

        self.key1_label.visible = key1_hint is not None
        self.key2_label.visible = key2_hint is not None
        self.key3_label.visible = key3_hint is not None

        self.add_subview(self.key1_label)
        self.add_subview(self.key2_label)
        self.add_subview(self.key3_label)

        self._font = font or Display.DEF_FONT

        self.border_line_padding_x = border_line_padding_x
        self.border_line_padding_y = border_line_padding_y
        self.border_line_width = border_line_width

        self.border_line = LineView(
            0, 0,
            0, 0,
            stroke_width=border_line_width
        )
        self.border_line.visible = border_line_enabled

        self.add_subview(self.border_line)

    @property
    def key1_hint(self) -> str:
        return self.key1_label.text

    @key1_hint.setter
    def key1_hint(self, value: str) -> None:
        self.key1_label.text = value

    @property
    def key2_hint(self) -> str:
        return self.key2_label.text

    @key2_hint.setter
    def key2_hint(self, value: str) -> None:
        self.key2_label.text = value
    
    @property
    def key3_hint(self) -> str:
        return self.key3_label.text

    @key3_hint.setter
    def key3_hint(self, value: str) -> None:
        self.key3_label.text = value

    @property
    def key1_enabled(self) -> bool:
        return self.key1_label.visible
    
    @key1_enabled.setter
    def key1_enabled(self, value: bool) -> None:
        self.key1_label.visible = value

    @property
    def key2_enabled(self) -> bool:
        return self.key2_label.visible
    
    @key2_enabled.setter
    def key2_enabled(self, value: bool) -> None:
        self.key2_label.visible = value

    @property
    def key3_enabled(self) -> bool:
        return self.key3_label.visible
    
    @key3_enabled.setter
    def key3_enabled(self, value: bool) -> None:
        self.key3_label.visible = value

    @property
    def border_line_enabled(self) -> bool:
        return self.border_line.visible
    
    @border_line_enabled.setter
    def border_line_enabled(self, value: bool) -> None:
        self.border_line.visible = value

    @property
    def font(self) -> ImageFont.ImageFont:
        return self._font
    
    @font.setter
    def font(self, new_font: Optional[ImageFont.ImageFont]) -> None:
        self._font = new_font or Display.DEF_FONT

    def _layout(self, parent_abs_x=0, parent_abs_y=0) -> None:
        super()._layout(parent_abs_x, parent_abs_y)

        key1_enabled = self.key1_enabled
        key2_enabled = self.key2_enabled
        key3_enabled = self.key3_enabled

        if not (key1_enabled or key2_enabled or key3_enabled):
            self.width = 0
            self.height = 0
            self.x = 0
            self.y = 0
            print("KeyHintView Layout: No key hints visible, setting width and height to 0")
            return

        key1_width, _ = self.key1_label.get_text_size() if key1_enabled else (0, 0)
        key2_width, key2_height = self.key2_label.get_text_size() if key2_enabled else (0, 0)
        key3_width, key3_height = self.key3_label.get_text_size() if key3_enabled else (0, 0)

        max_width = max(
            key1_width,
            key2_width,
            key3_width
        )

        if self.border_line_enabled:
            self.width = self.border_line_padding_x + self.border_line.stroke_width + max_width

            self.border_line.update_line_points(
                0,self.border_line_padding_y,
                0,self.superview.height - self.border_line_padding_y
            )
            self.border_line.stroke_width = self.border_line_width
            print("KeyHintView Border Line Layout: X:", self.border_line.x, "Y:", self.border_line.y, "Width:", self.border_line.width, "Height:", self.border_line.height)
            print("KeyHintView Attributes: Width:", self.width, "Max Width:", max_width, "Height:", self.superview.height)
            print("KeyHintView X:", self.x, "Y:", self.y)
            print("Border Line Padding X:", self.border_line_padding_x, "Padding Y:", self.border_line_padding_y)
            print("Border Line Stroke Width:", self.border_line.stroke_width)
        else:
            self.width = max_width

        self.height = self.superview.height
        self.x = self.superview.width - self.width
        self.y = 0
        print("KeyHintView Layout: Width:", self.width, "Height:", self.height)

        self.key1_label.x = self.width - key1_width
        self.key1_label.y = 0
        self.key1_label.font = self._font

        self.key2_label.x = self.width - key2_width
        self.key2_label.y = (self.superview.height - key2_height) / 2
        self.key2_label.font = self._font

        self.key3_label.x = self.width - key3_width
        self.key3_label.y = self.superview.height - key3_height
        self.key3_label.font = self._font
