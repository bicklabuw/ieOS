# # DebugViewer.py
# import pygame
# import numpy as np
# from PIL import Image
# from InputUtils import InputCode

# class DebugViewer:
#     code_to_keyboard: dict[InputCode, int] = {
#         InputCode.KEY1:  pygame.K_1,
#         InputCode.KEY2:  pygame.K_2,
#         InputCode.KEY3:  pygame.K_3,
#         InputCode.UP:       pygame.K_UP,
#         InputCode.DOWN:     pygame.K_DOWN,
#         InputCode.LEFT:     pygame.K_LEFT,
#         InputCode.RIGHT:    pygame.K_RIGHT,
#         InputCode.BUTTON: pygame.K_RETURN,
#     }
#     def __init__(self, size: tuple[int, int]):
#         pygame.init()
#         self.screen = pygame.display.set_mode(size)
#         pygame.display.set_caption("Debug Viewer")
#         self.clock = pygame.time.Clock()
#         self.running = True

#     def show(self, pil_image: Image, fps_limit: int = 30):
#         if pil_image.mode != "RGB":
#             pil_image = pil_image.convert("RGB")
#         array = np.array(pil_image)
#         surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
#         self.screen.blit(surface, (0, 0))
#         pygame.display.flip()
#         self.clock.tick(fps_limit)

#     def poll_inputs(self):
#         events = pygame.event.get()
#         keys_pressed = set()

#         for event in events:
#             if event.type == pygame.QUIT:
#                 self.running = False
#             elif event.type == pygame.KEYDOWN:
#                 keys_pressed.add(event.key)

#         return keys_pressed

#     def close(self):
#         pygame.quit()
# DebugViewer.py
import cv2
import numpy as np
from PIL import Image
from pynput import keyboard
from InputUtils import InputCode
import time
from Display import DISP_INV


class DebugViewer:
    # Mapping InputCode to pynput keys
    code_to_keyboard: dict[InputCode, keyboard.Key | keyboard.KeyCode] = {
        InputCode.KEY1: keyboard.KeyCode.from_char('1'),
        InputCode.KEY2: keyboard.KeyCode.from_char('2'),
        InputCode.KEY3: keyboard.KeyCode.from_char('3'),
        InputCode.UP: keyboard.Key.up,
        InputCode.DOWN: keyboard.Key.down,
        InputCode.LEFT: keyboard.Key.left,
        InputCode.RIGHT: keyboard.Key.right,
        InputCode.BUTTON: keyboard.Key.enter,
    }

    def __init__(self, size: tuple[int, int]):
        self.window_name = "Debug Viewer"
        self.size = size
        self.running = True
        self.pressed_keys = set()
        self._lock = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._lock.daemon = True
        self._lock.start()
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, *size)

    def _on_press(self, key):
        self.pressed_keys.add(key)

    def _on_release(self, key):
        self.pressed_keys.discard(key)

    def show(self, pil_image: Image):
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        arr = np.array(pil_image) if not DISP_INV else 255 - np.array(pil_image)
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        #print("Preparing to show image of size:", pil_image.size)
        cv2.imshow(self.window_name, bgr)
        #print("About to render the image")
        key = cv2.waitKey(1) & 0xFF
        time.sleep(0.001)
        cv2.imshow(self.window_name, bgr)
        cv2.waitKey(1)
        #print("Showing: ", pil_image.size, "Press ESC to exit")
        if key == 27:  # ESC
            self.running = False
            self.close()

    def poll_inputs(self) -> set[int]:
        return set(self.pressed_keys)

    def close(self):
        cv2.destroyWindow(self.window_name)
        self._lock.stop()