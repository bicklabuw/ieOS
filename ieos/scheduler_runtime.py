# ieos/scheduler_runtime.py
"""Holds the process-wide SchedulerService for settings and boot gating."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ieos.scheduler_service import SchedulerService

_scheduler: SchedulerService | None = None


def attach_scheduler(service: SchedulerService | None) -> None:
    global _scheduler
    _scheduler = service


def get_scheduler() -> SchedulerService | None:
    return _scheduler


def ensure_scheduler_started() -> None:
    s = _scheduler
    if s is not None:
        s.start()


def stop_scheduler() -> None:
    s = _scheduler
    if s is not None:
        s.stop()
