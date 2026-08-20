# tests/test_time_utils.py
from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

from gui.utils.time import TimeUtils


class NtpSyncedTests(unittest.TestCase):
    def test_not_linux(self) -> None:
        with patch.object(sys, "platform", "darwin"):
            self.assertFalse(TimeUtils.ntp_synchronized_linux())

    @patch.object(sys, "platform", "linux")
    @patch.object(TimeUtils.subprocess, "run", autospec=True)
    def test_yes_stdout(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="yes\n")
        self.assertTrue(TimeUtils.ntp_synchronized_linux())
        mock_run.assert_called_once()

    @patch.object(sys, "platform", "linux")
    @patch.object(TimeUtils.subprocess, "run", autospec=True)
    def test_no_stdout(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="no\n")
        self.assertFalse(TimeUtils.ntp_synchronized_linux())


class SetSystemTimeTests(unittest.TestCase):
    @patch.object(sys, "platform", "linux")
    @patch.object(TimeUtils.subprocess, "run", autospec=True)
    def test_reenables_ntp_after_set_time(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        ok, msg = TimeUtils.set_system_time("2026-05-05 12:00:00")
        self.assertTrue(ok)
        self.assertIn("success", msg.lower())
        self.assertEqual(mock_run.call_count, 3)
        calls = [c.args[0] for c in mock_run.call_args_list]
        self.assertEqual(
            calls,
            [
                ["sudo", "-n", "timedatectl", "set-ntp", "false"],
                ["sudo", "-n", "timedatectl", "set-time", "2026-05-05 12:00:00"],
                ["sudo", "-n", "timedatectl", "set-ntp", "true"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
