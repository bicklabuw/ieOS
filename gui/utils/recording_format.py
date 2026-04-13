# gui/utils/recording_format.py
"""PCM WAV capture parameters shared by recording and free-space estimates."""

from __future__ import annotations

# Must match SoundFile settings in RecordViewController / PlayAndRecordViewController.
SAMPLE_RATE = 44100
CHANNELS = 1
BYTES_PER_SAMPLE = 3  # PCM_24
WAV_SUBTYPE = "PCM_24"
MAX_USB_MICS = 3


def bytes_per_second_for_mic_count(num_mics: int) -> int:
    """Linear PCM payload rate (excludes WAV headers); clamped to 0..MAX_USB_MICS."""
    n = max(0, min(int(num_mics), MAX_USB_MICS))
    return SAMPLE_RATE * CHANNELS * BYTES_PER_SAMPLE * n


def estimate_record_seconds_remaining(free_bytes: int, num_mics: int) -> int:
    """
    Approximate seconds of simultaneous multi-mic recording storable in free_bytes.

    Real files add headers and may split into hourly segments; treat as a lower
    bound suitable for UI hints (e.g. "~2h free").
    """
    bps = bytes_per_second_for_mic_count(num_mics)
    if bps <= 0:
        return 0
    return int(free_bytes) // bps


def list_usb_recording_devices() -> list:
    """USB input device dicts from sounddevice, sorted by PortAudio index, at most MAX_USB_MICS."""
    import sounddevice as sd

    return sorted(
        (
            d
            for d in sd.query_devices()
            if d["name"].startswith("USB") and d["max_input_channels"] > 0
        ),
        key=lambda d: int(d["index"]),
    )[:MAX_USB_MICS]


def count_usb_input_mics() -> int:
    """USB input devices used for recording; same discovery as recording paths, capped at MAX_USB_MICS."""
    return len(list_usb_recording_devices())


def format_compact_duration_h_m(seconds: int, max_width_hint: int = 20) -> str:
    """Short string for 128px OLED (e.g. 2h15m, 45m, 0m)."""
    if seconds <= 0:
        return "0m"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0:
        s = f"{h}h{m:02d}m" if m else f"{h}h"
    else:
        s = f"{m}m"
    if len(s) > max_width_hint:
        s = s[: max_width_hint - 1] + "…"
    return s
