from __future__ import annotations

import unittest

import numpy as np

from ieos.LiveListenViewController import _AudioRingBuffer, select_next_enabled_slot


class LiveListenSelectionTests(unittest.TestCase):
    def test_selects_first_slot_when_current_missing(self) -> None:
        self.assertEqual(select_next_enabled_slot([1, 3], None, 1), 1)

    def test_wraps_forward_and_backward(self) -> None:
        self.assertEqual(select_next_enabled_slot([0, 2, 3], 3, 1), 0)
        self.assertEqual(select_next_enabled_slot([0, 2, 3], 0, -1), 3)

    def test_skips_unavailable_slots(self) -> None:
        self.assertEqual(select_next_enabled_slot([0, 1, 2], 0, 1, [1]), 2)
        self.assertIsNone(select_next_enabled_slot([0, 1], 0, 1, [0, 1]))


class AudioRingBufferTests(unittest.TestCase):
    def test_read_zero_fills_underrun(self) -> None:
        b = _AudioRingBuffer(max_frames=4, channels=1)
        b.write(np.array([[0.25], [0.5]], dtype=np.float32))

        out = b.read(4)

        np.testing.assert_array_equal(
            out,
            np.array([[0.25], [0.5], [0.0], [0.0]], dtype=np.float32),
        )
        self.assertEqual(b.available_frames, 0)

    def test_overflow_drops_oldest_audio(self) -> None:
        b = _AudioRingBuffer(max_frames=3, channels=1)
        b.write(np.array([[1.0], [2.0], [3.0]], dtype=np.float32))
        b.write(np.array([[4.0], [5.0]], dtype=np.float32))

        out = b.read(3)

        np.testing.assert_array_equal(
            out,
            np.array([[3.0], [4.0], [5.0]], dtype=np.float32),
        )


if __name__ == "__main__":
    unittest.main()
