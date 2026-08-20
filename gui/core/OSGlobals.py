from __future__ import annotations
import logging
import threading
from queue import SimpleQueue
from typing import TYPE_CHECKING, Optional
# Avoid Cyclic Import at runtime (TYPE_CHECKING is False at runtime)
if TYPE_CHECKING:
    from gui.ui_core.ViewController import ViewController, ViewControllerTransition

OSVersion = "0.2.0.0.dev2"

FRAME_TIME: float = 100 / 1000
POLLING_SLEEP_TIME: float = 50 / 1000

JOIN_TIMEOUT_TIME = 1
KEY_INIT_CHG_WAIT_TIME = 0.5
KEY_PRESSED_CHG_WAIT_TIME = 0.1
KEY_REPEAT_INTERVAL = KEY_PRESSED_CHG_WAIT_TIME

_polling = False
_runtime_testbench_input = False
_runtime_testbench_input_lock = threading.Lock()

_current_view_controller = None
_view_controller_transitions = SimpleQueue()
_view_controller_changed = False

_view_controller_transition_thread = None
_polling_thread = None
_view_controller_thread = None

_debug_viewer = None

_log = logging.getLogger(__name__)


def on_view_controller_transition_thread_thread() -> bool:
    return threading.current_thread() == _view_controller_transition_thread

def get_current_view_controller() -> Optional[ViewController]:
    global _current_view_controller
    return _current_view_controller

def set_current_view_controller(vc: ViewController):
    global _current_view_controller
    _current_view_controller = vc

def get_view_controller_thread() -> Optional[threading.Thread]:
    global _view_controller_thread
    return _view_controller_thread

def get_view_controller_changed_flag() -> bool:
    global _view_controller_changed
    return _view_controller_changed

def set_view_controller_changed_flag():
    global _view_controller_changed
    _view_controller_changed = True

def clear_view_controller_changed_flag():
    global _view_controller_changed
    if threading.current_thread() == threading.main_thread():
        _view_controller_changed = False
    else:
        raise RuntimeError("Cannot clear view controller changed flag from non-render (main) thread")

def pop_view_controller_transition() -> ViewControllerTransition:
    global _view_controller_transitions
    t = _view_controller_transitions.get()
    _log.debug("dequeued VC transition (blocked until available): %s", t)
    return t

def put_view_controller_transition(vc_transition: ViewControllerTransition):
    global _view_controller_transitions
    _log.debug("enqueue VC transition: %s", vc_transition)
    _view_controller_transitions.put(vc_transition)

def set_view_controller_thread(vc_thread: threading.Thread):
    # Only allow on main thread
    if on_view_controller_transition_thread_thread():
        global _view_controller_thread
        _view_controller_thread = vc_thread
    else:
        raise RuntimeError("Cannot set view controller thread from non view controller transition thread")

def set_view_controller_transition_thread(view_controller_transition_thread: threading.Thread):
    # Only allow on main thread
    if threading.current_thread() == threading.main_thread():
        global _view_controller_transition_thread
        if _view_controller_transition_thread is not None:
            raise RuntimeError("View Controller Transition Thread thread already set")
        _view_controller_transition_thread = view_controller_transition_thread
    else:
        raise RuntimeError("Cannot set view controller transition thread from non-main thread")

def set_polling_thread(polling_thread: threading.Thread):
    # Only allow on main thread
    if threading.current_thread() == threading.main_thread():
        global _polling_thread
        if _polling_thread is not None:
            raise RuntimeError("Polling thread already set")
        _polling_thread = polling_thread
    else:
        raise RuntimeError("Cannot set polling thread from non-main thread")

def get_polling() -> bool:
    global _polling
    return _polling

def set_polling(value: bool = True):
    global _polling
    _polling = value

def stop_polling_input():
    global _polling
    _polling = False


def set_runtime_testbench_input_enabled(enabled: bool) -> None:
    global _runtime_testbench_input
    with _runtime_testbench_input_lock:
        _runtime_testbench_input = enabled


def get_runtime_testbench_input_enabled() -> bool:
    with _runtime_testbench_input_lock:
        return _runtime_testbench_input

def get_debug_viewer():
    global _debug_viewer
    return _debug_viewer

def set_debug_viewer(debug_viewer):
    global _debug_viewer
    _debug_viewer = debug_viewer


# Requested by testbench / shutdown hooks; render (main) thread calls sys.exit when set.
_process_exit_code: Optional[int] = None
_process_exit_lock = threading.Lock()


def request_process_exit(code: int = 0) -> None:
    """Thread-safe. First non-None request wins until the render thread exits."""
    global _process_exit_code
    with _process_exit_lock:
        if _process_exit_code is None:
            _process_exit_code = code


def peek_process_exit_code() -> Optional[int]:
    """Render thread: if not None, exit the process with this code."""
    with _process_exit_lock:
        return _process_exit_code
