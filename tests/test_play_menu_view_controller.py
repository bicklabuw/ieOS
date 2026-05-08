from __future__ import annotations

import unittest
from unittest.mock import patch

from ieos.LiveListenViewController import LiveListenViewController
from ieos.PlayMenuViewController import PlayMenuViewController
from ieos.PlayRecordFileSelectViewController import PlayRecordFileSelectViewController
from ieos.PlaybackFileSelectViewController import PlaybackFileSelectViewController


class PlayMenuViewControllerTests(unittest.TestCase):
    def test_live_listen_sits_between_listen_and_play_record(self) -> None:
        vc = PlayMenuViewController()

        self.assertEqual(vc._items, ["Listen", "Live listen", "Play + record"])

    def test_routes_each_row_to_expected_controller(self) -> None:
        vc = PlayMenuViewController()

        with patch.object(vc, "push_view_controller") as push:
            vc.did_select_row_at(0, "Listen")
            self.assertIsInstance(push.call_args.args[0], PlaybackFileSelectViewController)

            vc.did_select_row_at(1, "Live listen")
            self.assertIsInstance(push.call_args.args[0], LiveListenViewController)

            vc.did_select_row_at(2, "Play + record")
            self.assertIsInstance(push.call_args.args[0], PlayRecordFileSelectViewController)


if __name__ == "__main__":
    unittest.main()
