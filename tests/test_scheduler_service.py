from __future__ import annotations

import unittest
from datetime import datetime

from ieos.schedule_store import MODE_DURATION, MODE_WINDOW, RecordingSchedule
from ieos.scheduler_service import compute_duration_seconds, is_due_now


class SchedulerServiceTests(unittest.TestCase):
    def test_duration_mode_duration(self) -> None:
        schedule = RecordingSchedule(
            schedule_id="a",
            name="A",
            enabled=True,
            days_of_week=[0],
            mode=MODE_DURATION,
            start_time="08:00",
            duration_seconds=900,
        )
        self.assertEqual(900, compute_duration_seconds(schedule))

    def test_window_mode_duration_crosses_midnight(self) -> None:
        schedule = RecordingSchedule(
            schedule_id="b",
            name="B",
            enabled=True,
            days_of_week=[0],
            mode=MODE_WINDOW,
            start_time="23:45",
            duration_seconds=None,
            end_time="00:15",
        )
        self.assertEqual(1800, compute_duration_seconds(schedule))

    def test_window_mode_long_overnight_eight_hours(self) -> None:
        schedule = RecordingSchedule(
            schedule_id="long",
            name="L",
            enabled=True,
            days_of_week=[0],
            mode=MODE_WINDOW,
            start_time="22:00",
            duration_seconds=None,
            end_time="06:00",
        )
        self.assertEqual(8 * 3600, compute_duration_seconds(schedule))

    def test_duration_mode_crosses_midnight_span_seconds(self) -> None:
        schedule = RecordingSchedule(
            schedule_id="d",
            name="D",
            enabled=True,
            days_of_week=[3],
            mode=MODE_DURATION,
            start_time="23:00",
            duration_seconds=3 * 3600,
        )
        self.assertEqual(3 * 3600, compute_duration_seconds(schedule))

    def test_is_due_now_matches_day_and_minute(self) -> None:
        schedule = RecordingSchedule(
            schedule_id="c",
            name="C",
            enabled=True,
            days_of_week=[4],  # Friday
            mode=MODE_DURATION,
            start_time="14:20",
            duration_seconds=300,
        )
        now = datetime(year=2026, month=4, day=24, hour=14, minute=20, second=5)  # Friday
        self.assertTrue(is_due_now(schedule, now))


if __name__ == "__main__":
    unittest.main()

