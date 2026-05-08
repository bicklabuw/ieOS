# gui/utils/recording_wav.py
"""Helpers for reliable WAV capture: bounded queue reads, periodic flush, clean errors."""

from __future__ import annotations

import os
import queue
import time
from typing import Callable, Optional

import soundfile as sf

from gui.utils.durable_io import fsync_directory, fsync_file


def sync_recording_file(path: str) -> None:
    fsync_file(path)
    fsync_directory(os.path.dirname(path) or ".")


def _flush_soundfile(wav: sf.SoundFile, durable_path: str | None) -> None:
    wav.flush()
    if durable_path:
        fsync_file(durable_path)


def write_queue_to_soundfile(
    wav: sf.SoundFile,
    q: queue.Queue,
    *,
    stop_check: Callable[[], bool],
    segment_end_time: float,
    flush_every: int = 64,
    queue_timeout: float = 0.5,
    durable_path: str | None = None,
) -> tuple[bool, Optional[str]]:
    """
    Drain audio from queue into an open SoundFile until segment time expires or stop_check.

    Returns (success, error_message). On failure, caller should stop_recording.
    """
    writes = 0
    try:
        while time.time() < segment_end_time and not stop_check():
            try:
                chunk = q.get(timeout=queue_timeout)
            except queue.Empty:
                continue
            wav.write(chunk)
            writes += 1
            if writes % flush_every == 0:
                _flush_soundfile(wav, durable_path)
        _flush_soundfile(wav, durable_path)
        return True, None
    except OSError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
