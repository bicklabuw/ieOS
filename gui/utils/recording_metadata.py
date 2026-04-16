# gui/utils/recording_metadata.py
import logging
import os
from datetime import datetime, timezone
from typing import Any

from gui.utils.PlatformUtils import get_device_serial

_log = logging.getLogger(__name__)


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return str(value)
    return repr(value)


def write_session_metadata(recordings_dir: str, file_prefix: str, **fields: Any) -> str | None:
    """
    Write one plain-text metadata file per recording session next to the WAV files.

    Filename: {file_prefix}_meta.txt
    Lines are ``key: value`` (value repr'd when not a simple scalar string).
    Returns the path, or None if the write failed (recording may still proceed).
    """
    path = os.path.join(recordings_dir, f"{file_prefix}_meta.txt")
    lines = [
        f"device_serial: {_format_value(get_device_serial())}",
        f"file_prefix: {_format_value(file_prefix)}",
        f"recorded_at_utc: {datetime.now(timezone.utc).isoformat()}",
    ]
    for key in sorted(fields):
        lines.append(f"{key}: {_format_value(fields[key])}")
    body = "\n".join(lines) + "\n"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    except OSError as e:
        _log.warning("Could not write recording metadata %s: %s", path, e)
        return None
    return path
