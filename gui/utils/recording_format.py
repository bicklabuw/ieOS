# gui/utils/recording_format.py
"""PCM WAV capture parameters shared by recording and free-space estimates."""

from __future__ import annotations

import time

# Must match SoundFile settings in RecordViewController / PlayAndRecordViewController.
SAMPLE_RATE = 44100
CHANNELS = 1
BYTES_PER_SAMPLE = 3  # PCM_24
WAV_SUBTYPE = "PCM_24"
MAX_USB_MICS = 4

# Delay between starting parallel USB capture streams (mitigates controller
# contention when multiple full-speed USB audio gadgets share a hub/tree).
USB_MIC_STREAM_START_STAGGER_SEC = 0.08

# After closing capture streams, ALSA/PortAudio on Pi often needs a beat before the
# next open; skipping this tends to manifest as crashes after several record sessions.
PORTAUDIO_CAPTURE_SETTLE_SEC = 0.25

FOUR_MIC_SAMPLE_RATE = 22050
NORMAL_CAPTURE_BLOCKSIZE = 750
FOUR_MIC_CAPTURE_BLOCKSIZE = 1024


def bytes_per_second_for_mic_count(num_mics: int) -> int:
    """Linear PCM payload rate (excludes WAV headers); clamped to 0..MAX_USB_MICS."""
    n = max(0, min(int(num_mics), MAX_USB_MICS))
    return SAMPLE_RATE * CHANNELS * BYTES_PER_SAMPLE * n


def select_capture_sample_rate(num_mics: int) -> int:
    """Prefer lower sample rate for 4-mic sessions to reduce USB bandwidth pressure."""
    return FOUR_MIC_SAMPLE_RATE if int(num_mics) >= 4 else SAMPLE_RATE


def select_capture_blocksize(num_mics: int) -> int:
    """Use larger buffers for 4-mic sessions to reduce stream startup/runtime churn."""
    return FOUR_MIC_CAPTURE_BLOCKSIZE if int(num_mics) >= 4 else NORMAL_CAPTURE_BLOCKSIZE


def settle_portaudio_after_capture_close(*, stop_streams: bool = True) -> None:
    """
    Wait before opening new capture streams (ALSA/PortAudio on Pi).

    When capture is the only sounddevice user, pass stop_streams=True (default) so
    sd.stop() clears any stuck host state. If playback is active (e.g. play+record),
    pass stop_streams=False and only sleep so playback is not cut off.
    """
    if stop_streams:
        import sounddevice as sd

        try:
            sd.stop()
        except Exception:
            pass
    time.sleep(PORTAUDIO_CAPTURE_SETTLE_SEC)


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


def format_compact_duration_d_h(seconds: int, max_width_hint: int = 20) -> str:
    """Like format_compact_duration_h_m but uses days when >= 24h (e.g. 3d, 3d5h)."""
    if seconds <= 0:
        return "0m"
    days = seconds // 86400
    if days <= 0:
        return format_compact_duration_h_m(seconds, max_width_hint=max_width_hint)
    rem = seconds % 86400
    h = rem // 3600
    if h:
        s = f"{days}d{h}h"
    else:
        s = f"{days}d"
    if len(s) > max_width_hint:
        s = s[: max_width_hint - 1] + "…"
    return s
