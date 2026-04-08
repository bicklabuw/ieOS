import os
import threading
import queue
import time
import sys
from datetime import datetime
import sounddevice as sd
import soundfile as sf
import numpy as np

import gui.core.Display as Display
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import MultilineTextView, TextAnchor, TextView
from gui.core.Display import SCREEN_WIDTH, SCREEN_HEIGHT
from gui.utils.recording_wav import write_queue_to_soundfile
from gui.utils.usb.USBDriveManager import (
    assert_recordings_still_ready,
    ensure_recordings_ready,
    get_recordings_path,
)

MAX_FILE_RECORD_TIME = 3600


class PlayAndRecordViewController(ViewController[None]):
    """
    Plays a WAV file and simultaneously records from all USB mics.
    Recording duration = file duration. Key2 stops both.
    File naming: rec_{MM}_{DD}_{YYYY}_{HH}_{MM}_{SS}mic{X}hour{Y}.wav
    """

    def __init__(self, file_path: str, name: str) -> None:
        super().__init__()
        self._file_path = file_path
        self._name = name
        self._stopped = False
        self.stop_recording = False

        self._status = MultilineTextView(0, 0, text=f"Play+Rec\n{name[:14]}", anchor=TextAnchor.LEFT_TOP)
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
        try:
            ensure_recordings_ready()
        except OSError as e:
            self._status.text = f"USB not ready:\n{e}"
            time.sleep(2)
            self.pop_view_controller()
            return

        # Get file duration
        try:
            with sf.SoundFile(self._file_path) as f:
                file_duration = int(len(f) / f.samplerate) + 1
        except Exception:
            self._status.text = "File error!"
            time.sleep(2)
            self.pop_view_controller()
            return

        self._stopped = False
        self.stop_recording = False

        # Start playback in background thread
        def _play():
            try:
                data, sr = sf.read(self._file_path)
                if self._stopped:
                    return
                sd.play(data, sr)
                sd.wait()
            except Exception as e:
                print(f"Playback error: {e}")

        play_thread = threading.Thread(target=_play, daemon=True)
        play_thread.start()

        # Run recording (blocks) for the file's duration
        self._run_recording(file_duration)

        # Signal playback to stop, then wait for the play thread to fully exit
        # before proceeding — prevents PortAudio heap corruption from concurrent
        # sd.stop() / sd.wait() access across threads.
        sd.stop()
        play_thread.join(timeout=3)

        self.pop_view_controller()

    def _run_recording(self, total_duration: int) -> None:
        """Same recording algorithm as RecordViewController but uses auto-generated name."""
        actual_time = total_duration
        duration = min(actual_time, MAX_FILE_RECORD_TIME)

        date_str = datetime.now().strftime("%m%d_%H%M%S")
        file_prefix = f"playback_{self._name}_{date_str}"

        num_channels = 1
        sample_rate = 44100

        devices = sd.query_devices()
        mic_ids = []
        mic_indices = []
        for d in devices:
            name = d["name"]
            if d['max_input_channels'] > 0 and name.startswith("USB"):
                mic_ids.append(d['index'])
                mic_indices.append(name[name.index("hw:")+3 : name.index(",")])
                if len(mic_ids) == 3:
                    break

        def record(mic_id, mic_idx, q):
            def callback(indata, frames, time_, status):
                if status:
                    print(status, file=sys.stderr)
                q.put(indata.copy())

            file_path = f"{get_recordings_path()}/{file_prefix}_mic{mic_idx}.wav"
            try:
                with sf.SoundFile(
                    file_path,
                    mode="x",
                    samplerate=sample_rate,
                    channels=num_channels,
                    subtype="PCM_24",
                ) as wav_f:
                    with sd.InputStream(
                        samplerate=sample_rate,
                        blocksize=750,
                        device=mic_id,
                        channels=num_channels,
                        callback=callback,
                    ):
                        t0 = time.time()
                        end_t = t0 + duration
                        ok, err = write_queue_to_soundfile(
                            wav_f,
                            q,
                            stop_check=lambda: self.stop_recording,
                            segment_end_time=end_t,
                        )
                        if not ok:
                            self._status.text = f"Write error:\n{err}"
                            self.stop_recording = True
            except Exception as e:
                self._status.text = f"Error:\n{e}"
                self.stop_recording = True

        def countdown(total):
            remaining = total
            while remaining >= 0 and not self.stop_recording and threading.current_thread() is cnt_thread:
                self._status.text = f"Play+Rec\n{get_duration_text(remaining)} left"
                if remaining == 0:
                    return
                else:
                    time.sleep(1)
                    remaining -= 1

        from gui.utils.time.TimeUtils import get_duration_text
        cnt_thread = threading.Thread(target=countdown, args=[actual_time], daemon=True)
        cnt_thread.start()

        while actual_time > 0:
            try:
                assert_recordings_still_ready()
            except OSError as e:
                self._status.text = f"USB removed:\n{e}"
                self.stop_recording = True
                break

            mic_threads = []
            for i in range(len(mic_ids)):
                q = queue.Queue()
                t = threading.Thread(target=record, args=[mic_ids[i], mic_indices[i], q])
                mic_threads.append(t)
            for t in mic_threads:
                t.start()
            for t in mic_threads:
                t.join()
            if self.stop_recording:
                break
            actual_time -= duration
            if duration > actual_time:
                duration = actual_time

        cnt_thread.join(0.5 if self.stop_recording else None)
        self._status.text = "Stopped" if self.stop_recording else "Done!"
        time.sleep(1)

    def on_key2_press(self) -> None:
        self._stopped = True
        self.stop_recording = True
        self._status.text = "Stopping..."

    def on_disappear(self) -> None:
        self._stopped = True
        self.stop_recording = True
