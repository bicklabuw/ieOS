from ViewController import ViewController, ChangeViewControllerType
from View import View
from Views import MultilineTextView, RectangleView, TextAnchor
import Main
import time
from Display import ON, OFF

from typing import Tuple
import random

class ViewControllerTest(ViewController):
    def __init__(self, x_speed: int = 1, y_speed: int = 1, prefix: str = "", pop: bool = False):
        super().__init__()

        self.prefix = prefix
        self.pop = pop

        self.main_view = MultilineTextView(0, 0, text="I.E.", anchor=TextAnchor.LEFT_ASCENDER)

        # self.rect_view = RectangleView(1, 1, 125, 61, fill=OFF, outline=ON, stroke_width=1)
        # self.view.add_subview(self.rect_view)

        text_width, text_height = self.main_view.get_text_size()
        init_x = self.view.width - text_width #random.randint(0, self.view.width - text_width)
        init_y = self.view.height - text_height - 2#random.randint(0, self.view.height - text_height)
        self.main_view.x = init_x
        self.main_view.y = init_y

        # self.txt_rect_view = RectangleView(init_x, init_y, text_width, text_height, fill=OFF, outline=ON, stroke_width=1)
        # self.view.add_subview(self.txt_rect_view)

        self.view.add_subview(self.main_view)
        self.main_view.text = prefix + self.main_view.text
        
        self.x_speed = x_speed
        self.y_speed = y_speed
    
    def on_appear(self):
        self.run = True
        
        x_dir_reversed = False
        y_dir_reversed = False
            
        while self.run:
            text_width, text_height = self.main_view.get_text_size()
            
            # Max distance text can move before part of text hits side of screen
            movement_width = self.view.width - text_width
            movement_height = self.view.height - text_height
            
            if not x_dir_reversed:
                new_x = self.main_view.x + self.x_speed
                
                if new_x >= movement_width:
                    self.main_view.x = movement_width - (new_x - movement_width)
                    x_dir_reversed = not x_dir_reversed
                else:
                    self.main_view.x = new_x
            else:
                new_x = self.main_view.x - self.x_speed
                
                if new_x <= 0:
                    self.main_view.x = -new_x
                    x_dir_reversed = not x_dir_reversed
                else:
                    self.main_view.x = new_x
                
            if not y_dir_reversed:
                new_y = self.main_view.y + self.y_speed
                
                if new_y >= movement_height:
                    self.main_view.y = movement_height - (new_y - movement_height)
                    y_dir_reversed = not y_dir_reversed
                else:
                    self.main_view.y = new_y
            else:
                new_y = self.main_view.y - self.y_speed
                
                if new_y <= 0:
                    print("New Y: ", -new_y)
                    self.main_view.y = -new_y
                    y_dir_reversed = not y_dir_reversed
                else:
                    self.main_view.y = new_y
            
            time.sleep(0.1)

    def on_disappear(self):
        self.run = False
    
    def on_key3_press(self):
        self.main_view.text = self.prefix + "K3-P"

    def on_key3_hold(self):
        self.main_view.text = self.prefix + "K3-H"

    def on_key3_release(self, held: bool):
        if held:
            self.main_view.text = self.prefix + "K3-RH"
        else:
            self.main_view.text = self.prefix + "K3-R"
            
    def on_key1_press(self):
        if self.pop:
            self.pop_view_controller()
        else:
            x_speed = random.randint(1,10)
            y_speed = random.randint(1,10)
            next_vc = ViewControllerTest(x_speed=x_speed, y_speed=y_speed,
                                         prefix=f"({x_speed},{y_speed}): ", pop=True)
            self.push_view_controller(next_vc)


if __name__ == "__main__":
    Main.main(ViewControllerTest())