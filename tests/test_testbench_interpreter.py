from __future__ import annotations

import json
import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ieos.testbench import interpreter


class TestbenchInterpreterTests(unittest.TestCase):
    def test_run_steps_can_return_without_requesting_exit(self) -> None:
        with TemporaryDirectory() as tmp, patch(
            "ieos.testbench.interpreter.request_process_exit"
        ) as request_exit:
            report_path = os.path.join(tmp, "report.json")

            result = interpreter.run_steps(
                [{"id": "done", "type": "log", "text": "ok"}],
                time_scale=1.0,
                scenario_sources=["quick.json"],
                report_path=report_path,
                exit_on_finish=False,
            )

            self.assertTrue(result.success)
            self.assertEqual(0, result.exit_code)
            self.assertEqual(report_path, result.report_path)
            request_exit.assert_not_called()
            with open(report_path, encoding="utf-8") as f:
                payload = json.load(f)
            self.assertTrue(payload["success"])
            self.assertEqual("ok", payload["message"])

    def test_run_steps_cli_mode_still_requests_exit(self) -> None:
        with TemporaryDirectory() as tmp, patch(
            "ieos.testbench.interpreter.request_process_exit"
        ) as request_exit:
            report_path = os.path.join(tmp, "report.json")

            result = interpreter.run_steps(
                [{"id": "done", "type": "log", "text": "ok"}],
                time_scale=1.0,
                scenario_sources=["default.json"],
                report_path=report_path,
            )

            self.assertTrue(result.success)
            request_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
