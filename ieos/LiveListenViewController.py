# ieos/LiveListenViewController.py
from __future__ import annotations

import threading
import time
from collections.abc import Sequence

import numpy as np
from PIL import ImageDraw, ImageFont

import gui.core.Display as Display
import gui.core.Main as Main
from gui.core.Display import SCREEN_HEIGHT, SCREEN_WIDTH
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import CoordinateView
from gui.utils.recording_format import (
    CHANNELS,
    SAMPLE_RATE,
    select_capture_blocksize,
    list_usb_recording_devices,
    settle_portaudio_after_capture_close,
)
from ieos.mic_selection_store import get_enabled_slots_for_count
from ieos.recording_runtime_state import is_any_recording_active


_METER_LEFT = 12
_METER_RIGHT = SCREEN_WIDTH - 13
_METER_TOP = 30
_METER_BOTTOM = 42
_BUFFER_SECONDS = 0.35


def select_next_enabled_slot(
    enabled_slots: Sequence[int],
    current_slot: int | None,
    delta: int,
    unavailable_slots: Sequence[int] = (),
) -> int | None:
    """Return the next enabled mic slot, wrapping around unavailable slots."""
    available = [slot for slot in enabled_slots if slot not in set(unavailable_slots)]
    if not available:
        return None
    if current_slot not in available:
        return available[0 if delta >= 0 else -1]
    idx = available.index(current_slot)
    return available[(idx + delta) % len(available)]


class _AudioRingBuffer:
    """Small callback-safe float32 ring buffer for mic-to-output passthrough."""

    def __init__(self, max_frames: int, channels: int) -> None:
        self._max_frames = max(1, int(max_frames))
        self._channels = max(1, int(channels))
        self._buffer = np.zeros((self._max_frames, self._channels), dtype=np.float32)
        self._read_pos = 0
        self._write_pos = 0
        self._available = 0
        self._lock = threading.Lock()

    @property
    def available_frames(self) -> int:
        with self._lock:
            return self._available

    def clear(self) -> None:
        with self._lock:
            self._read_pos = 0
            self._write_pos = 0
            self._available = 0
            self._buffer.fill(0)

    def write(self, data: np.ndarray) -> None:
        frames = np.asarray(data, dtype=np.float32)
        if frames.ndim == 1:
            frames = frames.reshape(-1, 1)
        if frames.shape[1] != self._channels:
            frames = frames[:, : self._channels]
            if frames.shape[1] < self._channels:
                padded = np.zeros((frames.shape[0], self._channels), dtype=np.float32)
                padded[:, : frames.shape[1]] = frames
                frames = padded

        if len(frames) >= self._max_frames:
            frames = frames[-self._max_frames :]

        with self._lock:
            overflow = max(0, self._available + len(frames) - self._max_frames)
            if overflow:
                self._read_pos = (self._read_pos + overflow) % self._max_frames
                self._available -= overflow

            remaining = len(frames)
            src_pos = 0
            while remaining:
                chunk = min(remaining, self._max_frames - self._write_pos)
                self._buffer[self._write_pos : self._write_pos + chunk] = frames[src_pos : src_pos + chunk]
                self._write_pos = (self._write_pos + chunk) % self._max_frames
                self._available += chunk
                src_pos += chunk
                remaining -= chunk

    def read(self, frames: int) -> np.ndarray:
        frames = max(0, int(frames))
        out = np.zeros((frames, self._channels), dtype=np.float32)
        if frames == 0:
            return out

        with self._lock:
            to_read = min(frames, self._available)
            remaining = to_read
            dst_pos = 0
            while remaining:
                chunk = min(remaining, self._max_frames - self._read_pos)
                out[dst_pos : dst_pos + chunk] = self._buffer[self._read_pos : self._read_pos + chunk]
                self._read_pos = (self._read_pos + chunk) % self._max_frames
                self._available -= chunk
                dst_pos += chunk
                remaining -= chunk
        return out


class _LiveListenView(CoordinateView):
    def __init__(self) -> None:
        super().__init__(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.selectable = False
        self._font = ImageFont.load_default()
        self._title = "Live listen"
        self._status = ""
        self._hint = "L/R: mic K2: stop"
        self._amplitude = 0.0

    def set_state(self, title: str, status: str, hint: str | None = None) -> None:
        self._title = title
        self._status = status
        if hint is not None:
            self._hint = hint
        self._mark_dirty()

    def update_amplitude(self, amp: float) -> None:
        self._amplitude = max(0.0, min(1.0, float(amp)))
        self._mark_dirty()

    def _center_text(self, draw: ImageDraw.ImageDraw, text: str, y: int) -> None:
        bbox = draw.textbbox((0, 0), text, font=self._font)
        x = (SCREEN_WIDTH - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), text, fill=Display.ON, font=self._font)

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        self._center_text(draw, self._title, 3)
        if self._status:
            self._center_text(draw, self._status, 15)

        draw.rectangle(
            [_METER_LEFT, _METER_TOP, _METER_RIGHT, _METER_BOTTOM],
            fill=Display.OFF,
            outline=Display.ON,
        )
        fill_width = int((_METER_RIGHT - _METER_LEFT - 2) * self._amplitude)
        if fill_width > 0:
            draw.rectangle(
                [_METER_LEFT + 1, _METER_TOP + 1, _METER_LEFT + fill_width, _METER_BOTTOM - 1],
                fill=Display.ON,
            )

        if self._hint:
            self._center_text(draw, self._hint, 52)


class LiveListenViewController(ViewController[None]):
    """Monitor one enabled USB microphone through the default audio output."""

    def __init__(self) -> None:
        super().__init__()
        self._view = _LiveListenView()
        self.view.add_subview(self._view)

        self._mics: list = []
        self._enabled_slots: list[int] = []
        self._unavailable_slots: set[int] = set()
        self._current_slot: int | None = None
        self._input_stream = None
        self._output_stream = None
        self._buffer = _AudioRingBuffer(int(SAMPLE_RATE * _BUFFER_SECONDS), CHANNELS)
        self._stop = False
        self._stream_generation = 0

    def on_appear(self) -> None:
        super().on_appear()
        self._stop = False
        if is_any_recording_active():
            self._view.set_state("Live listen", "Recorder busy", "K2: BACK")
            time.sleep(2)
            self.pop_view_controller()
            return

        self._mics = list_usb_recording_devices()
        if not self._mics:
            self._view.set_state("Live listen", "No mics found", "K2: BACK")
            return

        self._enabled_slots = [
            slot for slot in get_enabled_slots_for_count(len(self._mics))
            if 0 <= slot < len(self._mics)
        ]
        if not self._enabled_slots:
            self._view.set_state("Live listen", "No mics enabled", "K2: BACK")
            return

        first_slot = select_next_enabled_slot(self._enabled_slots, None, 1, self._unavailable_slots)
        if first_slot is None:
            self._view.set_state("Live listen", "No mics available", "K2: BACK")
            return
        self._start_slot(first_slot)

    def _start_slot(self, slot: int) -> None:
        import sounddevice as sd

        self._close_streams()
        self._buffer.clear()
        self._current_slot = slot
        self._stream_generation += 1
        generation = self._stream_generation

        title = f"Live mic {slot}"
        self._view.set_state(title, "Starting...", "L/R: mic K2: stop")
        capture_blocksize = select_capture_blocksize(1)

        def input_callback(indata, frames, time_info, status) -> None:
            if self._stop or generation != self._stream_generation:
                return
            self._buffer.write(indata.copy())
            if len(indata):
                self._view.update_amplitude(float(np.max(np.abs(indata))))

        def output_callback(outdata, frames, time_info, status) -> None:
            if self._stop or generation != self._stream_generation:
                outdata.fill(0)
                return
            outdata[:] = self._buffer.read(frames)

        try:
            self._output_stream = sd.OutputStream(
                samplerate=SAMPLE_RATE,
                blocksize=capture_blocksize,
                channels=CHANNELS,
                dtype="float32",
                callback=output_callback,
            )
            self._input_stream = sd.InputStream(
                device=self._mics[slot]["index"],
                samplerate=SAMPLE_RATE,
                blocksize=capture_blocksize,
                channels=CHANNELS,
                dtype="float32",
                callback=input_callback,
            )
            self._output_stream.start()
            self._input_stream.start()
        except Exception:
            self._unavailable_slots.add(slot)
            self._close_streams()
            next_slot = select_next_enabled_slot(self._enabled_slots, slot, 1, self._unavailable_slots)
            if next_slot is None:
                self._view.set_state("Live listen", "Output error", "K2: BACK")
                time.sleep(2)
                self.pop_view_controller()
                return
            self._view.set_state(title, "Mic open failed", "Trying next...")
            time.sleep(1)
            self._start_slot(next_slot)
            return

        self._view.set_state(title, f"{len(self._enabled_slots)} enabled", "L/R: mic K2: stop")

    def _switch(self, delta: int) -> None:
        if not self._enabled_slots or self._current_slot is None:
            return
        next_slot = select_next_enabled_slot(
            self._enabled_slots,
            self._current_slot,
            delta,
            self._unavailable_slots,
        )
        if next_slot is None or next_slot == self._current_slot:
            return
        self._view.set_state("Live listen", "Switching...", "L/R: mic K2: stop")
        self._start_slot(next_slot)

    def _close_streams(self) -> None:
        for attr in ("_input_stream", "_output_stream"):
            stream = getattr(self, attr)
            if stream is None:
                continue
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
            setattr(self, attr, None)
        settle_portaudio_after_capture_close()

    def _stop_all(self) -> None:
        self._stop = True
        self._stream_generation += 1
        self._close_streams()
        self._buffer.clear()

    def on_left_press(self) -> bool:
        self._switch(-1)
        return True

    def on_right_press(self) -> bool:
        self._switch(1)
        return True

    def on_key2_press(self) -> bool:
        self._view.set_state("Live listen", "Stopping...", "")
        self._stop_all()
        self.pop_view_controller()
        return True

    def on_disappear(self) -> None:
        self._stop_all()


if __name__ == "__main__":
    Main.main(LiveListenViewController())
