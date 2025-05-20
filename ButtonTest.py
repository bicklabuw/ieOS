import random
import threading
from Button import Button
from View import View
from ViewController import ViewController
from Display import SCREEN_WIDTH, SCREEN_HEIGHT
import Main


def _rects_overlap(a: tuple[int,int,int,int], b: tuple[int,int,int,int]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)


from PIL.ImageFont import ImageFont
from typing import Optional

class Label(View):
    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        font: Optional[ImageFont] = None
    ) -> None:
        # choose font and measure text size
        f = font or ImageFont.load_default()
        w, h = f.getsize(text)
        super().__init__(x, y, w, h)
        self._text = text
        self.font = f

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, new_text: str) -> None:
        self._text = new_text
        # adjust width/height when text changes
        w, h = self.font.getsize(new_text)
        self.width = w
        self.height = h

    def _render_self(self, draw) -> None:
        draw.text((self.abs_x, self.abs_y), self._text, fill=1)

class ResultViewController(ViewController[bool]):
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index
        # decide if we randomize on pop
        self.randomize = (random.random() < 0.5)
        # show messages
        msg1 = f"Button {index} was pressed"
        label1 = Label(10, 10, msg1)
        self.view.add_subview(label1)
        if self.randomize:
            label2 = Label(10, 30, "Randomizing buttons")
            self.view.add_subview(label2)

    def on_appear(self) -> None:
        # pop after 3 seconds, returning the randomize flag
        threading.Timer(3, lambda: self.pop_view_controller(self.randomize)).start()


class ButtonTestViewController(ViewController[None]):
    def __init__(self) -> None:
        super().__init__()
        self.buttons: list[Button] = []
        self._generate_buttons()

    def _generate_buttons(self) -> None:
        # clear existing buttons
        for b in self.buttons:
            self.view.remove_subview(b)
        self.buttons.clear()

        count = random.randint(3, 10)
        size = 40
        positions: list[tuple[int,int,int,int]] = []
        attempts = 0
        # generate non-overlapping rects
        while len(positions) < count and attempts < count * 50:
            x = random.randint(0, SCREEN_WIDTH - size)
            y = random.randint(0, SCREEN_HEIGHT - size)
            rect = (x, y, x + size, y + size)
            if all(not _rects_overlap(rect, other) for other in positions):
                positions.append(rect)
            attempts += 1

        # create buttons
        for idx, (x, y, _, _) in enumerate(positions):
            btn = Button(
                x, y, size, size,
                text=str(idx),
                callback=lambda idx=idx: self._on_button(idx)
            )
            self.buttons.append(btn)
            self.view.add_subview(btn)

    def _on_button(self, idx: int) -> None:
        # push result VC and handle return
        result_vc = ResultViewController(idx)
        self.push_view_controller(
            result_vc,
            return_callback=lambda rnd: self._on_result(rnd)
        )

    def _on_result(self, randomizing: bool) -> None:
        if randomizing:
            self._generate_buttons()


if __name__ == "__main__":
    # Create a ButtonTestViewController instance
    Main.main(ButtonTestViewController())

    
