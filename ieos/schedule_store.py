from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from gui.utils.durable_io import write_json_atomic

_log = logging.getLogger(__name__)

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "ieos")
_STORE_PATH = os.path.join(_CONFIG_DIR, "recording_schedules.json")

MODE_DURATION = "duration"
MODE_WINDOW = "window"
VALID_MODES = {MODE_DURATION, MODE_WINDOW}

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass(frozen=True)
class RecordingSchedule:
    schedule_id: str
    name: str
    enabled: bool
    days_of_week: list[int]
    mode: str
    start_time: str
    duration_seconds: int | None = None
    end_time: str | None = None
    last_run_status: str | None = None
    last_run_at: str | None = None
    last_trigger_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "name": self.name,
            "enabled": self.enabled,
            "days_of_week": list(self.days_of_week),
            "mode": self.mode,
            "start_time": self.start_time,
            "duration_seconds": self.duration_seconds,
            "end_time": self.end_time,
            "last_run_status": self.last_run_status,
            "last_run_at": self.last_run_at,
            "last_trigger_key": self.last_trigger_key,
        }

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> RecordingSchedule:
        schedule_id = str(raw.get("schedule_id", "")).strip() or str(uuid.uuid4())
        name = str(raw.get("name", "")).strip() or "Scheduled Recording"
        enabled = bool(raw.get("enabled", True))
        days = sorted({int(x) for x in raw.get("days_of_week", []) if 0 <= int(x) <= 6})
        mode = str(raw.get("mode", MODE_DURATION))
        start_time = str(raw.get("start_time", "00:00"))
        duration_seconds = raw.get("duration_seconds")
        end_time = raw.get("end_time")
        last_run_status = raw.get("last_run_status")
        last_run_at = raw.get("last_run_at")
        last_trigger_key = raw.get("last_trigger_key")
        if duration_seconds is not None:
            duration_seconds = int(duration_seconds)
        if end_time is not None:
            end_time = str(end_time)
        validate_schedule_fields(
            name=name,
            days_of_week=days,
            mode=mode,
            start_time=start_time,
            duration_seconds=duration_seconds,
            end_time=end_time,
        )
        return RecordingSchedule(
            schedule_id=schedule_id,
            name=name,
            enabled=enabled,
            days_of_week=days,
            mode=mode,
            start_time=start_time,
            duration_seconds=duration_seconds,
            end_time=end_time,
            last_run_status=last_run_status,
            last_run_at=last_run_at,
            last_trigger_key=last_trigger_key,
        )


def _parse_hhmm(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("time must be HH:MM")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("time must be HH:MM in 24h format")
    return hour, minute


def time_to_minutes(value: str) -> int:
    hour, minute = _parse_hhmm(value)
    return hour * 60 + minute


def minutes_to_hhmm(minutes: int) -> str:
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def validate_schedule_fields(
    *,
    name: str,
    days_of_week: list[int],
    mode: str,
    start_time: str,
    duration_seconds: int | None,
    end_time: str | None,
) -> None:
    if not name.strip():
        raise ValueError("name is required")
    if not days_of_week:
        raise ValueError("at least one day is required")
    if any(day < 0 or day > 6 for day in days_of_week):
        raise ValueError("days_of_week must be within 0..6")
    if mode not in VALID_MODES:
        raise ValueError("invalid schedule mode")
    _parse_hhmm(start_time)
    if mode == MODE_DURATION:
        if duration_seconds is None or duration_seconds <= 0:
            raise ValueError("duration_seconds must be > 0")
        if end_time is not None:
            raise ValueError("end_time must be empty for duration mode")
    if mode == MODE_WINDOW:
        if not end_time:
            raise ValueError("end_time is required for window mode")
        _parse_hhmm(end_time)
        start_min = time_to_minutes(start_time)
        end_min = time_to_minutes(end_time)
        if start_min == end_min:
            raise ValueError("start and end times cannot match in window mode")


class ScheduleStore:
    def __init__(self, path: str | None = None) -> None:
        self._path = path or _STORE_PATH

    def _load_raw(self) -> list[dict[str, Any]]:
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return []
        schedules = data.get("schedules")
        if not isinstance(schedules, list):
            return []
        return [x for x in schedules if isinstance(x, dict)]

    def _write_raw(self, schedules: list[dict[str, Any]]) -> None:
        payload = {"schedules": schedules}
        write_json_atomic(self._path, payload)

    def list_schedules(self) -> list[RecordingSchedule]:
        out: list[RecordingSchedule] = []
        for raw in self._load_raw():
            try:
                out.append(RecordingSchedule.from_dict(raw))
            except (ValueError, TypeError) as exc:
                _log.warning("Skipping invalid schedule entry: %s", exc)
        return out

    def save_schedule(
        self,
        *,
        name: str,
        days_of_week: list[int],
        mode: str,
        start_time: str,
        enabled: bool = True,
        duration_seconds: int | None = None,
        end_time: str | None = None,
        schedule_id: str | None = None,
    ) -> RecordingSchedule:
        validate_schedule_fields(
            name=name,
            days_of_week=days_of_week,
            mode=mode,
            start_time=start_time,
            duration_seconds=duration_seconds,
            end_time=end_time,
        )
        now_str = datetime.now().isoformat(timespec="seconds")
        new_schedule = RecordingSchedule(
            schedule_id=schedule_id or str(uuid.uuid4()),
            name=name.strip(),
            enabled=enabled,
            days_of_week=sorted(set(days_of_week)),
            mode=mode,
            start_time=start_time,
            duration_seconds=duration_seconds,
            end_time=end_time,
            last_run_status=None,
            last_run_at=now_str,
            last_trigger_key=None,
        )

        schedules = self.list_schedules()
        updated = False
        for idx, existing in enumerate(schedules):
            if existing.schedule_id == new_schedule.schedule_id:
                new_schedule = RecordingSchedule(
                    schedule_id=existing.schedule_id,
                    name=new_schedule.name,
                    enabled=new_schedule.enabled,
                    days_of_week=new_schedule.days_of_week,
                    mode=new_schedule.mode,
                    start_time=new_schedule.start_time,
                    duration_seconds=new_schedule.duration_seconds,
                    end_time=new_schedule.end_time,
                    last_run_status=existing.last_run_status,
                    last_run_at=existing.last_run_at,
                    last_trigger_key=existing.last_trigger_key,
                )
                schedules[idx] = new_schedule
                updated = True
                break
        if not updated:
            schedules.append(new_schedule)
        self._write_raw([s.to_dict() for s in schedules])
        return new_schedule

    def delete_schedule(self, schedule_id: str) -> None:
        schedules = [s for s in self.list_schedules() if s.schedule_id != schedule_id]
        self._write_raw([s.to_dict() for s in schedules])

    def update_schedule_enabled(self, schedule_id: str, enabled: bool) -> None:
        schedules = self.list_schedules()
        for idx, schedule in enumerate(schedules):
            if schedule.schedule_id == schedule_id:
                schedules[idx] = RecordingSchedule(
                    schedule_id=schedule.schedule_id,
                    name=schedule.name,
                    enabled=enabled,
                    days_of_week=schedule.days_of_week,
                    mode=schedule.mode,
                    start_time=schedule.start_time,
                    duration_seconds=schedule.duration_seconds,
                    end_time=schedule.end_time,
                    last_run_status=schedule.last_run_status,
                    last_run_at=schedule.last_run_at,
                    last_trigger_key=schedule.last_trigger_key,
                )
                break
        self._write_raw([s.to_dict() for s in schedules])

    def update_run_result(self, schedule_id: str, *, status: str, trigger_key: str | None) -> None:
        schedules = self.list_schedules()
        now_str = datetime.now().isoformat(timespec="seconds")
        for idx, schedule in enumerate(schedules):
            if schedule.schedule_id == schedule_id:
                schedules[idx] = RecordingSchedule(
                    schedule_id=schedule.schedule_id,
                    name=schedule.name,
                    enabled=schedule.enabled,
                    days_of_week=schedule.days_of_week,
                    mode=schedule.mode,
                    start_time=schedule.start_time,
                    duration_seconds=schedule.duration_seconds,
                    end_time=schedule.end_time,
                    last_run_status=status,
                    last_run_at=now_str,
                    last_trigger_key=trigger_key,
                )
                break
        self._write_raw([s.to_dict() for s in schedules])

