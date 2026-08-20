# ieos/SettingsViewController.py
from gui.ui_kit.TableViewController import TableViewController
from ieos.app_preferences import load_preferences, save_preferences
from ieos.ScheduledRecordingsViewController import ScheduledRecordingsViewController
from ieos.scheduler_runtime import ensure_scheduler_started, stop_scheduler
from ieos.SystemTime import SystemTimeViewController
from ieos.TestbenchViewController import TestbenchMenuViewController
from ieos.UpdateFromUSBViewController import UpdateFromUSBViewController
from ieos.version import APP_VERSION


class SettingsViewController(TableViewController):
    _ROW_SCHEDULED = 0
    _ROW_USB = 1
    _ROW_TESTBENCH = 2
    _ROW_SCHED_BOOT = 3
    _ROW_SET_TIME = 4
    _ROW_STARTUP_TIPS = 5
    _ROW_VERSION = 6

    def __init__(self) -> None:
        super().__init__(self._menu_items(), pop_on_confirm=False)

    @staticmethod
    def _menu_items() -> list[str]:
        p = load_preferences()
        sched = "On" if p.scheduler_enabled_on_startup else "Off"
        tips = "On" if p.show_tutorial_at_startup else "Off"
        return [
            "Scheduled Recordings",
            "Update from USB",
            "Run testbench",
            f"Schedules at boot: {sched}",
            "Set date/time",
            f"Startup tips: {tips}",
            f"Version {APP_VERSION}",
        ]

    def _refresh_items(self) -> None:
        self.set_items(self._menu_items())

    def did_select_row_at(self, index: int, item: str) -> None:
        if index == self._ROW_SCHEDULED:
            self.push_view_controller(ScheduledRecordingsViewController())
        elif index == self._ROW_USB:
            self.push_view_controller(UpdateFromUSBViewController())
        elif index == self._ROW_TESTBENCH:
            self.push_view_controller(TestbenchMenuViewController())
        elif index == self._ROW_SCHED_BOOT:
            prefs = load_preferences()
            prefs.scheduler_enabled_on_startup = not prefs.scheduler_enabled_on_startup
            save_preferences(prefs)
            if prefs.scheduler_enabled_on_startup:
                ensure_scheduler_started()
            else:
                stop_scheduler()
            self._refresh_items()
        elif index == self._ROW_SET_TIME:
            self.push_view_controller(
                SystemTimeViewController(),
                return_callback=lambda _: self._refresh_items(),
            )
        elif index == self._ROW_STARTUP_TIPS:
            prefs = load_preferences()
            prefs.show_tutorial_at_startup = not prefs.show_tutorial_at_startup
            save_preferences(prefs)
            self._refresh_items()
