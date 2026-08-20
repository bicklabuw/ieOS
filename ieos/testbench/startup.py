# ieos/testbench/startup.py
import logging
import time

from gui.ui_core.ViewController import ViewController
from ieos.MainMenuViewController import MainMenuViewController

_log = logging.getLogger(__name__)

_TESTBENCH_BOOT_DELAY_SEC = 0.35


class TestbenchStartupViewController(ViewController[None]):
    """Minimal splash then swap to main menu (skips tutorial and system time)."""

    def __init__(self) -> None:
        super().__init__()
        self._started = False

    def on_appear(self) -> None:
        super().on_appear()
        if self._started:
            return
        self._started = True
        time.sleep(_TESTBENCH_BOOT_DELAY_SEC)
        from ieos.testbench import runner

        runner.start_when_main_menu_ready()
        self.swap_view_controller(MainMenuViewController())
