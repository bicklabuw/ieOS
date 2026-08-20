from gui.ui_core.ViewController import ViewController
from gui.ui_kit.InputArrowView import InputArrowView
import random
from gui.utils.InputUtils import InputCode, InputPhase
import gui.core.Main as Main

class InputArrowViewTestViewController(ViewController):
    INPUT_CODES = [
            InputCode.UP,
            InputCode.DOWN,
            InputCode.LEFT,
            InputCode.RIGHT,
            InputCode.BUTTON
        ]
    def __init__(self):
        super().__init__()

        self.arrows = {}

        for code in self.INPUT_CODES:
            self.arrows[code] = InputArrowView(
                x=0, y=0, size=random.randint(20, 50),
                code=code,
                outline=random.randint(0, 1),
                fill=random.randint(0, 1),
                stroke_width=random.randint(1, 4)
            )
            self.view.add_subview(self.arrows[code])

    def handle_override(self, code: InputCode, phase: InputPhase, held: bool):
        if code == InputCode.KEY1 and phase == InputPhase.PRESS:
            self.update_arrows()
            print("Border line updated with new random attributes.")
            return True
        return False
        

    def update_arrows(self):
        rand_x = random.randint(0, 60)
        rand_y = random.randint(0, 20)

        for i, code in enumerate(self.INPUT_CODES):
            arrow = self.arrows[code]
            arrow.x = rand_x + 22 * (i // 2)
            arrow.y = rand_y + 22 * (i % 2)
            arrow.size = random.randint(4, 20)
            arrow.outline = random.randint(0, 1)
            arrow.fill = random.randint(0, 1)
            arrow.stroke_width = random.randint(1, 4)

            print(f"Updated {code.name} arrow: "
                  f"x={arrow.x}, y={arrow.y}, size={arrow.size}, "
                  f"outline={arrow.outline}, fill={arrow.fill}, stroke_width={arrow.stroke_width}")

# This test view controller can be used to test the InputArrowView functionality
# in a larger application or during development.
if __name__ == "__main__":
    # This is just a placeholder to show how the InputArrowViewTestViewController can be instantiated.
    # In a real application, this would be part of the main application logic.
    Main.main(InputArrowViewTestViewController())