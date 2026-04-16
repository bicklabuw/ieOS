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
from gui.utils.recording_format import (
    CHANNELS,
    SAMPLE_RATE,
    WAV_SUBTYPE,
    list_usb_recording_devices,
)
from ieos.mic_selection_store import get_enabled_slots_for_count
from gui.utils.recording_metadata import write_session_metadata
from gui.utils.recording_wav import write_queue_to_soundfile
from gui.utils.usb.USBDriveManager import (
    assert_recordings_still_ready,
    ensure_recordings_ready,
    get_recordings_path,
)

MAX_FILE_RECORD_TIME = 3600


class PlayAndRecordViewController(ViewController[None]):
    """
    Plays a WAV file and simultaneously records from selected USB mics (by logical slot).
    Recording duration = file duration. Key2 stops both.
    File naming: …mic<slot>…wav — slot is the global mic index (mic test order), not ALSA hw numbers.
    """

    def __init__(self, file_path: str, name: str) -> None:
        super().__init__()
        self._file_path = file_path
        self._name = name
        self._recording_slots: list[int] = []
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

        all_mics = list_usb_recording_devices()
        self._recording_slots = get_enabled_slots_for_count(len(all_mics))
        if not self._recording_slots:
            self._status.text = "No mics to record"
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

        num_channels = CHANNELS
        sample_rate = SAMPLE_RATE

        all_mics = list_usb_recording_devices()
        mic_entries: list[tuple[int, int]] = [
            (all_mics[slot]["index"], slot) for slot in self._recording_slots
        ]
        n_mics = len(self._recording_slots)
        mic_word = "mic" if n_mics == 1 else "mics"

        write_session_metadata(
            get_recordings_path(),
            file_prefix,
            recording_mode="playback_record",
            source_wav=os.path.basename(self._file_path),
            duration_seconds=actual_time,
            mic_indices=list(self._recording_slots),
            sample_rate=SAMPLE_RATE,
            wav_name_pattern=f"{file_prefix}_mic<index>.wav",
        )

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
                    subtype=WAV_SUBTYPE,
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
                self._status.text = (
                    f"Play+Rec\nwith {n_mics} {mic_word}\n"
                    f"{get_duration_text(remaining)} left"
                )
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
            for mic_id, slot in mic_entries:
                q = queue.Queue()
                t = threading.Thread(target=record, args=[mic_id, slot, q])
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
