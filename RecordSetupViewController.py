from ViewController import ViewController, ChangeViewControllerType
from MicTestViewController import MicTestViewController
from RecordViewController import RecordViewController
from TimeUtils import get_duration_text
from ControlView import ControlView

class RecordSetupViewController(ViewController):
    KEY_HOLD_INCR_LOW_AMT = 5 * 60 # 5 min
    KEY_HOLD_INCR_HIGH_AMT = 60 * 60 # 1 hr
    KEY_HOLD_LOW_HIGH_SEPARATOR = 120 * 60 # 2 hrs

    JOY_HOLD_INCR_LOW_AMT = 60 * 60 # 1 hr
    JOY_HOLD_INCR_HIGH_AMT = 24 * 60 * 60 # 1 day
    JOY_HOLD_LOW_HIGH_SEPARATOR = KEY_HOLD_LOW_HIGH_SEPARATOR # Keep them the same so it's not confusing

    BUTTON_CHG_AMT = 60 # 1 min
    JOY_CHG_AMT = 10 * 60 # 10 min

    DEF_DURATION = 10 * 60 # 10 min

    MIN_TIME = 60 # 1 min
    
    def __init__(self):
        super().__init__()

        self.view = SelectView()
        self._duration = self.DEF_DURATION

        self.present_view(self.view)
    
    def on_key_1_press(self):
        self._duration += self.BUTTON_CHG_AMT
        self.view.update_select_view(self._duration)

    def on_key_1_hold(self):
        self._duration += (self.KEY_HOLD_INCR_HIGH_AMT - (self._duration % self.KEY_HOLD_INCR_HIGH_AMT)
                            if self._duration > self.KEY_HOLD_LOW_HIGH_SEPARATOR
                            else self.KEY_HOLD_INCR_LOW_AMT - (self._duration % self.KEY_HOLD_INCR_LOW_AMT))
        self.view.update_select_view(self._duration)

    def on_key_2_press(self):
        self._duration -= self.BUTTON_CHG_AMT if self._duration >= self.MIN_TIME + self.BUTTON_CHG_AMT else self._duration - self.MIN_TIME
        self.view.update_select_view(self._duration)

    def on_key_2_hold(self):
        if self._duration > self.KEY_HOLD_LOW_HIGH_SEPARATOR:
            mod_val = self._duration % self.KEY_HOLD_INCR_HIGH_AMT
            self._duration -= mod_val if mod_val != 0 else self.KEY_HOLD_INCR_HIGH_AMT
        else:
            mod_val = self._duration % self.KEY_HOLD_INCR_LOW_AMT
            self._duration -= mod_val if mod_val != 0 else self.KEY_HOLD_INCR_LOW_AMT
        
        if self._duration < self.MIN_TIME:
            self._duration = self.MIN_TIME
        self.view.update_select_view(self._duration)

    def on_key_3_press(self):
        print("start")
        self.change_view_controller(RecordViewController(), ChangeViewControllerType.PUSH)
        #draw_text(f" Started for {self._duration}s")
        #view_controller.present_view(record_view)

    def on_joy_up_press(self):
        self._duration += self.JOY_CHG_AMT
        self.view.update_select_view(self._duration)

    def on_joy_up_hold(self):
        self._duration += (self.JOY_HOLD_INCR_HIGH_AMT - (self._duration % self.JOY_HOLD_INCR_HIGH_AMT)
                            if self._duration > self.JOY_HOLD_LOW_HIGH_SEPARATOR
                            else self.JOY_HOLD_INCR_LOW_AMT - (self._duration % self.JOY_HOLD_INCR_LOW_AMT))
        self.view.update_select_view(self._duration)

    def on_joy_down_press(self):
        self._duration -= self.JOY_CHG_AMT if self._duration >= self.MIN_TIME + self.JOY_CHG_AMT else self._duration - self.MIN_TIME
        self.view.update_select_view(self._duration)

    def on_joy_down_hold(self):
        if self._duration > self.JOY_HOLD_LOW_HIGH_SEPARATOR:
            mod_val = self._duration % self.JOY_HOLD_INCR_HIGH_AMT
            self._duration -= mod_val if mod_val != 0 else self.JOY_HOLD_INCR_HIGH_AMT

            if self._duration < self.JOY_HOLD_LOW_HIGH_SEPARATOR:
                self._duration = self.JOY_HOLD_LOW_HIGH_SEPARATOR
        else:
            mod_val = self._duration % self.JOY_HOLD_INCR_LOW_AMT
            self._duration -= mod_val if mod_val != 0 else self.JOY_HOLD_INCR_LOW_AMT
        
        if self._duration < self.MIN_TIME:
            self._duration = self.MIN_TIME
        self.view.update_select_view(self._duration)

    def on_joy_left_press(self):
        self.change_view_controller(MicTestViewController(), ChangeViewControllerType.PUSH)
        #self.change_view_controller(mic_test_view)

    def on_joy_button_press(self):
        self._duration = self.DEF_DURATION
        self.view.update_select_view(self._duration)
        pass

class SelectView(ControlView):
    def __init__(self, duration: int = RecordSetupViewController.DEF_DURATION):
        super().__init__()

        self.key1_text = "+"
        self.key2_text = "-"
        self.key3_text = "Go"
        self.up_text = "+10"
        self.down_text = "-10"
        self.left_text = "Mics"
        self.button_text = "RST"

        self.update_select_view(duration)

    def update_select_view(self, duration: int):
        self.view_text = f"Duration:\n{get_duration_text(duration)}"