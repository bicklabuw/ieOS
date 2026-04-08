import threading
import time

from gui.ui_kit.DateTimeViewController import DateTimeInputViewController
import gui.core.Main as Main
from datetime import datetime
from gui.utils.time.TimeUtils import set_system_time
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import MultilineTextView, TextAnchor


class SystemTimeViewController(ViewController[datetime]):
    def __init__(self):
        super().__init__()
        self._started = False
        self.title = MultilineTextView(0, 0, text="", anchor=TextAnchor.LEFT_TOP)
        self.title.selectable = False
        self.view.add_subview(self.title)

    def on_appear(self) -> None:
        super().on_appear()
        if not self._started:
            self._started = True
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
        self.pop_view_controller(None)
        return True

    def on_layout(self):
        label_width, label_height = self.title.get_text_size()
        self.title.x = (self.view.width - label_width) / 2
        self.title.y = (self.view.height - label_height) / 2


if __name__ == "__main__":
    Main.main(SystemTimeViewController())
