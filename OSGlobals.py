from __future__ import annotations
import threading
from queue import SimpleQueue
from typing import TYPE_CHECKING, Optional
# Avoid Cyclic Import at runtime (TYPE_CHECKING is False at runtime)
if TYPE_CHECKING:
    from ViewController import ViewController, ViewControllerTransition

OSVersion = "0.2.0.0.dev2"

FRAME_TIME: float = 100 / 1000
POLLING_SLEEP_TIME: float = 50 / 1000

JOIN_TIMEOUT_TIME = 1
KEY_INIT_CHG_WAIT_TIME = 0.5
KEY_PRESSED_CHG_WAIT_TIME = 0.1

_polling = False

_current_view_controller = None
_view_controller_transitions = SimpleQueue()
_view_controller_changed = False

_render_thread = None
_polling_thread = None
_view_controller_thread = None

def on_render_thread() -> bool:
    return threading.current_thread() == _render_thread

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
    if on_render_thread():
        _view_controller_changed = False
    else:
        raise RuntimeError("Cannot clear view controller changed flag from non-render thread")
    
def pop_view_controller_transition() -> ViewControllerTransition:
    global _view_controller_transitions
    print("VC Getting")
    return _view_controller_transitions.get()

def put_view_controller_transition(vc_transition: ViewControllerTransition):
    global _view_controller_transitions
    print("Putting: ", vc_transition)
    _view_controller_transitions.put(vc_transition)
    print("Updated VC Transitions List: ", _view_controller_transitions)

def set_view_controller_thread(vc_thread: threading.Thread):
    # Only allow on main thread
    if threading.current_thread() == threading.main_thread():
        global _view_controller_thread
        _view_controller_thread = vc_thread
    else:
        raise RuntimeError("Cannot set view controller thread from non-main thread")
    
def set_render_thread(render_thread: threading.Thread):
    # Only allow on main thread
    if threading.current_thread() == threading.main_thread():
        global _render_thread
        if _render_thread is not None:
            raise RuntimeError("Render thread already set")
        _render_thread = render_thread
    else:
        raise RuntimeError("Cannot set render thread from non-main thread")
    
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

def stop_polling_input(self):
    global _polling
    _polling = False