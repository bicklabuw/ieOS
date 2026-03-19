from __future__ import annotations
from View import View
from InputUtils import InputPhase, InputCode
from typing import Optional
from math import sqrt
from enum import Enum
from Display import SCREEN_HEIGHT, SCREEN_WIDTH
from collections import deque

class Direction(Enum):
    UP = InputCode.UP
    DOWN = InputCode.DOWN
    LEFT = InputCode.LEFT
    RIGHT = InputCode.RIGHT

    @classmethod
    def from_code(cls, code: InputCode) -> Direction:
        for direction in cls:
            if direction.value == code:
                return direction
        raise ValueError(f"Invalid code: {code}")

class SelectionManager:
    def __init__(
        self, root: View,
        wrap: bool = True
    ) -> None:

        
        root.manager = self
        root.on_select()
        self._stack: list[View] = [root]
        self.wrap = wrap
        self._enter(0)
        self.current = None

    @property
    def current_parent(self) -> View:
        return self._stack[-1] if len(self._stack) > 0 else None

    def _siblings(self) -> list[View]:
        return [
            c for c in self._stack[-1].subviews
            if getattr(c, "selectable", False) and c.visible
        ]

    def _enter(self, idx: int) -> None:
        siblings = self._siblings()
        if not siblings:
            return
        if idx >= len(siblings):
            idx = len(siblings) - 1
        self.current = siblings[idx]
        self.current.on_select()
        # if len(siblings) == 1:
            # self.drill_in()
    
    def _enter_view(self, view: View) -> None:
        if not issubclass(type(view), View):
            raise TypeError(f"{view} is not a View")
        if not view.selectable:
            raise ValueError(f"View {view} is not selectable")
        if view not in self._siblings():
            raise ValueError(f"View {view} is not a sibling of current view {self.current}")
        idx = self._siblings().index(view)
        self._enter(idx)

    def select(self, view: View) -> None:
        """
        select a view
        figure out what i need to do to get there
        """
        if not issubclass(type(view), View):
            raise TypeError(f"{view} is not a View")
        if not view.selectable:
            raise ValueError(f"View {view} is not selectable")
        
        view_stack = deque()
        dummy_view = view
        while dummy_view is not None:
            view_stack.appendleft(dummy_view)
            dummy_view = dummy_view.superview
        
        # check for root error
        if view_stack[0] != self._stack[0]:
            print("ERROR")
            print(f"View stack to select {view}: {list(view_stack)}"
                    f"\nCurrent stack: {self._stack}")
            raise ValueError(f"View {view} is not a descendant of root view {self._stack[0]}")

        n = min(len(view_stack), len(self._stack))
        stop_index = n
        for i in range(1, n):
            if view_stack[i] != self._stack[i]:
                stop_index = i
                break

        print(f"View stack to select {view}: {list(view_stack)}"
              f"\nCurrent stack: {self._stack}\nStop index: {stop_index}")

        self.current.on_deselect()
        for _ in range(stop_index, len(self._stack)):
            self.current = self._stack.pop()

        if self.current != view_stack[stop_index]: 
            self._enter_view(view_stack[stop_index])
        
        for i in range(stop_index+1, len(view_stack)):
            print(self._siblings())
            self.drill_in(view_stack[i])

    def _find_nearest(self, direction: Direction) -> Optional[int]:
        """
        Internal: find index of subview whose center lies in (dx,dy) from views[idx].
        Returns None if no candidate.
        """
        best, best_proj, is_inside = self._find_nearest_helper(direction, False)
        if self.wrap:
            wrap_best, wrap_best_proj, wrap_is_inside = self._find_nearest_helper(direction, True)

            if wrap_best is not None and (best is None or 
                    (wrap_best_proj < best_proj and is_inside == wrap_is_inside) or 
                    (not is_inside and wrap_is_inside)):
                return wrap_best
        return best
    
    def _find_nearest_helper(self, direction: Direction, wrap: bool = False) -> Optional[int]:
        views = self._siblings()
        if not views:
            return False

        cx = self.current.abs_x + self.current.width / 2
        cy = self.current.abs_y + self.current.height / 2
        best = None
        best_proj = float('inf')
        outside_best = None
        outside_best_proj = float('inf')
        for i, v in enumerate(views):
            if v == self.current:
                continue
            vx = v.abs_x + v.width / 2
            vy = v.abs_y + v.height / 2

            if direction == Direction.UP:
                if (not wrap and vy >= cy) or (wrap and vy < cy):
                    continue
            elif direction == Direction.DOWN:
                if (not wrap and vy <= cy) or (wrap and vy > cy):
                    continue
            elif direction == Direction.LEFT:
                if (not wrap and vx >= cx) or (wrap and vx < cx):
                    continue
            elif direction == Direction.RIGHT:
                if (not wrap and vx <= cx) or (wrap and vx > cx):
                    continue

            dcx, dcy = abs(vx - cx), abs(vy - cy)

            if wrap:
                if direction == Direction.UP:
                    dcy = abs(cy) + abs(SCREEN_HEIGHT - vy)
                elif direction == Direction.DOWN:
                    dcy = abs(vy) + abs(SCREEN_HEIGHT - cy)
                elif direction == Direction.LEFT:
                    dcx = abs(cx) + abs(SCREEN_WIDTH - vx)
                elif direction == Direction.RIGHT:
                    dcx = abs(vx) + abs(SCREEN_WIDTH - cx)

            if direction in (Direction.UP, Direction.DOWN):
                proj = dcx*1.5 + dcy
            else:
                proj = dcy*1.5 + dcx

            if direction in (Direction.UP, Direction.DOWN) and dcx > dcy:
                # Outside the best
                if outside_best is None or proj < outside_best_proj:
                    outside_best_proj = proj
                    outside_best = i
                continue

            elif direction in (Direction.LEFT, Direction.RIGHT) and dcy > dcx:
                # Outside the best
                if outside_best is None or proj < outside_best_proj:
                    outside_best_proj = proj
                    outside_best = i
                continue
            elif proj < best_proj:
                best_proj = proj
                best = i
        
        return (best, best_proj, True) if best is not None else (outside_best, outside_best_proj, False)

    def move(self, direction: Direction) -> bool:
        cur = self.current
        siblings = self._siblings()
        if not siblings:
            return False
        next_idx = self._find_nearest(direction)
        if next_idx is None:
            return False
        cur.on_deselect()
        self.current = siblings[next_idx]
        self.current.on_select()
        return True

    def drill_in(self, view: View | None = None) -> None:
        cur = self.current
        if not cur or not cur.subviews:
            return
        cur.on_deselect()
        self._stack.append(cur)
        if view is not None:
            self._enter_view(view)
        else:
            self._enter(0)

    def handle_selected_view_being_removed(self, view: View) -> None:
        """
        Called when a selected view is removed from the tree.
        This is a no-op if the view is not selected.
        """

        if view is not self.current:
            ind = self._stack.index(view)
            for i in range(ind, len(self._stack)):
                self.exit()

            if view is not self.current:
                raise RuntimeError("Selected view not found in stack, cannot exit")
        

        views = self._siblings()
        ind = views.index(view)
        if ind == 0:
            # First view selected, move to the next one
            if len(views) > 1:
                self._enter(1)
            else:
                # No more views, drill out
                self.exit()
                self.current = None
        elif ind == len(views) - 1:
            # Last view selected, move to the previous one
            self._enter(ind - 1)
        else:
            # Middle view selected, move to the next one
            self._enter(ind + 1)
            

        print(f"Selected view {view} removed, current is now {self.current}")
        print(f"INDEX: {ind}, SIBLINGS: {len(views)}")

    def exit(self,) -> None:
        if len(self._stack) <= 1:
            return
        cur = self.current
        if cur:
            cur.on_deselect()
        self.current = self._stack.pop()
        self.current.on_select()