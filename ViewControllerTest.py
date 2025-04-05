from ViewController import ViewController, ChangeViewControllerType
from View import View
from Components import MultiLineTextComponent
import Main
import time

from typing import Tuple
import random

class ViewControllerTest(ViewController):
    def __init__(self, x_speed: int = 1, y_speed: int = 1, prefix: str = "", pop: bool = False):
        super().__init__()

        self.prefix = prefix
        self.pop = pop

        self.view = ViewTest(text="DVD")
        self.view.text = prefix + self.view.text
        self.present_view(self.view)
        
        self.x_speed = x_speed
        self.y_speed = y_speed
    
    def on_appear(self):
        self.run = True
        
        x_dir_reversed = False
        y_dir_reversed = False
            
        while self.run:
            text_width, text_height = self.view.get_text_size()
            
            # Max distance text can move before part of text hits side of screen
            movement_width = self.view.SCREEN_WIDTH - text_width
            movement_height = self.view.SCREEN_HEIGHT - text_height
            
            if not x_dir_reversed:
                new_x = self.view.x + self.x_speed
                
                if new_x >= movement_width:
                    self.view.x = movement_width - (new_x - movement_width)
                    x_dir_reversed = not x_dir_reversed
                else:
                    self.view.x = new_x
            else:
                new_x = self.view.x - self.x_speed
                
                if new_x <= 0:
                    self.view.x = -new_x
                    x_dir_reversed = not x_dir_reversed
                else:
                    self.view.x = new_x
                
            if not y_dir_reversed:
                new_y = self.view.y + self.y_speed
                
                if new_y >= movement_height:
                    self.view.y = movement_height - (new_y - movement_height)
                    y_dir_reversed = not y_dir_reversed
                else:
                    self.view.y = new_y
            else:
                new_y = self.view.y - self.y_speed
                
                if new_y <= 0:
                    self.view.y = -new_y
                    y_dir_reversed = not y_dir_reversed
                else:
                    self.view.y = new_y
            
            time.sleep(0.1)

    def on_disappear(self):
        self.run = False
    
    def on_key_3_press(self):
        self.view.text = self.prefix + "K3-P"

    def on_key_3_hold(self):
        self.view.text = self.prefix + "K3-H"

    def on_key_3_release(self, held: bool):
        if held:
            self.view.text = self.prefix + "K3-RH"
        else:
            self.view.text = self.prefix + "K3-R"
            
    def on_key_1_press(self):
        if self.pop:
            self.pop_view_controller()
        else:
            x_speed = random.randint(1,10)
            y_speed = random.randint(1,10)
            next_vc = ViewControllerTest(x_speed=x_speed, y_speed=y_speed,
                                         prefix=f"({x_speed},{y_speed}): ", pop=True)
            self.change_view_controller(next_vc, ChangeViewControllerType.PUSH)


class ViewTest(View):
    def __init__(self, x: int = 10, y: int = 10, text: str = "Hello World"):
        super().__init__()

        self._x = x
        self._y = y
        self._text = text

        self.run = False

        self.text_component = MultiLineTextComponent(x, y, text)
        self.add_component(self.text_component)

    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value):
        self._x = value
        self.text_component.x = value
    
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value):
        self._y = value
        self.text_component.y = value
    
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        self._text = value
        self.text_component.text = value
        
    def get_text_size(self) -> Tuple[int, int]:
        return self.text_component.get_text_size()


if __name__ == "__main__":
    Main.main(ViewControllerTest())