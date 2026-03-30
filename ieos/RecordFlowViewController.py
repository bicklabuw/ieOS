from __future__ import annotations

import gui.core.Main as Main
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.KeyboardViewController import KeyboardViewController
from ieos.RecordSetupViewController import RecordSetupViewController
from ieos.RecordViewController import RecordViewController
from ieos.MicTestViewController import MicTestViewController


class RecordFlowViewController(ViewController[None]):
    """
    Orchestrates the full recording flow:
      1. User enters a name (KeyboardViewController)
      2. User sets duration (RecordSetupViewController)
      3. Mic check (MicTestViewController)
      4. Recording starts (RecordViewController)
    """

    def __init__(self) -> None:
        super().__init__()
        self._flow_started = False
        self._name: str = ""
        self._duration: int = 0

    def on_appear(self) -> None:
        super().on_appear()
        # Only start the flow once (on_appear is called again when sub-VCs briefly pop back)
        if not self._flow_started:
            self._flow_started = True
            self.push_view_controller(
                KeyboardViewController(prompt_text="Name?"),
                return_callback=self._got_name,
            )

    def _got_name(self, name: str | None) -> None:
        if not name:
            self.pop_view_controller()
            return
        self._name = name
        self.push_view_controller(
            RecordSetupViewController(),
            return_callback=self._got_duration,
        )

    def _got_duration(self, duration: int | None) -> None:
        if duration is None:
            self.pop_view_controller()
            return
        self._duration = duration
        self.push_view_controller(
            MicTestViewController(show_go=True),
            return_callback=self._got_mic_ok,
        )

    def _got_mic_ok(self, ok: bool | None) -> None:
        if not ok:
            self.pop_view_controller()
            return
        self.push_view_controller(
            RecordViewController(self._name, self._duration),
            return_callback=lambda _: self.pop_view_controller(),
        )


if __name__ == "__main__":
    Main.main(RecordFlowViewController())
