# ieos/mic_selection_store.py
"""Persist which logical USB mic slots (0..n-1) are enabled for recording."""

from __future__ import annotations

import json
import logging
import os
from typing import Iterable

from gui.utils.durable_io import write_json_atomic

_log = logging.getLogger(__name__)

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "ieos")
_STORE_PATH = os.path.join(_CONFIG_DIR, "mic_selection.json")


def _load_raw() -> list[int] | None:
    try:
        with open(_STORE_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    slots = data.get("enabled_slots")
    if not isinstance(slots, list):
        return None
    out: list[int] = []
    for x in slots:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            continue
    return out


def get_enabled_slots_for_count(n: int) -> list[int]:
    """
    Enabled slot indices for n currently present USB mics, sorted.
    Intersects stored selection with range(n). If empty, defaults to all slots.
    """
    if n <= 0:
        return []
    stored = _load_raw()
    if not stored:
        return list(range(n))
    valid = sorted({i for i in stored if 0 <= i < n})
    if not valid:
        return list(range(n))
    return valid


def set_enabled_slots(slots: Iterable[int]) -> None:
    """Write enabled slot indices to disk durably (best-effort on errors)."""
    unique = sorted({int(i) for i in slots})
    payload = {"enabled_slots": unique}
    try:
        write_json_atomic(_STORE_PATH, payload)
    except OSError as e:
        _log.warning("Could not save mic selection: %s", e)
