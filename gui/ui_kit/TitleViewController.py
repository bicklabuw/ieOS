from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Views import MultilineTextView, TextAlignment, TextAnchor
from gui.utils.TextOverflowUtils import add_newlines_to_oveflowing_text
from typing import TypeVar, Generic

T = TypeVar('T')
class TitleViewController(ViewController[T]):
    def __init__(self, title: str) -> None:
        super().__init__()

        self._title_label = MultilineTextView(0, 0, text=title, 
                                        anchor=TextAnchor.LEFT_ASCENDER, align=TextAlignment.CENTER)
        width, _ = self._title_label.get_text_size()
        msg = add_newlines_to_oveflowing_text(self._title_label.text, width)
        print(msg)
        self._title_label.text = msg
        self._title_label.selectable = False  # Labels are not selectable by default
        self.view.add_subview(self._title_label)

    def on_layout(self):
        width, height = self._title_label.get_text_size()

        self._title_label.x = (self.view.width - width) / 2
        self._title_label.y = (self.view.height - height) / 2

    def set_title(self, title: str) -> None:
        """
        Set the title of the view controller.
        """
        self._title_label.text = title
        width, _ = self._title_label.get_text_size()
        msg = add_newlines_to_oveflowing_text(self._title_label.text, width)
        print(msg)
        self._title_label.text = msg

    def get_title(self) -> str:
        """
        Get the title of the view controller.
        """
        return self._title_label.text