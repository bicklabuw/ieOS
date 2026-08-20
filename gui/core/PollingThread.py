import logging
import time
from typing import Dict
import gui.core.Display as Display
from gui.core.OSGlobals import get_polling, set_polling, get_current_view_controller, get_debug_viewer
from gui.core.OSGlobals import (
    KEY_INIT_CHG_WAIT_TIME,
    KEY_PRESSED_CHG_WAIT_TIME,
    KEY_REPEAT_INTERVAL,
    get_runtime_testbench_input_enabled,
)
from gui.utils.InputUtils import InputCode, InputPhase

_log = logging.getLogger(__name__)


def polling_thread(
    sleep_time: float,
    on_disp: bool = True,
    on_keyboard: bool = False,
    testbench: bool = False,
) -> None:
    """
    Poll hardware inputs at `sleep_time` intervals, dispatching press/hold/release
    events into the current ViewController via on_event(code, phase, held).

    Hold-repeat (periodic HOLD while a key stays down) runs only in the GPIO and
    keyboard branches. When ieOS starts with ``--testbench``, Main disables both
    branches and only drains the synthetic queue—so scenarios that enqueue
    PRESS/RELEASE taps are unaffected by repeat timing.
    """
    _log.info(
        "polling thread running (display_gpio=%s, keyboard=%s, testbench=%s, interval=%.3fs)",
        on_disp,
        on_keyboard,
        testbench,
        sleep_time,
    )
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
        next_hold_at: Dict[InputCode, float] = {code: 0.0 for code in code_to_pin}
        hold_occurred: Dict[InputCode, bool] = {code: False for code in code_to_pin}

    if on_keyboard:
        from gui.core.DebugViewer import DebugViewer
        debug_viewer: DebugViewer = get_debug_viewer()

        prev_keyboard_vals: Dict[InputCode, int] = {code: 0 for code in debug_viewer.code_to_keyboard}
        next_keyboard_hold_at: Dict[InputCode, float] = {
            code: 0.0 for code in debug_viewer.code_to_keyboard
        }
        hold_keyboard_occurred: Dict[InputCode, bool] = {
            code: False for code in debug_viewer.code_to_keyboard
        }

    while get_polling():
        time.sleep(sleep_time)
        vc = get_current_view_controller()
        if vc is None:
            continue

        now = time.time()
        runtime_testbench = testbench or get_runtime_testbench_input_enabled()

        if on_disp and not runtime_testbench:
            for code, pin in code_to_pin.items():
                curr = disp.RPI.digital_read(pin)
                prev = prev_vals[code]

                # Press or repeating hold
                if curr == 1:
                    if prev == 0:
                        vc.on_event(code, InputPhase.PRESS)
                        next_hold_at[code] = (
                            now + KEY_INIT_CHG_WAIT_TIME - KEY_PRESSED_CHG_WAIT_TIME
                        )
                        hold_occurred[code] = False
                    elif now >= next_hold_at[code]:
                        vc.on_event(code, InputPhase.HOLD)
                        hold_occurred[code] = True
                        next_hold_at[code] = now + KEY_REPEAT_INTERVAL

                # Release logic
                elif prev == 1:
                    vc.on_event(code, InputPhase.RELEASE, hold_occurred[code])
                    hold_occurred[code] = False

                prev_vals[code] = curr

        if on_keyboard and not runtime_testbench:
            keys_pressed = debug_viewer.poll_inputs()
            for code, key in debug_viewer.code_to_keyboard.items():
                    curr = 1 if key in keys_pressed else 0
                    prev = prev_keyboard_vals[code]

                    # Press or repeating hold
                    if curr == 1:
                        if prev == 0:
                            _log.debug("keyboard key %r -> %s PRESS", key, code.name)

                            vc.on_event(code, InputPhase.PRESS)
                            next_keyboard_hold_at[code] = (
                                now + KEY_INIT_CHG_WAIT_TIME - KEY_PRESSED_CHG_WAIT_TIME
                            )
                            hold_keyboard_occurred[code] = False
                        elif now >= next_keyboard_hold_at[code]:
                            vc.on_event(code, InputPhase.HOLD)
                            hold_keyboard_occurred[code] = True
                            next_keyboard_hold_at[code] = now + KEY_REPEAT_INTERVAL

                    # Release logic
                    elif prev == 1:
                        vc.on_event(
                            code, InputPhase.RELEASE, hold_keyboard_occurred[code]
                        )
                        hold_keyboard_occurred[code] = False

                    prev_keyboard_vals[code] = curr

        if runtime_testbench:
            from gui.core import testbench_input

            testbench_input.drain_queue_to(vc)
