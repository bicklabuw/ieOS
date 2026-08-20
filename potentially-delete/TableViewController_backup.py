from View import View
from ViewController import ViewController
from Components import Component, RectangleComponent, TextComponent
from ABC import ABC
from PIL import ImageDraw

class TableViewController(ViewController):
    def __init__(self):
        super().__init__()

    def on_appear(self):
        pass



class TableView(View):
    def __init__(self, data:list[str]):
        super().__init__()

        self._data = []
        self.selected_index = 0

        for item in self._data:
            self.add_row(item)


    def add_row(self, item:str, index:int=None):
        if index is None:
            index = len(self._data)
        self._data.insert(index, item)

        new_component = self.create_component(item)


class TableViewRow(Component, ABC):
    def __init__(self, x: float, y: float, width: float, height: float, selected: bool = False, **kwargs):
        super().__init__(x, y, width,height,selected, **kwargs)

        self._rect_comp = RectangleComponent(x,y,width,height)

    def draw(self, draw: ImageDraw):
        if self.selected:
            self._rect_comp.fill = 0
        else:
            self._rect_comp.fill = 255

        self._rect_comp.draw(draw)

class TextTableViewRow(TableViewRow):
    def __init__(self, x: float, y: float, width: float, height: float, text: str = "", selected: bool = False):
        super().__init__(x, y, width, height, selected, text)
        self._text = text

        text_height = TextComponent.get_text_size_of(self._text, spacing=self.LINE_SPACING)[1]

        self._rect_comp = RectangleComponent(x,y,width,height)
        self._text_comp = TextComponent(x,y + (height - text_height)/2,text)

    def draw(self, draw: ImageDraw):
        if self.selected:
            self._rect_comp.fill = 0
        else:
            self._rect_comp.fill = 255

        self._rect_comp.draw(draw)
        self._text_comp.draw(draw)
