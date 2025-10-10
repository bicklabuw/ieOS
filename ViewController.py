from __future__ import annotations
from View import View, ViewControllerView
from SelectionManager import SelectionManager, Direction
from abc import ABC
from OSGlobals import put_view_controller_transition
from enum import Enum
from typing import Callable, Generic, TypeVar, Any
from InputUtils import InputCode, InputPhase

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
        print("ViewController init")
        print(self)
        self.view = ViewControllerView(self)
        self.selection = SelectionManager(self.view, wrap=True)

    def on_appear(self) -> None:
        self.view._mark_dirty()

    def on_disappear(self) -> None:
        pass

    def handle_override(
        self, code: InputCode,
        phase: InputPhase,
        held: bool
    ) -> bool:
        name = f'on_{code.name.lower()}_{phase.name.lower()}'
        method = getattr(self, name, None)
        print(f"Handling override for {code} in phase {phase}")
        if not method:
            return False
        print(f"Method found: {method}")
        ret_val = method(held) if phase == InputPhase.RELEASE else method()
        return ret_val if isinstance(ret_val, bool) else True

    def handle_wrap(self, code: InputCode) -> None:
        pass

    def on_event(
        self, code: InputCode,
        phase: InputPhase,
        held: bool = False
    ) -> None:
        print(f"ViewController on_event: {code}, {phase}, held={held}")
        if self.handle_override(code, phase, held):
            return
        cur = self.selection.current
        if cur and cur._dispatch_event(code, phase, held):
            return
        if phase == InputPhase.PRESS and code in (
            InputCode.UP, InputCode.DOWN,
            InputCode.LEFT, InputCode.RIGHT
        ):
            print("Attempting toi move")
            if self.selection.move(Direction.from_code(code)):
                return
            self.handle_wrap(code)
            return
        if code == InputCode.BUTTON and phase == InputPhase.PRESS:
            cur = self.selection.current
            if cur is None:
                print("No current selection to handle button press")
                return
            if cur.selectable and len(cur.subviews) > 0:
                self.selection.drill_in()
                return

    def on_layout(self) -> None:
        """Override this method to handle layout changes."""
        pass

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
        print(f"Pop view controller: {t}")
        put_view_controller_transition(t)

    def pop_to_root_view_controller(self) -> None:
        """Pop back to the initial/root controller."""
        t = ViewControllerTransition(None, ViewControllerTransitionType.POP_TO_ROOT)
        print(f"Pop to root view controller: {t}")
        put_view_controller_transition(t)

    def on_removing_selected_view(self, subview: View) -> None:
        """
        Called when a selected view is removed from its parent.
        Override to handle any special cleanup.
        """
        self.selection.handle_selected_view_being_removed(subview)

    def on_adding_selectable_view(
        self, parent: View,
        subview: View
    ) -> None:
        """
        Called when a selectable view is added to its parent.
        Override to handle any special setup.
        """
        print(f"Adding selectable view: {subview}")
        if parent == self.selection.current_parent and self.selection.current is None:
            print(f"Adding selectable view to current parent: {parent}")
            self.selection._enter(0)
    
class ViewControllerTransition:
    def __init__(self, vc: ViewController, vc_transition_type: ViewControllerTransitionType):
        self.type = vc_transition_type
        self.vc = vc
        
    def __repr__(self):
        return "ViewControllerTransition(" + str(self.vc) + ", " + str(self.type) + ")"