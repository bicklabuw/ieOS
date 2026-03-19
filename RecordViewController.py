import sounddevice as sd
import soundfile as sf
from datetime import datetime
import time
import threading
import queue
import sys

import numpy as np

import Display
from ViewController import ViewController
from Views import MultilineTextView, TextView, TextAnchor
from Display import SCREEN_WIDTH, SCREEN_HEIGHT
from USBDriveManager import mount_pendrive, unmount_pendrive, create_recordings_dir, get_recordings_path
from TimeUtils import get_duration_text

MAX_FILE_RECORD_TIME = 3600  # 1 hour per file segment


class RecordViewController(ViewController[None]):
    def __init__(self, name: str, duration: int) -> None:
        super().__init__()
        self._name = name
        self._duration = duration
        self.stop_recording = False

        self._status = MultilineTextView(0, 0, text="", anchor=TextAnchor.LEFT_TOP)
        self._status.selectable = False
        self.view.add_subview(self._status)

        self._hint = TextView(0, 0, text="K2: STOP", anchor=TextAnchor.LEFT_TOP)
        self._hint.selectable = False
        self.view.add_subview(self._hint)

    def on_layout(self) -> None:
        sw, sh = self._status.get_text_size()
        self._status.x = max(0, (SCREEN_WIDTH - sw) / 2)
        self._status.y = max(0, (SCREEN_HEIGHT - sh) / 2)

        hw, hh = self._hint.get_text_size()
        self._hint.x = (SCREEN_WIDTH - hw) / 2
        self._hint.y = SCREEN_HEIGHT - hh - 2

    def on_appear(self) -> None:
        super().on_appear()

        # 1. Mount pendrive
        try:
            mount_pendrive()
        except OSError as e:
            self._status.text = f"No USB drive:\n{e}"
            time.sleep(2)
            self.pop_view_controller()
            return

        # 2. Create recordings directory
        try:
            create_recordings_dir()
        except OSError as e:
            unmount_pendrive()
            self._status.text = f"Dir error:\n{e}"
            time.sleep(2)
            self.pop_view_controller()
            return

        # 3. Reset stop flag
        self.stop_recording = False

        # 4. Run recording (blocks until done)
        self._run_recording()

        # 5. Unmount and pop
        unmount_pendrive()
        self.pop_view_controller()

    def _run_recording(self) -> None:
        indefinite = self._duration == 0
        now = datetime.now()
        date_str = now.strftime("%m_%d_%Y_%H_%M_%S")
        file_prefix = f"{self._name}_{date_str}"

        # Detect USB mics (up to 3)
        devices = sd.query_devices()
        mic_ids = []
        mic_indices = []
        for d in devices:
            name = d['name']
            if name.startswith("USB") and d['max_input_channels'] > 0:
                mic_ids.append(d['index'])
                mic_indices.append(name[name.index("hw:") + 3 : name.index(",")])
                if len(mic_ids) == 3:
                    break

        num_channels = 1
        sample_rate = 44100
        segment_duration = MAX_FILE_RECORD_TIME

        def record(id, index, hour, q):
            def callback(indata, frames, time_, status):
                q.put(indata.copy())
            file_path = f"{get_recordings_path()}/{file_prefix}mic{index}hour{hour}.wav"
            try:
                with sf.SoundFile(file_path, mode='x', samplerate=sample_rate, channels=num_channels, subtype='PCM_24') as f:
                    with sd.InputStream(samplerate=sample_rate, blocksize=750, device=id, channels=num_channels, callback=callback):
                        t0 = time.time()
                        while time.time() - t0 < segment_duration and not self.stop_recording:
                            f.write(q.get())
            except Exception as e:
                self._status.text = f"Error:\n{e}"
                self.stop_recording = True

        def countdown_indefinite():
            while not self.stop_recording and threading.current_thread() is cnt_thread:
                self._status.text = "Recording..."
                time.sleep(1)

        def countdown_timed(total):
            remaining = total
            while remaining >= 0 and not self.stop_recording and threading.current_thread() is cnt_thread:
                self._status.text = f"Recording...\n{get_duration_text(remaining)} left"
                if remaining == 0:
                    return
                elif remaining <= 60:
                    time.sleep(1)
                    remaining -= 1
                else:
                    time.sleep(60)
                    remaining -= 60

        rec_cnt = 0
        if indefinite:
            cnt_thread = threading.Thread(target=countdown_indefinite, daemon=True)
        else:
            cnt_thread = threading.Thread(target=countdown_timed, args=[self._duration], daemon=True)
        cnt_thread.start()

        remaining_time = self._duration if not indefinite else None
        while indefinite or remaining_time > 0:
            seg = segment_duration if indefinite else min(remaining_time, segment_duration)
            segment_duration = seg  # used by record() closure

            mic_threads = []
            for mic_id, mic_index in zip(mic_ids, mic_indices):
                q = queue.Queue()
                t = threading.Thread(
                    target=record,
                    args=(mic_id, mic_index, rec_cnt, q),
                    daemon=True,
                )
                mic_threads.append(t)
                t.start()

            for t in mic_threads:
                t.join()

            if self.stop_recording:
                break

            rec_cnt += 1
            if not indefinite:
                remaining_time -= seg

        cnt_thread.join(0.5 if self.stop_recording else None)
        self._status.text = "Stopped" if self.stop_recording else "Done!"
        time.sleep(1)

    def on_key2_press(self) -> None:
        self._status.text = "Stopping..."
        self.stop_recording = True
        # Do NOT call pop_view_controller here — on_appear handles it

    def on_disappear(self) -> None:
        self.stop_recording = True
