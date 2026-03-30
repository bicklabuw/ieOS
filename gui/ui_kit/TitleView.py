from gui.ui_kit.ControlView import ControlView
import time

from PIL import ImageFont

class TitleView(ControlView):
    def __init__(self, text: str = "", font: ImageFont = ControlView.DEF_FONT):
        super().__init__(self, False, False, view_text = text, view_font = font)
    
    @property
    def text(self):
        return self.view_text
    
    @text.setter
    def text(self, text: str):
        self.view_text = text
        
    @property
    def font(self):
        return self.view_font
    
    @font.setter
    def font(self, font: ImageFont):
        self.view_font = font
    
def test():
    view = TitleView()
    view.draw()
    
    time.sleep(1)
    
    view.text = "HELLO WORLD!"
    view.draw()
    
if __name__ == "__main__":
    test()