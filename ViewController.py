from __future__ import annotations
from View import View
from SelectableView import SelectableView
from SelectionManager import SelectionManager
from abc import ABC
from OSGlobals import put_view_controller_transition
from enum import Enum
from typing import Callable, Generic, TypeVar, Any
from InputUtils import InputCode, InputPhase
import Display

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

T = TypeVar('T')

class ViewController(Generic[T]):
    def __init__(self) -> None:
        """Initialize with a full-screen default view."""
        # Root view covers the entire screen by default
        self.view = View(0, 0, Display.SCREEN_WIDTH, Display.SCREEN_HEIGHT)
        self.selection = SelectionManager(self.view, wrap=True)

    def on_appear(self) -> None:
        pass

    def on_disappear(self) -> None:
        pass

    def handle_override(
        self, code: InputCode,
        phase: InputPhase,
        held: bool
    ) -> bool:
        return False

    def handle_wrap(self, code: InputCode) -> None:
        self.pop_view_controller()

    def on_event(
        self, code: InputCode,
        phase: InputPhase,
        held: bool = False
    ) -> None:
        if self.handle_override(code, phase, held):
            return
        cur = self.selection.current
        if cur and cur._dispatch_event(code, phase, held):
            return
        if phase == InputPhase.PRESS and code in (
            InputCode.UP, InputCode.DOWN,
            InputCode.LEFT, InputCode.RIGHT
        ):
            dx = -1 if code == InputCode.LEFT else 1 if code == InputCode.RIGHT else 0
            dy = -1 if code == InputCode.UP else 1 if code == InputCode.DOWN else 0
            if self.selection.move(dx, dy):
                return
            self.handle_wrap(code)
            return
        if code == InputCode.ACTIVATE and phase == InputPhase.PRESS:
            cur = self.selection.current
            if isinstance(cur, SelectableView) and cur.children:
                self.selection.drill_in()
                return

    def push_view_controller(
        self, vc: ViewController[T],
        *,
        return_callback: Callable[[T], None] | None = None
    ) -> None:
        """
        Push `vc` onto the nav stack.
        If provided, `return_callback` is called with one argument of type `T`
        when `vc.pop_view_controller(data)` is invoked.
        """
        if return_callback is not None:
            setattr(vc, '_return_callback', return_callback)
        t = ViewControllerTransition(vc, ViewControllerTransitionType.PUSH)
        put_view_controller_transition(t)

    def swap_view_controller(self, vc: ViewController[Any]) -> None:
        """Replace the current top controller with `vc` (no callback)."""
        t = ViewControllerTransition(vc, ViewControllerTransitionType.SWAP)
        put_view_controller_transition(t)

    def replace_root_view_controller(self, vc: ViewController[Any]) -> None:
        """Clear the stack and set `vc` as the new root."""
        t = ViewControllerTransition(vc, ViewControllerTransitionType.CLEAR)
        put_view_controller_transition(t)

    def pop_view_controller(self, return_data: T | None = None) -> None:
        """
        Pop the top controller.  If it was pushed with a callback, pass `return_data` back.
        """
        if hasattr(self, '_return_callback'):
            self._return_callback(return_data)
        t = ViewControllerTransition(None, ViewControllerTransitionType.POP)
        put_view_controller_transition(t)

    def pop_to_root_view_controller(self) -> None:
        """Pop back to the initial/root controller."""
        t = ViewControllerTransition(None, ViewControllerTransitionType.POP_TO_ROOT)
        put_view_controller_transition(t)
    
class ViewControllerTransition:
    def __init__(self, vc: ViewController, vc_transition_type: ViewControllerTransitionType):
        self.type = vc_transition_type
        self.vc = vc
        
    def __repr__(self):
        return "ViewControllerTransition(" + str(self.vc) + ", " + str(self.type) + ")"