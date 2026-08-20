from __future__ import annotations

import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ieos.app_preferences import AppPreferences, load_preferences, save_preferences


class AppPreferencesTests(unittest.TestCase):
    def test_missing_file_returns_defaults(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "none.json")
            p = load_preferences(path)
            self.assertTrue(p.show_tutorial_at_startup)
            self.assertTrue(p.scheduler_enabled_on_startup)

    def test_save_and_round_trip(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "app_preferences.json")
            save_preferences(
                AppPreferences(
                    show_tutorial_at_startup=False,
                    scheduler_enabled_on_startup=False,
                ),
                path,
            )
            loaded = load_preferences(path)
            self.assertFalse(loaded.show_tutorial_at_startup)
            self.assertFalse(loaded.scheduler_enabled_on_startup)

    def test_save_syncs_file_and_directory_for_reboot_durability(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "app_preferences.json")

            with (
                patch("gui.utils.durable_io.os.fsync") as fsync,
                patch("gui.utils.durable_io.os.open", return_value=123),
                patch("gui.utils.durable_io.os.close") as close,
            ):
                save_preferences(AppPreferences(show_tutorial_at_startup=False), path)

            self.assertEqual(2, fsync.call_count)
            fsync.assert_any_call(123)
            close.assert_called_once_with(123)

    def test_invalid_json_returns_defaults(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("not json")
            p = load_preferences(path)
            self.assertTrue(p.show_tutorial_at_startup)


if __name__ == "__main__":
    unittest.main()
