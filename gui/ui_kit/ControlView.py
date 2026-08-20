from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from enum import Enum
from PIL import ImageFont
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import (
    CoordinateView,
    TextView,
    MultilineTextView,
    LineView
)
from gui.ui_kit.InputArrowView import InputArrowView
from gui.utils.InputUtils import InputCode, InputPhase
import threading
import time
import gui.core.Display as Display
import random

import gui.core.Main as Main

KEY_ORDER = [InputCode.KEY1, InputCode.KEY2, InputCode.KEY3]

# Default joystick order for left panel
DEFAULT_JOYSTICK_ORDER = [
    InputCode.UP,
    InputCode.DOWN,
    InputCode.LEFT,
    InputCode.RIGHT,
    InputCode.BUTTON
]

class ControlPanelView(CoordinateView):
    """
    A panel view showing joystick and key help segments.
    Segments auto-hide if disabled or all labels empty.
    Pre-creates all widgets; toggles `.visible` and repositions in `layout()`.
    """
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        joystick_items: Dict[InputCode, str],
        key_items: Dict[InputCode, str],
        controller: Optional[ViewController] = None,
        joystick_order: Optional[List[InputCode]] = None,
        arrow_size: float = 24.0,
        icon_text_padding: float = 8.0,
        help_h_padding: float = 12.0,
        center_h_padding: float = 0.0,
        center_v_padding: float = 0.0,
        sep_padding: float = 6.0,
        sep_width: float = 2.0,
        sep_height: Optional[float] = None,
        joystick_help_en: bool = True,
        key_help_en: bool = True,
        font: Optional[ImageFont.ImageFont] = None
    ) -> None:
        super().__init__(x, y, width, height, controller)
        # config
        self.joystick_items = joystick_items
        self.key_items = key_items
        self.joystick_order = joystick_order or DEFAULT_JOYSTICK_ORDER
        self.arrow_size = arrow_size
        self.icon_text_padding = icon_text_padding
        self.help_h_padding = help_h_padding
        self.center_h_padding = center_h_padding
        self.center_v_padding = center_v_padding
        self.sep_padding = sep_padding
        self.sep_width = sep_width
        self.sep_height = sep_height or height
        self.joystick_help_en = joystick_help_en
        self.key_help_en = key_help_en
        self.font = font or ImageFont.load_default()
        # pre-create segments
        self._create_widgets()
        # initial layout
        self.layout()

    def _create_widgets(self) -> None:
        # joystick arrows & labels
        self.arrow_widgets: Dict[InputCode, InputArrowView] = {}
        self.text_widgets: Dict[InputCode, TextView] = {}
        for code in DEFAULT_JOYSTICK_ORDER:
            arrow = InputArrowView(0, 0, self.arrow_size, code)
            arrow.visible = False
            self.add_subview(arrow)
            self.arrow_widgets[code] = arrow
            label = TextView(0, 0, '', font=self.font, fill=0)
            label.visible = False
            self.add_subview(label)
            self.text_widgets[code] = label
        # key labels
        self.key_widgets: Dict[InputCode, TextView] = {}
        for code in KEY_ORDER:
            label = TextView(0, 0, '', font=self.font, fill=0)
            label.visible = False
            self.add_subview(label)
            self.key_widgets[code] = label
        # separators
        self.sep1 = LineView(0, 0, 0, 0, fill=0, stroke_width=self.sep_width)
        self.sep1.visible = False
        self.add_subview(self.sep1)
        self.sep2 = LineView(0, 0, 0, 0, fill=0, stroke_width=self.sep_width)
        self.sep2.visible = False
        self.add_subview(self.sep2)
        # center
        self.center_view = CoordinateView(0, 0, 0, 0)
        self.center_view.visible = True
        self.add_subview(self.center_view)

    def layout(self) -> None:
        """Reposition and toggle visibility of widgets."""
        w, h = self.width, self.height
        f = self.font
        # segment visibilities
        show_js = self.joystick_help_en and any(
            self.joystick_items.get(c) for c in self.joystick_order
        )
        show_keys = self.key_help_en and any(
            self.key_items.get(c) for c in KEY_ORDER
        )
        # compute panel widths
        left_w = 0
        if show_js:
            max_txt = max((f.getbbox(self.joystick_items.get(c,'')[0]) if self.joystick_items.get(c) else (0,0,0,0))[2]
                          for c in self.joystick_order)
            left_w = self.arrow_size + self.icon_text_padding + max_txt + 2*self.help_h_padding
        right_w = 0
        if show_keys:
            max_k = max((f.getbbox(self.key_items.get(c,'')[0]) if self.key_items.get(c) else (0,0,0,0))[2]
                         for c in KEY_ORDER)
            right_w = max_k + 2*self.help_h_padding
        # separators
        sep1_x = left_w + self.sep_padding if show_js else 0
        sep2_x = w - right_w - self.sep_padding - self.sep_width if show_keys else w
        sy0 = (h - self.sep_height)/2; sy1 = sy0 + self.sep_height
        self.sep1.visible = show_js
        if show_js:
            self.sep1.x1 = self.sep1.x2 = sep1_x
            self.sep1.y1 = sy0; self.sep1.y2 = sy1
        self.sep2.visible = show_keys
        if show_keys:
            self.sep2.x1 = self.sep2.x2 = sep2_x
            self.sep2.y1 = sy0; self.sep2.y2 = sy1
        # layout joystick
        js_codes = [c for c in self.joystick_order if self.joystick_items.get(c)]
        n = len(js_codes)
        for idx,code in enumerate(self.joystick_order):
            arrow = self.arrow_widgets[code]
            txtv = self.text_widgets[code]
            if show_js and code in js_codes:
                frac = (js_codes.index(code)+1)/(n+1)
                yc = frac*h
                arrow.visible=True; arrow.x=self.help_h_padding; arrow.y=yc-self.arrow_size/2
                txt = self.joystick_items[code]
                txtv.visible=True; txtv.text=txt; txtv.font=f
                th = f.getbbox(txt)[3]-f.getbbox(txt)[1]
                txtv.x=self.help_h_padding+self.arrow_size+self.icon_text_padding
                txtv.y=yc-th/2
            else:
                arrow.visible=False; txtv.visible=False
        # layout center
        left_bound = sep1_x + (self.sep_width if show_js else 0)
        right_bound = sep2_x
        cc = self.center_view
        cc.visible=True
        cc.x = left_bound + self.center_h_padding
        cc.y = self.center_v_padding
        cc.width = right_bound-left_bound-2*self.center_h_padding
        cc.height = h-2*self.center_v_padding
        # layout keys
        pos = [0, (h - self.font.getsize('Ay')[1])/2, h-self.font.getsize('Ay')[1]]
        for i,code in enumerate(KEY_ORDER):
            kv = self.key_widgets[code]
            txt = self.key_items.get(code,'')
            if show_keys and txt:
                kv.visible=True; kv.text=txt; kv.font=f
                kv.x=sep2_x+self.sep_width+self.help_h_padding
                kv.y=pos[i]
            else:
                kv.visible=False

class ControlPanelViewController(ViewController[None]):
    """
    Thin controller to embed ControlPanelView, expose center_view for anchoring.
    """
    def __init__(
        self,
        joystick_items: Dict[InputCode,str],
        key_items: Dict[InputCode,str],
        **kwargs
    ) -> None:
        super().__init__()
        # full-screen panel
        panel = ControlPanelView(
            x=0, y=0,
            width=Display.SCREEN_WIDTH,
            height=Display.SCREEN_HEIGHT,
            controller=self,
            joystick_items=joystick_items,
            key_items=key_items,
            **kwargs
        )
        self.view = panel

    @property
    def center_view(self) -> CoordinateView:
        return cast(CoordinateView, self.view.center_view)

class ControlPanelViewTestController(ViewController[None]):
    """
    Test controller for ControlPanelView:
    - Randomizes joystick order on init
    - Toggles each help text on press
    - Animates paddings up/down every 3 sec
    - Displays last selected input in center
    """
    def __init__(
        self
    ) -> None:
        super().__init__()
        # initial help texts
        initial_joystick = {
            InputCode.UP: "Up Help",
            InputCode.DOWN: "Down Help",
            InputCode.LEFT: "Left Help",
            InputCode.RIGHT: "Right Help",
            InputCode.BUTTON: "Button Help"
        }
        initial_keys = {
            KEY_ORDER[0]: "Key1 Help",
            KEY_ORDER[1]: "Key2 Help",
            KEY_ORDER[2]: "Key3 Help"
        }
        # random joystick order
        order = list(initial_joystick.keys())
        random.shuffle(order)

        # create panel view full-screen
        panel = ControlPanelView(
            x=0, y=0,
            width=Display.SCREEN_WIDTH,
            height=Display.SCREEN_HEIGHT,
            controller=self,
            joystick_items=initial_joystick,
            key_items=initial_keys,
            joystick_order=order,
            arrow_size=5.0,
            icon_text_padding=0,
            help_h_padding=0,
            center_h_padding=2,
            center_v_padding=2,
            sep_padding=1,
            sep_width=1,
            sep_height=54,
            joystick_help_en=True,
            key_help_en=True,
            font=ImageFont.load_default()
        )
        self.view = panel

        # keep originals for toggling
        self._orig_joystick = initial_joystick.copy()
        self._orig_keys = initial_keys.copy()

        # create and center last-input TextView in center_view
        font = panel.font
        text = "Last Input:\nNone"

        lv = MultilineTextView(0, 0, text, font=font, fill=0)
        panel.center_view.add_subview(lv)
        self._last_input = lv
        self._update_last_input(None)

        # start padding animation
        self._animating = True
        self._pad_dir = 1
        threading.Thread(target=self._padding_loop, daemon=True).start()

    def _update_last_input(self, code: Optional[InputCode]) -> None:
        text = f"Last Input:\n{code.name if code else 'None'}"
        self._last_input.text = text
        # re-center
        font = self.view.font

        w, h = self._last_input.get_text_size()

        cc = self.view.center_view
        self._last_input.x = (cc.width - w) / 2
        self._last_input.y = (cc.height - h) / 2

    def _padding_loop(self) -> None:
        min_pad, max_pad = 0, 30
        while self._animating:
            time.sleep(3)
            new_hp = self.view.help_h_padding + self._pad_dir
            new_chp = self.view.center_h_padding + self._pad_dir
            new_cvp = self.view.center_v_padding + self._pad_dir
            new_sp = self.view.sep_padding + self._pad_dir
            if not (min_pad <= new_hp <= max_pad):
                self._pad_dir *= -1
                continue
            # apply
            self.view.help_h_padding = new_hp
            self.view.center_h_padding = new_chp
            self.view.center_v_padding = new_cvp
            self.view.sep_padding = new_sp

    def handle_override(
        self,
        code: InputCode,
        phase: InputPhase,
        held: bool = False
    ) -> bool:
        # intercept press events to toggle help and update center
        if phase == InputPhase.PRESS:
            if code in (InputCode.UP, InputCode.DOWN,
                        InputCode.LEFT, InputCode.RIGHT,
                        InputCode.BUTTON):
                # toggle joystick help
                cur = self.view.joystick_items.get(code, '')
                self.view.joystick_items[code] = '' if cur else self._orig_joystick[code]
                self._update_last_input(code)
                return True
            if code in KEY_ORDER:
                cur = self.view.key_items.get(code, '')
                self.view.key_items[code] = '' if cur else self._orig_keys[code]
                self._update_last_input(code)
                return True
        return False

    def on_disappear(self) -> None:
        self._animating = False

if __name__ == "__main__":
    Main.main(ControlPanelViewTestController())