from gui.ui_core.ViewController import ViewController
from gui.ui_core.View import View
import random
import gui.core.Display as Display
from typing import Optional, Tuple
import gui.core.Main as Main
from PIL import ImageDraw
from gui.ui_kit.Views import TextView, LineView, CircleView, RectangleView, TextAnchor
import math
import time
from datetime import datetime

"""
Example view controller 
"""

class ExampleController(ViewController):
    def __init__(self):
        super().__init__()
        self.gui = TextView(0,0, text="Hello World!", anchor=TextAnchor.LEFT_TOP)
        self.view.add_subview(self.gui)

    # def on_appear(self):
    #     super().on_appear()
    #     self.run = True          
    #     while self.run:
    #         self.gui.x += 1
    #         if self.gui.x > self.view.width:
    #             self.gui.x = -self.gui.width
    #         time.sleep(0.1)

    # def on_disappear(self):
    #     self.run = False
    #     return super().on_disappear()

    def on_key2_press(self):
        cur = datetime.now()
        self.pop_view_controller(cur)
        return True


if __name__ == "__main__":
    my_view_controller = ExampleController()
    Main.main(my_view_controller)
