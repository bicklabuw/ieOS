from __future__ import annotations
from abc import ABC, abstractmethod
from PIL import Image, ImageDraw
from PIL import ImageFont
from enum import Enum
from typing import AnyStr, List, Tuple, Optional
from gui.ui_core.View import View
from gui.ui_core.ViewController import ViewController

import gui.core.Display as Display

'''
Note: Requires libraqm to be installed
More info here: https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.multiline_text
'''
# Enums for clearer parameter options
class TextDirection(Enum):
    LEFT_TO_RIGHT = "ltr"
    RIGHT_TO_LEFT = "rtl"
    TOP_TO_BOTTOM = "ttb"

class LineJointType(Enum):
    CURVE = "curve"
    STRAIGHT = None

class TextAlignment(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'
    JUSTIFY = 'justify'

class VerticalAnchor(Enum):
    ASCENDER = "a"      # Only for horizontal text
    TOP = "t"           # Only for single-line text
    MIDDLE = "m"
    BASELINE = "s"      # Only for horizontal text
    BOTTOM = "b"        # Only for single-line text
    DESCENDER = "d"     # Only for horizontal text

class HorizontalAnchor(Enum):
    LEFT = "l"
    MIDDLE = "m"
    RIGHT = "r"
    BASELINE = "s"      # Only for vertical text

class TextAnchor(Enum):
    """
    Represents a combination of horizontal and vertical text anchors.
    
    Important Notes:
    - Horizontal Anchor Notes:
        - LEFT is for Left Aligned Text
        - MIDDLE is for Centered Text
        - RIGHT is for Right Aligned Text
        - BASELINE is the middle of text when vertical (Vertical Text ONLY)
        
    - Vertical Anchor Notes:
        - ASCENDER is the top of the text when horizontal (Horizontal Text ONLY)
        - TOP is the top of the text (Single Line Text ONLY)
        - MIDDLE is the middle of the text
        - BASELINE is the bottom of the text when horizontal (Horizontal Text ONLY)
        - BOTTOM is the bottom of the text (Single Line Text ONLY)
        - DESCENDER is the bottom of the text when horizontal (Horizontal Text ONLY)"""
    LEFT_ASCENDER = (HorizontalAnchor.LEFT, VerticalAnchor.ASCENDER)
    LEFT_TOP = (HorizontalAnchor.LEFT, VerticalAnchor.TOP)
    LEFT_MIDDLE = (HorizontalAnchor.LEFT, VerticalAnchor.MIDDLE)
    LEFT_BASELINE = (HorizontalAnchor.LEFT, VerticalAnchor.BASELINE)
    LEFT_BOTTOM = (HorizontalAnchor.LEFT, VerticalAnchor.BOTTOM)
    LEFT_DESCENDER = (HorizontalAnchor.LEFT, VerticalAnchor.DESCENDER)

    MIDDLE_ASCENDER = (HorizontalAnchor.MIDDLE, VerticalAnchor.ASCENDER)
    MIDDLE_TOP = (HorizontalAnchor.MIDDLE, VerticalAnchor.TOP)
    MIDDLE_MIDDLE = (HorizontalAnchor.MIDDLE, VerticalAnchor.MIDDLE)
    MIDDLE_BASELINE = (HorizontalAnchor.MIDDLE, VerticalAnchor.BASELINE)
    MIDDLE_BOTTOM = (HorizontalAnchor.MIDDLE, VerticalAnchor.BOTTOM)
    MIDDLE_DESCENDER = (HorizontalAnchor.MIDDLE, VerticalAnchor.DESCENDER)

    RIGHT_ASCENDER = (HorizontalAnchor.RIGHT, VerticalAnchor.ASCENDER)
    RIGHT_TOP = (HorizontalAnchor.RIGHT, VerticalAnchor.TOP)
    RIGHT_MIDDLE = (HorizontalAnchor.RIGHT, VerticalAnchor.MIDDLE)
    RIGHT_BASELINE = (HorizontalAnchor.RIGHT, VerticalAnchor.BASELINE)
    RIGHT_BOTTOM = (HorizontalAnchor.RIGHT, VerticalAnchor.BOTTOM)
    RIGHT_DESCENDER = (HorizontalAnchor.RIGHT, VerticalAnchor.DESCENDER)

    BASELINE_ASCENDER = (HorizontalAnchor.BASELINE, VerticalAnchor.ASCENDER)
    BASELINE_TOP = (HorizontalAnchor.BASELINE, VerticalAnchor.TOP)
    BASELINE_MIDDLE = (HorizontalAnchor.BASELINE, VerticalAnchor.MIDDLE)
    BASELINE_BASELINE = (HorizontalAnchor.BASELINE, VerticalAnchor.BASELINE)
    BASELINE_BOTTOM = (HorizontalAnchor.BASELINE, VerticalAnchor.BOTTOM)
    BASELINE_DESCENDER = (HorizontalAnchor.BASELINE, VerticalAnchor.DESCENDER)

    @property
    def horizontal(self) -> HorizontalAnchor:
        return self.value[0]

    @property
    def vertical(self) -> VerticalAnchor:
        return self.value[1]

    def to_pillow(self) -> str:
        # Combine anchor codes, e.g. 'lt', 'mr'
        return f"{self.horizontal.value}{self.vertical.value}"

    def __repr__(self) -> str:
        return f"TextAnchor(h={self.horizontal}, v={self.vertical})"

class CoordinateView(View):
    """
    Base view with a rectangular frame at (x, y, width, height).
    """
    def __init__(self, x: float, y: float, width: float, height: float, controller: Optional[ViewController] = None) -> None:
        super().__init__(x, y, width, height, controller)

class RectangleView(CoordinateView):
    def __init__(
        self, x: float, y: float, width: float, height: float,
        fill: int = Display.ON, outline: Optional[int] = None,
        stroke_width: int = 2
    ) -> None:
        super().__init__(x, y, width, height)
        self.fill = fill
        self.outline = outline
        self.stroke_width = stroke_width

    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)

        outline_width = self.stroke_width if self.outline == Display.ON else 0
        self.outline_x = outline_width
        self.outline_y = outline_width
        
    
    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        outline_width = self.stroke_width if self.outline == Display.ON else 0
        # print(outline_width, self.stroke_width)
        # print(f"Rendering RectangleView at ({outline_width}, {outline_width}) with size ({self.width}, {self.height})")
        draw.rectangle(
            [outline_width, outline_width,
             self.width + outline_width, self.height + outline_width],
            fill=self.fill,
            outline=self.outline,
            width=self.stroke_width
        )

class EllipseView(CoordinateView):
    def __init__(
        self, x: float, y: float, width: float, height: float,
        fill: int = Display.OFF, outline: Optional[int] = Display.ON,
        stroke_width: int = 1
    ) -> None:
        super().__init__(x, y, width, height)
        self.fill = fill
        self.outline = outline
        self.stroke_width = stroke_width

    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)

        outline_width = self.stroke_width if self.outline == Display.ON else 0
        self.outline_x = outline_width
        self.outline_y = outline_width

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        outline_width = self.stroke_width if self.outline == Display.ON else 0
        draw.ellipse(
            [outline_width, outline_width,
             self.width  + outline_width, self.height + outline_width],
            fill=self.fill,
            outline=self.outline,
            width=self.stroke_width
        )

class CircleView(EllipseView):
    def __init__(
        self, x: float, y: float, radius: float,
        fill: int = Display.OFF, outline: Optional[int] = Display.ON,
        stroke_width: int = 1
    ) -> None:
        super().__init__(
            x - radius, y - radius,
            radius * 2, radius * 2,
            fill=fill, outline=outline,
            stroke_width=stroke_width
        )
    
    @property
    def radius(self) -> int:
        return self.width / 2
    
    @radius.setter
    def radius(self, radius: int):
        rad_chg = radius - self.radius
        rx2 = radius * 2

        self.x += rad_chg
        self.y += rad_chg
        self.width = rx2
        self.height = rx2


class LineView(CoordinateView):
    def __init__(
        self, x1: float, y1: float, x2: float, y2: float,
        fill: Optional[int] = None, stroke_width: int = 1,
        joint: Optional[LineJointType] = None
    ) -> None:
        minx, maxx = min(x1, x2), max(x1, x2)
        miny, maxy = min(y1, y2), max(y1, y2)
        super().__init__(minx, miny, maxx - minx, maxy - miny)
        self.x1 = x1 - minx; self.y1 = y1 - miny
        self.x2 = x2 - minx; self.y2 = y2 - miny
        self.fill = fill
        self.stroke_width = stroke_width
        self.joint = joint
        self.x = minx
        self.y = miny
        self.width = max(maxx - minx, stroke_width)
        self.height = max(maxy - miny, stroke_width)

    def update_line_points(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """
        Update the line's start and end points.
        """
        #print(f"Updating LineView points: ({x1}, {y1}) to ({x2}, {y2})")
        self.x1 = x1; self.y1 = y1
        self.x2 = x2; self.y2 = y2
        # Update the bounding box
        minx, maxx = min(x1, x2), max(x1, x2)
        miny, maxy = min(y1, y2), max(y1, y2)
        self.x1 = x1 - minx; self.y1 = y1 - miny
        self.x2 = x2 - minx; self.y2 = y2 - miny

        self.x = minx
        self.y = miny
        self.width = max(maxx - minx, self.stroke_width)
        self.height = max(maxy - miny, self.stroke_width)

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        #print(f"Rendering LineView from ({self.x1}, {self.y1}) to ({self.x2}, {self.y2})")
        draw.line(
            [(int(self.x1), (self.y1)),
             (int(self.x2), (self.y2))],
            fill=self.fill,
            width=int(self.stroke_width),
            joint=self.joint.value if self.joint else None
        )

class PolygonView(CoordinateView):
    def __init__(
        self, x: float, y: float,
        points: list[tuple[float, float]],
        fill: Optional[int] = None, outline: Optional[int] = None
    ) -> None:
        xs, ys = zip(*points)
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        super().__init__(x + minx, y + miny, maxx - minx, maxy - miny)
        self.points = [(px - minx, py - miny) for px, py in points]
        self.fill = fill
        self.outline = outline

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        abs_pts = [(px, py) for px, py in self.points]
        draw.polygon(
            abs_pts,
            fill=self.fill,
            outline=self.outline
        )

class PolylineView(PolygonView):
    def __init__(
        self, x: float, y: float,
        points: list[tuple[float, float]],
        stroke_width: int = 1, fill: Optional[int] = None,
        joint: Optional[LineJointType] = None
    ) -> None:
        super().__init__(x, y, points, fill=None, outline=fill)
        self.stroke_width = stroke_width
        self.joint = joint

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        abs_pts = [(px, py) for px, py in self.points]
        draw.line(
            abs_pts,
            fill=self.outline,
            width=self.stroke_width,
            joint=self.joint.value if self.joint else None
        )

class ArcView(CoordinateView):
    def __init__(
        self, x: float, y: float,
        width: float, height: float,
        start: float, end: float,
        fill: Optional[int] = None, stroke_width: int = 1,
        direction: Optional[TextDirection] = None
    ) -> None:
        super().__init__(x, y, width, height)
        self.start = start; self.end = end
        self.fill = fill; self.stroke_width = stroke_width

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        draw.arc([
            0, 0,
            self.width, self.height
        ], start=self.start, end=self.end,
        fill=self.fill,
        width=self.stroke_width)

class ChordView(CoordinateView):
    def __init__(
        self, x: float, y: float,
        width: float, height: float,
        start: float, end: float,
        fill: Optional[int] = None, outline: Optional[int] = None
    ) -> None:
        super().__init__(x, y, width, height)
        self.start = start; self.end = end
        self.fill = fill; self.outline = outline

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        draw.chord([
            0, 0,
            self.width, self.height
        ], start=self.start, end=self.end,
        fill=self.fill,
        outline=self.outline)

class PieSliceView(ChordView):
    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        draw.pieslice([
            0, 0,
            self.width, self.height
        ], start=self.start, end=self.end,
        fill=self.fill,
        outline=self.outline)

class PointView(CoordinateView):
    def __init__(
        self, x: float, y: float,
        fill: Optional[int] = None
    ) -> None:
        super().__init__(x, y, 1, 1)
        self.fill = fill

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        draw.point((0,0), fill=self.fill)

class BitmapView(View):
    def __init__(
        self, x: float, y: float,
        image: Image.Image
    ) -> None:
        super().__init__(x, y, image.width, image.height)
        self.image = image.convert('1')

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        draw.bitmap((0, 0), self.image, fill=1)

class RoundedRectangleView(CoordinateView):
    def __init__(
        self, x: float, y: float,
        width: float, height: float,
        radius: float = 0,
        fill: Optional[int] = None, outline: Optional[int] = None,
        stroke_width: int = 1
    ) -> None:
        super().__init__(x, y, width, height)
        self.radius = radius; self.fill = fill; self.outline = outline; self.stroke_width = stroke_width

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        draw.rounded_rectangle([
            0, 0,
            self.width, self.height
        ], radius=self.radius,
        fill=self.fill,
        outline=self.outline,
        width=self.stroke_width)

class TextView(CoordinateView):
    def __init__(
        self, x: float, y: float, text: str,
        font: Optional[ImageFont.ImageFont] = None,
        fill: Optional[int] = None,
        anchor: Optional[TextAnchor] = None,
        spacing: int = 4,
        align: TextAlignment = TextAlignment.LEFT,
        direction: Optional[TextDirection] = None,
        features: Optional[List[str]] = None,
        language: Optional[str] = None,
        stroke_width: int = 0,
        stroke_fill: Optional[int] = None,
        embedded_color: bool = False,
        font_size: Optional[int] = None
    ) -> None:
        f = font or ImageFont.load_default()
        bbox = f.getbbox(text)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        super().__init__(x, y, w, h)
        self.text = text; self.font = f; self.fill = fill
        self.anchor = anchor; self.spacing = spacing; self.align = align
        self.direction = direction; self.features = features; self.language = language
        self.stroke_width = stroke_width; self.stroke_fill = stroke_fill
        self.embedded_color = embedded_color; self.font_size = font_size

    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)

        if self.get_dirty():
            self.width, self.height = self.get_text_size()
            #print(f"TextView layout: {self.text} at ({self.abs_x}, {self.abs_y}) with size ({self.width}, {self.height})")

    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        draw.text((0, 0), self.text,
                  fill=self.fill,
                  font=self.font,
                  anchor=self.anchor.to_pillow() if self.anchor else None,
                  spacing=self.spacing,
                  align=self.align.value,
                  direction=self.direction.value if self.direction else None,
                  features=self.features,
                  language=self.language,
                  stroke_width=self.stroke_width,
                  stroke_fill=self.stroke_fill,
                  embedded_color=self.embedded_color,
                  font_size=self.font_size)

    def get_text_bbox(self, draw: Optional[ImageDraw.ImageDraw] = None) -> Tuple[float, float, float, float]:
        """
        Returns the bounding box of the text.
        """
        bbox = (draw or Display.DEF_DRAW).textbbox((0, 0), self.text,
                  font=self.font,
                  anchor=self.anchor.to_pillow() if self.anchor else None,
                  spacing=self.spacing,
                  align=self.align.value,
                  direction=self.direction.value if self.direction else None,
                  features=self.features,
                  language=self.language,
                  stroke_width=self.stroke_width,
                  embedded_color=self.embedded_color)
        return (bbox[0], bbox[1],
                bbox[2], bbox[3])

    def get_abs_text_bbox(self, draw: Optional[ImageDraw.ImageDraw] = None) -> Tuple[float, float, float, float]:
        """
        Returns the bounding box of the text in absolute coordinates on the screen.
        """
        bbox = self.get_text_bbox(draw)
        return (self.abs_x + bbox[0], self.abs_y + bbox[1],
                self.abs_x + bbox[2], self.abs_y + bbox[3])

    def get_text_size(self, draw: Optional[ImageDraw.ImageDraw] = None) -> Tuple[float, float]:
        """
        Returns the size of the text.
        """
        bbox = self.get_text_bbox(draw)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        # Note: This is not the same as the width and height of the view
        # because the view may have padding or other decorations.
        # Use get_text_bbox() to get the actual bounding box of the text
        # in the view's coordinate space.

class MultilineTextView(CoordinateView):
    """
    Renders multiple lines of text with full multiline support.
    """
    def __init__(
        self, x: float, y: float, text: str,
        font: Optional[ImageFont.ImageFont] = None,
        fill: Optional[int] = None,
        anchor: Optional[TextAnchor] = None,
        spacing: int = 4,
        align: TextAlignment = TextAlignment.LEFT,
        direction: Optional[TextDirection] = None,
        features: Optional[List[str]] = None,
        language: Optional[str] = None,
        stroke_width: int = 0,
        stroke_fill: Optional[int] = None,
        embedded_color: bool = False,
        font_size: Optional[int] = None
    ) -> None:
        f = font or ImageFont.load_default()
        temp_img = Image.new('1', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.multiline_textbbox(
            (0, 0), text,
            font=f,
            spacing=spacing,
            align=align.value,
            direction=direction.value if direction else None,
            features=features,
            language=language,
            stroke_width=stroke_width,
            embedded_color=embedded_color,
            font_size=font_size
        )
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        super().__init__(x, y, w, h)
        self.text = text; self.font = f; self.fill = fill
        self.anchor = anchor; self.spacing = spacing; self.align = align
        self.direction = direction; self.features = features; self.language = language
        self.stroke_width = stroke_width; self.stroke_fill = stroke_fill
        self.embedded_color = embedded_color; self.font_size = font_size
    
    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)

        if self.get_dirty():
            self.width, self.height = self.get_text_size()
            # TODO: Remove this line - temp workaround
            # FIXME: This is a temporary workaround to ensure the height is tall enough - need to figure out exact reasoning for why height isn't always tall enough
            # Issue is clear in PendrvieReformatViewController.py when accessing the AlertViewController
            self.height += len(self.text.split('\n')) * self.spacing  # Add spacing for each line
            #print(f"TextView layout: {self.text} at ({self.abs_x}, {self.abs_y}) with size ({self.width}, {self.height})")
    
    def _render_self(self, draw: ImageDraw.ImageDraw) -> None:
        draw.multiline_text(
            (0, 0), self.text,
            fill=self.fill,
            font=self.font,
            anchor=None,
            spacing=self.spacing,
            align=self.align.value,
            direction=self.direction.value if self.direction else None,
            features=self.features,
            language=self.language,
            stroke_width=self.stroke_width,
            stroke_fill=self.stroke_fill,
            embedded_color=self.embedded_color
        )

    def get_text_bbox(self, draw: Optional[ImageDraw.ImageDraw] = None) -> Tuple[float, float, float, float]:
        """
        Returns the bounding box of the text.
        """
        # PIL does not support anchor for multiline text
        bbox = (draw or Display.DEF_DRAW).textbbox((0, 0), self.text,
                  font=self.font,
                  anchor=None,
                  spacing=self.spacing,
                  align=self.align.value,
                  direction=self.direction.value if self.direction else None,
                  features=self.features,
                  language=self.language,
                  stroke_width=self.stroke_width,
                  embedded_color=self.embedded_color)
        return (bbox[0], bbox[1],
                bbox[2], bbox[3])

    def get_abs_text_bbox(self, draw: Optional[ImageDraw.ImageDraw] = None) -> Tuple[float, float, float, float]:
        """
        Returns the bounding box of the text in absolute coordinates on the screen.
        """
        bbox = self.get_text_bbox(draw)
        return (self.abs_x + bbox[0], self.abs_y + bbox[1],
                self.abs_x + bbox[2], self.abs_y + bbox[3])

    def get_text_size(self, draw: Optional[ImageDraw.ImageDraw] = None) -> Tuple[float, float]:
        """
        Returns the size of the text.
        """
        bbox = self.get_text_bbox(draw)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        # Note: This is not the same as the width and height of the view
        # because the view may have padding or other decorations.
        # Use get_text_bbox() to get the actual bounding box of the text
        # in the view's coordinate space.