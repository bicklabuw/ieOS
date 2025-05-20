from View import View
from SelectableView import SelectableView
from InputUtils import InputPhase, InputCode
from typing import Optional

class SelectionManager:
    def __init__(
        self, root: View,
        wrap: bool = True
    ) -> None:
        self._stack: list[View] = [root]
        self._indices: list[int] = [0]
        self.wrap = wrap
        self._enter(0)

    def _siblings(self) -> list[SelectableView]:
        return [
            sv for sv in self._stack[-1].subviews
            if isinstance(sv, SelectableView) and sv.enabled
        ]

    @property
    def current(self) -> Optional[SelectableView]:
        siblings = self._siblings()
        if not siblings:
            return None
        idx = self._indices[-1]
        return siblings[idx]

    def _enter(self, idx: int) -> None:
        siblings = self._siblings()
        if not siblings:
            return
        if idx >= len(siblings):
            idx = len(siblings) - 1
        self._indices[-1] = idx
        siblings[idx].on_select()

    def _find_nearest(self, idx: int, dx: int, dy: int) -> Optional[int]:
        """
        Internal: find index of subview whose center lies in (dx,dy) from views[idx].
        Returns None if no candidate.
        """
        views = self._siblings()
        if not views:
            return False

        cur = views[idx]
        cx = cur.abs_x + cur.width / 2
        cy = cur.abs_y + cur.height / 2
        best = None
        best_proj = 0.0
        for i, v in enumerate(views):
            if i == idx:
                continue
            vx = v.abs_x + v.width / 2
            vy = v.abs_y + v.height / 2
            dcx, dcy = vx - cx, vy - cy
            proj = dcx * dx + dcy * dy
            if proj <= 0:
                continue
            if proj > best_proj:
                best_proj = proj
                best = i
        return best

    def move(self, dx: int, dy: int) -> bool:
        cur = self.current
        siblings = self._siblings()
        if not siblings:
            return False
        idx = self._indices[-1]
        next_idx = self._find_nearest(idx, dx, dy)
        if next_idx is None and self.wrap:
            if dx > 0:
                next_idx = 0
            elif dx < 0:
                next_idx = len(siblings) - 1
        if next_idx is None:
            return False
        cur.on_deselect()
        self._indices[-1] = next_idx
        self.current.on_select()
        return True

    def drill_in(self) -> None:
        cur = self.current
        if not cur or not cur.subviews:
            return
        cur.on_deselect()
        self._stack.append(cur)
        self._indices.append(0)
        self._enter(0)

    def exit(self) -> None:
        if len(self._stack) <= 1:
            return
        cur = self.current
        if cur:
            cur.on_deselect()
        self._stack.pop()
        self._indices.pop()
        new_cur = self.current
        if new_cur:
            new_cur.on_select()