import logging
import time
from gui.ui_core.View import View
from gui.core.OSGlobals import get_current_view_controller, get_debug_viewer
import gui.core.Display as Display

_log = logging.getLogger(__name__)


def _subtree_dirty(view: View) -> bool:
    # Recursively check this view and all subviews for a dirty flag.
    if getattr(view, "_dirty", False):
        #print("Subtree dirty: ", view)
        return True
    for sv in view.subviews:
        if _subtree_dirty(sv):
            #print("Checking subview dirty: ", sv)
            return True
    return False

def render_thread(frame_time: float, on_disp: bool = True, on_screen: bool = False) -> None:
    """
    Redraw the current view controller's main view up to once every `frame_time`
    seconds, but only when something's actually changed.
    If `on_disp` is True, it will push the rendered image to the external display.
    If `on_screen` is True, it will push the rendered image to the OS's screen as an application.
    """
    debug_viewer = get_debug_viewer()
    frame_limit = int(1 / frame_time) if frame_time > 0 else None

    prev_img = None
    max_sec_before_unresponsive = 1
    screen_max_wait = max_sec_before_unresponsive / frame_time
    screen_cur_wait_frames = 0

    while True:
        start = time.time()
        vc = get_current_view_controller()
        if vc is None:
            time.sleep(frame_time)
            continue

        view = vc.view
        if view is None:
            time.sleep(frame_time)
            continue

        # Only redraw if any view/subview is dirty
        if _subtree_dirty(view):
            # print("Render Thread: ", view)
            # New monochrome buffer
            img = Display.create_image()
            #draw = ImageDraw.Draw(img)

            # Let the framework walk the tree and clear dirty flags
            view.draw(img)

            # Push to the physical display
            if on_disp:
                Display.disp.ShowImage(Display.disp.getbuffer(img))

            if on_screen:
                # Push to the OS's screen
                # print("RENDER - ON CHANGE TO VIEW")
                # print(img)
                # img.show()
                debug_viewer.show(img)
                prev_img = img
                screen_cur_wait_frames = 0
        elif on_screen:
            if screen_cur_wait_frames == screen_max_wait and prev_img is not None:
                # Push to the OS's screen to prevent appearing unresponsive
                _log.debug("debug screen refresh: no framebuffer change, re-pushing last image")
                debug_viewer.show(prev_img)
                screen_cur_wait_frames = 0

            screen_cur_wait_frames += 1

        # Sleep to maintain roughly the desired frame rate
        elapsed = time.time() - start
        if elapsed < frame_time:
            time.sleep(frame_time - elapsed)
