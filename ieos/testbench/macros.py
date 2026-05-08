# ieos/testbench/macros.py
"""Macro catalog and step expansion (no gui imports — safe for unit tests)."""

from __future__ import annotations

from typing import Any


def _keyboard_name_a_go() -> list[dict[str, Any]]:
    return [
        {"type": "tap", "code": "KEY1"},
        {"type": "tap", "code": "DOWN"},
        {"type": "tap", "code": "DOWN"},
        {"type": "tap", "code": "RIGHT"},
        {"type": "tap", "code": "RIGHT"},
        {"type": "tap", "code": "RIGHT"},
        {"type": "tap", "code": "KEY1"},
    ]


def _record_setup_60_seconds() -> list[dict[str, Any]]:
    return [{"type": "tap", "code": "KEY3"} for _ in range(9)] + [{"type": "tap", "code": "BUTTON"}]


def _main_menu_select(row: int) -> list[dict[str, Any]]:
    # Main menu selection persists after child VCs pop, so reset to the top before moving down.
    reset_to_top = [{"type": "tap", "code": "UP"} for _ in range(5)]
    return reset_to_top + [{"type": "tap", "code": "DOWN"} for _ in range(row)] + [
        {"type": "tap", "code": "BUTTON"}
    ]


MACROS: dict[str, list[dict[str, Any]]] = {
    "keyboard_name_a_go": _keyboard_name_a_go(),
    "main_menu_open_record": _main_menu_select(0),
    "record_setup_60_seconds": _record_setup_60_seconds(),
    "record_setup_default_confirm": [{"type": "tap", "code": "BUTTON"}],
    "main_menu_play": _main_menu_select(1),
    "play_menu_listen": [{"type": "tap", "code": "BUTTON"}],
    "play_menu_live_listen": [{"type": "tap", "code": "DOWN"}, {"type": "tap", "code": "BUTTON"}],
    "play_menu_play_record": [
        {"type": "tap", "code": "DOWN"},
        {"type": "tap", "code": "DOWN"},
        {"type": "tap", "code": "BUTTON"},
    ],
    "main_menu_mic_test": _main_menu_select(2),
    "main_menu_files": _main_menu_select(3),
    "files_open_browse": [{"type": "tap", "code": "DOWN"}, {"type": "tap", "code": "BUTTON"}],
    "main_menu_settings": _main_menu_select(4),
    "back_key2": [{"type": "tap", "code": "KEY2"}],
    "settings_open_scheduled": [{"type": "tap", "code": "BUTTON"}],
    "settings_open_update_usb": [{"type": "tap", "code": "DOWN"}, {"type": "tap", "code": "BUTTON"}],
    "cancel_record_at_keyboard": [
        {"type": "macro", "name": "main_menu_open_record"},
        {"type": "wait", "seconds": 0.5},
        {"type": "wait_for_vc", "class": "KeyboardViewController", "timeout_sec": 25},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "MainMenuViewController", "timeout_sec": 25},
    ],
    "record_flow_60": [
        {"type": "macro", "name": "main_menu_open_record"},
        {"type": "wait", "seconds": 0.5},
        {"type": "wait_for_vc", "class": "KeyboardViewController", "timeout_sec": 25},
        {"type": "macro", "name": "keyboard_name_a_go"},
        {"type": "wait_for_vc", "class": "RecordSetupViewController", "timeout_sec": 30},
        {"type": "macro", "name": "record_setup_60_seconds"},
        {"type": "wait", "seconds": 2},
        {"type": "wait_for_vc", "class": "MicTestViewController", "timeout_sec": 45},
        {"type": "mic_confirm_go", "max_wait_sec": 90},
        {"type": "wait", "seconds": 75},
        {"type": "wait_for_vc", "class": "MainMenuViewController", "timeout_sec": 300},
    ],
    "record_flow_600_default": [
        {"type": "macro", "name": "main_menu_open_record"},
        {"type": "wait", "seconds": 0.5},
        {"type": "wait_for_vc", "class": "KeyboardViewController", "timeout_sec": 25},
        {"type": "macro", "name": "keyboard_name_a_go"},
        {"type": "wait_for_vc", "class": "RecordSetupViewController", "timeout_sec": 30},
        {"type": "macro", "name": "record_setup_default_confirm"},
        {"type": "wait", "seconds": 2},
        {"type": "wait_for_vc", "class": "MicTestViewController", "timeout_sec": 45},
        {"type": "mic_confirm_go", "max_wait_sec": 90},
        {"type": "wait", "seconds": 660},
        {"type": "wait_for_vc", "class": "MainMenuViewController", "timeout_sec": 300},
    ],
    "play_listen_flow": [
        {"type": "macro", "name": "main_menu_play"},
        {"type": "wait_for_vc", "class": "PlayMenuViewController", "timeout_sec": 20},
        {"type": "macro", "name": "play_menu_listen"},
        {"type": "wait_for_vc", "class": "PlaybackFileSelectViewController", "timeout_sec": 25},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "PlayMenuViewController", "timeout_sec": 20},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "MainMenuViewController", "timeout_sec": 20},
    ],
    "mic_test_visit": [
        {"type": "macro", "name": "main_menu_mic_test"},
        {"type": "wait_for_vc", "class": "MicTestViewController", "timeout_sec": 25},
        {"type": "wait", "seconds": 5},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "MainMenuViewController", "timeout_sec": 20},
    ],
    "files_browse_flow": [
        {"type": "macro", "name": "main_menu_files"},
        {"type": "wait_for_vc", "class": "FilesMenuViewController", "timeout_sec": 30},
        {"type": "macro", "name": "files_open_browse"},
        {"type": "wait_for_vc", "class": "RecordingsFilesViewController", "timeout_sec": 30},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "FilesMenuViewController", "timeout_sec": 20},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "MainMenuViewController", "timeout_sec": 20},
    ],
    "settings_tour": [
        {"type": "macro", "name": "main_menu_settings"},
        {"type": "wait_for_vc", "class": "SettingsViewController", "timeout_sec": 25},
        {"type": "macro", "name": "settings_open_scheduled"},
        {"type": "wait_for_vc", "class": "ScheduledRecordingsViewController", "timeout_sec": 25},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "SettingsViewController", "timeout_sec": 20},
        {"type": "macro", "name": "settings_open_update_usb"},
        {"type": "wait_for_vc", "class": "UpdateFromUSBViewController", "timeout_sec": 25},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "SettingsViewController", "timeout_sec": 20},
        {"type": "macro", "name": "back_key2"},
        {"type": "wait_for_vc", "class": "MainMenuViewController", "timeout_sec": 20},
    ],
}


def expand_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in steps:
        t = s.get("type")
        if t == "macro":
            name = s["name"]
            inner = MACROS.get(name)
            if inner is None:
                raise ValueError(f"unknown macro: {name}")
            out.extend(expand_steps([dict(x) for x in inner]))
        elif t == "repeat":
            n = int(s["times"])
            inner = s["steps"]
            for _ in range(n):
                out.extend(expand_steps(list(inner)))
        else:
            out.append(dict(s))
    return out
