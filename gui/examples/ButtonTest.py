import random
import threading
from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Button import Button
from gui.core.Display import SCREEN_WIDTH, SCREEN_HEIGHT
from gui.ui_kit.Label import Label

import gui.core.Main as Main

def _rects_overlap(a: tuple[int,int,int,int], b: tuple[int,int,int,int]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)


class ResultViewController(ViewController[bool]):
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index
        self.randomize = (random.random() < 0.5)
        msg1 = f"Button {index} was pressed"
        label1 = Label(10, 10, msg1)
        print("Label BBOX:", label1.get_text_bbox())
        self.view.add_subview(label1)
        if self.randomize:
            label2 = Label(10, 30, "Randomizing buttons")
            self.view.add_subview(label2)

    def on_appear(self) -> None:
        super().on_appear()
        print("Appeared")
        threading.Timer(
            3,
            lambda: self.pop_view_controller(self.randomize)
        ).start()


class ButtonTestViewController(ViewController[None]):
    def __init__(self) -> None:
        super().__init__()
        self.buttons: list[Button] = []
        self._generate_buttons()

    def _generate_buttons(self) -> None:
        for b in self.buttons:
            self.view.remove_subview(b)
        self.buttons.clear()

        count = random.randint(3, 10)
        size = 10
        positions: list[tuple[int,int,int,int]] = []
        attempts = 0
        while len(positions) < count and attempts < count * 50:
            x = random.randint(0, SCREEN_WIDTH - size)
            y = random.randint(0, SCREEN_HEIGHT - size)
            rect = (x, y, x + size, y + size)
            if all(not _rects_overlap(rect, other) for other in positions):
                positions.append(rect)
            attempts += 1

        for idx, (x, y, _, _) in enumerate(positions):
            btn = Button(
                x, y, size, size,
                text=str(idx),
                callback=lambda idx=idx: self._on_button(idx)
            )
            self.buttons.append(btn)
            self.view.add_subview(btn)

    def _on_button(self, idx: int) -> None:
        print("Pushing button", idx)
        result_vc = ResultViewController(idx)
        self.push_view_controller(
            result_vc,
            return_callback=lambda rnd: self._on_result(rnd)
        )

    def _on_result(self, randomizing: bool) -> None:
        if randomizing:
            self._generate_buttons()


if __name__ == "__main__":
    Main.main(ButtonTestViewController())