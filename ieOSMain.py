import time

import Main
from TitleViewController import TitleViewController
from MainMenuViewController import MainMenuViewController
from SystemTime import SystemTime

STARTUP_DURATION = 3  # seconds


class StartupViewController(TitleViewController):
    def __init__(self) -> None:
        super().__init__("Insect Eavesdropper")
        self._setup_done = False

    def on_appear(self) -> None:
        super().on_appear()
        if self._setup_done:
            return
        self._setup_done = True
        time.sleep(STARTUP_DURATION)
        self.push_view_controller(
            SystemTime(),
            return_callback=lambda _: self.swap_view_controller(MainMenuViewController()),
        )


if __name__ == "__main__":
    Main.main(StartupViewController())
