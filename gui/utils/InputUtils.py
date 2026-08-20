from enum import Enum, auto
class InputCode(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    BUTTON = 4
    KEY1 = 5
    KEY2 = 6
    KEY3 = 7

class InputPhase(Enum):
    PRESS = 0
    HOLD = 1
    RELEASE = 2