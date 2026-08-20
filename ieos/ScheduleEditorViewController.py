from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from gui.ui_core.ViewController import ViewController
from gui.ui_kit.DateTimeViewController import DateTimeInputViewController
from gui.ui_kit.KeyboardViewController import KeyboardViewController
from gui.ui_kit.TableViewController import TableViewController
from ieos.MicTestViewController import MicTestViewController
from ieos.RecordSetupViewController import RecordSetupViewController
from ieos.schedule_interval import new_schedule_overlaps_any
from ieos.schedule_store import DAY_NAMES, MODE_DURATION, MODE_WINDOW, RecordingSchedule, ScheduleStore


class _DaySemanticsHintViewController(TableViewController):
    """One-line semantics before picking weekdays (anchor = start time)."""

    def __init__(self) -> None:
        super().__init__(["Day = START time", "Continue"], pop_on_confirm=False)

    def on_appear(self) -> None:
        super().on_appear()
        self.select(self._cells[1])

    def did_select_row_at(self, index: int, item: str) -> None:
        self.pop_view_controller(True)


class _OverlapConfirmViewController(TableViewController):
    def __init__(self) -> None:
        super().__init__(["Save anyway", "Cancel"], pop_on_confirm=False)

    def did_select_row_at(self, index: int, item: str) -> None:
        self.pop_view_controller(index == 0)


class _ModeSelectViewController(TableViewController):
    _ITEMS = ["Start + Duration", "Start + End Window"]

    def __init__(self, initial_mode: str) -> None:
        super().__init__(self._ITEMS, pop_on_confirm=False)
        self._initial_mode = initial_mode

    def on_appear(self) -> None:
        super().on_appear()
        if self._initial_mode == MODE_WINDOW:
            self.select(self._cells[1])

    def did_select_row_at(self, index: int, item: str) -> None:
        mode = MODE_DURATION if index == 0 else MODE_WINDOW
        self.pop_view_controller(mode)


class _DaysOfWeekSelectViewController(TableViewController):
    _SELECT_ALL_INDEX = 0
    _DESELECT_ALL_INDEX = 1
    _DAYS_START_INDEX = 2

    def __init__(self, initial_days: list[int]) -> None:
        self._selected_days = set(initial_days)
        super().__init__(self._build_items(self._selected_days), pop_on_confirm=False)

    @staticmethod
    def _build_items(selected_days: set[int]) -> list[str]:
        items = ["Select All", "Deselect All"]
        for idx, name in enumerate(DAY_NAMES):
            prefix = "[x]" if idx in selected_days else "[ ]"
            items.append(f"{prefix} {name}")
        items.append("Done")
        return items

    def _refresh(self) -> None:
        # Keep offset/selection stable so toggling a day does not jump to top.
        current = self.selection.current
        current_position = self._cells.index(current) if current in self._cells else 0
        current_index = self._offset + current_position

        self._items = self._build_items(self._selected_days)
        max_offset = max(0, len(self._items) - len(self._cells))
        if self._offset > max_offset:
            self._offset = max_offset
        self._reload_cells()
        self._update_arrows()

        if not self._cells:
            return
        target_index = max(0, min(current_index, len(self._items) - 1))
        target_pos = target_index - self._offset
        if 0 <= target_pos < len(self._cells) and self._cells[target_pos].selectable:
            self.select(self._cells[target_pos])
            return
        for cell in self._cells:
            if cell.selectable:
                self.select(cell)
                return

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == self._SELECT_ALL_INDEX:
            self._selected_days = set(range(7))
            self._refresh()
            return
        if index == self._DESELECT_ALL_INDEX:
            self._selected_days.clear()
            self._refresh()
            return
        done_index = self._DAYS_START_INDEX + len(DAY_NAMES)
        if index == done_index:
            if not self._selected_days:
                return
            self.pop_view_controller(sorted(self._selected_days))
            return
        day_idx = index - self._DAYS_START_INDEX
        if day_idx in self._selected_days:
            self._selected_days.remove(day_idx)
        else:
            self._selected_days.add(day_idx)
        self._refresh()


@dataclass
class _DraftSchedule:
    name: str = ""
    mode: str = MODE_DURATION
    start_time: str = "08:00"
    duration_seconds: int = 600
    end_time: str = "09:00"
    days_of_week: list[int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.days_of_week is None:
            self.days_of_week = [0, 1, 2, 3, 4]


class ScheduleEditorViewController(ViewController[bool]):
    def __init__(self, schedule: RecordingSchedule | None = None) -> None:
        super().__init__()
        self._store = ScheduleStore()
        self._schedule = schedule
        self._started = False
        self._draft = _DraftSchedule()
        if schedule is not None:
            self._draft = _DraftSchedule(
                name=schedule.name,
                mode=schedule.mode,
                start_time=schedule.start_time,
                duration_seconds=schedule.duration_seconds or 600,
                end_time=schedule.end_time or "09:00",
                days_of_week=schedule.days_of_week,
            )

    def on_appear(self) -> None:
        super().on_appear()
        if self._started:
            return
        self._started = True
        self.push_view_controller(
            KeyboardViewController(initial_text=self._draft.name, prompt_text="Name"),
            return_callback=self._on_name,
        )

    def _on_name(self, name: str | None) -> None:
        if not name:
            self.pop_view_controller(False)
            return
        self._draft.name = name.strip()
        self.push_view_controller(
            _ModeSelectViewController(self._draft.mode),
            return_callback=self._on_mode,
        )

    def _on_mode(self, mode: str | None) -> None:
        if mode is None:
            self.pop_view_controller(False)
            return
        self._draft.mode = mode
        self.push_view_controller(
            DateTimeInputViewController(input_type=DateTimeInputViewController.DateTimeInputType.TIME),
            return_callback=self._on_start_time,
        )

    def _on_start_time(self, when: datetime | None) -> None:
        if when is None:
            self.pop_view_controller(False)
            return
        self._draft.start_time = when.strftime("%H:%M")
        if self._draft.mode == MODE_DURATION:
            self.push_view_controller(
                RecordSetupViewController(),
                return_callback=self._on_duration,
            )
            return
        self.push_view_controller(
            DateTimeInputViewController(input_type=DateTimeInputViewController.DateTimeInputType.TIME),
            return_callback=self._on_end_time,
        )

    def _on_duration(self, duration_seconds: int | None) -> None:
        if not duration_seconds:
            self.pop_view_controller(False)
            return
        self._draft.duration_seconds = duration_seconds
        self._push_mic_test_then_day_flow()

    def _on_end_time(self, when: datetime | None) -> None:
        if when is None:
            self.pop_view_controller(False)
            return
        self._draft.end_time = when.strftime("%H:%M")
        self._push_mic_test_then_day_flow()

    def _push_mic_test_then_day_flow(self) -> None:
        self.push_view_controller(
            MicTestViewController(show_go=True),
            return_callback=self._on_mic_ok_before_days,
        )

    def _on_mic_ok_before_days(self, ok: bool | None) -> None:
        if not ok:
            self.pop_view_controller(False)
            return
        self.push_view_controller(
            _DaySemanticsHintViewController(),
            return_callback=lambda hint_ok: self.push_view_controller(
                _DaysOfWeekSelectViewController(self._draft.days_of_week),
                return_callback=self._on_days,
            )
            if hint_ok
            else self.pop_view_controller(False),
        )

    def _on_days(self, days: list[int] | None) -> None:
        if not days:
            self.pop_view_controller(False)
            return
        self._draft.days_of_week = days
        candidate = RecordingSchedule(
            schedule_id=self._schedule.schedule_id if self._schedule else str(uuid.uuid4()),
            name=self._draft.name.strip(),
            enabled=True if self._schedule is None else self._schedule.enabled,
            days_of_week=sorted(days),
            mode=self._draft.mode,
            start_time=self._draft.start_time,
            duration_seconds=self._draft.duration_seconds if self._draft.mode == MODE_DURATION else None,
            end_time=self._draft.end_time if self._draft.mode == MODE_WINDOW else None,
            last_run_status=None,
            last_run_at=None,
            last_trigger_key=None,
        )
        if new_schedule_overlaps_any(candidate, self._store.list_schedules()):
            self.push_view_controller(
                _OverlapConfirmViewController(),
                return_callback=self._on_overlap_choice,
            )
            return
        self._persist_schedule()

    def _on_overlap_choice(self, save_anyway: bool | None) -> None:
        if save_anyway:
            self._persist_schedule()
        else:
            self.pop_view_controller(False)

    def _persist_schedule(self) -> None:
        self._store.save_schedule(
            schedule_id=self._schedule.schedule_id if self._schedule else None,
            name=self._draft.name.strip(),
            enabled=True if self._schedule is None else self._schedule.enabled,
            days_of_week=self._draft.days_of_week,
            mode=self._draft.mode,
            start_time=self._draft.start_time,
            duration_seconds=self._draft.duration_seconds if self._draft.mode == MODE_DURATION else None,
            end_time=self._draft.end_time if self._draft.mode == MODE_WINDOW else None,
        )
        self.pop_view_controller(True)

