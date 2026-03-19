from __future__ import annotations

import sounddevice as sd

import Display
import Main
from DateTimeViewController import ARROW_PADDING, ARROW_SIZE, ARROW_GAP
from MicTestViewController import MicTestViewController
from ViewController import ViewController
from Views import CoordinateView, TextView, TextAnchor
from Display import SCREEN_WIDTH, SCREEN_HEIGHT
from PIL import ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Researcher-friendly customization — tweak these freely
# ---------------------------------------------------------------------------

DEFAULT_DURATION   = 10 * 60       # Duration shown on first open (10 min)

MIN_DURATION       = 60            # Smallest timed value; below this → No Limit

MAX_DURATION       = 24 * 3600     # Hard ceiling (24 hours)

# Joystick press: ±N seconds, snapped to a clean multiple
JOY_PRESS_STEP     = 10 * 60       # ±10 min per press

# Joystick hold: two-tier acceleration
JOY_HOLD_TIER1_STEP     = 60 * 60      # ±1 hr  (when duration < tier boundary)
JOY_HOLD_TIER2_STEP     = 6 * 3600     # ±6 hrs (when duration ≥ tier boundary)
JOY_HOLD_TIER_BOUNDARY  = 2 * 3600     # 2 hrs  (threshold between tiers)

# Key1/Key2 fine adjustment
KEY_FINE_STEP      = 60            # ±1 min per press
KEY_COARSE_STEP    = 5 * 60        # ±5 min per hold (snapped)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
_BOX_H      = 14
_BOX_W      = 80
_TITLE_GAP  = 4     # px between title and box slot
_HINT_GAP   = 4     # px between box slot and hint row


# ---------------------------------------------------------------------------
# Duration formatting
# ---------------------------------------------------------------------------
def _format_duration(seconds: int) -> str:
    if seconds == 0:
        return "No Limit"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h == 0:
        return f"{m} min"
    if m == 0:
        return f"{h} hr" if h == 1 else f"{h} hrs"
    return f"{h}:{m:02d}"


# ---------------------------------------------------------------------------
# Display view
# ---------------------------------------------------------------------------
class _DurationDisplayView(CoordinateView):
    """Single-field duration box with up/down arrows when selected."""

    def __init__(self, x: float, y: float, width: float) -> None:
        super().__init__(x, y, width, ARROW_PADDING + _BOX_H + ARROW_SIZE)
        self._seconds: int = 0
        self._font = ImageFont.load_default()
        self.selectable = True

    @property
    def seconds(self) -> int:
        return self._seconds

    @seconds.setter
    def seconds(self, value: int) -> None:
        self._seconds = value
        self._mark_dirty()

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        box_top = ARROW_PADDING
        fill     = Display.ON  if self.selected else Display.OFF
        text_fill = Display.OFF if self.selected else Display.ON

        draw.rectangle(
            [0, box_top, self.width - 1, box_top + _BOX_H - 1],
            fill=fill, outline=Display.ON, width=1,
        )

        text = _format_duration(self._seconds)
        bbox = draw.textbbox((0, 0), text, font=self._font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((self.width - tw) / 2, box_top + (_BOX_H - th) / 2),
            text, fill=text_fill, font=self._font,
        )

        if self.selected:
            cx = self.width / 2
            draw.polygon([
                (cx,                  ARROW_GAP),
                (cx - ARROW_SIZE / 2, box_top),
                (cx + ARROW_SIZE / 2, box_top),
            ], fill=Display.ON)
            below = box_top + _BOX_H
            draw.polygon([
                (cx,                  below + ARROW_SIZE),
                (cx - ARROW_SIZE / 2, below),
                (cx + ARROW_SIZE / 2, below),
            ], fill=Display.ON)

    def on_select(self) -> None:
        super().on_select()
        self._mark_dirty()

    def on_deselect(self) -> None:
        super().on_deselect()
        self._mark_dirty()


# ---------------------------------------------------------------------------
# View controller
# ---------------------------------------------------------------------------
class RecordSetupViewController(ViewController[int]):

    def __init__(self) -> None:
        super().__init__()

        self._title = TextView(
            0, 0, text="Duration",
            anchor=TextAnchor.LEFT_TOP, fill=Display.ON,
        )
        self._title.selectable = False

        self._display = _DurationDisplayView(0, 0, _BOX_W)

        self._hint = TextView(
            0, 0, text="K3: GO",
            anchor=TextAnchor.LEFT_TOP, fill=Display.ON,
        )
        self._hint.selectable = False

        self.view.add_subview(self._title)
        self.view.add_subview(self._display)
        self.view.add_subview(self._hint)

        self._set_duration(DEFAULT_DURATION)

    def on_appear(self) -> None:
        super().on_appear()
        count = sum(
            1 for d in sd.query_devices()
            if d['name'].startswith("USB") and d['max_input_channels'] > 0
        )
        count = min(count, 3)
        noun = "MIC" if count == 1 else "MICS"
        self._hint.text = f"K3: GO ({count} {noun})"

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def on_layout(self) -> None:
        slot_h = ARROW_PADDING + _BOX_H + ARROW_SIZE
        title_w, title_h = self._title.get_text_size()
        hint_w,  hint_h  = self._hint.get_text_size()

        content_h = title_h + _TITLE_GAP + slot_h + _HINT_GAP + hint_h
        top_y = max(2, (SCREEN_HEIGHT - content_h) // 2)

        self._title.x = (SCREEN_WIDTH - title_w) / 2
        self._title.y = top_y

        self._display.x = (SCREEN_WIDTH - _BOX_W) / 2
        self._display.y = top_y + title_h + _TITLE_GAP

        self._hint.x = (SCREEN_WIDTH - hint_w) / 2
        self._hint.y = self._display.y + slot_h + _HINT_GAP

    # ------------------------------------------------------------------
    # Duration helpers
    # ------------------------------------------------------------------
    def _set_duration(self, seconds: int) -> None:
        if seconds < 0:
            seconds = 0
        if 0 < seconds < MIN_DURATION:
            seconds = 0         # snap below minimum to No Limit
        if seconds > MAX_DURATION:
            seconds = MAX_DURATION
        self._display.seconds = seconds

    def _snap_up(self, seconds: int, step: int) -> int:
        return (seconds // step + 1) * step

    def _snap_down(self, seconds: int, step: int) -> int:
        return max(0, (seconds - 1) // step * step)

    # ------------------------------------------------------------------
    # Joystick UP/DOWN — coarse, snapped navigation
    # ------------------------------------------------------------------
    def on_up_press(self) -> bool:
        self._set_duration(self._snap_up(self._display.seconds, JOY_PRESS_STEP))
        return True

    def on_up_hold(self) -> bool:
        dur  = self._display.seconds
        step = JOY_HOLD_TIER2_STEP if dur >= JOY_HOLD_TIER_BOUNDARY else JOY_HOLD_TIER1_STEP
        self._set_duration(self._snap_up(dur, step))
        return True

    def on_down_press(self) -> bool:
        self._set_duration(self._snap_down(self._display.seconds, JOY_PRESS_STEP))
        return True

    def on_down_hold(self) -> bool:
        dur  = self._display.seconds
        step = JOY_HOLD_TIER2_STEP if dur >= JOY_HOLD_TIER_BOUNDARY else JOY_HOLD_TIER1_STEP
        self._set_duration(self._snap_down(dur, step))
        return True

    # ------------------------------------------------------------------
    # Key1 / Key2 — fine ±1 min, hold ±5 min
    # ------------------------------------------------------------------
    def on_key1_press(self) -> None:
        self._set_duration(self._display.seconds + KEY_FINE_STEP)

    def on_key1_hold(self) -> None:
        self._set_duration(self._snap_up(self._display.seconds, KEY_COARSE_STEP))

    def on_key2_press(self) -> None:
        self._set_duration(self._display.seconds - KEY_FINE_STEP)

    def on_key2_hold(self) -> None:
        self._set_duration(self._snap_down(self._display.seconds, KEY_COARSE_STEP))

    # ------------------------------------------------------------------
    # Key3 — confirm
    # ------------------------------------------------------------------
    def on_key3_press(self) -> None:
        self.pop_view_controller(self._display.seconds)

    # ------------------------------------------------------------------
    # Left — mic test
    # ------------------------------------------------------------------
    def on_left_press(self) -> bool:
        self.push_view_controller(MicTestViewController())
        return True

    # ------------------------------------------------------------------
    # Button — reset to default
    # ------------------------------------------------------------------
    def on_button_press(self) -> bool:
        self._set_duration(DEFAULT_DURATION)
        return True


if __name__ == "__main__":
    vc = RecordSetupViewController()
    Main.main(vc)
