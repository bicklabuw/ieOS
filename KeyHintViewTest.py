from ViewController import ViewController
from KeyHintView import KeyHintView
import random
from InputUtils import InputCode, InputPhase
import Main

class KeyHintViewTestViewController(ViewController):
    def __init__(self):
        super().__init__()

        self.key1_int = 1
        self.key2_int = 2
        self.key3_int = 3

        self.key_hint_view = KeyHintView(
            f"Key {self.key1_int}", 
            f"Key {self.key2_int}", 
            f"Key {self.key3_int}", 
            None, 
            random.choice([True, False]), 
            random.randint(1, 5), 
            random.randint(0, 10), 
            random.randint(0, 10))
        self.update_border_line()

        self.view.add_subview(self.key_hint_view)

    def handle_override(self, code: InputCode, phase: InputPhase, held: bool):
        if code == InputCode.KEY1 and phase == InputPhase.PRESS:
            self.key1_int += 1
            self.key_hint_view.key1_hint = f"Key {self.key1_int}"
            self.key_hint_view.key3_enabled = self.key1_int % 2 == 1
            return True
        elif code == InputCode.KEY2 and phase == InputPhase.HOLD:
            self.key2_int += 1
            self.key_hint_view.key2_hint = f"Key {self.key2_int}"
            return True
        elif code == InputCode.KEY3 and phase == InputPhase.RELEASE and (held ^ self.key_hint_view.border_line_enabled):
            self.key3_int += 1
            self.key_hint_view.key3_hint = f"Key {self.key3_int}"
            return True
        elif code == InputCode.BUTTON and phase == InputPhase.PRESS:
            self.update_border_line()
            print("Border line updated with new random attributes.")
            return True
        return False
        

    def update_border_line(self):
        # Randomly generate line attributes
        self.key_hint_view.border_line_enabled = not self.key_hint_view.border_line_enabled
        if self.key_hint_view.border_line_enabled:
            print("Border line is enabled. Updating attributes...")
            self.key_hint_view.border_line_width = random.randint(1, 5)
            self.key_hint_view.border_line_padding_x = random.randint(0, 10)
            self.key_hint_view.border_line_padding_y = random.randint(0, 10)

            print("Border Line Enabled:", self.key_hint_view.border_line_enabled)
            print("Border Line Width:", self.key_hint_view.border_line_width)
            print("Border Line Padding X:", self.key_hint_view.border_line_padding_x)
            print("Border Line Padding Y:", self.key_hint_view.border_line_padding_y)
        else:
            print("Border line is disabled. No attributes to update.")

# This test view controller can be used to test the KeyHintView functionality
# in a larger application or during development.
if __name__ == "__main__":
    # This is just a placeholder to show how the KeyHintViewTestViewController can be instantiated.
    # In a real application, this would be part of the main application logic.
    Main.main(KeyHintViewTestViewController())