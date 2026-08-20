from __future__ import annotations

import threading

_lock = threading.Lock()
_active_context: str | None = None


def try_begin_recording(context: str) -> bool:
    global _active_context
    with _lock:
        if _active_context is not None:
            return False
        _active_context = context
        return True


def end_recording(context: str) -> None:
    global _active_context
    with _lock:
        if _active_context == context:
            _active_context = None


def is_any_recording_active() -> bool:
    with _lock:
        return _active_context is not None


def is_manual_recording_active() -> bool:
    with _lock:
        return _active_context == "manual"

