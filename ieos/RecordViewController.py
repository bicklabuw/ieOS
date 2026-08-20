import sounddevice as sd
import soundfile as sf
from datetime import datetime
import time
import threading
import queue
import sys

import numpy as np

import gui.core.Display as Display
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import MultilineTextView, TextView, TextAnchor
from gui.core.Display import SCREEN_WIDTH, SCREEN_HEIGHT
from gui.utils.recording_format import (
    CHANNELS,
    SAMPLE_RATE,
    select_capture_blocksize,
    settle_portaudio_after_capture_close,
    USB_MIC_STREAM_START_STAGGER_SEC,
    WAV_SUBTYPE,
    list_usb_recording_devices,
)
from ieos.mic_selection_store import get_enabled_slots_for_count
from gui.utils.recording_metadata import write_session_metadata
from gui.utils.recording_wav import sync_recording_file, write_queue_to_soundfile
from gui.utils.usb.USBDriveManager import (
    assert_recordings_still_ready,
    ensure_recordings_ready,
    get_recordings_path,
    unmount_pendrive,
)
from gui.utils.time.TimeUtils import get_duration_text
from ieos.recording_runtime_state import try_begin_recording, end_recording

MAX_FILE_RECORD_TIME = 3600  # 1 hour per file segment


class RecordViewController(ViewController[None]):
    def __init__(
        self,
        name: str,
        duration: int,
        *,
        recording_source: str = "manual",
        schedule_id: str | None = None,
    ) -> None:
        super().__init__()
        self._name = name
        self._duration = duration
        self._recording_source = recording_source
        self._schedule_id = schedule_id
        self._recording_context = (
            "manual" if recording_source == "manual" else f"scheduled:{schedule_id or 'unknown'}"
        )
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
        if not try_begin_recording(self._recording_context):
            self._status.text = "Recorder busy"
            time.sleep(2)
            self.pop_view_controller()
            return

        # 1. Mount USB, create /WAV, verify writable (retries on hot-plug)
        try:
            ensure_recordings_ready()
            # 3. Reset stop flag
            self.stop_recording = False

            # 4. Run recording (blocks until done)
            self._run_recording()

            # 5. Unmount and pop
            unmount_pendrive()
            self.pop_view_controller()
        except OSError as e:
            self._status.text = f"USB not ready:\n{e}"
            time.sleep(2)
            self.pop_view_controller()
        finally:
            end_recording(self._recording_context)

    def _run_recording(self) -> None:
        indefinite = self._duration == 0
        now = datetime.now()
        date_str = now.strftime("%m_%d_%Y_%H_%M_%S")
        file_prefix = f"{self._name}_{date_str}"

        mics = list_usb_recording_devices()
        mic_slots = get_enabled_slots_for_count(len(mics))
        if not mic_slots:
            self._status.text = "No mics to record"
            time.sleep(2)
            return

        settle_portaudio_after_capture_close()

        n_mics = len(mic_slots)
        mic_word = "mic" if n_mics == 1 else "mics"
        sample_rate = SAMPLE_RATE
        capture_blocksize = select_capture_blocksize(n_mics)

        write_session_metadata(
            get_recordings_path(),
            file_prefix,
            recording_mode="record",
            session_name=self._name,
            duration_seconds=None if indefinite else self._duration,
            indefinite=indefinite,
            mic_indices=mic_slots,
            sample_rate=sample_rate,
            wav_name_pattern=f"{file_prefix}mic<index>hour<segment>.wav",
        )

        num_channels = CHANNELS
        segment_duration = MAX_FILE_RECORD_TIME

        def record(id, index, hour, q):
            def callback(indata, frames, time_, status):
                q.put(indata.copy())

            file_path = f"{get_recordings_path()}/{file_prefix}mic{index}hour{hour}.wav"
            try:
                with sf.SoundFile(
                    file_path,
                    mode="x",
                    samplerate=sample_rate,
                    channels=num_channels,
                    subtype=WAV_SUBTYPE,
                ) as f:
                    with sd.InputStream(
                        samplerate=sample_rate,
                        blocksize=capture_blocksize,
                        device=id,
                        channels=num_channels,
                        callback=callback,
                    ):
                        t0 = time.time()
                        end_t = t0 + segment_duration
                        ok, err = write_queue_to_soundfile(
                            f,
                            q,
                            stop_check=lambda: self.stop_recording,
                            segment_end_time=end_t,
                            durable_path=file_path,
                        )
                        if not ok:
                            self._status.text = f"Write error:\n{err}"
                            self.stop_recording = True
                sync_recording_file(file_path)
            except Exception as e:
                self._status.text = f"Error:\n{e}"
                self.stop_recording = True

        def countdown_indefinite():
            while not self.stop_recording and threading.current_thread() is cnt_thread:
                self._status.text = f"Recording...\nwith {n_mics} {mic_word}"
                time.sleep(1)

        def countdown_timed(total):
            remaining = total
            while remaining >= 0 and not self.stop_recording and threading.current_thread() is cnt_thread:
                self._status.text = (
                    f"Recording...\nwith {n_mics} {mic_word}\n"
                    f"{get_duration_text(remaining)} left"
                )
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
            try:
                assert_recordings_still_ready()
            except OSError as e:
                self._status.text = f"USB removed:\n{e}"
                self.stop_recording = True
                break

            seg = segment_duration if indefinite else min(remaining_time, segment_duration)
            segment_duration = seg  # used by record() closure

            mic_threads = []
            n_slots = len(mic_slots)
            for k, slot in enumerate(mic_slots):
                mic_id = mics[slot]["index"]
                q = queue.Queue()
                t = threading.Thread(
                    target=record,
                    args=(mic_id, slot, rec_cnt, q),
                    daemon=True,
                )
                mic_threads.append(t)
                t.start()
                if n_slots >= 2 and k < n_slots - 1:
                    time.sleep(USB_MIC_STREAM_START_STAGGER_SEC)

            for t in mic_threads:
                t.join()

            if self.stop_recording:
                break

            rec_cnt += 1
            if not indefinite:
                remaining_time -= seg

            will_continue = indefinite or (remaining_time is not None and remaining_time > 0)
            if will_continue and not self.stop_recording:
                settle_portaudio_after_capture_close()

        settle_portaudio_after_capture_close()

        cnt_thread.join(0.5 if self.stop_recording else None)
        self._status.text = "Stopped" if self.stop_recording else "Done!"
        time.sleep(1)

    def on_key2_press(self) -> None:
        self._status.text = "Stopping..."
        self.stop_recording = True
        # Do NOT call pop_view_controller here — on_appear handles it

    def on_disappear(self) -> None:
        self.stop_recording = True
