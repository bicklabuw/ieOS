from Views import TextView, TextAnchor, TextAlignment
from PIL import ImageFont
from typing import Optional

class CenteredXLabel(TextView):
    def __init__(
        self,
        y: float,
        text: str,
        font: Optional[ImageFont.ImageFont] = None
    ) -> None:
        # choose font and measure text size
        super().__init__(0, y, font=font or ImageFont.load_default(), text=text, anchor=TextAnchor.LEFT_TOP, align=TextAlignment.CENTER)
        self.selectable = False  # Labels are not selectable by default

    def _layout(self, parent_abs_x=0, parent_abs_y=0):
        super()._layout(parent_abs_x, parent_abs_y)
        self.x = (self.superview.width - self.width) / 2

class CenteredYLabel(TextView):
    def __init__(
        self,
        x: float,
        text: str,
        font: Optional[ImageFont.ImageFont] = None
    ) -> None:
        # choose font and measure text size
        super().__init__(x, 0, font=font or ImageFont.load_default(), text=text, anchor=TextAnchor.LEFT_TOP, align=TextAlignment.CENTER)
        self.selectable = False  # Labels are not selectable by default

    def _layout(self, parent_abs_x=0, parent_abs_y=0):
        super()._layout(parent_abs_x, parent_abs_y)
        self.y = (self.superview.height - self.width) / 2

class CenteredLabel(TextView):
    def __init__(
        self,
        text: str,
        font: Optional[ImageFont.ImageFont] = None
    ) -> None:
        # choose font and measure text size
        super().__init__(0, 0, font=font or ImageFont.load_default(), text=text, anchor=TextAnchor.LEFT_TOP, align=TextAlignment.CENTER)
        self.selectable = False  # Labels are not selectable by default

    def _layout(self, parent_abs_x=0, parent_abs_y=0):
        super()._layout(parent_abs_x, parent_abs_y)
        self.x = (self.superview.width - self.width) / 2
        self.y = (self.superview.height - self.height) / 2

class Label(TextView):
    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        font: Optional[ImageFont.ImageFont] = None,
        text_allign: TextAlignment = TextAlignment.LEFT
    ) -> None:
        # choose font and measure text size
        print("TextAnchor:", TextAnchor.LEFT_TOP.to_pillow())
        super().__init__(x, y, font=font or ImageFont.load_default(), text=text, anchor=TextAnchor.LEFT_TOP, align=text_allign)
        self.selectable = False  # Labels are not selectable by default

    # @property
    # def text(self) -> str:
    #     return self._text

    # @text.setter
    # def text(self, new_text: str) -> None:
    #     self._text = new_text
    #     bbox = self.font.getbbox(new_text)
    #     self.width = bbox[2] - bbox[0]
    #     self.height = bbox[3] - bbox[1]

    # def _render_self(self, draw) -> None:
    #     print("Drawing Label")
    #     print("Label text:", self._text)
    #     print("Label font:", self.font)
    #     print("Label size:", self.width, self.height)
    #     print("Label position:", self.abs_x, self.abs_y)
    #     draw.text((0, 0), self._text, font=self.font, fill=0)