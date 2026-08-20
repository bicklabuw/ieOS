from __future__ import annotations

from gui.ui_kit.TableViewController import TableViewController
from ieos.ScheduleEditorViewController import ScheduleEditorViewController
from ieos.schedule_store import DAY_NAMES, MODE_DURATION, RecordingSchedule, ScheduleStore


def _compact_days(days: list[int]) -> str:
    return ",".join(DAY_NAMES[i] for i in days)


def _format_duration(seconds: int) -> str:
    mins = seconds // 60
    if mins < 60:
        return f"{mins}m"
    hours = mins // 60
    rem = mins % 60
    if rem == 0:
        return f"{hours}h"
    return f"{hours}h{rem:02d}m"


def _schedule_row_label(schedule: RecordingSchedule) -> str:
    prefix = "ON " if schedule.enabled else "OFF "
    if schedule.mode == MODE_DURATION:
        mode = f"{schedule.start_time} {_format_duration(schedule.duration_seconds or 0)}"
    else:
        mode = f"{schedule.start_time}-{schedule.end_time}"
    return f"{prefix}{schedule.name} {_compact_days(schedule.days_of_week)} {mode}"


class _ScheduleActionsViewController(TableViewController):
    def __init__(self, schedule: RecordingSchedule) -> None:
        self._schedule = schedule
        items = [
            "Edit",
            "Disable" if schedule.enabled else "Enable",
            "Delete",
            "Back",
        ]
        super().__init__(items, pop_on_confirm=False)
        self._store = ScheduleStore()

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == 0:
            self.push_view_controller(
                ScheduleEditorViewController(self._schedule),
                return_callback=lambda _: self.pop_view_controller(True),
            )
        elif index == 1:
            self._store.update_schedule_enabled(self._schedule.schedule_id, not self._schedule.enabled)
            self.pop_view_controller(True)
        elif index == 2:
            self._store.delete_schedule(self._schedule.schedule_id)
            self.pop_view_controller(True)
        else:
            self.pop_view_controller(False)


class ScheduledRecordingsViewController(TableViewController):
    def __init__(self) -> None:
        # First row: short hint that selected weekdays anchor START time (overnight OK).
        super().__init__(["+Add day=start"], pop_on_confirm=False)
        self._store = ScheduleStore()
        self._schedules: list[RecordingSchedule] = []
        self._reload_items()

    def on_appear(self) -> None:
        super().on_appear()
        self._reload_items()

    def _reload_items(self) -> None:
        self._schedules = self._store.list_schedules()
        rows = ["+Add day=start"]
        rows.extend(_schedule_row_label(s) for s in self._schedules)
        self.set_items(rows)

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == 0:
            self.push_view_controller(
                ScheduleEditorViewController(),
                return_callback=lambda _: self._reload_items(),
            )
            return
        selected = self._schedules[index - 1]
        self.push_view_controller(
            _ScheduleActionsViewController(selected),
            return_callback=lambda _: self._reload_items(),
        )

