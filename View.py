from __future__ import annotations
from Display import SCREEN_WIDTH, SCREEN_HEIGHT, create_image_from_image, SCREEN_TEXT_COLOR
from typing import Optional, Callable, final
from InputUtils import InputCode, InputPhase
from PIL import ImageDraw, Image

import inspect

class View:
    def __init__(
        self, x: float = 0, y: float = 0, width: float = 0, height: float = 0,
        controller: Optional[ViewController] = None,
        selectable: bool = True
    ) -> None:
        # Set General Default View Constants
        self.CHAR_LINE_SPACE = 1 # Added space to each line (built in space)
        #self.CHAR_WIDTH: int = 6 # No Space Between some chars - ONLY WORKS FOR DEFAULT FONT
        self.CHAR_HEIGHT: int = 9 # ONLY WORKS FOR DEFAULT FONT
        self.LINE_HEIGHT: int = self.CHAR_HEIGHT + self.CHAR_LINE_SPACE
        self.LINE_SPACING: int = 1 # Space between lines
        self.TEXT_ALIGN: str = "center"
        
        self.TEXT_COLOR: str = "WHITE"

        # Get the Screen Width and Height
        self.SCREEN_WIDTH: int = SCREEN_WIDTH
        self.SCREEN_HEIGHT: int = SCREEN_HEIGHT

        self.outline_x = 0
        self.outline_y = 0

        # Set the View's x, y, width, height
        # and other default values
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.subviews: list[View] = []
        self.superview: Optional[View] = None
        self._dirty = True
        #print("View initialized with x:", x, "y:", y, "width:", width, "height:", height)
        #self._needs_layout = True
        self.abs_x = x
        self.abs_y = y
        self._event_handlers: dict[tuple[InputCode, InputPhase], Callable] = {}

        self._selectable = selectable
        self.selected = False

        self._visible: bool = True

        #print("CONTROLLER", controller)
        #print("SELECTABLE", selectable)
        self.controller: Optional[ViewController] = controller

        for name, fn in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
            if hasattr(fn, "_event_binding"):
                code, phase = fn._event_binding
                # bind it to this instance
                bound = fn.__get__(self, self.__class__)
                self._event_handlers[(code, phase)] = bound


    def __setattr__(self, name, value) -> None:
        super().__setattr__(name, value)
        if not name.startswith('_') and name not in ('subviews', 'superview'):
            #print(f"Setting attribute {name} to {value} on {self}")
            self._mark_dirty()

    def _mark_dirty(self) -> None:
        self._dirty = True
        #print("Marking dirty for view: ", self)
        parent = getattr(self, 'superview', None)
        if parent:
            self.superview._mark_dirty()

    def get_dirty(self) -> bool:
        return self._dirty
    
    def _clear_dirty(self) -> None:
        #print("Clearing dirty for view: ", self)
        self._dirty = False
        for sv in self.subviews:
            sv._clear_dirty()

    def add_subview(self, subview: View) -> None:
        if subview.superview != None:
            raise RuntimeError("Adding Subview that currently has a Superview")
        subview.superview = self
        self.subviews.append(subview)
        
        def add_vc_for_subviews(subview: View):
            subview.controller = self.controller
            for sv in subview.subviews:
                add_vc_for_subviews(sv)
        #self._needs_layout = True
        #print("Added subview:", subview, "to", self)
        add_vc_for_subviews(subview)
        self._mark_dirty()

        #print(self.controller)

        if self.controller and self.selectable and self.visible and subview.selectable and subview.visible:
            self.controller.on_adding_selectable_view(self, subview)

    def remove_subview(self, subview: View) -> None:
        if subview in self.subviews:
            # notify the hook so anyone (e.g. SelectionManager) can react
            if self.controller and subview.selectable and subview.visible and subview.selected:
                self.controller.on_removing_selected_view(subview)
            self.subviews.remove(subview)
            subview.superview = None
            #self._needs_layout = True
            print("Removed subview:", subview, "from", self)
            self._mark_dirty()
        else:
            raise RuntimeError("Removing Subview that is not in Subviews")

    def _layout(
        self, parent_abs_x: float = 0,
        parent_abs_y: float = 0
    ) -> None:
        self.abs_x = parent_abs_x + self.x
        self.abs_y = parent_abs_y + self.y
        #self._needs_layout = False
        # for sv in self.subviews:
        #     sv._layout(self.abs_x, self.abs_y)

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        pass

    @final
    def draw(self, img: Image.Image) -> None:
        if not self.visible:
            #print("View is not visible, skipping draw: ", self)
            self._clear_dirty()
            return
        
        #if self._needs_layout:
        self._layout()


        if self.width <= 0 or self.height <= 0:
            print("View has no width or height, skipping draw: ", self)
            print("Abs X: ", self.abs_x, "Abs Y: ", self.abs_y)
            print("Width: ", self.width, "Height: ", self.height)
            self._clear_dirty()
            return

        # Create temporary image for rendering
        # This is useful for when the view goes outside of its rect but not the screen's rect.
        # As such the view gets cut off instead of flowing past the boundary of it's rect.
        if self.x == 0 and self.y == 0 and self.width == self.SCREEN_WIDTH and self.height == self.SCREEN_HEIGHT:
            # If the view covers the entire screen, we can draw directly
            temp_image = img
            using_temp_image = False
        else:
            # Create a temporary image to draw the view
            # This allows us to draw the view without affecting the parent drawing context
            # and then paste it onto the parent drawing context.
            # print("Creating temporary image for view: ", self)
            # print("Width: ", self.width, "Height: ", self.height)
            # print("Abs X: ", self.abs_x, "Abs Y: ", self.abs_y)
            # print("Drawing at X: ", self.x, "Y: ", self.y)
            using_temp_image = True
            temp_image = create_image_from_image(img,
                int(self.x - self.outline_x), int(self.y - self.outline_y),
                width=self.width + 2 * self.outline_x, height=self.height + 2 * self.outline_y
            )
            
        draw = ImageDraw.Draw(temp_image)

        self._render_self(draw)
        for sv in self.subviews:
            sv.draw(temp_image)

        if using_temp_image:
            # Paste the temporary image onto the parent drawing context
            # TODO: Check if this would be faster: parent_image.paste(temp_image, (int(self.abs_x), int(self.abs_y)))
            # print("Drawing View: ", self)
            # print("Image: ", temp_image)
            img.paste(temp_image, (int(self.x - self.outline_x), int(self.y - self.outline_y)))
            # if draw_bitmap:
            #     draw.bitmap((self.x, self.y), temp_image)
        
        #print("Drew - Now clearing dirty for view: ", self)
        self._dirty = False

    def set_event_handler(
        self, code: InputCode,
        phase: InputPhase,
        handler: Callable
    ) -> None:
        if not callable(handler):
            raise ValueError("Handler must be callable")
        if hasattr(handler, '_event_binding'):
            raise ValueError("Handler already has an event binding")
        if not isinstance(code, InputCode):
            raise ValueError("Code must be an instance of InputCode")
        if not isinstance(phase, InputPhase):
            raise ValueError("Phase must be an instance of InputPhase")
        
        bound = handler.__get__(self, self.__class__)
        self._event_handlers[(code, phase)] = bound

    def on_event(code: InputCode, phase: InputPhase):
        def decorator(fn):
            fn._event_binding = (code, phase)
            return fn
        return decorator

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
        ret_val = method(held) if phase == InputPhase.RELEASE else method()
        return ret_val if isinstance(ret_val, bool) else True

    def on_select(self) -> None:
        self.selected = True
        self._mark_dirty()
        print("View selected:", self)

    def on_deselect(self) -> None:
        self.selected = False
        self._mark_dirty()
        print("View deselected:", self)

    def get_edge_distances(
        self, screen_w: int,
        screen_h: int
    ) -> dict[str, int]:
        left = self.abs_x
        top = self.abs_y
        right = screen_w - (self.abs_x + self.width)
        bottom = screen_h - (self.abs_y + self.height)
        return {'left': left, 'top': top, 'right': right, 'bottom': bottom}

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if self._visible != value:
            if self.controller and self.selectable and self.selected and self._visible:
                self.controller.on_removing_selected_view(self)  
            
            self._visible = value

            if self.controller and self.selectable and self._visible and self.superview:
                self.controller.on_adding_selectable_view(self.superview, self)
            
            self._mark_dirty()
            print(f"View visibility changed to {value} for {self}")

    @property
    def selectable(self) -> bool:
        return self._selectable

    @selectable.setter
    def selectable(self, value: bool) -> None:
        if self._selectable != value:

            if self.controller and self.selectable and self.selected and self._visible:
                self.controller.on_removing_selected_view(self)  
            
            self._selectable = value

            if self.controller and self.selectable and self._visible and self.superview:
                self.controller.on_adding_selectable_view(self.superview, self)
            
            print(f"View selectable changed to {value} for {self}")
            self._mark_dirty()
    def select(self) -> None:
        self.controller.select(self)

class ViewControllerView(View):
    def __init__(self, vc: ViewController, selectable: bool = True) -> None:
        print("VIEW CONTROLLER VIEW")
        print(vc)
        super().__init__(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, vc, selectable)

    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)
        self.controller.on_layout()