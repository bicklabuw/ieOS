from TitleViewController import TitleViewController
from DateTimeViewController import DateTimeInputViewController
from Button import Button
from enum import Enum
import Main
from datetime import datetime
from TimeUtils import set_system_time
from ViewController import ViewController
from Views import MultilineTextView, TextAnchor, TextAlignment


"""

ask user what they want to set
date, time, or both -- buttons with labels

push view controller

set time

"""

class InputState(Enum):
    BOTH = 0
    DATE = 1
    TIME = 2
    

class SystemTime(ViewController[datetime]):
    def __init__(self):
        super().__init__()
        self.title = MultilineTextView(
            0, 0, 
            text="What do you\nwant to set?",
            anchor=TextAnchor.LEFT_ASCENDER, 
            align=TextAlignment.CENTER
        )
        self.title.selectable = False
        self.view.add_subview(self.title)
        self.buttons: list[Button] = []
        self._create_buttons()

    def _create_buttons(self) -> None:
        for mode in InputState:
            button = Button(
                x=0,
                y=0,
                width=20,
                height=12,
                text=mode.name.title(),
                callback=lambda mode=mode: self._start_input(mode),
            )
            button.set_size_from_text()
            self.buttons.append(button)
            self.view.add_subview(button)
            

    def _start_input(self, mode: InputState) -> None:
        if mode == InputState.DATE:
            input_type = DateTimeInputViewController.DateTimeInputType.DATE
        elif mode == InputState.TIME:
            input_type = DateTimeInputViewController.DateTimeInputType.TIME
        else:
            input_type = DateTimeInputViewController.DateTimeInputType.BOTH

        self.push_view_controller(
            DateTimeInputViewController(input_type=input_type),
            return_callback=self.process_date
        )
        

    def process_date(self, date: datetime | None):
        if date is None:
            print("Date selection cancelled")
            self.title.text = "Date selection\ncancelled"
            return
        datetime_str = date.strftime("%Y-%m-%d %H:%M:%S")
        print(f"Setting system time to: {datetime_str}")
        set_system_time(datetime_str)
        self.title.text = f"System time set to:\n{datetime_str}"
        print(f"System time set:\n{datetime_str}")
    def on_layout(self):
        # center the title
        label_width, label_height = self.title.get_text_size()
        self.title.x = (self.view.width - label_width) / 2
        self.title.y = 3

        total_width = sum(button.width for button in self.buttons)
        spacing = 7
        total_width += spacing * (len(self.buttons) - 1)  # spacing between buttons
        
        x = (self.view.width - total_width) / 2
        y = label_height + 14
        
        for button in self.buttons:
            button.x = x
            button.y = y
            x += button.width + spacing


if __name__ == "__main__":
    my_view_controller = SystemTime()
    Main.main(my_view_controller)
