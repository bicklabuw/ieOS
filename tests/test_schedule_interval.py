# tests/test_schedule_interval.py
from __future__ import annotations

import unittest

from ieos.schedule_interval import (
    MINUTES_PER_WEEK,
    new_schedule_overlaps_any,
    recording_span_minutes,
    schedules_overlap_week,
    week_minute_mask,
)
from ieos.schedule_store import MODE_DURATION, MODE_WINDOW, RecordingSchedule


def _sched(
    sid: str,
    *,
    days: list[int],
    mode: str,
    start: str,
    dur: int | None = None,
    end: str | None = None,
    enabled: bool = True,
) -> RecordingSchedule:
    return RecordingSchedule(
        schedule_id=sid,
        name="n",
        enabled=enabled,
        days_of_week=days,
        mode=mode,
        start_time=start,
        duration_seconds=dur,
        end_time=end,
    )


class ScheduleIntervalTests(unittest.TestCase):
    def test_window_22_to_06_span_minutes(self) -> None:
        s = _sched("a", days=[0], mode=MODE_WINDOW, start="22:00", end="06:00")
        self.assertEqual(480, recording_span_minutes(s))

    def test_duration_cross_midnight_span(self) -> None:
        s = _sched("b", days=[0], mode=MODE_DURATION, start="23:00", dur=3 * 3600)
        self.assertEqual(180, recording_span_minutes(s))

    def test_week_mask_wraps_mod_week(self) -> None:
        s = _sched("c", days=[6], mode=MODE_DURATION, start="23:30", dur=120)
        m = week_minute_mask(s)
        start_ix = 6 * 1440 + 23 * 60 + 30
        self.assertIn(start_ix, m)
        self.assertIn((start_ix + 1) % MINUTES_PER_WEEK, m)

    def test_overlap_same_start(self) -> None:
        a = _sched("a", days=[0], mode=MODE_DURATION, start="08:00", dur=3600)
        b = _sched("b", days=[0], mode=MODE_DURATION, start="08:30", dur=3600)
        self.assertTrue(schedules_overlap_week(a, b))

    def test_no_overlap_disjoint(self) -> None:
        a = _sched("a", days=[0], mode=MODE_DURATION, start="08:00", dur=1800)
        b = _sched("b", days=[0], mode=MODE_DURATION, start="10:00", dur=1800)
        self.assertFalse(schedules_overlap_week(a, b))

    def test_new_schedule_overlaps_any_respects_same_id(self) -> None:
        a = _sched("same", days=[1], mode=MODE_DURATION, start="12:00", dur=3600)
        self.assertFalse(new_schedule_overlaps_any(a, [a]))

    def test_disabled_skipped_in_overlap_pair(self) -> None:
        a = _sched("a", days=[2], mode=MODE_DURATION, start="15:00", dur=3600, enabled=True)
        b = _sched("b", days=[2], mode=MODE_DURATION, start="15:30", dur=3600, enabled=False)
        self.assertFalse(schedules_overlap_week(a, b))


if __name__ == "__main__":
    unittest.main()
