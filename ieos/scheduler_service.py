from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from ieos.schedule_store import (
    MODE_DURATION,
    MODE_WINDOW,
    RecordingSchedule,
    ScheduleStore,
    time_to_minutes,
)

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScheduledRecordingRequest:
    name: str
    duration_seconds: int
    schedule_id: str


def compute_duration_seconds(schedule: RecordingSchedule) -> int:
    if schedule.mode == MODE_DURATION:
        if schedule.duration_seconds is None:
            raise ValueError("duration mode requires duration_seconds")
        return schedule.duration_seconds
    if schedule.mode == MODE_WINDOW:
        if not schedule.end_time:
            raise ValueError("window mode requires end_time")
        start_min = time_to_minutes(schedule.start_time)
        end_min = time_to_minutes(schedule.end_time)
        if end_min <= start_min:
            end_min += 24 * 60
        return (end_min - start_min) * 60
    raise ValueError(f"unsupported mode: {schedule.mode}")


def build_trigger_key(now: datetime) -> str:
    return now.strftime("%Y-%m-%d %H:%M")


def is_due_now(schedule: RecordingSchedule, now: datetime) -> bool:
    if not schedule.enabled:
        return False
    if now.weekday() not in schedule.days_of_week:
        return False
    hhmm = now.strftime("%H:%M")
    return hhmm == schedule.start_time


class SchedulerService:
    def __init__(
        self,
        *,
        start_recording: Callable[[ScheduledRecordingRequest], bool],
        is_manual_recording_active: Callable[[], bool],
        is_any_recording_active: Callable[[], bool],
        store: ScheduleStore | None = None,
        now_fn: Callable[[], datetime] | None = None,
        sleep_seconds: float = 1.0,
    ) -> None:
        self._start_recording = start_recording
        self._is_manual_recording_active = is_manual_recording_active
        self._is_any_recording_active = is_any_recording_active
        self._store = store or ScheduleStore()
        self._now_fn = now_fn or datetime.now
        self._sleep_seconds = sleep_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_minute_key: str | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="scheduled-recording-service")
        self._thread.start()
        _log.info("Scheduled recording service started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            now = self._now_fn()
            minute_key = build_trigger_key(now)
            if minute_key != self._last_minute_key:
                self._last_minute_key = minute_key
                self._run_minute_tick(now, minute_key)
            time.sleep(self._sleep_seconds)

    def _run_minute_tick(self, now: datetime, trigger_key: str) -> None:
        for schedule in self._store.list_schedules():
            if not is_due_now(schedule, now):
                continue
            if schedule.last_trigger_key == trigger_key:
                continue

            if self._is_manual_recording_active():
                self._store.update_run_result(
                    schedule.schedule_id,
                    status="skipped_manual_active",
                    trigger_key=trigger_key,
                )
                continue

            if self._is_any_recording_active():
                self._store.update_run_result(
                    schedule.schedule_id,
                    status="skipped_recorder_busy",
                    trigger_key=trigger_key,
                )
                continue

            try:
                duration = compute_duration_seconds(schedule)
            except ValueError as exc:
                _log.warning("Invalid schedule %s: %s", schedule.schedule_id, exc)
                self._store.update_run_result(
                    schedule.schedule_id,
                    status="invalid_schedule",
                    trigger_key=trigger_key,
                )
                continue

            started = self._start_recording(
                ScheduledRecordingRequest(
                    name=schedule.name,
                    duration_seconds=duration,
                    schedule_id=schedule.schedule_id,
                )
            )
            self._store.update_run_result(
                schedule.schedule_id,
                status="started" if started else "launch_failed",
                trigger_key=trigger_key,
            )

