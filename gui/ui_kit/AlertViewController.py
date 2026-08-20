from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import MultilineTextView, TextAlignment, TextAnchor
from gui.ui_kit.Button import Button
from typing import Optional, Callable

from gui.ui_kit.TitleViewController import TitleViewController
from gui.utils.TextOverflowUtils import add_newlines_to_oveflowing_text

import gui.core.Main as Main

class AlertViewController(ViewController):
    ALERT_MESSAGE_Y = 10
    BUTTON_Y_FROM_BOTTOM = 10

    def __init__(self, alert_message: str = "") -> None:
        super().__init__()

        self._options = []
        self.cancel_button = Button(
            x=0, y=0, width=100, height=40,
            text="Cancel",
            callback=self.pop_view_controller
        )
        self.view.add_subview(self.cancel_button)

        self._label = MultilineTextView(0, 0, text=alert_message, 
                                        anchor=TextAnchor.LEFT_ASCENDER, align=TextAlignment.CENTER)
        width, _ = self._label.get_text_size()
        msg = add_newlines_to_oveflowing_text(self._label.text, width)
        print(msg)
        self._label.text = msg
        
        self._label.selectable = False
        self.view.add_subview(self._label)

        self.pop_after_callback = True

    def on_appear(self):
        super().on_appear()
        
        if len(self._options) == 0:
            self.view.selection

    def _callback(self, callback: Callable[[None], None]):
        print("Executing callback...")
        callback()
        if self.pop_after_callback:
            print("Popping view controller after callback")
            self.pop_view_controller()

    def test_pop(self):
        print("Test pop called")
        self.pop_view_controller()
        
    def add_option(self, option_text: str, callback: Optional[Callable[[None], None]] = None) -> Button:
        """
        Add an option button to the alert.
        """
        if callback is None:
            updated_callback = self.test_pop#self.pop_view_controller
        else:
            if not isinstance(callback, Callable):
                raise ValueError("callback must be a callable function")

            updated_callback = lambda: self._callback(callback)
        
        option_button = Button(
            x=0, y=0, width=100, height=40,
            text=option_text, callback=updated_callback
        )
        self.view.add_subview(option_button)
        self._options.append(option_button)

    def get_options(self) -> list[Button]:
        """
        Get the list of option buttons added to the alert.
        """
        return self._options
    
    def remove_option(self, option_button: Button) -> None:
        """
        Remove an option button from the alert.
        """
        if option_button in self._options:
            self.view.remove_subview(option_button)
            self._options.remove(option_button)
        else:
            raise ValueError("Option button not found in alert options")

    def set_message(self, message: str) -> None:
        """
        Set the alert message.
        """
        self._label.text = message

    def get_message(self) -> str:
        """
        Get the current alert message.
        """
        return self._label.text

    def on_layout(self):
        width, height = self._label.get_text_size()
        print(f"Alert message size: {width}x{height}")
        self._label.x = (self.view.width - width) / 2
        self._label.y = max(self.ALERT_MESSAGE_Y - height / 2, 0)

        print(f"Alert message position: {self._label.x}, {self._label.y}")

        # Add a button to close the alert
        num_options = len(self._options)
        if num_options > 0:
            self.cancel_button.visible = False
            for i, button in enumerate(self._options):
                button_text_width, button_text_height = button.set_size_from_text()

                button.x = (i + 1/2) * (self.view.width / num_options) - (button_text_width / 2)
                button.y = self.view.height - self.BUTTON_Y_FROM_BOTTOM - (button_text_height / 2)
        else:
            self.cancel_button.set_size_from_text()
            self.cancel_button.x = (self.view.width - self.cancel_button.width) / 2
            self.cancel_button.y = self.view.height - self.BUTTON_Y_FROM_BOTTOM - (self.cancel_button.height / 2)
            self.cancel_button.visible = True


class AlertTestViewController(TitleViewController):
    def __init__(self) -> None:
        super().__init__("Alert Test")
        self.alert = AlertViewController("This is\nAlert Message.")
        self.alert.add_option("OK", callback=lambda: self.set_title("OK clicked"))
        self.alert.add_option("Cancel", callback=lambda: self.set_title("Cancel clicked"))

    def on_up_press(self) -> None:
        """
        Handle joystick up event.
        """
        print("Joystick up pressed")
        num_options = len(self.alert.get_options())
        # self.alert.add_option(f"Opt({num_options})", callback=lambda: self.set_title(f"New Option ({num_options}) clicked"))
        self.push_view_controller(self.alert)

if __name__ == "__main__":
    # Example usage
    Main.main(AlertTestViewController())
    
     