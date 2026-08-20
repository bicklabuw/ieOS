# tests/test_datetime_number_input.py
"""Regression tests for NumberInputView tap vs hold step (DateTimeViewController)."""

import unittest

from gui.ui_kit.DateTimeViewController import NumberInputView, TimeInputView


class NumberInputHoldStepTests(unittest.TestCase):
    def test_hold_step_advances_by_configured_amount(self) -> None:
        v = NumberInputView(value=10, min_value=0, max_value=59, hold_step=5)
        v.on_up_hold()
        self.assertEqual(v.value, 15)
        v.on_down_hold()
        self.assertEqual(v.value, 10)

    def test_press_still_steps_by_one(self) -> None:
        v = NumberInputView(value=10, min_value=0, max_value=59, hold_step=5)
        v.on_up_press()
        self.assertEqual(v.value, 11)

    def test_time_input_minutes_seconds_use_hold_step_five(self) -> None:
        t = TimeInputView()
        self.assertEqual(t.hours.hold_step, 1)
        self.assertEqual(t.minutes.hold_step, 5)
        self.assertEqual(t.seconds.hold_step, 5)


if __name__ == "__main__":
    unittest.main()
