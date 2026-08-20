import logging
import sys
import time

import gui.core.Main as Main
from gui.core.logging_config import configure_logging
from gui.ui_kit.TitleViewController import TitleViewController
from ieos.app_preferences import load_preferences, save_preferences
from ieos.MainMenuViewController import MainMenuViewController
from ieos.recording_runtime_state import is_any_recording_active, is_manual_recording_active
from ieos.schedule_recording_bridge import launch_scheduled_recording
from ieos.scheduler_runtime import attach_scheduler, ensure_scheduler_started
from ieos.scheduler_service import SchedulerService
from ieos.SystemTime import SystemTimeViewController
from ieos.TutorialViewController import TutorialViewController
from ieos.version import APP_VERSION

STARTUP_DURATION = 3  # seconds


class StartupViewController(TitleViewController):
    def __init__(self) -> None:
        super().__init__(f"Insect Eavesdropper\nv{APP_VERSION}")
        self._setup_done = False

    def on_appear(self) -> None:
        super().on_appear()
        if self._setup_done:
            return
        self._setup_done = True
        time.sleep(STARTUP_DURATION)
        if load_preferences().show_tutorial_at_startup:
            self.push_view_controller(
                TutorialViewController(),
                return_callback=self._after_tutorial,
            )
        else:
            self._push_system_time()

    def _after_tutorial(self, hide_next_boot: bool | None) -> None:
        if hide_next_boot is True:
            prefs = load_preferences()
            prefs.show_tutorial_at_startup = False
            save_preferences(prefs)
        self._push_system_time()

    def _push_system_time(self) -> None:
        self.push_view_controller(
            SystemTimeViewController(),
            return_callback=lambda _: self.swap_view_controller(MainMenuViewController()),
        )


if __name__ == "__main__":
    # Default logging until Main.main() reapplies config from CLI (-v / -q).
    configure_logging()
    logging.getLogger(__name__).info(
        "Insect Eavesdropper OS v%s — invoking Main.main",
        APP_VERSION,
    )
    scheduler = SchedulerService(
        start_recording=launch_scheduled_recording,
        is_manual_recording_active=is_manual_recording_active,
        is_any_recording_active=is_any_recording_active,
    )
    attach_scheduler(scheduler)
    if load_preferences().scheduler_enabled_on_startup:
        ensure_scheduler_started()
    if "--testbench" in sys.argv:
        from ieos.testbench.startup import TestbenchStartupViewController

        Main.main(TestbenchStartupViewController())
    else:
        Main.main(StartupViewController())
