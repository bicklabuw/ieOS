from ViewController import ViewController
from TableViewController import TableViewController
from Button import Button
from Views import MultilineTextView, TextAnchor, TextAlignment
import Display
import Main


ITEMS = [
    "5 seconds",
    "10 seconds",
    "30 seconds",
    "1 minute",
    "5 minutes",
    "10 minutes",
    "30 minutes",
]


class TableViewSample(ViewController):
    """
    Sample that shows how to push a TableViewController and handle
    its return value, analogous to how SystemTime.py uses
    DateTimeInputViewController.
    """

    def __init__(self):
        super().__init__()

        self.status = MultilineTextView(
            0, 0,
            text="No selection\nyet.",
            anchor=TextAnchor.LEFT_ASCENDER,
            align=TextAlignment.CENTER,
        )
        self.status.selectable = False
        self.view.add_subview(self.status)

        self.select_button = Button(
            x=0, y=0,
            width=20, height=12,
            text="Select",
            callback=self._open_table,
        )
        self.select_button.set_size_from_text()
        self.view.add_subview(self.select_button)

    def _open_table(self) -> None:
        self.push_view_controller(
            TableViewController(ITEMS),
            return_callback=self._handle_selection,
        )

    def _handle_selection(self, item: str | None) -> None:
        if item is None:
            self.status.text = "Cancelled."
            return
        self.status.text = f"Selected:\n{item}"

    def on_layout(self) -> None:
        label_w, label_h = self.status.get_text_size()
        self.status.x = (self.view.width - label_w) / 2
        self.status.y = 3

        self.select_button.x = (self.view.width - self.select_button.width) / 2
        self.select_button.y = label_h + 16


if __name__ == "__main__":
    Main.main(TableViewSample())
