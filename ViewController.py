from __future__ import annotations
from View import View
from abc import ABC
from OSGlobals import put_view_controller_transition
from enum import Enum
from typing import Callable

class ViewControllerTransitionType(Enum):
    PUSH = 0
    SWAP = 1
    CLEAR = 2
    POP = 3
    POP_TO_ROOT = 4

class ChangeViewControllerType(Enum):
    PUSH = ViewControllerTransitionType.PUSH
    SWAP = ViewControllerTransitionType.SWAP
    CLEAR = ViewControllerTransitionType.CLEAR

class ViewController(ABC):
    def __init__(self):
        self.presented_view: View = None
    
    def present_view(self, view: View):
        self.presented_view = view

    def change_view_controller(self, vc: ViewController, vc_transition_type: ChangeViewControllerType):
        vc_transition = ViewControllerTransition(vc, ViewControllerTransitionType(vc_transition_type.value))
        put_view_controller_transition(vc_transition)

    def pop_view_controller(self):
        vc_transition = ViewControllerTransition(None, ViewControllerTransitionType.POP)
        put_view_controller_transition(vc_transition)

    def pop_to_root_view_controller(self):
        vc_transition = ViewControllerTransition(None, ViewControllerTransitionType.POP_TO_ROOT)
        put_view_controller_transition(vc_transition)
    
    def get_presented_view(self):
        return self.presented_view
    
    # Appear / Disappear Event Handlers
    def on_appear(self) -> None:
        pass
    def on_disappear(self) -> None:
        pass
    
    # Key Input Event Handlers
    def on_key_1_press(self) -> None:
        pass
    def on_key_1_hold(self) -> None:
        pass
    def on_key_1_release(self, held: bool) -> None:
        pass
    
    def on_key_2_press(self) -> None:
        pass
    def on_key_2_hold(self) -> None:
        pass
    def on_key_2_release(self, held: bool) -> None:
        pass
    
    def on_key_3_press(self) -> None:
        pass
    def on_key_3_hold(self) -> None:
        pass
    def on_key_3_release(self, held: bool) -> None:
        pass
    
    # Joystick Input Event Handlers
    def on_joy_up_press(self) -> None:
        pass
    def on_joy_up_hold(self) -> None:
        pass
    def on_joy_up_release(self, held: bool) -> None:
        pass
    
    def on_joy_down_press(self) -> None:
        pass
    def on_joy_down_hold(self) -> None:
        pass
    def on_joy_down_release(self, held: bool) -> None:
        pass
    
    def on_joy_left_press(self) -> None:
        pass
    def on_joy_left_hold(self) -> None:
        pass
    def on_joy_left_release(self, held: bool) -> None:
        pass
    
    def on_joy_right_press(self) -> None:
        pass
    def on_joy_right_hold(self) -> None:
        pass
    def on_joy_right_release(self, held: bool) -> None:
        pass
    
    def on_joy_button_press(self) -> None:
        pass
    def on_joy_button_hold(self) -> None:
        pass
    def on_joy_button_release(self, held: bool) -> None:
        pass
    
class ViewControllerTransition:
    def __init__(self, vc: ViewController, vc_transition_type: ViewControllerTransitionType):
        self.type = vc_transition_type
        self.vc = vc
        
    def __repr__(self):
        return "ViewControllerTransition(" + str(self.vc) + ", " + str(self.type) + ")"