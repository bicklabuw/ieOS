import logging
import time

import gui.core.Main as Main
from gui.core.logging_config import configure_logging
from gui.ui_kit.TitleViewController import TitleViewController
from ieos.MainMenuViewController import MainMenuViewController
from ieos.SystemTime import SystemTimeViewController
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
    Main.main(StartupViewController())
