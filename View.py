from __future__ import annotations
import Display
from Components import Component
from typing import Optional, Callable
from InputUtils import InputCode, InputPhase
from PIL import ImageDraw

class View:
    def __init__(
        self, x: float, y: float, width: float, height: float
    ) -> None:
        # Set General Default View Constants
        self.CHAR_LINE_SPACE = 1 # Added space to each line (built in space)
        #self.CHAR_WIDTH: int = 6 # No Space Between some chars - ONLY WORKS FOR DEFAULT FONT
        #self.CHAR_HEIGHT: int = 9 # ONLY WORKS FOR DEFAULT FONT
        self.LINE_HEIGHT: int = self.CHAR_HEIGHT + self.CHAR_LINE_SPACE
        self.LINE_SPACING: int = 1 # Space between lines
        self.TEXT_ALIGN: str = "center"
        
        self.TEXT_COLOR: str = "WHITE"

        # Get the Screen Width and Height
        self.SCREEN_WIDTH: int = Display.SCREEN_WIDTH
        self.SCREEN_HEIGHT: int = Display.SCREEN_HEIGHT

        # Set the View's x, y, width, height
        # and other default values
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.subviews: list[View] = []
        self.superview: Optional[View] = None
        self._dirty = True
        self._needs_layout = True
        self.abs_x = x
        self.abs_y = y
        self._event_handlers: dict[tuple[InputCode, InputPhase], Callable] = {}

    def __setattr__(self, name, value) -> None:
        super().__setattr__(name, value)
        if not name.startswith('_') and name not in ('subviews', 'superview'):
            self._mark_dirty()

    def _mark_dirty(self) -> None:
        self._dirty = True
        if self.superview:
            self.superview._mark_dirty()

    def add_subview(self, subview: View) -> None:
        subview.superview = self
        self.subviews.append(subview)
        self._needs_layout = True
        self._mark_dirty()

    def remove_subview(self, subview: View) -> None:
        if subview in self.subviews:
            self.subviews.remove(subview)
            subview.superview = None
            self._needs_layout = True
            self._mark_dirty()

    def _layout(
        self, parent_abs_x: float = 0,
        parent_abs_y: float = 0
    ) -> None:
        self.abs_x = parent_abs_x + self.x
        self.abs_y = parent_abs_y + self.y
        self._needs_layout = False
        for sv in self.subviews:
            sv._layout(self.abs_x, self.abs_y)

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        pass

    def draw(self, draw: ImageDraw.ImageDraw) -> None:
        if self._needs_layout:
            self._layout()
        if not self._dirty:
            return
        self._render_self(draw)
        for sv in self.subviews:
            sv.draw(draw)
        self._dirty = False

    def set_event_handler(
        self, code: InputCode,
        phase: InputPhase,
        handler: Callable
    ) -> None:
        bound = handler.__get__(self, self.__class__)
        self._event_handlers[(code, phase)] = bound

    def _dispatch_event(
        self, code: InputCode,
        phase: InputPhase,
        held: bool = False
    ) -> bool:
        handler = self._event_handlers.get((code, phase))
        if handler:
            return handler(held) if phase == InputPhase.RELEASE else handler()
        name = f'on_{code.name.lower()}_{phase.name.lower()}'
        method = getattr(self, name, None)
        if not method:
            return False
        return method(held) if phase == InputPhase.RELEASE else method()

    def get_edge_distances(
        self, screen_w: int,
        screen_h: int
    ) -> dict[str, int]:
        left = self.abs_x
        top = self.abs_y
        right = screen_w - (self.abs_x + self.width)
        bottom = screen_h - (self.abs_y + self.height)
        return {'left': left, 'top': top, 'right': right, 'bottom': bottom}

    