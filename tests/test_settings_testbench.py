from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from ieos.SettingsViewController import SettingsViewController
from ieos.TestbenchViewController import TestbenchMenuViewController
from ieos.testbench import runner


class SettingsTestbenchTests(unittest.TestCase):
    def test_settings_menu_includes_testbench_entry(self) -> None:
        items = SettingsViewController._menu_items()

        self.assertIn("Run testbench", items)
        self.assertLess(items.index("Update from USB"), items.index("Run testbench"))

    def test_testbench_menu_exposes_quick_and_long(self) -> None:
        vc = TestbenchMenuViewController()

        self.assertEqual(["Quick testbench", "Long testbench"], vc._base_items)

    def test_mode_selection_uses_explicit_scenario_not_env_default(self) -> None:
        with patch.dict(os.environ, {"IEOS_TESTBENCH_QUICK": "1"}):
            _, sources = runner.load_steps_for_mode("long")

        self.assertEqual(1, len(sources))
        self.assertTrue(sources[0].endswith(os.path.join("scenarios", "default.json")))


if __name__ == "__main__":
    unittest.main()
