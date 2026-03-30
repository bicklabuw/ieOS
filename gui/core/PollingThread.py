import time
from typing import Dict
import gui.core.Display as Display
from gui.core.OSGlobals import get_polling, set_polling, get_current_view_controller, get_debug_viewer
from gui.core.OSGlobals import KEY_INIT_CHG_WAIT_TIME, KEY_PRESSED_CHG_WAIT_TIME
from gui.utils.InputUtils import InputCode, InputPhase


def polling_thread(sleep_time: float, on_disp: bool = True, on_keyboard: bool = False) -> None:
    """
    Poll hardware inputs at `sleep_time` intervals, dispatching press/hold/release
    events into the current ViewController via on_event(code, phase, held).
    """
    set_polling()
    if on_disp:
        disp = Display.disp

        # Map each InputCode to its GPIO pin
        code_to_pin: dict[InputCode, int] = {
            InputCode.KEY1:  disp.RPI.GPIO_KEY1_PIN,
            InputCode.KEY2:  disp.RPI.GPIO_KEY2_PIN,
            InputCode.KEY3:  disp.RPI.GPIO_KEY3_PIN,
            InputCode.UP:       disp.RPI.GPIO_KEY_UP_PIN,
            InputCode.DOWN:     disp.RPI.GPIO_KEY_DOWN_PIN,
            InputCode.LEFT:     disp.RPI.GPIO_KEY_LEFT_PIN,
            InputCode.RIGHT:    disp.RPI.GPIO_KEY_RIGHT_PIN,
            InputCode.BUTTON: disp.RPI.GPIO_KEY_PRESS_PIN,
        }

        # Tracking state per code
        prev_vals: Dict[InputCode, int] = {code: 0 for code in code_to_pin}
        hold_time: Dict[InputCode, float] = {code: 0.0 for code in code_to_pin}
        hold_fired: Dict[InputCode, bool] = {code: False for code in code_to_pin}

    if on_keyboard:
        from gui.core.DebugViewer import DebugViewer
        debug_viewer: DebugViewer = get_debug_viewer()

        prev_keyboard_vals: Dict[InputCode, int] = {code: 0 for code in debug_viewer.code_to_keyboard}
        hold_keyboard_time: Dict[InputCode, float] = {code: 0.0 for code in debug_viewer.code_to_keyboard}
        hold_keyboard_fired: Dict[InputCode, bool] = {code: False for code in debug_viewer.code_to_keyboard}

    while get_polling():
        time.sleep(sleep_time)
        vc = get_current_view_controller()
        if vc is None:
            continue

        now = time.time()
        if on_disp:
            for code, pin in code_to_pin.items():
                curr = disp.RPI.digital_read(pin)
                prev = prev_vals[code]

                # Press or Hold logic
                if curr == 1:
                    if prev == 0:
                        # Initial press
                        vc.on_event(code, InputPhase.PRESS)
                        # Schedule a single hold event
                        hold_time[code] = now + KEY_INIT_CHG_WAIT_TIME - KEY_PRESSED_CHG_WAIT_TIME
                        hold_fired[code] = False
                    elif not hold_fired[code] and now >= hold_time[code]:
                        vc.on_event(code, InputPhase.HOLD)
                        hold_fired[code] = True

                # Release logic
                elif prev == 1:
                    vc.on_event(code, InputPhase.RELEASE, hold_fired[code])
                    hold_fired[code] = False

                prev_vals[code] = curr

        if on_keyboard:
            keys_pressed = debug_viewer.poll_inputs()
            for code, key in debug_viewer.code_to_keyboard.items():
                    curr = 1 if key in keys_pressed else 0
                    prev = prev_keyboard_vals[code]

                    # Press or Hold logic
                    if curr == 1:
                        if prev == 0:
                            print(f"Key Pressed: {key} - Code: {code}")

                            # Initial press
                            vc.on_event(code, InputPhase.PRESS)
                            # Schedule a single hold event
                            hold_keyboard_time[code] = now + KEY_INIT_CHG_WAIT_TIME - KEY_PRESSED_CHG_WAIT_TIME
                            hold_keyboard_fired[code] = False
                        elif not hold_keyboard_fired[code] and now >= hold_keyboard_time[code]:
                            vc.on_event(code, InputPhase.HOLD)
                            hold_keyboard_fired[code] = True

                    # Release logic
                    elif prev == 1:
                        vc.on_event(code, InputPhase.RELEASE, hold_keyboard_fired[code])
                        hold_keyboard_fired[code] = False

                    prev_keyboard_vals[code] = curr
