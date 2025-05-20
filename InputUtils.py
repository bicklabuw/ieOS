from enum import Enum, auto
class InputCode(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    BUTTON = auto()
    KEY1 = auto()
    KEY2 = auto()
    KEY3 = auto()

class InputPhase(Enum):
    PRESS = auto()
    HOLD = auto()
    RELEASE = auto()