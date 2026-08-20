# tests/test_testbench_macros.py
from __future__ import annotations

import unittest

from ieos.testbench.macros import MACROS, expand_steps


class TestbenchMacrosTests(unittest.TestCase):
    def test_expand_back_key2(self) -> None:
        e = expand_steps([{"type": "macro", "name": "back_key2"}])
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0], {"type": "tap", "code": "KEY2"})

    def test_cancel_keyboard_expands(self) -> None:
        e = expand_steps([{"type": "macro", "name": "cancel_record_at_keyboard"}])
        self.assertGreater(len(e), 3)
        self.assertTrue(any(s.get("type") == "tap" for s in e))

    def test_unknown_macro_raises(self) -> None:
        with self.assertRaises(ValueError):
            expand_steps([{"type": "macro", "name": "no_such_macro"}])

    def test_macros_nonempty(self) -> None:
        self.assertIn("record_flow_60", MACROS)

    def test_main_menu_macros_reset_selection_before_navigating(self) -> None:
        reset = [{"type": "tap", "code": "UP"} for _ in range(5)]
        self.assertEqual(MACROS["main_menu_open_record"], reset + [{"type": "tap", "code": "BUTTON"}])
        self.assertEqual(
            MACROS["main_menu_mic_test"],
            reset
            + [
                {"type": "tap", "code": "DOWN"},
                {"type": "tap", "code": "DOWN"},
                {"type": "tap", "code": "BUTTON"},
            ],
        )

    def test_play_menu_macros_account_for_live_listen_row(self) -> None:
        self.assertEqual(MACROS["play_menu_listen"], [{"type": "tap", "code": "BUTTON"}])
        self.assertEqual(
            MACROS["play_menu_live_listen"],
            [{"type": "tap", "code": "DOWN"}, {"type": "tap", "code": "BUTTON"}],
        )
        self.assertEqual(
            MACROS["play_menu_play_record"],
            [
                {"type": "tap", "code": "DOWN"},
                {"type": "tap", "code": "DOWN"},
                {"type": "tap", "code": "BUTTON"},
            ],
        )

    def test_record_flow_uses_mic_confirm_go(self) -> None:
        e = expand_steps([{"type": "macro", "name": "record_flow_60"}])
        types = [s.get("type") for s in e]
        self.assertIn("mic_confirm_go", types)
        self.assertNotIn("mic_go", types)


if __name__ == "__main__":
    unittest.main()
