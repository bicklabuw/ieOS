from abc import ABC, abstractmethod
from typing import Callable
from PIL import ImageFont
import Display

class View(ABC):
    DEF_FONT: ImageFont = ImageFont.load_default()

    def __init__(self):
        # Init the display
        Display.init()

        # Set General Default View Constants
        self.CHAR_LINE_SPACE = 1 # Added space to each line (built in space)
        self.CHAR_WIDTH: int = 6 # No Space Between some chars - ONLY WORKS FOR DEFAULT FONT
        self.CHAR_HEIGHT: int = 9 # ONLY WORKS FOR DEFAULT FONT
        self.LINE_HEIGHT: int = self.CHAR_HEIGHT + self.CHAR_LINE_SPACE
        self.LINE_SPACING: int = 1 # Space between lines
        self.TEXT_ALIGN: str = "center"
        
        self.TEXT_COLOR: str = "WHITE"

        # Get the Screen Width and Height
        self.SCREEN_WIDTH: int = Display.disp.width
        self.SCREEN_HEIGHT: int = Display.disp.height

        # Set Callbacks to None
        self.on_key_1_press: Callable[[], None] = None
        self.on_key_1_hold: Callable[[], None] = None
        self.on_key_1_release: Callable[[bool], None] = None
        
        self.on_key_2_press: Callable[[], None] = None
        self.on_key_2_hold: Callable[[], None] = None
        self.on_key_2_release: Callable[[bool], None] = None
        
        self.on_key_3_press: Callable[[], None] = None
        self.on_key_3_hold: Callable[[], None] = None
        self.on_key_3_release: Callable[[bool], None] = None
        
        self.on_joy_up_press: Callable[[], None] = None
        self.on_joy_up_hold: Callable[[], None] = None
        self.on_joy_up_release: Callable[[bool], None] = None
        
        self.on_joy_down_press: Callable[[], None] = None
        self.on_joy_down_hold: Callable[[], None] = None
        self.on_joy_down_release: Callable[[bool], None] = None
        
        self.on_joy_left_press: Callable[[], None] = None
        self.on_joy_left_hold: Callable[[], None] = None
        self.on_joy_left_release: Callable[[bool], None] = None
        
        self.on_joy_right_press: Callable[[], None] = None
        self.on_joy_right_hold: Callable[[], None] = None
        self.on_joy_right_release: Callable[[bool], None] = None
        
        self.on_joy_button_press: Callable[[], None] = None
        self.on_joy_button_hold: Callable[[], None] = None
        self.on_joy_button_release: Callable[[bool], None] = None
        
        self.on_appear: Callable[[], None] = None
        self.on_disappear: Callable[[], None] = None
    
    @abstractmethod
    def draw():
        pass
    
    