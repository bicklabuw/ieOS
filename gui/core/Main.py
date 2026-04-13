import logging
import threading
from gui.core.OSGlobals import get_current_view_controller, set_current_view_controller
from gui.core.OSGlobals import get_view_controller_thread, set_view_controller_thread
from gui.core.OSGlobals import set_polling_thread, set_view_controller_transition_thread
from gui.core.OSGlobals import pop_view_controller_transition
from gui.core.OSGlobals import set_view_controller_changed_flag
from gui.core.OSGlobals import set_debug_viewer
from gui.core.OSGlobals import FRAME_TIME, POLLING_SLEEP_TIME
from gui.core.OSGlobals import JOIN_TIMEOUT_TIME
from collections import deque
from typing import Optional
from gui.utils.PlatformUtils import is_raspberry_pi

import argparse

import gui.core.RenderThread as RenderThread
import gui.core.PollingThread as PollingThread
import gui.core.Display as Display

from gui.ui_core.ViewController import ViewController, ViewControllerTransition, ViewControllerTransitionType
from gui.core.logging_config import configure_logging

_log = logging.getLogger(__name__)

VC_Heirarchy = deque()

def update_vc_heirarchy(vc_transition: ViewControllerTransition) -> Optional[ViewController]:
    global VC_Heirarchy
    if vc_transition.type == ViewControllerTransitionType.PUSH:
        VC_Heirarchy.append(vc_transition.vc)
        _log.debug("nav stack after PUSH: %s", list(VC_Heirarchy))
    elif vc_transition.type == ViewControllerTransitionType.SWAP:
        VC_Heirarchy.pop()
        VC_Heirarchy.append(vc_transition.vc)
    elif vc_transition.type == ViewControllerTransitionType.CLEAR:
        VC_Heirarchy.clear()
        VC_Heirarchy.append(vc_transition.vc)
    elif vc_transition.type == ViewControllerTransitionType.POP:
        _log.debug("nav stack before POP: %s", list(VC_Heirarchy))
        VC_Heirarchy.pop()
        return VC_Heirarchy[-1]
    elif vc_transition.type == ViewControllerTransitionType.POP_TO_ROOT:
        # Return the root view controller and clear the heirarchy
        root_vc = VC_Heirarchy.popleft()
        VC_Heirarchy.clear()
        VC_Heirarchy.append(root_vc)
        return root_vc


def change_view_controller(vc_transition: ViewControllerTransition):
    old_vc = get_current_view_controller()
    if old_vc is not None and old_vc.on_disappear is not None:
        old_vc.on_disappear()

    old_vc_thread = get_view_controller_thread()
    if old_vc_thread is not None:
        old_vc_thread.join(JOIN_TIMEOUT_TIME)

        if old_vc_thread.is_alive():
            # Do not abort the transition thread if the previous VC's on_appear
            # is still winding down; continue the navigation transition.
            _log.warning(
                "previous VC on_appear thread still alive after %.1fs join; continuing transition",
                JOIN_TIMEOUT_TIME,
            )

    new_vc = update_vc_heirarchy(vc_transition)
    new_vc = new_vc if new_vc is not None else vc_transition.vc
    set_current_view_controller(new_vc)

    # Run in a separate thread because this allows the view to run something while the
    # View Controller continues to monitor input
    if new_vc.on_appear is not None:
        new_vc_thread = threading.Thread(target=new_vc.on_appear, args=())
        set_view_controller_thread(new_vc_thread)
        new_vc_thread.start()
    else:
        new_vc_thread = None
        set_view_controller_thread(new_vc_thread)

    set_view_controller_changed_flag()


def view_controller_transition_thread(initial_view_controller: ViewController):
    change_view_controller(ViewControllerTransition(initial_view_controller, ViewControllerTransitionType.CLEAR))

    while True:
        # Process view controller transitions
        vc_transition = pop_view_controller_transition()
        if vc_transition is not None:
            _log.info("applying transition: %s", vc_transition)
            change_view_controller(vc_transition)

def start_polling_thread(sleep_time: float, on_disp: bool = True, on_keyboard: bool = False):
    # Create and start the polling thread
    polling_thread = threading.Thread(target=PollingThread.polling_thread, args=(sleep_time, on_disp, on_keyboard), daemon=True)
    set_polling_thread(polling_thread)
    polling_thread.start()

def start_view_controller_transition_thread(initial_view_controller: ViewController):
    # Create and start the view controller transition thread
    transition_thread = threading.Thread(target=view_controller_transition_thread, args=(initial_view_controller,), daemon=True) # Comma is necessary
    set_view_controller_transition_thread(transition_thread)
    transition_thread.start()

def main(initial_view_controller: ViewController):
    parser = argparse.ArgumentParser("Debug Settings")
    parser.add_argument("-k", "--keyboard", action='store_true', help="Enable keyboard input")
    parser.add_argument("-s", "--screen", action='store_true', help="Enable output on OS's screen")
    parser.add_argument("-K", "--keyboard_only", action='store_true', help="Enable keyboard input and disable display input")
    parser.add_argument("-S", "--screen_only", action='store_true', help="Enable output on OS's screen and disable output on display")
    parser.add_argument("-o", "--no_display", action='store_true', help="Only use keyboard input and OS's screen as output. No display needed in this configuration.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging (DEBUG)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet logging (WARNING and above)")

    args = parser.parse_args()
    configure_logging(verbose=args.verbose, quiet=args.quiet)

    is_not_rpi = not is_raspberry_pi()

    disp_in_en = not (args.keyboard_only or args.no_display or is_not_rpi)
    keyboard_en = args.keyboard or args.keyboard_only or args.no_display or is_not_rpi

    disp_out_en = not (args.screen_only or args.no_display or is_not_rpi)
    screen_en = args.screen or args.screen_only or args.no_display or is_not_rpi

    _log.info(
        "starting ieOS main (raspberry_pi=%s, display_in=%s, display_out=%s, keyboard=%s, debug_screen=%s)",
        not is_not_rpi,
        disp_in_en,
        disp_out_en,
        keyboard_en,
        screen_en,
    )

    # Init the display
    if disp_in_en or disp_out_en:
        Display.init()

    if keyboard_en or screen_en:
        from gui.core.DebugViewer import DebugViewer
        set_debug_viewer(DebugViewer((Display.SCREEN_WIDTH, Display.SCREEN_HEIGHT)))

    start_polling_thread(POLLING_SLEEP_TIME, disp_in_en, keyboard_en)
    _log.debug("polling thread started (sleep=%.3fs)", POLLING_SLEEP_TIME)
    start_view_controller_transition_thread(initial_view_controller)
    _log.debug("view-controller transition thread started")

    # Start the render thread (now the main thread)
    _log.info("entering render loop (frame_time=%.3fs)", FRAME_TIME)
    RenderThread.render_thread(FRAME_TIME, disp_out_en, screen_en)
