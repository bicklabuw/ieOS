from __future__ import annotations

import queue
import threading
import time

import numpy as np
import sounddevice as sd

import Display
import Main
from Display import SCREEN_HEIGHT, SCREEN_WIDTH
from PIL import ImageDraw, ImageFont
from ViewController import ViewController
from Views import CoordinateView

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
_BAR_TOP    = 2
_BAR_BOTTOM = 52
_BAR_H      = _BAR_BOTTOM - _BAR_TOP   # 52 usable px
_HINT_Y     = 54

# Fixed bar geometry per mic count: (bar_w, gap, left_margin)
_BAR_GEOMETRY = {
    1: (60,  0, 34),
    2: (44, 16, 14),
    3: (30,  9, 10),
}

_BLOCKSIZE = 512   # small block = low latency (~12ms at 44100Hz)


class _MicCheckView(CoordinateView):
    """Single full-screen view that draws the entire mic check UI.

    Draws title, bars, status, and hint all in one _render_self so there
    is no z-order overlap between subviews.
    """

    def __init__(self) -> None:
        super().__init__(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.selectable = False
        self._font = ImageFont.load_default()

        self._n: int = 0
        self._amplitude: list[float] = []
        self._peak: list[int] = []
        self._peak_hold_frames: list[int] = []
        self._status_text: str = ""
        self._hint_text: str = ""

    def setup(self, n: int, status: str, hint: str) -> None:
        self._n = n
        self._amplitude = [0.0] * n
        self._peak = [0] * n
        self._peak_hold_frames = [0] * n
        self._status_text = status
        self._hint_text = hint
        self._mark_dirty()

    def set_texts(self, status: str, hint: str) -> None:
        self._status_text = status
        self._hint_text = hint
        self._mark_dirty()

    def update_amplitude(self, mic_idx: int, amp: float) -> None:
        bar_h = max(0, min(_BAR_H, int(amp * _BAR_H)))
        if bar_h >= self._peak[mic_idx]:
            self._peak[mic_idx] = bar_h
            self._peak_hold_frames[mic_idx] = 7
        elif self._peak_hold_frames[mic_idx] > 0:
            self._peak_hold_frames[mic_idx] -= 1
        else:
            self._peak[mic_idx] = max(0, self._peak[mic_idx] - 1)
        self._amplitude[mic_idx] = amp
        self._mark_dirty()

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        font = self._font

        if self._n > 0:
            # --- Bars ---
            bar_w, gap, left_margin = _BAR_GEOMETRY.get(self._n, _BAR_GEOMETRY[3])
            for i in range(self._n):
                x0 = left_margin + i * (bar_w + gap)
                x1 = x0 + bar_w - 1

                # Outline shell
                draw.rectangle([x0, _BAR_TOP, x1, _BAR_BOTTOM],
                                fill=Display.OFF, outline=Display.ON)

                # Amplitude fill
                bh = max(0, min(_BAR_H, int(self._amplitude[i] * _BAR_H)))
                if bh > 0:
                    draw.rectangle([x0, _BAR_BOTTOM - bh, x1, _BAR_BOTTOM],
                                   fill=Display.ON)

                # Peak-hold line
                pk = self._peak[i]
                if pk > bh + 1:
                    py = _BAR_BOTTOM - pk
                    draw.line([(x0, py), (x1, py)], fill=Display.ON, width=1)
        else:
            # --- No mics ---
            msg = self._status_text
            mb = draw.textbbox((0, 0), msg, font=font)
            draw.text(((SCREEN_WIDTH - (mb[2] - mb[0])) / 2,
                       (SCREEN_HEIGHT - (mb[3] - mb[1])) / 2 - 5),
                      msg, fill=Display.ON, font=font)

        # --- Hint ---
        if self._hint_text:
            hb = draw.textbbox((0, 0), self._hint_text, font=font)
            draw.text((SCREEN_WIDTH - (hb[2] - hb[0]) - 2, _HINT_Y),
                      self._hint_text, fill=Display.ON, font=font)


class MicTestViewController(ViewController[bool]):

    def __init__(self, show_go: bool = False) -> None:
        super().__init__()
        self._show_go = show_go
        self._stop = False
        self._streams: list = []
        self._queues: list[queue.Queue] = []

        self._view = _MicCheckView()
        self.view.add_subview(self._view)

    def on_appear(self) -> None:
        super().on_appear()
        devices = sd.query_devices()
        mics = [d for d in devices
                if d["name"].startswith("USB") and d["max_input_channels"] > 0][:3]

        if not mics:
            self._view.setup(0, "No mics found", "K2: BACK")
            return

        n = len(mics)
        hint = "K2: BACK  K3: GO" if self._show_go else "K2: BACK"
        self._view.setup(n, f"{n} mic{'s' if n != 1 else ''} found", hint)

        self._queues = [queue.Queue() for _ in mics]
        self._stop = False
        self._streams = []

        for i, d in enumerate(mics):
            def _cb(indata, frames, t, status, _i=i):
                if not self._stop:
                    self._queues[_i].put(indata.copy())

            stream = sd.InputStream(
                device=d["index"],
                channels=1,
                blocksize=_BLOCKSIZE,
                callback=_cb,
            )
            stream.start()
            self._streams.append(stream)

        threading.Thread(target=self._process_audio, daemon=True).start()

    def _process_audio(self) -> None:
        while not self._stop:
            for i, q in enumerate(self._queues):
                peak = None
                while True:
                    try:
                        data = q.get_nowait()
                        amp = float(np.max(np.abs(data)))
                        if peak is None or amp > peak:
                            peak = amp
                    except queue.Empty:
                        break
                if peak is not None:
                    self._view.update_amplitude(i, peak)
            time.sleep(0.05)

    def _stop_all(self) -> None:
        self._stop = True
        for stream in self._streams:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        self._streams = []

    def on_key2_press(self) -> None:
        self._stop_all()
        self.pop_view_controller(None)

    def on_key3_press(self) -> None:
        self._stop_all()
        self.pop_view_controller(True if self._show_go else None)

    def on_disappear(self) -> None:
        self._stop_all()


if __name__ == "__main__":
    Main.main(MicTestViewController(show_go=True))
