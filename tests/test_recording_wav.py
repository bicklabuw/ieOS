from __future__ import annotations

import queue
import time
import unittest
from unittest.mock import patch

from gui.utils import recording_wav


class _FakeSoundFile:
    def __init__(self) -> None:
        self.writes = 0
        self.flushes = 0

    def write(self, chunk: object) -> None:
        self.writes += 1

    def flush(self) -> None:
        self.flushes += 1


class RecordingWavTests(unittest.TestCase):
    def test_write_queue_fsyncs_path_on_periodic_flushes(self) -> None:
        q: queue.Queue[object] = queue.Queue()
        q.put(object())
        q.put(object())
        wav = _FakeSoundFile()

        with patch("gui.utils.recording_wav.fsync_file") as fsync_file:
            ok, err = recording_wav.write_queue_to_soundfile(
                wav,
                q,
                stop_check=lambda: q.empty(),
                segment_end_time=time.time() + 10,
                flush_every=1,
                durable_path="/tmp/recording.wav",
            )

        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertEqual(2, wav.writes)
        self.assertEqual(3, wav.flushes)
        self.assertEqual(3, fsync_file.call_count)
        fsync_file.assert_any_call("/tmp/recording.wav")

    def test_sync_recording_file_syncs_file_and_directory(self) -> None:
        with (
            patch("gui.utils.recording_wav.fsync_file") as fsync_file,
            patch("gui.utils.recording_wav.fsync_directory") as fsync_directory,
        ):
            recording_wav.sync_recording_file("/mnt/usb/WAV/a.wav")

        fsync_file.assert_called_once_with("/mnt/usb/WAV/a.wav")
        fsync_directory.assert_called_once_with("/mnt/usb/WAV")


if __name__ == "__main__":
    unittest.main()
