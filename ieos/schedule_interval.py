# ieos/schedule_interval.py
"""Pure helpers for weekly recording schedule wall-clock spans and overlap checks."""

from __future__ import annotations

from ieos.schedule_store import MODE_DURATION, MODE_WINDOW, RecordingSchedule, time_to_minutes
from ieos.scheduler_service import compute_duration_seconds

MINUTES_PER_WEEK = 7 * 24 * 60


def recording_span_minutes(schedule: RecordingSchedule) -> int:
    """Wall-clock span in whole minutes (>= 1)."""
    sec = compute_duration_seconds(schedule)
    return max(1, (sec + 59) // 60)


def week_minute_mask(schedule: RecordingSchedule) -> set[int]:
    """
    Set of minute indices 0..MINUTES_PER_WEEK-1 covered by this schedule's
    recurring pattern (each anchor day fires at start_time for span_minutes).
    """
    span = recording_span_minutes(schedule)
    covered: set[int] = set()
    for d in schedule.days_of_week:
        start_min = d * 24 * 60 + time_to_minutes(schedule.start_time)
        for k in range(span):
            covered.add((start_min + k) % MINUTES_PER_WEEK)
    return covered


def schedules_overlap_week(a: RecordingSchedule, b: RecordingSchedule) -> bool:
    """True if some minute in the week is covered by both schedules."""
    if a.schedule_id == b.schedule_id:
        return False
    if not a.enabled or not b.enabled:
        return False
    ma = week_minute_mask(a)
    mb = week_minute_mask(b)
    return not ma.isdisjoint(mb)


def find_overlapping_schedule_ids(
    schedules: list[RecordingSchedule],
    *,
    exclude_id: str | None = None,
) -> list[tuple[str, str]]:
    """Return unordered pairs (id_a, id_b) that overlap on the weekly timeline."""
    enabled = [s for s in schedules if s.enabled and (exclude_id is None or s.schedule_id != exclude_id)]
    pairs: list[tuple[str, str]] = []
    for i, s1 in enumerate(enabled):
        for s2 in enabled[i + 1 :]:
            if schedules_overlap_week(s1, s2):
                pairs.append((s1.schedule_id, s2.schedule_id))
    return pairs


def new_schedule_overlaps_any(
    candidate: RecordingSchedule,
    existing: list[RecordingSchedule],
) -> bool:
    """Whether candidate overlaps any other enabled schedule (by weekly minute mask)."""
    for other in existing:
        if other.schedule_id == candidate.schedule_id:
            continue
        if not other.enabled:
            continue
        if schedules_overlap_week(candidate, other):
            return True
    return False
