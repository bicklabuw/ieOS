from View import View
from ViewController import ViewController
from OSGlobals import get_current_view_controller
from OSGlobals import get_view_controller_changed_flag, clear_view_controller_changed_flag
from Components import Component
from PIL import Image, ImageDraw
from typing import List

import Display
import time

def render_thread(frame_time: float):
    # TODO make frame_time more accurate (doesn't account for time in checking if view changed)
    while True:
        start_time = time.time()

        view_controller: ViewController = get_current_view_controller()
        if view_controller is None:
            continue
        
        view = view_controller.get_presented_view()
        if view is None:
            continue

        components: List[Component] = view.get_components()
        any_changed = get_view_controller_changed_flag()

        if any_changed:
            clear_view_controller_changed_flag()

        for component in components:
            if component.get_changed_flag():
                any_changed = True
                component.clear_changed_flag()
        
        if any_changed:
            draw(components)

        end_time = time.time()
        time_diff = end_time - start_time
        if time_diff < frame_time:
            time.sleep(frame_time - time_diff)

def draw(components: List[Component]):
    image = Image.new('1', (Display.SCREEN_WIDTH, Display.SCREEN_HEIGHT), Display.SCREEN_TEXT_COLOR)

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    for component in components:
        component.draw(draw)
    
    # Draw the Screen onto the display
    Display.disp.ShowImage(Display.disp.getbuffer(image))