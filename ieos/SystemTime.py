import sys
import threading
import time
from datetime import datetime

import gui.core.Main as Main
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.DateTimeViewController import DateTimeInputViewController
from gui.ui_kit.Views import MultilineTextView, TextAnchor
from gui.utils.PlatformUtils import is_raspberry_pi
from gui.utils.time.TimeUtils import set_system_time, wait_for_ntp_sync_linux


TIME_SYNC_STATUS_TEXT = "Syncing time..."
ENABLE_STARTUP_TIME_SYNC = False


class SystemTimeViewController(ViewController[datetime]):
    def __init__(self):
        super().__init__()
        self._started = False
        self._abort_picker = False
        self.title = MultilineTextView(
            0,
            0,
            text=TIME_SYNC_STATUS_TEXT,
            anchor=TextAnchor.LEFT_TOP,
        )
        self.title.selectable = False
        self.view.add_subview(self.title)

    def on_appear(self) -> None:
        super().on_appear()
        if not self._started:
            self._started = True
            threading.Thread(target=self._open_picker_after_ntp, daemon=True).start()

    def _open_picker_after_ntp(self) -> None:
        # Without a battery RTC the kernel restores fake-hwclock (last shutdown), so
        # datetime.now() is wrong by the whole power-off interval unless NTP fixes it.
        if (
            ENABLE_STARTUP_TIME_SYNC
            and not self._abort_picker
            and sys.platform == "linux"
            and is_raspberry_pi()
        ):
            wait_for_ntp_sync_linux()
        if self._abort_picker:
            return
        self.push_view_controller(
            DateTimeInputViewController(input_type=DateTimeInputViewController.DateTimeInputType.BOTH),
            return_callback=self.process_date,
        )

    def process_date(self, date: datetime | None):
        if date is None:
            self.pop_view_controller(None)
            return
        datetime_str = date.strftime("%Y-%m-%d %H:%M:%S")
        # Update UI first so the screen never appears blank while setting system time.
        self.title.text = f"Setting time...\n{datetime_str}"
        ok, message = set_system_time(datetime_str)
        if ok:
            self.title.text = f"Time set:\n{datetime_str}"
        else:
            self.title.text = f"Time not set:\n{message}"
        threading.Thread(target=self._pop_after_delay, daemon=True).start()

    def _pop_after_delay(self) -> None:
        time.sleep(2)
        self.pop_view_controller(None)

    def on_key2_press(self) -> bool:
        self._abort_picker = True
        self.pop_view_controller(None)
        return True

    def on_layout(self):
        label_width, label_height = self.title.get_text_size()
        self.title.x = (self.view.width - label_width) / 2
        self.title.y = (self.view.height - label_height) / 2


if __name__ == "__main__":
    Main.main(SystemTimeViewController())
