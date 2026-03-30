from gui.core.SH1106 import LCD_WIDTH  as _LCD_WIDTH
from gui.core.SH1106 import LCD_HEIGHT as _LCD_HEIGHT
from PIL import Image, ImageDraw, ImageFont

disp = None

SCREEN_WIDTH = _LCD_WIDTH
SCREEN_HEIGHT = _LCD_HEIGHT

SCREEN_TEXT_COLOR = "WHITE"

IMAGE_MODE: str = "1"  # Monochrome mode

DEF_IMAGE: Image = Image.new(IMAGE_MODE, (SCREEN_WIDTH, SCREEN_HEIGHT), SCREEN_TEXT_COLOR)
DEF_DRAW: ImageDraw = ImageDraw.Draw(DEF_IMAGE)
DEF_FONT: ImageFont = ImageFont.load_default()

# Specifies if the display has inverted colors (i.e. ON is 0 instead of 255 or 1, OFF is 225 or 1 instead of 0)
DISP_INV: bool = True
ON: int  = 0
OFF: int = 1

def init():
    global disp
    import gui.core.SH1106 as SH1106
    # If not created yet, create display object
    if disp is None:
        print("HI")
        # Create, Initialize and Clear display object.
        disp = SH1106.SH1106()
        disp.Init()
        disp.clear()

def create_image(
    width: int = SCREEN_WIDTH,
    height: int = SCREEN_HEIGHT
) -> Image:
    """
    Create a new image with the specified width, height, and mode.
    """
    width = int(width)
    height = int(height)
    return Image.new(IMAGE_MODE, (width, height), SCREEN_TEXT_COLOR)

def create_image_from_image(
    image: Image.Image,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    height: int = 0
) -> Image:
    """
    Create a new image from an existing image.
    """
    if width <= 0:
        width = image.width
    if height <= 0:
        height = image.height
    return image.crop((x, y, x + width, y + height))
