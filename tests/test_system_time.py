from __future__ import annotations

import sys
import threading
import unittest
from unittest.mock import patch

from ieos.SystemTime import SystemTimeViewController, TIME_SYNC_STATUS_TEXT


class SystemTimeStartupTests(unittest.TestCase):
    def test_shows_status_while_waiting_for_ntp(self) -> None:
        wait_started = threading.Event()
        release_wait = threading.Event()

        def wait_for_ntp() -> bool:
            wait_started.set()
            release_wait.wait(timeout=1)
            return False

        vc = SystemTimeViewController()

        with (
            patch.object(sys, "platform", "linux"),
            patch("ieos.SystemTime.is_raspberry_pi", return_value=True),
            patch("ieos.SystemTime.wait_for_ntp_sync_linux", side_effect=wait_for_ntp),
            patch.object(vc, "push_view_controller") as push_view_controller,
        ):
            vc.on_appear()
            self.assertTrue(wait_started.wait(timeout=1))
            self.assertEqual(vc.title.text, TIME_SYNC_STATUS_TEXT)
            self.assertTrue(vc.title.text.strip())
            push_view_controller.assert_not_called()

            vc._abort_picker = True
            release_wait.set()


if __name__ == "__main__":
    unittest.main()
