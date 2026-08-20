from __future__ import annotations

import logging

from gui.core.OSGlobals import get_current_view_controller
from ieos.recording_runtime_state import is_any_recording_active
from ieos.RecordViewController import RecordViewController
from ieos.scheduler_service import ScheduledRecordingRequest

_log = logging.getLogger(__name__)


def launch_scheduled_recording(request: ScheduledRecordingRequest) -> bool:
    if is_any_recording_active():
        _log.info("Skip scheduled launch: recorder already active")
        return False
    current_vc = get_current_view_controller()
    if current_vc is None:
        _log.warning("Cannot launch scheduled recording: no active view controller")
        return False
    current_vc.push_view_controller(
        RecordViewController(
            request.name,
            request.duration_seconds,
            recording_source="scheduled",
            schedule_id=request.schedule_id,
        )
    )
    return True

