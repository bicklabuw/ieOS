# gui/utils/recording_metadata.py
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from gui.utils.PlatformUtils import get_device_serial

_log = logging.getLogger(__name__)


def write_session_metadata(recordings_dir: str, file_prefix: str, **fields: Any) -> str | None:
    """
    Write one JSON metadata file per recording session next to the WAV files.

    Filename: {file_prefix}.meta.json
    Returns the path, or None if the write failed (recording may still proceed).
    """
    path = os.path.join(recordings_dir, f"{file_prefix}.meta.json")
    payload: dict[str, Any] = {
        "device_serial": get_device_serial(),
        "file_prefix": file_prefix,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        _log.warning("Could not write recording metadata %s: %s", path, e)
        return None
    return path
