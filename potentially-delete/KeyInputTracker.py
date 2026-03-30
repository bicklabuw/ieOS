# key_input_tracker.py
from pynput import keyboard
import threading

class KeyInputTracker:
    def __init__(self):
        print("Starting key input tracker...")
        self.pressed_keys = set()
        self._lock = threading.Lock()
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()

    def _on_press(self, key):
        with self._lock:
            self.pressed_keys.add(key)

    def _on_release(self, key):
        with self._lock:
            self.pressed_keys.discard(key)

    def get_pressed_keys(self):
        with self._lock:
            return set(self.pressed_keys)

    def stop(self):
        self._listener.stop()