import SH1106
from PIL import Image, ImageDraw, ImageFont

disp = None

SCREEN_WIDTH = SH1106.LCD_WIDTH
SCREEN_HEIGHT = SH1106.LCD_HEIGHT

SCREEN_TEXT_COLOR = "WHITE"

DEF_IMAGE: Image = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), SCREEN_TEXT_COLOR)
DEF_DRAW: ImageDraw = ImageDraw.Draw(DEF_IMAGE)
DEF_FONT: ImageFont = ImageFont.load_default()

def init():
    global disp
    # If not created yet, create display object
    if disp is None:
        print("HI")
        # Create, Initialize and Clear display object.
        disp = SH1106.SH1106()
        disp.Init()
        disp.clear()