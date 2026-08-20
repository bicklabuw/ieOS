from __future__ import annotations

import json
import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from gui.utils import durable_io


class DurableIoTests(unittest.TestCase):
    def test_write_json_atomic_round_trips_and_syncs_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "state.json")

            with (
                patch("gui.utils.durable_io.os.fsync") as fsync,
                patch("gui.utils.durable_io.os.open", return_value=123),
                patch("gui.utils.durable_io.os.close") as close,
            ):
                durable_io.write_json_atomic(path, {"ok": True})

            with open(path, encoding="utf-8") as f:
                self.assertEqual({"ok": True}, json.load(f))
            self.assertGreaterEqual(fsync.call_count, 2)
            fsync.assert_any_call(123)
            close.assert_called_once_with(123)

    def test_copy_file_durable_syncs_destination_and_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "source.txt")
            dest = os.path.join(tmp, "nested", "dest.txt")
            with open(src, "w", encoding="utf-8") as f:
                f.write("payload\n")

            with (
                patch("gui.utils.durable_io.fsync_file") as fsync_file,
                patch("gui.utils.durable_io.fsync_directory") as fsync_directory,
            ):
                durable_io.copy_file_durable(src, dest)

            with open(dest, encoding="utf-8") as f:
                self.assertEqual("payload\n", f.read())
            fsync_file.assert_called_once_with(dest)
            fsync_directory.assert_called_once_with(os.path.dirname(dest))


if __name__ == "__main__":
    unittest.main()
