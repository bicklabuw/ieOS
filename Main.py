import threading
from OSGlobals import get_current_view_controller, set_current_view_controller
from OSGlobals import get_view_controller_thread, set_view_controller_thread
from OSGlobals import set_polling_thread, set_view_controller_transition_thread
from OSGlobals import pop_view_controller_transition
from OSGlobals import set_view_controller_changed_flag
from OSGlobals import set_debug_viewer
from OSGlobals import FRAME_TIME, POLLING_SLEEP_TIME
from OSGlobals import JOIN_TIMEOUT_TIME
from collections import deque
from typing import Optional
from PlatformUtils import is_raspberry_pi

import argparse

import RenderThread
import PollingThread
import Display

from ViewController import ViewController, ViewControllerTransition, ViewControllerTransitionType

VC_Heirarchy = deque()

def update_vc_heirarchy(vc_transition: ViewControllerTransition) -> Optional[ViewController]:
    global VC_Heirarchy
    if vc_transition.type == ViewControllerTransitionType.PUSH:
        VC_Heirarchy.append(vc_transition.vc)
        print(VC_Heirarchy)
    elif vc_transition.type == ViewControllerTransitionType.SWAP:
        VC_Heirarchy.pop()
        VC_Heirarchy.append(vc_transition.vc)
    elif vc_transition.type == ViewControllerTransitionType.CLEAR:
        VC_Heirarchy.clear()
        VC_Heirarchy.append(vc_transition.vc)
    elif vc_transition.type == ViewControllerTransitionType.POP:
        print("Popping VC: ", VC_Heirarchy)
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
            raise RuntimeError("Previous View Did Not Finish Running After on_disappear()")
    
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

# def present_view(self, view: View):
#     # Check if current thread is active_view_thread then append to queue to wait for main thread to update the view
#     if threading.current_thread() is self.active_view_thread:
#         self.present_view_queue.append(view)
#         return
    
#     # Not run in separate thread because it should be ending all actions in the view
#     if self.active_view is not None and self.active_view.on_disappear is not None:
#         self.active_view.on_disappear()

#     # TODO: Determine if error or just warning if active_view_thread is still running 
#     # after on_disappear
#     # Give thread enough time to join and then confirm active_view_thread is no longer running
#     # so deactivated views are not running
#     if self.active_view_thread is not None:
#         self.active_view_thread.join(JOIN_TIMEOUT_TIME)

#         if self.active_view_thread.is_alive():
#             raise RuntimeError("Previous View Did Not Finish Running After on_disappear()")
    
#     self.active_view = view
#     view.draw()
    
#     # Run in a separate thread because this allows the view to run something while the 
#     # View Controller continues to monitor input
#     if self.active_view.on_appear is not None:
#         self.active_view_thread = threading.Thread(target=self.active_view.on_appear, args=())
#         self.active_view_thread.start()
#     else:
#         self.active_view_thread = None

def view_controller_transition_thread(initial_view_controller: ViewController):
    change_view_controller(ViewControllerTransition(initial_view_controller, ViewControllerTransitionType.CLEAR))

    while True:
        # Process view controller transitions
        vc_transition = pop_view_controller_transition()
        print("Got VC: ", vc_transition)
        if vc_transition is not None:
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

    args = parser.parse_args()

    is_not_rpi = not is_raspberry_pi()
    
    disp_in_en = not (args.keyboard_only or args.no_display or is_not_rpi)
    keyboard_en = args.keyboard or args.keyboard_only or args.no_display or is_not_rpi

    disp_out_en = not (args.screen_only or args.no_display or is_not_rpi)
    screen_en = args.screen or args.screen_only or args.no_display or is_not_rpi

    # Init the display
    if disp_in_en or disp_out_en:
        Display.init()
    
    if keyboard_en or screen_en:
        from DebugViewer import DebugViewer
        set_debug_viewer(DebugViewer((Display.SCREEN_WIDTH, Display.SCREEN_HEIGHT)))

    start_polling_thread(POLLING_SLEEP_TIME, disp_in_en, keyboard_en)
    start_view_controller_transition_thread(initial_view_controller)

    # Start the render thread (now the main thread)
    RenderThread.render_thread(FRAME_TIME, disp_out_en, screen_en)
