from unittest import case
from ViewController import ViewController
from View import View
import random
import Display
from typing import Optional, Tuple
import Main
from PIL import ImageDraw
from Views import TextView, LineView, CircleView, RectangleView, TextAnchor, MultilineTextView, TextAlignment, TextAnchor, CoordinateView
import math
import time
import logging
from datetime import datetime
from enum import Enum


"""

class DateTimeViewController(ViewController)
    class TimeInputView(View)
        class CounterView(View)
        class CounterView(View)
        class CounterView(View)
    class DateInputView(View)
        class CounterView(View)
        class CounterView(View)
        class SpecialCounterViewThatsReallyATextViewToSelectTheMonths(View)
- 
self.enabled


----------------
| 00 | 00 | 00 |
----- SEC ------


optional:
- help screen
- start time, end time
- make customizable afterwards
2 States for input
state 1:
    DAY MONTH YEAR
state 2:
    HOUR MINUTE SECOND

       
"""

class InputState(Enum):
    BOTH = 0
    DATE = 1
    TIME = 2
    
# use set_system_time from TimeUtils.py to set the system time
# Margins
MARGIN_LEFT = 40
MARGIN_TOP = 25

# Arrow dimensions for NumberInputView selection indicators
ARROW_SIZE = 5
ARROW_GAP = 2
ARROW_PADDING = ARROW_SIZE + ARROW_GAP  # total space reserved above/below the box


class NumberInputView(CoordinateView):
    def __init__(
        self,
        x=0,
        y=0,
        width=28,
        height=14,
        enabled=True,
        wraparound=True,
        value=0,
        min_value=0,
        max_value=99,
        digit_padding=0
    ):
        super().__init__(x=x, y=y, width=width, height=height)
        self.digit_padding = digit_padding
        self.gui = TextView(x=0, y=0, text="", anchor=TextAnchor.LEFT_TOP)
        self.gui.selectable = False
        self.add_subview(self.gui)

        self.wraparound = wraparound

        if min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")
        if value < min_value or value > max_value:
            logging.getLogger().warning(f"Initial value {value} is out of bounds ({min_value}-{max_value}), setting to min_value {min_value}")
            value = min_value

        self.min_value = min_value
        self.max_value = max_value
        self.enabled = enabled
        self.value = value
        self.outline_y = ARROW_PADDING
        self._refresh_display_text()

    def _format_value_text(self) -> str:
        if self.digit_padding > 0:
            return f"{self.value:0{self.digit_padding}d}"
        return f"{self.value}"

    def _refresh_display_text(self) -> None:
        self.gui.text = self._format_value_text()
        tw, th = self.gui.get_text_size()
        self.gui.x = (self.width - tw) / 2
        self.gui.y = self.outline_y + (self.height - th) / 2
        self.gui.fill = Display.OFF if self.selected else Display.ON

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        box_top = self.outline_y
        draw.rectangle(
            [0, box_top, self.width - 1, box_top + self.height - 1],
            outline=Display.ON,
            fill=Display.ON if self.selected else Display.OFF,
            width=1
        )
        if self.selected and self.enabled:
            cx = self.width / 2
            # Up arrow above the box
            draw.polygon([
                (cx, ARROW_GAP),
                (cx - ARROW_SIZE / 2, box_top),
                (cx + ARROW_SIZE / 2, box_top)
            ], fill=Display.ON)
            # Down arrow below the box
            below = box_top + self.height
            draw.polygon([
                (cx, below + ARROW_SIZE),
                (cx - ARROW_SIZE / 2, below),
                (cx + ARROW_SIZE / 2, below)
            ], fill=Display.ON)

    def on_select(self) -> None:
        super().on_select()
        self._refresh_display_text()

    def on_deselect(self) -> None:
        super().on_deselect()
        self._refresh_display_text()

    def on_up_press(self):
        if self.enabled:
            self.value += 1
            if self.value > self.max_value:
                if self.wraparound:
                    self.value = self.min_value
                else:
                    self.value = self.max_value
            self._refresh_display_text()
        return True

    def on_down_press(self):
        if self.enabled:
            self.value -= 1
            if self.value < self.min_value:
                if self.wraparound:
                    self.value = self.max_value
                else:
                    self.value = self.min_value
            self._refresh_display_text()
        return True

class IndexToStringMappingInputView(NumberInputView):
    def __init__(self, x=0, y=0, width=30, height=14, enabled=True, wraparound=True, value=1, mappings=["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]):
        self.mappings = mappings
        super().__init__(x=x, y=y, width=width, height=height, enabled=enabled, wraparound=wraparound, value=value, min_value=1, max_value=12)
        self._refresh_display_text()

    def _format_value_text(self) -> str:
        return f"{self.mappings[self.value-1]}"

    def on_up_press(self):
        if self.enabled:
            self.value += 1
            if self.value > self.max_value:
                if self.wraparound:
                    self.value = self.min_value
                else:
                    self.value = self.max_value
            self._refresh_display_text()
        return True

    def on_down_press(self):
        if self.enabled:
            self.value -= 1
            if self.value < self.min_value:
                if self.wraparound:
                    self.value = self.max_value
                else:
                    self.value = self.min_value
            self._refresh_display_text()
        return True

class TimeInputView(View):
    def __init__(self, x=0, y=0, width=Display.SCREEN_WIDTH, height=Display.SCREEN_HEIGHT, hint_text="BTN: DONE"):
        super().__init__(x=x, y=y, width=width, height=height)
        self.row_y = 0
        self.row_spacing = 7

        self.hours = NumberInputView(x=0, y=0, width=24, height=14, value=0, min_value=0, max_value=23, digit_padding=2)
        self.minutes = NumberInputView(x=0, y=0, width=24, height=14, value=0, min_value=0, max_value=59, digit_padding=2)
        self.seconds = NumberInputView(x=0, y=0, width=24, height=14, value=0, min_value=0, max_value=59, digit_padding=2)

        self.sep_left = TextView(x=0, y=0, text=":", anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.sep_right = TextView(x=0, y=0, text=":", anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.sep_left.selectable = False
        self.sep_right.selectable = False

        self.hud = TextView(x=0, y=0, text="HRS    MIN    SEC", anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.hud.selectable = False

        _circle_r = 4
        self.hint_circle = CircleView(x=0, y=0, radius=_circle_r)
        self.hint_circle.selectable = False
        self.hint_label = TextView(x=0, y=0, text=hint_text.replace("BTN", ""), anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.hint_label.selectable = False

        self.add_subview(self.sep_left)
        self.add_subview(self.sep_right)
        self.add_subview(self.hud)
        self.add_subview(self.hint_circle)
        self.add_subview(self.hint_label)
        self.add_subview(self.hours)
        self.add_subview(self.minutes)
        self.add_subview(self.seconds)

    def _layout(self, parent_abs_x=0, parent_abs_y=0):
        super()._layout(parent_abs_x, parent_abs_y)
        label_w, label_h = self.hint_label.get_text_size()
        _, hud_h = self.hud.get_text_size()

        # total content height: top-arrow + box + bottom-arrow + gap + hud + gap + hint
        content_h = ARROW_PADDING + self.hours.height + ARROW_SIZE + 4 + hud_h + 3 + label_h
        self.row_y = max(2, (self.height - content_h) // 2)

        total_width = self.hours.width + self.minutes.width + self.seconds.width + (self.row_spacing * 2)
        row_x = (self.width - total_width) / 2

        self.hours.x = row_x
        self.hours.y = self.row_y
        self.minutes.x = self.hours.x + self.hours.width + self.row_spacing
        self.minutes.y = self.row_y
        self.seconds.x = self.minutes.x + self.minutes.width + self.row_spacing
        self.seconds.y = self.row_y

        self.sep_left.x = self.hours.x + self.hours.width + ((self.row_spacing - self.sep_left.width) / 2)
        self.sep_left.y = self.row_y + 2
        self.sep_right.x = self.minutes.x + self.minutes.width + ((self.row_spacing - self.sep_right.width) / 2)
        self.sep_right.y = self.row_y + 2

        hud_w, _ = self.hud.get_text_size()
        self.hud.x = (self.width - hud_w) / 2
        self.hud.y = self.row_y + self.hours.height + ARROW_PADDING + 4

        hint_gap = 3
        hint_total_w = self.hint_circle.width + hint_gap + label_w
        hint_x = (self.width - hint_total_w) / 2
        hint_y = self.hud.y + hud_h + 3
        self.hint_circle.x = hint_x
        self.hint_circle.y = hint_y + (label_h - self.hint_circle.height) / 2
        self.hint_label.x = hint_x + self.hint_circle.width + hint_gap
        self.hint_label.y = hint_y

    def on_select(self):
        super().on_select()
        self.hours.select()

class DateInputView(View):
    def __init__(self, x=0, y=0, width=Display.SCREEN_WIDTH, height=Display.SCREEN_HEIGHT, hint_text="BTN: NEXT"):
        super().__init__(x=x, y=y, width=width, height=height)
        self.row_y = 0
        self.row_spacing = 7

        self.day = NumberInputView(x=0, y=0, width=24, height=14, value=1, min_value=1, max_value=31, digit_padding=2)
        self.month = IndexToStringMappingInputView(x=0, y=0, width=30, height=14, value=1)
        # TODO find a better default value for the year, maybe read from system time?
        self.year = NumberInputView(x=0, y=0, width=32, height=14, value=2026, min_value=1970, max_value=2100, digit_padding=4)

        self.hud = TextView(x=0, y=0, text="DAY   MONTH   YEAR", anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.hud.selectable = False

        _circle_r = 4
        self.hint_circle = CircleView(x=0, y=0, radius=_circle_r)
        self.hint_circle.selectable = False
        self.hint_label = TextView(x=0, y=0, text=hint_text.replace("BTN", ""), anchor=TextAnchor.LEFT_TOP, fill=Display.ON)
        self.hint_label.selectable = False

        self.add_subview(self.hud)
        self.add_subview(self.hint_circle)
        self.add_subview(self.hint_label)
        self.add_subview(self.day)
        self.add_subview(self.month)
        self.add_subview(self.year)

    def _layout(self, parent_abs_x=0, parent_abs_y=0):
        super()._layout(parent_abs_x, parent_abs_y)
        label_w, label_h = self.hint_label.get_text_size()
        _, hud_h = self.hud.get_text_size()

        # total content height: top-arrow + box + bottom-arrow + gap + hud + gap + hint
        content_h = ARROW_PADDING + self.day.height + ARROW_SIZE + 4 + hud_h + 3 + label_h
        self.row_y = max(2, (self.height - content_h) // 2)

        total_width = self.day.width + self.month.width + self.year.width + (self.row_spacing * 2)
        row_x = (self.width - total_width) / 2

        self.day.x = row_x
        self.day.y = self.row_y
        self.month.x = self.day.x + self.day.width + self.row_spacing
        self.month.y = self.row_y
        self.year.x = self.month.x + self.month.width + self.row_spacing
        self.year.y = self.row_y

        hud_w, _ = self.hud.get_text_size()
        self.hud.x = (self.width - hud_w) / 2
        self.hud.y = self.row_y + self.day.height + ARROW_PADDING + 4

        hint_gap = 3
        hint_total_w = self.hint_circle.width + hint_gap + label_w
        hint_x = (self.width - hint_total_w) / 2
        hint_y = self.hud.y + hud_h + 3
        self.hint_circle.x = hint_x
        self.hint_circle.y = hint_y + (label_h - self.hint_circle.height) / 2
        self.hint_label.x = hint_x + self.hint_circle.width + hint_gap
        self.hint_label.y = hint_y

    def on_select(self):
        super().on_select()
        self.day.select()


class DateTimeInputViewController(ViewController[datetime]):
    class DateTimeInputType(Enum):
        BOTH = 0
        DATE = 1
        TIME = 2
    class DateTimeState(Enum):
        DATE = 0
        TIME = 1
    def __init__(self, input_type: DateTimeInputType = DateTimeInputType.BOTH, use_system_time: bool = True):
        super().__init__()
        self.done = False
        # default to date input, but if they only want time input, skip the date input
        self.input_type = input_type
        self.state = self.DateTimeState.TIME if self.input_type == self.DateTimeInputType.TIME else self.DateTimeState.DATE
        
        date_hint = "BTN: DONE" if input_type == self.DateTimeInputType.DATE else "BTN: NEXT"
        self.time_input_view = TimeInputView(x=self.view.x, y=self.view.y)
        self.date_input_view = DateInputView(x=self.view.x, y=self.view.y, hint_text=date_hint)

        if use_system_time:
            now = datetime.now()
            self.time_input_view.hours.value = now.hour
            self.time_input_view.minutes.value = now.minute
            self.time_input_view.seconds.value = now.second
            self.time_input_view.hours._refresh_display_text()
            self.time_input_view.minutes._refresh_display_text()
            self.time_input_view.seconds._refresh_display_text()

            self.date_input_view.day.value = now.day
            self.date_input_view.month.value = now.month
            self.date_input_view.year.value = now.year
            self.date_input_view.day._refresh_display_text()
            self.date_input_view.month._refresh_display_text()
            self.date_input_view.year._refresh_display_text()

        if self.state == self.DateTimeState.DATE:
            self.view.add_subview(self.date_input_view)
            
        elif self.state == self.DateTimeState.TIME:
            self.view.add_subview(self.time_input_view)

        print(self.selection.current_parent)


    def on_button_press(self):
        if self.state == self.DateTimeState.DATE:
            self.state = self.DateTimeState.TIME
            if self.input_type != self.DateTimeInputType.DATE:
                self.view.remove_subview(self.date_input_view)
                self.view.add_subview(self.time_input_view)
                self.select(self.time_input_view)
        else:
            self.pop()
            
        return True
    def pop(self):
        self.date = datetime(year=self.date_input_view.year.value, month=self.date_input_view.month.value, day=self.date_input_view.day.value, hour=self.time_input_view.hours.value, minute=self.time_input_view.minutes.value, second=self.time_input_view.seconds.value)
        self.pop_view_controller(self.date)
        
if __name__ == "__main__":
    my_view_controller = DateTimeInputViewController()
    Main.main(my_view_controller)
