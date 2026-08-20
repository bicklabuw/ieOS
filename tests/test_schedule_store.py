from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory

from ieos.schedule_store import MODE_DURATION, MODE_WINDOW, ScheduleStore, validate_schedule_fields


class ScheduleStoreTests(unittest.TestCase):
    def test_validate_duration_mode_requires_positive_duration(self) -> None:
        with self.assertRaises(ValueError):
            validate_schedule_fields(
                name="Morning",
                days_of_week=[0, 1],
                mode=MODE_DURATION,
                start_time="08:00",
                duration_seconds=0,
                end_time=None,
            )

    def test_validate_window_mode_rejects_same_start_end(self) -> None:
        with self.assertRaises(ValueError):
            validate_schedule_fields(
                name="Evening",
                days_of_week=[2, 3],
                mode=MODE_WINDOW,
                start_time="20:00",
                duration_seconds=None,
                end_time="20:00",
            )

    def test_save_and_reload_schedule(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = ScheduleStore(path=f"{tmp_dir}/recording_schedules.json")
            schedule = store.save_schedule(
                name="Lunch",
                days_of_week=[0, 2, 4],
                mode=MODE_DURATION,
                start_time="12:30",
                duration_seconds=1800,
            )
            loaded = store.list_schedules()
            self.assertEqual(1, len(loaded))
            self.assertEqual(schedule.schedule_id, loaded[0].schedule_id)


if __name__ == "__main__":
    unittest.main()

