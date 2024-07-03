from __future__ import annotations
from enum import Enum
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import SH1106
import textwrap

from View import View
import Display
import math

class JoystickInput(Enum):
    '''
    This class is an :class:`Enum` that represents where a Joystick input / direction (UP, DOWN, LEFT, RIGHT, BUTTON)
    '''
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    BUTTON = 4

class KeyInput(Enum):
    '''
    This class is an :class:`Enum` that represents where a Key input (Key1, Key2, Key3)
    '''
    KEY1 = 1
    KEY2 = 2
    KEY3 = 3

# class JoyHintPos(Enum):
#     '''
#     This class is an :class:`Enum` that represents where a Joystick hint should be placed. At the top (Top), between 
#     top and middle (MID_TOP), middle (MIDDLE), between middle and bottom (MID_BOTTOM), and bottom (BOTTOM).
#     '''
#     TOP = 0
#     MID_TOP = 1
#     MIDDLE = 2
#     MID_BOT = 3
#     BOTTOM = 4

# Select the desired order for the Joystick help text to appear from top to bottom
DEF_JOY_ORDER: list[JoystickInput] = [JoystickInput.UP, 
                              JoystickInput.LEFT, 
                              JoystickInput.BUTTON, 
                              JoystickInput.RIGHT,
                              JoystickInput.DOWN]

class ControlView(View):
    def __init__(self, uses_keys_inp: bool = True, uses_joy_inp: bool = True,
                 max_key_chars: int = 5, max_joy_chars: int = 4, view_text = "",
                 up_text: str = "", down_text = "", left_text = "", right_text = "", button_text = "",
                 key1_text = "", key2_text = "", key3_text = "",
                 cont_font: ImageFont = View.DEF_FONT, view_font: ImageFont = View.DEF_FONT,
                 sep_width: int = 3, sep_fill_width: int = 1, sep_fill_height: int = None,
                 JOY_ORDER: list[JoystickInput] = DEF_JOY_ORDER):
        """
        Initializes an ControlView object
        
        NOTE: Changing Font Is Currently Disabled - Need to Determine Char Width & Height for Each Font
        TODO: Allow change in font
        TODO: Add joystick button press control hint option
        
        :param uses_keys_inp: Indicates if the view uses key inputs, defaults to True
        :type uses_keys_inp: bool, optional
        :param uses_joy_inp: Indicates if the view uses joystick inputs, defaults to True
        :type uses_joy_inp: bool, optional
        
        :param max_key_chars: Max number of chars allowed for each key hint, defaults to 5
        :type max_key_chars: int, optional
        :param max_joy_chars: Max number of chars allowed for each joystick hint
            (excluding 1 char for arrows), defaults to 4
        :type max_joy_chars: int, optional
        
        :param view_text: The view's main text, defaults to ""
        :type view_text: str, optional
        
        :param up_text: Joystick Up Hint Text, defaults to ""
        :type up_text: str, optional
        :param down_text: Joystick Down Hint Text, defaults to ""
        :type down_text: str, optional
        :param left_text: Joystick Left Hint Text, defaults to ""
        :type left_text: str, optional
        :param right_text: Joystick Right Hint Text, defaults to ""
        :type right_text: str, optional
        :param button_text: Joystick Button Hint Text, defaults to ""
        :type button_text: str, optional
        
        :param key1_text: Key 1 Hint Text, defaults to ""
        :type key1_text: str, optional
        :param key2_text: Key 2 Hint Text, defaults to ""
        :type key2_text: str, optional
        :param key3_text: Key 3 Hint Text, defaults to ""
        :type key3_text: str, optional
        
        :param cont_font: DISABLED - Controls Help Text Font, defaults to ImageFont default
        :type cont_font: class: `PIL.ImageFont`, optional
        :param view_font: DISABLED - View Text Font, defaults to ImageFont default
        :type view_font: class: `PIL.ImageFont`, optional
        
        :param sep_width: Pixels between View and Control Help Text on each side, defaults to 3
        :type sep_width: int, optional
        :param sep_fill_width: Pixel width of the separator line, defaults to 1
        :type sep_fill_width: int, optional
        :param sep_fill_height: Pixel height of the separator line, defaults to View Height
        :type sep_fill_height: int, optional

        :param JOY_ORDER: The order the Joystick Inputs should be displayed as a list. 
        Any JoystickInputs not included in this list will get appended in the default order.
        Defaults to [UP, LEFT, BUTTON, RIGHT, DOWN]
        :type JOY_ORDER: list[:class:`JoystickInput`]
        """

        super().__init__()
        
        # Define Class Variables
        self.key_controls_en = uses_keys_inp
        self.joy_controls_en = uses_joy_inp
        
        self.MAX_KEY_CHARS = max_key_chars
        self.MAX_JOY_CHARS = max_joy_chars
        
        self.view_text = view_text
        
        self.up_text = up_text
        self.down_text = down_text
        self.left_text = left_text
        self.right_text = right_text
        self.button_text = button_text
        
        self.key1_text = key1_text
        self.key2_text = key2_text
        self.key3_text = key3_text
        
        self.cont_font = self.DEF_FONT#cont_font
        self.view_font = self.DEF_FONT#view_font
        
        self.SEP_WIDTH = sep_width
        self.SEP_FILL_WIDTH = sep_fill_width
        self.SEP_FILL_HEIGHT = sep_fill_height if sep_fill_height is not None else self.SCREEN_HEIGHT

        self.JOY_ORDER = JOY_ORDER

        for input in DEF_JOY_ORDER:
            if input not in self.JOY_ORDER:
                self.JOY_ORDER.append(input)
    
    def _get_text_height(self, text: str) -> int:
        '''
        Gets the height of the text in Pixels
        
        NOTE: Does not text wrap, no matter the length of the line
        
        :param text: The text to get the height of
        :type text: str
        
        :return: The height of the string in pixels
        :rtype: int
        '''
        return (text.count('\n') + 1) * self.LINE_HEIGHT
    
    def _get_text_width(self, text: str) -> int:
        '''
        Gets the width of the text in Pixels (width of the longest line)
        
        :param text: The text to get the width of
        :type text: str
        
        :return: The width of the string in pixels
        :rtype: int
        '''
        max_line_len = 0
        
        for line in text.split('\n'):
            if len(line) > max_line_len:
                max_line_len = len(line)
        
        return max_line_len * self.CHAR_WIDTH

    def __get_key_text_coords_and_text(self):
        '''
        Gets the coordinates, help texts, and max width for the Key Control Hint Texts

        :return: A tuple with first with a dict containing the Coordinate for each Key input that has help text. 
        Then a dict containing the text for each Key Input that has help text. Then an int with the max width 
        of all the help text. Overall: (dict[KeyInput: (x,y)], dict[KeyInput: help_text], max_width)
        :rtype: (dict[:class:`KeyInput`, (int, int)], dict[:class:`KeyInput`, str], int) 
        '''
        widths: dict[KeyInput, int] = {} # Widths with the key being the Key Input
        max_width: int = 0 # Max width of all text

        key_texts: dict[KeyInput, str] = {}
        key_coords: dict[KeyInput, (int, int)] = {}

        def log_text_info(text: str, input: KeyInput):
            '''
            Logs the text into key_texts and text_width into widths and gets the total_height and max_width

            :param text: The help text to log the info for
            :type text: str

            :param input: The Key Input the help text represents
            :type input: class: `KeyInput`
            '''
            nonlocal max_width
            nonlocal key_texts
            nonlocal widths

            # Wrap the text
            text = "\n".join([textwrap.fill(line, width=self.MAX_KEY_CHARS) for line in text.split('\n')])

            # Get the width and make it the max width if it is
            width: int = self._get_text_width(text)
            max_width = width if width > max_width else max_width

            # Add the text to key_texts and add the size to size_coords
            key_texts[input] = text
            widths[input] = width

        def get_x(input: KeyInput) -> int:
            '''
            Gets the x value for a Key Hint for the KeyInput

            :param input: The KeyInput to get the x value for
            :type input: class: `KeyInput`

            :return: The x value for the KeyInput's Help Text
            :rtype: int
            '''
            return self.SCREEN_WIDTH - widths[input] - ((max_width - widths[input]) // 2)
        
        def get_y(input: KeyInput) -> int:
            '''
            Gets the y value for a Key Hint for the KeyInput

            :param input: The KeyInput to get the y value for
            :type input: class: `KeyInput`

            :return: The y value for the KeyInput's Help Text
            :rtype: int
            '''

            if input == KeyInput.KEY1:
                return 0
            elif input == KeyInput.KEY2:
                return (self.SCREEN_HEIGHT - self._get_text_height(key_texts[KeyInput.KEY2])) // 2
            elif input == KeyInput.KEY3:
                return self.SCREEN_HEIGHT - self._get_text_height(key_texts[KeyInput.KEY3])

        # Add height for all text that is not empty
        if self.key1_text != "":
            log_text_info(self.key1_text, KeyInput.KEY1)

        if self.key2_text != "":
            log_text_info(self.key2_text, KeyInput.KEY2)
        
        if self.key3_text != "":
            log_text_info(self.key3_text, KeyInput.KEY3)

        for input in key_texts:
            key_coords[input] = (get_x(input), get_y(input))

        # Return tuple
        return (key_coords, key_texts, max_width)

    def __get_joy_text_coords_and_text(self):
        '''
        Gets the coordinates, help texts, and max width for the Joystick Control Hint Texts

        :return: A tuple with first with a dict containing the Coordinate for each Joystick input that has help text. 
        Then a dict containing the text for each Joystick Input that has help text. Then an int with the max width 
        of all the help text. Overall: (dict[JoystickInput: (x,y)], dict[JoystickInput: help_text], max_width)
        :rtype: (dict[:class:`JoystickInput`, (int, int)], dict[:class:`JoystickInput`, str], int) 
        '''
        # Dict of coords (x, y)
        size_coords: dict[JoystickInput, (int, int)] = {} # Size in coordinate form (width, height) for each input
        total_height: int = 0 # Total Height of just the text
        max_width: int = 0 # Max width of all text

        joy_texts: dict[JoystickInput, str] = {}
        joy_coords: dict[JoystickInput, (int, int)] = {}

        def log_text_info(text: str, input: JoystickInput):
            '''
            Logs the text into joy_texts and (text_width, text_height) into size_coords and gets the total_height and max_width

            :param text: The help text to log the info for
            :type text: str

            :param input: The Joystick Input the help text represents
            :type input: class: `JoystickInput`
            '''
            nonlocal total_height
            nonlocal max_width
            nonlocal joy_texts
            nonlocal size_coords

            # Wrap the text
            text = " " + text
            text = "\n".join([textwrap.fill(line, width=self.MAX_JOY_CHARS+1) for line in text.split('\n')])

            # Get the height and add it to the total height
            height: int = self._get_text_height(text)
            total_height += height

            # Get the width and make it the max width if it is
            width: int = self._get_text_width(text)
            max_width = width if width > max_width else max_width

            # Add the text to joy_texts and add the size to size_coords
            joy_texts[input] = text
            size_coords[input] = (width, height)

        # Add height for all text that is not empty
        if self.up_text != "":
            log_text_info(self.up_text, JoystickInput.UP)

        if self.left_text != "":
            log_text_info(self.left_text, JoystickInput.LEFT)
        
        if self.button_text != "":
            log_text_info(self.button_text, JoystickInput.BUTTON)

        if self.right_text != "":
            log_text_info(self.right_text, JoystickInput.RIGHT)

        if self.down_text != "":
            log_text_info(self.down_text, JoystickInput.DOWN)

        # If no help text just return
        if len(joy_texts) == 0:
            return (joy_coords, joy_texts, max_width)

        # Calculate spacer between each text hint
        spacer: int = (self.SCREEN_HEIGHT - total_height) // len(size_coords)
        spacer = 0 if spacer < 0 else spacer


        # Get the current y to know where to place the next help text
        cur_y = spacer / 2 # Start with half spacer on top (causes another half spacer on bottom)

        # Get the x,y values for each input in the right order
        for input in self.JOY_ORDER:
            # Make sure the Joystick Input has non empty help text (won't be in joy_texts)
            if input not in joy_texts:
                continue
            
            # Get the height and width of this input's help text
            width, height = size_coords[input]
            
            # Center the text then add the coordinate for the input
            x = (max_width - width) // 2 
            joy_coords[input] = (x, cur_y)

            # Set the cur_y to be at the y of the next input
            cur_y += height + spacer
        
        # Return tuple
        return (joy_coords, joy_texts, max_width)

    def draw_controls_on_image(self, draw: ImageDraw):
        '''
        Draws the control hints on an image to be displayed.

        :param draw: The draw object for the image to add the control hints to
        :type draw: class: `PIL.ImageDraw`

        :return: Tuple (start_x, end_x) representing where the undrawn center view can start and end
        :rtype: (int, int)
        '''
         # Joystick Area Used
        joy_used = True
        joy_max_width = 0
        
        # Keys Area Used
        keys_used = True
        key_max_width = 0

        # Draw the text        
        # Draw Joystick Controls if Enabled
        if self.joy_controls_en: # Left Side
            icon_height = self.LINE_HEIGHT
            icon_width = self.CHAR_WIDTH - 1 # Leave a pixel space before text
            
            arrow_size = min(icon_height, icon_width) + 2
            arrow_top = math.ceil((icon_height - arrow_size) / 2)
            arrow_left = (icon_width - arrow_size) // 2 - 1
            arrow_bottom = arrow_size + arrow_top
            arrow_right = arrow_size + arrow_left
            arrow_mid_x = arrow_left + (arrow_size // 2)
            arrow_mid_y = arrow_top + (arrow_size // 2)

            circle_size = min(icon_height, icon_width) + 1
            circle_top = math.ceil((icon_height - circle_size) / 2)
            circle_left = (icon_width - circle_size) // 2
            circle_bottom = circle_top + circle_size
            circle_right = circle_left + circle_size

            # Coordinates, Wrapped Text, and Max Width for the Joystick Help Text
            joy_coords, joy_text, joy_max_width = self.__get_joy_text_coords_and_text()
            
            # Draw up text if not empty
            if self.up_text != "":
                coord = joy_coords[JoystickInput.UP]
                text = joy_text[JoystickInput.UP]

                # Draw Arrow
                arrow_coords = [(arrow_left,arrow_bottom + coord[1]),(arrow_right,arrow_bottom + coord[1]),(arrow_mid_x,arrow_top + coord[1])]
                draw.polygon(arrow_coords, outline=255, fill=0)
                
                # Draw Text
                draw.multiline_text(coord, text, font=self.cont_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)
            
            # Draw left text if not empty
            if self.left_text != "":
                coord = joy_coords[JoystickInput.LEFT]
                text = joy_text[JoystickInput.LEFT]
                
                # Draw Arrow
                arrow_coords = [(arrow_left-1,coord[1] + arrow_mid_y),(arrow_right-1,coord[1] + arrow_bottom),(arrow_right-1,coord[1] + arrow_top)]
                draw.polygon(arrow_coords, outline=255, fill=0)
                
                # Draw Text
                draw.multiline_text(coord, text, font=self.cont_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)

            # Draw button text if not empty
            if self.button_text != "":
                coord = joy_coords[JoystickInput.BUTTON]
                text = joy_text[JoystickInput.BUTTON]

                # Draw Circle
                icon_coords = [(circle_left, coord[1] + circle_top), (circle_right, coord[1] + circle_bottom)]
                draw.ellipse(icon_coords, outline=255, fill=0)
                
                # Draw Text
                draw.multiline_text(coord, text, font=self.cont_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)
                
            # Draw right text if not empty
            if self.right_text != "":
                coord = joy_coords[JoystickInput.RIGHT]
                text = joy_text[JoystickInput.RIGHT]

                # Draw Arrow
                arrow_coords = [(arrow_left,coord[1] + arrow_top),(arrow_left,coord[1] + arrow_bottom),(arrow_right, coord[1] + arrow_mid_y)]
                draw.polygon(arrow_coords, outline=255, fill=0)
                
                # Draw Text
                draw.multiline_text(coord, text, font=self.cont_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)

            # Draw down text if not empty
            if self.down_text != "":
                coord = joy_coords[JoystickInput.DOWN]
                text = joy_text[JoystickInput.DOWN]

                # Draw Arrow
                arrow_coords = [(arrow_left,coord[1] + arrow_top),(arrow_right,coord[1] + arrow_top),(arrow_mid_x,coord[1] + arrow_bottom)]
                draw.polygon(arrow_coords, outline=255, fill=0)
                
                # Draw Text
                draw.multiline_text(coord, text, font=self.cont_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)
            
            # Draw Separator if not all Empty
            if self.up_text != "" or self.down_text != "" or self.left_text != "" or self.right_text != "":
                sep_x = joy_max_width + ((self.SEP_WIDTH - self.SEP_FILL_WIDTH) // 2)
                sep_y = (self.SCREEN_HEIGHT - self.SEP_FILL_HEIGHT) // 2
                draw.line([(sep_x,sep_y),(sep_x + self.SEP_FILL_WIDTH - 1,sep_y + self.SEP_FILL_HEIGHT)], fill=0)
            # Empty - Give room to View Text
            else:
                joy_used = False
        
            
        # Draw Key Controls if Enabled
        if self.key_controls_en: # Right Side
            # Coordinates, Wrapped Text, and Max Width for the Joystick Help Text
            key_coords, key_text, key_max_width = self.__get_key_text_coords_and_text()

            # Draw key 1 text if not empty
            if self.key1_text != "":
                coord = key_coords[KeyInput.KEY1]
                text = key_text[KeyInput.KEY1]

                draw.multiline_text(coord, text, font=self.cont_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)
                
            # Draw key 2 text if not empty
            if self.key2_text != "":
                coord = key_coords[KeyInput.KEY2]
                text = key_text[KeyInput.KEY2]
                
                draw.multiline_text(coord, text, font=self.cont_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)
                
            # Draw key 3 text if not empty
            if self.key3_text != "":
                coord = key_coords[KeyInput.KEY3]
                text = key_text[KeyInput.KEY3]
                
                draw.multiline_text(coord, text, font=self.cont_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)
            
            # Draw Separator if not all Empty
            if self.key1_text != "" or self.key2_text != "" or self.key3_text != "":
                sep_x = self.SCREEN_WIDTH - key_max_width - ((self.SEP_WIDTH + self.SEP_FILL_WIDTH) // 2)
                sep_y = (self.SCREEN_HEIGHT - self.SEP_FILL_HEIGHT) // 2
                draw.line([(sep_x,sep_y),(sep_x + self.SEP_FILL_WIDTH - 1,sep_y + self.SEP_FILL_HEIGHT)], fill=0)
            # Empty - Give room to View Text
            else:
                keys_used = False
        
        start_x = ((joy_max_width + self.SEP_WIDTH)
                if self.joy_controls_en and joy_used
                else 0)
            
        end_x = ((self.SCREEN_WIDTH - key_max_width - self.SEP_WIDTH)
            if self.key_controls_en and keys_used
            else self.SCREEN_WIDTH)

        return (start_x, end_x)
    
    def draw(self):
        '''
        Redraws the screen on the SH116
        '''
        # Create new image to clear screen
        # Make sure to create image with mode '1' for 1-bit color.
        image = Image.new('1', (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), self.TEXT_COLOR)

        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)

        start_x, end_x = self.draw_controls_on_image(draw)
        
        # Draw View Text
        if self.view_text != "":
            max_width = end_x - start_x
            wrap_len = max_width // self.CHAR_WIDTH
            
            wrapped_text = "\n".join([textwrap.fill(line, width=wrap_len) for line in self.view_text.split('\n')])
            view_x = start_x + ((max_width - self._get_text_width(wrapped_text)) // 2)
            view_y = (self.SCREEN_HEIGHT - self._get_text_height(wrapped_text)) // 2
            coord = (view_x, view_y)
            
            draw.multiline_text(coord, wrapped_text, font=self.view_font, fill=0, spacing=self.LINE_SPACING, align=self.TEXT_ALIGN)
        
        # Draw the Screen onto the display
        Display.disp.ShowImage(Display.disp.getbuffer(image))
