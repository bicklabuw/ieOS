import os
import threading
import time

import sounddevice as sd
import soundfile as sf

import Display
from ViewController import ViewController
from Views import MultilineTextView, TextAnchor, TextView
from Display import SCREEN_WIDTH, SCREEN_HEIGHT
from USBDriveManager import mount_pendrive, unmount_pendrive


class PlaybackViewController(ViewController[None]):
    """Plays a WAV file. Key2 stops playback."""

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self._file_path = file_path
        self._stopped = False

        filename = os.path.basename(file_path)
        # Show first 16 chars of filename + "Playing..." status
        self._status = MultilineTextView(0, 0, text=f"{filename[:16]}\nPreparing...", anchor=TextAnchor.LEFT_TOP)
        self._status.selectable = False
        self.view.add_subview(self._status)

        self._hint = TextView(0, 0, text="K2: STOP", anchor=TextAnchor.LEFT_TOP)
        self._hint.selectable = False
        self.view.add_subview(self._hint)

    def on_layout(self) -> None:
        sw, sh = self._status.get_text_size()
        self._status.x = (SCREEN_WIDTH - sw) / 2
        self._status.y = (SCREEN_HEIGHT - sh) / 2 - 5

        hw, hh = self._hint.get_text_size()
        self._hint.x = SCREEN_WIDTH - hw - 2
        self._hint.y = SCREEN_HEIGHT - hh - 2

    def on_appear(self) -> None:
        super().on_appear()
        self._stopped = False

        try:
            mount_pendrive()
        except OSError as e:
            self._status.text = f"No USB drive:\n{e}"
            time.sleep(2)
            self.pop_view_controller()
            return

        def _play() -> None:
            try:
                data, sr = sf.read(self._file_path)
                self._status.text = f"{os.path.basename(self._file_path)[:16]}\nPlaying..."
                sd.play(data, sr)
                sd.wait()
            except Exception as e:
                print(f"Playback error: {e}")
            finally:
                if not self._stopped:
                    self._status.text = "Done!"
                    time.sleep(1)
                    self.pop_view_controller()

        threading.Thread(target=_play, daemon=True).start()

    def on_key2_press(self) -> None:
        if not self._stopped:
            self._stopped = True
            sd.stop()
            self.pop_view_controller()

    def on_disappear(self) -> None:
        self._stopped = True
        sd.stop()
        unmount_pendrive()
