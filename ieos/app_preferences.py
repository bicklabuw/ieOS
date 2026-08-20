# ieos/app_preferences.py
"""Persisted app-wide preferences (tutorial, scheduler on boot)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

from gui.utils.durable_io import write_json_atomic

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "ieos")
_DEFAULT_PATH = os.path.join(_CONFIG_DIR, "app_preferences.json")


@dataclass
class AppPreferences:
    show_tutorial_at_startup: bool = True
    scheduler_enabled_on_startup: bool = True


def _default_path(path: str | None) -> str:
    return path if path is not None else _DEFAULT_PATH


def load_preferences(path: str | None = None) -> AppPreferences:
    p = _default_path(path)
    try:
        with open(p, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return AppPreferences()
    if not isinstance(raw, dict):
        return AppPreferences()
    show_t = raw.get("show_tutorial_at_startup", True)
    sched = raw.get("scheduler_enabled_on_startup", True)
    return AppPreferences(
        show_tutorial_at_startup=bool(show_t),
        scheduler_enabled_on_startup=bool(sched),
    )


def save_preferences(prefs: AppPreferences, path: str | None = None) -> None:
    write_json_atomic(_default_path(path), asdict(prefs))
