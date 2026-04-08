# gui/utils/recording_wav.py
"""Helpers for reliable WAV capture: bounded queue reads, periodic flush, clean errors."""

from __future__ import annotations

import queue
import time
from typing import Callable, Optional

import soundfile as sf


def write_queue_to_soundfile(
    wav: sf.SoundFile,
    q: queue.Queue,
    *,
    stop_check: Callable[[], bool],
    segment_end_time: float,
    flush_every: int = 64,
    queue_timeout: float = 0.5,
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
                wav.flush()
        wav.flush()
        return True, None
    except OSError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
