from abc import ABC, abstractmethod
from PIL import Image, ImageDraw
from PIL.ImageFont import ImageFont
from OSGlobals import on_render_thread
from enum import Enum
from typing import AnyStr, List, Tuple, Optional

import Display

class Component(ABC):
    def __init__(self, **kwargs):
        self._changed = False
        for key, value in kwargs.items():
            self._add_property(key, value)

    def _add_property(self, name, value):
        private_name = f"_{name}"

        def getter(self):
            return getattr(self, private_name)

        def setter(self, new_value):
            setattr(self, private_name, new_value)
            self.set_changed_flag()  # Set the changed flag when a property is changed

        setattr(self, private_name, value)
        setattr(self.__class__, name, property(getter, setter))
    
    def get_changed_flag(self):
        return self._changed
    
    def set_changed_flag(self):
        self._changed = True

    def clear_changed_flag(self):
        if on_render_thread():
            self._changed = False
        else:
           raise Exception("Cannot clear changed flag from non-render thread")

    @abstractmethod
    def draw(self,  draw: ImageDraw):
        pass

'''
Justify requires newer version of Pillow (PIL)
'''
class TextAllignment(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'
    #JUSTIFY = 'justify'

class VerticalAnchor(Enum):
    ASCENDER = "a"      # Only for horizontal text
    TOP = "t"           # Only for single line text
    MIDDLE = "m"
    BASELINE = "s"      # Only for horizontal text
    BOTTOM = "b"        # Only for single line text
    DESCENDER = "d"     # Only for horizontal text

class HorizontalAnchor(Enum):
    LEFT = "l"
    MIDDLE = "m"
    RIGHT = "r"
    BASELINE = "s"      # Only for vertical text

'''
More info here: https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html#text-anchors
'''
class TextAnchor:
    def __init__(self, vertical: VerticalAnchor, horizontal: HorizontalAnchor):
        self.vertical = vertical
        self.horizontal = horizontal

    def __repr__(self):
        return f"TextAnchor(vertical={self.vertical.value}, horizontal={self.horizontal.value})"
    
    def to_PIL_str(self):
        return str(self.horizontal.value + self.vertical.value)

'''
Note: Requires libraqm to be installed
More info here: https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.multiline_text
'''
class TextDirection(Enum):
    LEFT_TO_RIGHT = "ltr"
    RIGHT_TO_LEFT = "rtl"
    TOP_TO_BOTTOM = "ttb"
'''
TODO: Change Image Renderer to RGBA Type
TODO: If screen is just 1 color, change back to 1 bit color
'''
class RGBAColor:
    def __init__(self, r: int, g: int, b: int, a: int = 255):
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))
        self.a = max(0, min(255, a))

    def __repr__(self):
        return f"RGBAColor(r={self.r}, g={self.g}, b={self.b}, a={self.a})"
    
    def __eq__(self, other):
        if not isinstance(other, RGBAColor):
            return False
        return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a
    
    def to_tuple(self):
        return (self.r, self.g, self.b, self.a)
'''
More info generally here: https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.multiline_text

More info on features here: https://learn.microsoft.com/en-us/typography/opentype/spec/featurelist
More info on languages here: https://www.w3.org/International/articles/language-tags/
More info on language codes here: https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry

Note: Commented out methods include parameters that require newer version of Pillow (PIL)
'''
class MultiLineTextComponent(Component):
    def __init__(self, x: int, y: int, text: AnyStr, fill: Optional[RGBAColor] = None, 
                 font: Optional[ImageFont] = None,  anchor: Optional[TextAnchor] = None, 
                 spacing: float = 4, align: TextAllignment = TextAllignment.LEFT, 
                 direction: Optional[TextDirection] = None, features: Optional[List[str]] = None, 
                 language: Optional[str] = None, stroke_width: float = 0, 
                 stroke_fill: Optional[RGBAColor] = None, embedded_color: bool = False, 
                 font_size: Optional[float] = None):
        super().__init__(x=x, y=y, text=text, fill=fill, font=font,  anchor=anchor, spacing=spacing, 
                         align=align, direction=direction, features=features, language=language, 
                         stroke_width=stroke_width, stroke_fill=stroke_fill, 
                         embedded_color=embedded_color, font_size=font_size)
    # ~ def __init__(self, x: int, y: int, text: AnyStr, fill: Optional[RGBAColor] = None, 
                 # ~ font: Optional[ImageFont] = None,  anchor: Optional[TextAnchor] = None, 
                 # ~ spacing: float = 4, align: TextAllignment = TextAllignment.LEFT, 
                 # ~ direction: Optional[TextDirection] = None, features: Optional[List[str]] = None):
        # ~ super().__init__(x=x, y=y, text=text, fill=fill, font=font,  anchor=anchor, spacing=spacing, 
                         # ~ align=align, direction=direction, features=features)
        
    def draw(self, draw: ImageDraw):
        draw.multiline_text((self.x, self.y), self.text, 
                            fill=None if self.fill is None else self.fill.to_tuple(),
                            font=self.font, 
                            anchor=None if self.anchor is None else self.anchor.to_PIL_str(), 
                            spacing=self.spacing, align=self.align.value, 
                            direction=None if self.direction is None else self.direction.value,
                            features=self.features, language=self.language, 
                            stroke_width=self.stroke_width,
                            stroke_fill=None if self.stroke_fill is None else self.stroke_fill.to_tuple(),
                            embedded_color=self.embedded_color, font_size=self.font_size)
    # def draw(self, draw: ImageDraw):
        # draw.multiline_text((self.x, self.y), self.text, 
                            # fill=None if self.fill is None else self.fill.to_tuple(),
                            # font=self.font, 
                            # anchor=None if self.anchor is None else self.anchor.to_PIL_str(), 
                            # spacing=self.spacing, align=self.align.value, 
                            # direction=None if self.direction is None else self.direction.value,
                            # features=self.features)
        
    def get_text_size(self, draw: ImageDraw = Display.DEF_DRAW) -> Tuple[int, int]:
        left, top, right, bottom = draw.multiline_textbbox((self.x, self.y), self.text, font=self.font,
                                                            anchor=None if self.anchor is None else self.anchor.to_PIL_str(), 
                                                            spacing=self.spacing, align=self.align.value, 
                                                            direction=None if self.direction is None else self.direction.value,
                                                            features=self.features, language=self.language, 
                                                            stroke_width=self.stroke_width,
                                                            embedded_color=self.embedded_color)#,
                                                            #font_size=self.font_size)
                             
        return (right - left, top - bottom)
    
class CircleComponent(Component):
    def __init__(self, x: int, y: int, radius: int, fill: Optional[RGBAColor] = None, 
                 outline: Optional[RGBAColor] = None, line_width: int = 1):
        super().__init__(x=x, y=y, radius=radius, fill=fill, outline=outline, line_width=line_width)

    def draw(self, draw: ImageDraw):
        draw.ellipse((self.x - self.radius, self.y - self.radius, 
                      self.x + self.radius, self.y + self.radius),
                      fill=self.fill.to_tuple() if self.fill else None,
                      outline=self.outline.to_tuple() if self.outline else None, 
                      width=self.line_width
                    )

class EllipseComponent(Component):
    def __init__(self, x: int, y: int, width: int, height: int, fill: Optional[RGBAColor] = None, 
                 outline: Optional[RGBAColor] = None, line_width: int = 1):
        super().__init__(x=x, y=y, width=width, height=height, fill=fill, outline=outline, 
                         line_width=line_width)

    def draw(self, draw: ImageDraw):
        draw.ellipse((self.x, self.y, self.x + self.width, self.y + self.height), 
                     fill=self.fill.to_tuple() if self.fill else None,
                     outline=self.outline.to_tuple() if self.outline else None, 
                     width=self.line_width
                    )

class RectangleComponent(Component):
    def __init__(self, x: int, y: int, width: int, height: int, fill: Optional[RGBAColor] = None, 
                 outline: Optional[RGBAColor] = None, line_width: int = 1):
        super().__init__(x=x, y=y, width=width, height=height, fill=fill, outline=outline, 
                         line_width=line_width)

    def draw(self, draw: ImageDraw):
        draw.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), 
                       fill=self.fill.to_tuple() if self.fill else None,
                       outline=self.outline.to_tuple() if self.outline else None, 
                       width=self.line_width
                      )

# Rounded Rectangles (draw.rounded_rectangle) require Newer Pillow (PIL) Version
# class RoundedRectangleComponent(Component):
#     def __init__(self, x: int, y: int, width: int, height: int, radius: int = 0, 
#                  fill: Optional[RGBAColor] = None, outline: Optional[RGBAColor] = None, 
#                  line_width: int = 1, corners: Optional[tuple[bool, bool, bool, bool]] = None):
#         super().__init__(x=x, y=y, width=width, height=height, radius=radius, fill=fill, 
#                          outline=outline, line_width=line_width, corners=corners)
        
#     def draw(self, draw: ImageDraw):
#         draw.rounded_rectangle((self.x, self.y, self.x + self.width, self.y + self.height), 
#                                radius=self.radius,
#                                fill=self.fill.to_tuple() if self.fill else None,
#                                outline=self.outline.to_tuple() if self.outline else None, 
#                                line_width=self.line_width,
#                                corners=self.corners
#                               )

class LineJointType(Enum):
    CURVE = "curve"
    STRAIGHT = None

class LineComponent(Component):
    def __init__(self, x1: int, y1: int, x2: int, y2: int, fill: Optional[RGBAColor] = None, 
                 width: int = 0, joint: LineJointType = LineJointType.STRAIGHT):
        super().__init__(x1=x1, y1=y1, x2=x2, y2=y2, fill=fill, width=width, joint=joint)
    
    def draw(self, draw: ImageDraw):
        draw.line((self.x1, self.y1, self.x2, self.y2),
                  fill=self.fill.to_tuple() if self.fill else None,
                  width=self.width, joint=self.joint.value)

if __name__ == "__main__":
    # Test MultiLineTextComponent
    from PIL import Image

    image = Image.new('1', (500, 500), "WHITE")
    draw = ImageDraw.Draw(image)
    textBox = MultiLineTextComponent(10, 10, "Hello World!")
    print("Changed Flag: ", textBox.get_changed_flag())

    # Change the text
    textBox.text = "Goodbye World!"
    print("Changed Flag: ", textBox.get_changed_flag())
    textBox.clear_changed_flag()
    print("Changed Flag Cleared: ", textBox.get_changed_flag())

    # Change the location
    textBox.x = 100
    textBox.y = 100
    print("Changed Flag: ", textBox.get_changed_flag())
    textBox.clear_changed_flag()
    print("Changed Flag Cleared: ", textBox.get_changed_flag())

    textBox.draw(draw)
    print(textBox)
    image.show()

