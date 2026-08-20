from gui.ui_core.View import View
from gui.ui_kit.Views import LineView
from gui.ui_kit.Label import Label
from gui.utils.InputUtils import InputCode
from gui.ui_kit.InputArrowView import InputArrowView
from typing import Optional
from PIL import ImageFont
import gui.core.Display as Display

class JoystickHintView(View):
    # Default joystick order for left panel
    DEFAULT_JOYSTICK_ORDER = [
        InputCode.UP,
        InputCode.DOWN,
        InputCode.LEFT,
        InputCode.RIGHT,
        InputCode.BUTTON
    ]

    def __init__(self, up_hint: Optional[str] = None, down_hint: Optional[str] = None,
                 left_hint: Optional[str] = None, right_hint: Optional[str] = None,
                 button_hint: Optional[str] = None, font: Optional[ImageFont.ImageFont] = None, 
                 joystick_order: list[InputCode] = DEFAULT_JOYSTICK_ORDER, arrow_size: Optional[int] = None,
                 arrow_outline: int = Display.ON, arrow_fill: Optional[int] = None, arrow_padding: int = 2, arrow_stroke_width: int = 2,
                 border_line_enabled: bool = True, border_line_width: int = 2, 
                 border_line_padding_x: int = 3, border_line_padding_y: int = 5) -> None:
        super().__init__(x=0, y=0)

        self.selectable = False

        self.JOYSTICK_ORDER = joystick_order

        for input in self.DEFAULT_JOYSTICK_ORDER:
            if input not in self.JOYSTICK_ORDER:
                self.JOYSTICK_ORDER.append(input)

        self.joystick_enables  = {
            InputCode.UP: up_hint is not None,
            InputCode.DOWN: down_hint is not None,
            InputCode.LEFT: left_hint is not None,
            InputCode.RIGHT: right_hint is not None,
            InputCode.BUTTON: button_hint is not None
        }

        self.joystick_views = {
            InputCode.UP: View(0, 0),
            InputCode.DOWN: View(0, 0),
            InputCode.LEFT: View(0, 0),
            InputCode.RIGHT: View(0, 0),
            InputCode.BUTTON: View(0, 0)
        }

        for code, view in self.joystick_views.items():
            view.visible = self.joystick_enables[code]
        
        self.arrow_size = arrow_size
        self.arrow_outline = arrow_outline
        self.arrow_fill = arrow_fill
        self.arrow_padding = arrow_padding
        self.arrow_stroke_width = arrow_stroke_width

        self.joystick_arrows = {
            InputCode.UP: InputArrowView(0,0, arrow_size or 0, InputCode.UP),
            InputCode.DOWN: InputArrowView(0,0, arrow_size or 0, InputCode.DOWN),
            InputCode.LEFT: InputArrowView(0,0, arrow_size or 0, InputCode.LEFT),
            InputCode.RIGHT: InputArrowView(0,0, arrow_size or 0, InputCode.RIGHT),
            InputCode.BUTTON: InputArrowView(0,0, arrow_size or 0, InputCode.BUTTON)
        }

        self._font = font or Display.DEF_FONT

        self.joystick_labels = {
            InputCode.UP:  Label(0, 0, up_hint or ""),
            InputCode.DOWN:  Label(0, 0, down_hint or ""),
            InputCode.LEFT:  Label(0, 0, left_hint or ""),
            InputCode.RIGHT:  Label(0, 0, right_hint or ""),
            InputCode.BUTTON:  Label(0, 0, button_hint or "")
        }

        for code, view in self.joystick_views.items():
            print(f"JoystickHintView: Adding joystick view for {code} with visibility {self.joystick_enables[code]}")
            print(f"JoystickHintView: Adding joystick label for {code} with text '{self.joystick_labels[code].text}'")
            print(f"JoystickHintView: Adding joystick arrow for {code} - {self.joystick_arrows[code]}")
            view.add_subview(self.joystick_arrows[code])
            view.add_subview(self.joystick_labels[code])

            self.add_subview(view)

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
    def up_hint(self) -> str:
        return self.joystick_labels[InputCode.UP].text

    @up_hint.setter
    def up_hint(self, value: str) -> None:
        self.joystick_labels[InputCode.UP].text = value

    @property
    def down_hint(self) -> str:
        return self.joystick_labels[InputCode.DOWN].text

    @down_hint.setter
    def down_hint(self, value: str) -> None:
        self.joystick_labels[InputCode.DOWN].text = value

    @property
    def left_hint(self) -> str:
        return self.joystick_labels[InputCode.LEFT].text

    @left_hint.setter
    def left_hint(self, value: str) -> None:
        self.joystick_labels[InputCode.LEFT].text = value

    @property
    def right_hint(self) -> str:
        return self.joystick_labels[InputCode.RIGHT].text

    @right_hint.setter
    def right_hint(self, value: str) -> None:
        self.joystick_labels[InputCode.RIGHT].text = value

    @property
    def button_hint(self) -> str:
        return self.joystick_labels[InputCode.BUTTON].text

    @button_hint.setter
    def button_hint(self, value: str) -> None:
        self.joystick_labels[InputCode.BUTTON].text = value

    @property
    def up_enabled(self) -> bool:
        return self.joystick_enables[InputCode.UP]
    
    @up_enabled.setter
    def up_enabled(self, value: bool) -> None:
        self.joystick_enables[InputCode.UP] = value
        self.joystick_views[InputCode.UP].visible = value

    @property
    def down_enabled(self) -> bool:
        return self.joystick_enables[InputCode.DOWN]
    
    @down_enabled.setter
    def down_enabled(self, value: bool) -> None:
        self.joystick_enables[InputCode.DOWN] = value
        self.joystick_views[InputCode.DOWN].visible = value

    @property
    def left_enabled(self) -> bool:
        return self.joystick_enables[InputCode.LEFT]
    
    @left_enabled.setter
    def left_enabled(self, value: bool) -> None:
        self.joystick_enables[InputCode.LEFT] = value
        self.joystick_views[InputCode.LEFT].visible = value

    @property
    def right_enabled(self) -> bool:
        return self.joystick_enables[InputCode.RIGHT]
    
    @right_enabled.setter
    def right_enabled(self, value: bool) -> None:
        self.joystick_enables[InputCode.RIGHT] = value
        self.joystick_views[InputCode.RIGHT].visible = value

    @property
    def button_enabled(self) -> bool:
        return self.joystick_enables[InputCode.BUTTON]
    
    @button_enabled.setter
    def button_enabled(self, value: bool) -> None:
        self.joystick_enables[InputCode.BUTTON] = value
        self.joystick_views[InputCode.BUTTON].visible = value

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

        if not any(self.joystick_enables.values()):
            self.width = 0
            self.height = 0
            self.x = 0
            self.y = 0
            print("JoystickHintView Layout: No joystick hints visible, setting width and height to 0")
            return

        num_hints = sum(self.joystick_enables.values())

        joystick_hint_widths = {}
        joystick_hint_heights = {}

        for code, label in self.joystick_labels.items():
            joystick_hint_widths[code], joystick_hint_heights[code] = label.get_text_size() if self.joystick_enables[code] else (0, 0)

        max_hint_height = max(
            joystick_hint_heights.values()
        )

        arrow_size = self.arrow_size or max_hint_height

        max_hint_width = max(
            joystick_hint_widths.values()
        )
        max_width = max_hint_width + arrow_size + self.arrow_padding

        self.height = self.superview.height
        self.x = 0
        self.y = 0

        en_ind = 0
        for code in self.JOYSTICK_ORDER:
            if not self.joystick_enables[code]:
                continue

            view = self.joystick_views[code]
            view.width = arrow_size + self.arrow_padding + joystick_hint_widths[code]
            view.height = max(arrow_size, joystick_hint_heights[code])
            view.x = 0
            view.y = (en_ind + 1/2) * self.height / num_hints - view.height / 2

            label = self.joystick_labels[code]
            label.x = arrow_size + self.arrow_padding
            label.y = (view.height - joystick_hint_heights[code]) / 2
            label.font = self._font

            arrow = self.joystick_arrows[code]
            arrow.x = 0
            arrow.y = (view.height - arrow_size) / 2
            arrow.size = arrow_size
            arrow.outline = self.arrow_outline
            arrow.fill = self.arrow_fill
            arrow.stroke_width = self.arrow_stroke_width

            en_ind += 1

        if self.border_line_enabled:
            line_x = self.border_line_padding_x + max_width
            self.width = line_x + self.border_line.stroke_width

            self.border_line.update_line_points(
                line_x,self.border_line_padding_y,
                line_x,self.superview.height - self.border_line_padding_y
            )
            self.border_line.stroke_width = self.border_line_width
            print("JoystickHintView Border Line Layout: X:", self.border_line.x, "Y:", self.border_line.y, "Width:", self.border_line.width, "Height:", self.border_line.height)
            print("JoystickHintView Attributes: Width:", self.width, "Max Width:", max_width, "Height:", self.superview.height)
            print("JoystickHintView X:", self.x, "Y:", self.y)
            print("Border Line Padding X:", self.border_line_padding_x, "Padding Y:", self.border_line_padding_y)
            print("Border Line Stroke Width:", self.border_line.stroke_width)
        else:
            self.width = max_width

        print("JoystickHintView Layout: Width:", self.width, "Height:", self.height)
