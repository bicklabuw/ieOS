from ViewController import ViewController
from JoystickHintView import JoystickHintView
import random
from InputUtils import InputCode, InputPhase
import Main

class JoystickHintViewTestViewController(ViewController):
    def __init__(self):
        super().__init__()

        self.up_int = 1
        self.down_int = 2
        self.left_int = 3
        self.right_int = 4
        self.button_int = 5

        self.joy_hint_view = JoystickHintView(
            f"Up {self.up_int}",
            f"Down {self.down_int}",
            f"Left {self.left_int}",
            f"Right {self.right_int}",
            f"Button {self.button_int}"
        )
        #KeyHintView(f"Key {self.key1_int}", f"Key {self.key2_int}", f"Key {self.key3_int}", random.choice([True, False]), random.randint(1, 5), random.randint(0, 10), random.randint(0, 10))
        self.update_border_line()

        self.view.add_subview(self.joy_hint_view)

    def handle_override(self, code: InputCode, phase: InputPhase, held: bool):
        if code == InputCode.UP and phase == InputPhase.PRESS:
            self.up_int += 1
            self.joy_hint_view.up_hint = f"Up {self.up_int}"
            self.joy_hint_view.button_hint = f"BTN {self.button_int}" if self.up_int % 2 == 1 else ""
            return True
        elif code == InputCode.DOWN and phase == InputPhase.HOLD:
            self.down_int += 1
            self.joy_hint_view.left_enabled = self.down_int % 2 == 1
            self.joy_hint_view.down_hint = f"DWN {self.down_int}"
            return True
        elif code == InputCode.LEFT and phase == InputPhase.RELEASE:
            self.left_int += 1
            self.joy_hint_view.left_hint = f"LFT {self.left_int}"
            return True
        elif code == InputCode.RIGHT and phase == InputPhase.RELEASE and held:
            self.right_int += 1
            self.joy_hint_view.right_hint = f"RGT {self.right_int}"
            return True
        elif code == InputCode.BUTTON and phase == InputPhase.RELEASE and not held:
            self.button_int += 1
            self.joy_hint_view.button_hint = f"BTN {self.button_int}" if self.up_int % 2 == 1 else ""
            return True
        elif code == InputCode.KEY1 and phase == InputPhase.PRESS:
            self.update_border_line()
            print("Border line updated with new random attributes.")
            return True
        elif code == InputCode.KEY2 and phase == InputPhase.HOLD:
            self.update_arrows()
            print("Arrows updated with new random attributes.")
            return True
        return False
        

    def update_border_line(self):
        # Randomly generate line attributes
        self.joy_hint_view.border_line_enabled = not self.joy_hint_view.border_line_enabled
        if self.joy_hint_view.border_line_enabled:
            print("Border line is enabled. Updating attributes...")
            self.joy_hint_view.border_line_width = random.randint(1, 5)
            self.joy_hint_view.border_line_padding_x = random.randint(0, 10)
            self.joy_hint_view.border_line_padding_y = random.randint(0, 10)

            print("Border Line Enabled:", self.joy_hint_view.border_line_enabled)
            print("Border Line Width:", self.joy_hint_view.border_line_width)
            print("Border Line Padding X:", self.joy_hint_view.border_line_padding_x)
            print("Border Line Padding Y:", self.joy_hint_view.border_line_padding_y)
        else:
            print("Border line is disabled. No attributes to update.")

    def update_arrows(self):
        # Randomly generate arrow attributes
        self.joy_hint_view.arrow_size = random.randint(4, 10)
        self.joy_hint_view.arrow_outline = random.randint(0,1)
        self.joy_hint_view.arrow_fill = random.randint(0,1)
        self.joy_hint_view.arrow_padding = random.randint(0, 6)
        self.joy_hint_view.arrow_stroke_width = random.randint(1, 4)

        print("Arrows updated with new random attributes:")
        print("Arrow Size:", self.joy_hint_view.arrow_size)
        print("Arrow Outline:", self.joy_hint_view.arrow_outline)
        print("Arrow Fill:", self.joy_hint_view.arrow_fill)
        print("Arrow Padding:", self.joy_hint_view.arrow_padding)
        print("Arrow Stroke Width:", self.joy_hint_view.arrow_stroke_width)

# This test view controller can be used to test the JoystickHintView functionality
# in a larger application or during development.
if __name__ == "__main__":
    # This is just a placeholder to show how the JoystickHintViewTestViewController can be instantiated.
    # In a real application, this would be part of the main application logic.
    Main.main(JoystickHintViewTestViewController())