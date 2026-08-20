# ieos/MicTestViewController.py
from __future__ import annotations

import queue
import threading
import time

import numpy as np
import sounddevice as sd

import gui.core.Display as Display
import gui.core.Main as Main
from gui.core.Display import SCREEN_HEIGHT, SCREEN_WIDTH
from PIL import ImageDraw, ImageFont
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import CoordinateView
from gui.utils.recording_format import (
    select_capture_blocksize,
    SAMPLE_RATE,
    USB_MIC_STREAM_START_STAGGER_SEC,
    list_usb_recording_devices,
    settle_portaudio_after_capture_close,
)
from ieos.mic_selection_store import get_enabled_slots_for_count, set_enabled_slots

# ---------------------------------------------------------------------------
# Layout constants (64px tall display; bottom row for centered hint)
# ---------------------------------------------------------------------------
_BAR_TOP       = 2
_BAR_BOTTOM    = 34  # bar shell ends here; selection box extends +2px below
_BAR_H         = _BAR_BOTTOM - _BAR_TOP
_MIC_LABEL_Y   = 37  # below selection chrome (~36), clear gap before hint
_HINT_Y        = 50  # moved up with bars shortened by the same amount

# Fixed bar geometry per mic count: (bar_w, gap, left_margin)
_BAR_GEOMETRY = {
    1: (60,  0, 34),
    2: (44, 16, 14),
    3: (30,  9, 10),
    4: (27,  4,  4),  # left + 4*bar_w + 3*gap - 1 = 123 <= 127
}

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
        self._enabled: list[bool] = []
        self._selected_idx: int = 0

    def setup(
        self,
        n: int,
        status: str,
        hint: str,
        *,
        enabled: list[bool] | None = None,
        selected_idx: int = 0,
    ) -> None:
        self._n = n
        self._amplitude = [0.0] * n
        self._peak = [0] * n
        self._peak_hold_frames = [0] * n
        self._status_text = status
        self._hint_text = hint
        self._enabled = list(enabled) if enabled else [True] * n
        self._selected_idx = max(0, min(selected_idx, max(0, n - 1)))
        self._mark_dirty()

    def set_texts(self, status: str, hint: str) -> None:
        self._status_text = status
        self._hint_text = hint
        self._mark_dirty()

    def set_selection(self, idx: int) -> None:
        if self._n > 0:
            self._selected_idx = max(0, min(idx, self._n - 1))
        self._mark_dirty()

    def set_enabled_list(self, enabled: list[bool]) -> None:
        self._enabled = list(enabled)
        self._mark_dirty()

    def zero_slot(self, idx: int) -> None:
        if 0 <= idx < self._n:
            self._amplitude[idx] = 0.0
            self._peak[idx] = 0
            self._peak_hold_frames[idx] = 0
        self._mark_dirty()

    @property
    def enabled_mask(self) -> list[bool]:
        return list(self._enabled)

    def update_amplitude(self, mic_idx: int, amp: float) -> None:
        if not (0 <= mic_idx < self._n) or not self._enabled[mic_idx]:
            return
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
            bar_w, gap, left_margin = _BAR_GEOMETRY.get(self._n, _BAR_GEOMETRY[3])
            for i in range(self._n):
                x0 = left_margin + i * (bar_w + gap)
                x1 = x0 + bar_w - 1
                on = self._enabled[i]
                sel = i == self._selected_idx

                if sel:
                    draw.rectangle(
                        [x0 - 2, _BAR_TOP - 2, x1 + 2, _BAR_BOTTOM + 2],
                        fill=Display.OFF,
                        outline=Display.ON,
                    )

                if not on:
                    draw.rectangle([x0, _BAR_TOP, x1, _BAR_BOTTOM],
                                   fill=Display.OFF, outline=Display.ON)
                else:
                    draw.rectangle([x0, _BAR_TOP, x1, _BAR_BOTTOM],
                                   fill=Display.OFF, outline=Display.ON)

                    bh = max(0, min(_BAR_H, int(self._amplitude[i] * _BAR_H)))
                    if bh > 0:
                        draw.rectangle([x0, _BAR_BOTTOM - bh, x1, _BAR_BOTTOM],
                                       fill=Display.ON)

                    pk = self._peak[i]
                    if pk > bh + 1:
                        py = _BAR_BOTTOM - pk
                        draw.line([(x0, py), (x1, py)], fill=Display.ON, width=1)

                mark = "[x]" if on else "[ ]"
                label = f"{mark}{i}"
                lb = draw.textbbox((0, 0), label, font=font)
                lw = lb[2] - lb[0]
                tx = x0 + (bar_w - lw) / 2
                draw.text((tx, _MIC_LABEL_Y), label, fill=Display.ON, font=font)
        else:
            msg = self._status_text
            mb = draw.textbbox((0, 0), msg, font=font)
            draw.text(((SCREEN_WIDTH - (mb[2] - mb[0])) / 2,
                       (SCREEN_HEIGHT - (mb[3] - mb[1])) / 2 - 5),
                      msg, fill=Display.ON, font=font)

        if self._hint_text:
            hb = draw.textbbox((0, 0), self._hint_text, font=font)
            hw = hb[2] - hb[0]
            draw.text(((SCREEN_WIDTH - hw) / 2, _HINT_Y),
                      self._hint_text, fill=Display.ON, font=font)


class MicTestViewController(ViewController[bool]):
    """Mic levels / slot enable. Hardware map:
      KEY1 — proceed (GO) when ``show_go`` (record flow); returns False when off so KEY1 reaches TableView menus
      KEY2 — back → pop(None)
      LEFT / RIGHT — move mic selection; BUTTON — toggle enabled slot for selected mic
      (No KEY3 GO — matches on-screen legend K1=GO.)
    """

    def __init__(self, show_go: bool = False) -> None:
        super().__init__()
        self._show_go = show_go
        self._stop = False
        self._mics: list = []
        self._streams: list = []
        self._queues: list[queue.Queue] = []
        self._enabled: list[bool] = []
        self._selected_idx: int = 0
        self._audio_thread: threading.Thread | None = None

        self._view = _MicCheckView()
        self.view.add_subview(self._view)
        self._title_str: str = ""

    def _hint_for_mode(self) -> str:
        if self._show_go:
            return "L/R B:toggle K2 K1=GO"
        return "L/R B:toggle K2"

    def on_appear(self) -> None:
        super().on_appear()
        self._stop_all()
        if self._audio_thread is not None:
            self._audio_thread.join(timeout=2)
            self._audio_thread = None
        self._stop = False

        self._mics = list_usb_recording_devices()

        if not self._mics:
            self._view.setup(0, "No mics found", "K2: BACK")
            return

        n = len(self._mics)
        slots = set(get_enabled_slots_for_count(n))
        self._enabled = [i in slots for i in range(n)]
        self._selected_idx = 0

        self._title_str = f"{n} mic{'s' if n != 1 else ''}"
        hint = self._hint_for_mode()
        self._view.setup(
            n,
            self._title_str,
            hint,
            enabled=self._enabled,
            selected_idx=0,
        )

        self._queues = [queue.Queue() for _ in self._mics]
        self._stop = False
        self._streams = [None] * n

        self._start_or_update_streams()
        self._audio_thread = threading.Thread(target=self._process_audio, daemon=True)
        self._audio_thread.start()

    def _start_or_update_streams(self) -> None:
        n = len(self._mics)
        capture_sample_rate = SAMPLE_RATE
        capture_blocksize = select_capture_blocksize(n)
        to_start = [i for i in range(n) if self._enabled[i] and self._streams[i] is None]
        n_start = len(to_start)
        for j, i in enumerate(to_start):
            def _cb(indata, frames, t, status, _i=i):
                if not self._stop:
                    self._queues[_i].put(indata.copy())

            try:
                stream = sd.InputStream(
                    device=self._mics[i]["index"],
                    samplerate=capture_sample_rate,
                    channels=1,
                    blocksize=capture_blocksize,
                    callback=_cb,
                )
                stream.start()
                self._streams[i] = stream
            except Exception:
                # Keep mic test usable when one USB device cannot open
                # with current ALSA/PortAudio parameters.
                self._enabled[i] = False
                self._view.set_enabled_list(self._enabled)
                self._view.zero_slot(i)
                self._view.set_texts(self._title_str, f"Mic {i} open failed")
            if n_start >= 2 and j < n_start - 1:
                time.sleep(USB_MIC_STREAM_START_STAGGER_SEC)

        for i in range(n):
            if self._enabled[i]:
                continue
            else:
                if self._streams[i] is not None:
                    try:
                        self._streams[i].stop()
                        self._streams[i].close()
                    except Exception:
                        pass
                    self._streams[i] = None
                while True:
                    try:
                        self._queues[i].get_nowait()
                    except queue.Empty:
                        break
                self._view.zero_slot(i)

    def _process_audio(self) -> None:
        while not self._stop:
            for i, q in enumerate(self._queues):
                if not self._enabled[i]:
                    continue
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

    def _persist_enabled(self) -> None:
        indices = [i for i, on in enumerate(self._enabled) if on]
        set_enabled_slots(indices)

    def _toggle_at(self, idx: int) -> None:
        if not self._mics or idx < 0 or idx >= len(self._enabled):
            return
        self._enabled[idx] = not self._enabled[idx]
        self._view.set_enabled_list(self._enabled)
        self._persist_enabled()
        self._start_or_update_streams()
        self._view.set_texts(self._title_str, self._hint_for_mode())

    def _move_selection(self, delta: int) -> None:
        n = len(self._mics)
        if n <= 0:
            return
        self._selected_idx = (self._selected_idx + delta) % n
        self._view.set_selection(self._selected_idx)

    def on_left_press(self) -> bool:
        if not self._mics:
            return True
        self._move_selection(-1)
        return True

    def on_right_press(self) -> bool:
        if not self._mics:
            return True
        self._move_selection(1)
        return True

    def on_button_press(self) -> bool:
        if not self._mics:
            return True
        self._toggle_at(self._selected_idx)
        return True

    def _stop_all(self) -> None:
        self._stop = True
        for i, stream in enumerate(self._streams):
            if stream is not None:
                try:
                    stream.stop()
                    stream.close()
                except Exception:
                    pass
                self._streams[i] = None
        settle_portaudio_after_capture_close()

    def on_key2_press(self) -> None:
        self._stop_all()
        self.pop_view_controller(None)

    def on_key1_press(self) -> bool:
        if not self._show_go:
            return False
        if not self._mics:
            return True
        if not any(self._enabled):
            self._view.set_texts(self._title_str, "Need 1+ mic")
            return True
        self._stop_all()
        self.pop_view_controller(True)
        return True

    def on_disappear(self) -> None:
        self._stop_all()


if __name__ == "__main__":
    Main.main(MicTestViewController(show_go=True))
