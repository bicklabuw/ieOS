from View import View
from typing import Callable
import threading
import time

import Display

JOIN_TIMEOUT_TIME = 1

KEY_INIT_CHG_WAIT_TIME = 0.5
KEY_PRESSED_CHG_WAIT_TIME = 0.1

class ViewController:
    def __init__(self):
        self.active_view: View = None
        self.active_view_thread: threading.Thread = None
        self.present_view_queue: list[View] = []
        
    def present_view(self, view: View):
        # Check if current thread is active_view_thread then append to queue to wait for main thread to update the view
        if threading.current_thread() is self.active_view_thread:
            self.present_view_queue.append(view)
            return
        
        # Not run in separate thread because it should be ending all actions in the view
        if self.active_view is not None and self.active_view.on_disappear is not None:
            self.active_view.on_disappear()

        # TODO: Determine if error or just warning if active_view_thread is still running 
        # after on_disappear
        # Give thread enough time to join and then confirm active_view_thread is no longer running
        # so deactivated views are not running
        if self.active_view_thread is not None:
            self.active_view_thread.join(JOIN_TIMEOUT_TIME)

            if self.active_view_thread.is_alive():
                raise RuntimeError("Previous View Did Not Finish Running After on_disappear()")
        
        self.active_view = view
        view.draw()
        
        # Run in a separate thread because this allows the view to run something while the 
        # View Controller continues to monitor input
        if self.active_view.on_appear is not None:
            self.active_view_thread = threading.Thread(target=self.active_view.on_appear, args=())
            self.active_view_thread.start()
        else:
            self.active_view_thread = None
        
    def start_polling_input(self):
        if self.active_view is None:
            raise TypeError("Active View is None (No View Was Presented) - Input Cannot Be Processed")

        self.polling = True
        
        key_1_val = 0
        key_2_val = 0
        key_3_val = 0
        
        key_1_time = 0
        key_2_time = 0
        key_3_time = 0
        
        prev_key_1_val = 0
        prev_key_2_val = 0
        prev_key_3_val = 0
        
        joy_up_val = 0
        joy_down_val = 0
        joy_left_val = 0
        joy_right_val = 0
        joy_button_val = 0
        
        joy_up_time = 0
        joy_down_time = 0
        joy_left_time = 0
        joy_right_time = 0
        joy_button_time = 0
        
        prev_joy_up_val = 0
        prev_joy_down_val = 0
        prev_joy_left_val = 0
        prev_joy_right_val = 0
        prev_joy_button_val = 0
        
        disp = Display.disp
        
        while self.polling:
            time.sleep(0.05)

            if len(self.present_view_queue) > 0:
                self.present_view(self.present_view_queue.pop(0))

            view = self.active_view
            
            prev_key_1_val = key_1_val
            prev_key_2_val = key_2_val
            prev_key_3_val = key_3_val
            
            key_1_val = disp.RPI.digital_read(disp.RPI.GPIO_KEY1_PIN)
            key_2_val = disp.RPI.digital_read(disp.RPI.GPIO_KEY2_PIN)
            key_3_val = disp.RPI.digital_read(disp.RPI.GPIO_KEY3_PIN)
            
            prev_joy_up_val = joy_up_val
            prev_joy_down_val = joy_down_val
            prev_joy_left_val = joy_left_val
            prev_joy_right_val = joy_right_val
            prev_joy_button_val = joy_button_val
            
            joy_up_val = disp.RPI.digital_read(disp.RPI.GPIO_KEY_UP_PIN)
            joy_down_val = disp.RPI.digital_read(disp.RPI.GPIO_KEY_DOWN_PIN)
            joy_left_val = disp.RPI.digital_read(disp.RPI.GPIO_KEY_LEFT_PIN)
            joy_right_val = disp.RPI.digital_read(disp.RPI.GPIO_KEY_RIGHT_PIN)
            joy_button_val = disp.RPI.digital_read(disp.RPI.GPIO_KEY_PRESS_PIN)
            
            # Check is Key 1 Pressed
            if key_1_val == 1:
                print("KEY 1 PRESSED")
                key_1_time = self.__check_for_press_or_hold(prev_key_1_val, key_1_time, 
                    view.on_key_1_press, view.on_key_1_hold)
            elif key_2_val == 1:
                print("KEY 2 PRESSED")
                key_2_time = self.__check_for_press_or_hold(prev_key_2_val, key_2_time, 
                    view.on_key_2_press, view.on_key_2_hold)
            elif key_3_val == 1:
                print("KEY 3 PRESSED")
                key_3_time = self.__check_for_press_or_hold(prev_key_3_val, key_3_time, 
                    view.on_key_3_press, view.on_key_3_hold)
            elif joy_up_val == 1:
                print("JOYSTICK - UP")
                joy_up_time = self.__check_for_press_or_hold(prev_joy_up_val, joy_up_time, 
                    view.on_joy_up_press, view.on_joy_up_hold)
            elif joy_down_val == 1:
                print("JOYSTICK - DOWN")
                joy_down_time = self.__check_for_press_or_hold(prev_joy_down_val, joy_down_time, 
                    view.on_joy_down_press, view.on_joy_down_hold)
            elif joy_left_val == 1:
                print("JOYSTICK - LEFT")
                print(view.on_joy_left_press)
                joy_left_time = self.__check_for_press_or_hold(prev_joy_left_val, joy_left_time, 
                    view.on_joy_left_press, view.on_joy_left_hold)
            elif joy_right_val == 1:
                print("JOYSTICK - RIGHT")
                joy_right_time = self.__check_for_press_or_hold(prev_joy_right_val, joy_right_time, 
                    view.on_joy_right_press, view.on_joy_right_hold)
            elif joy_button_val == 1:
                print("JOYSTICK - BUTTON")
                joy_button_time = self.__check_for_press_or_hold(prev_joy_button_val, joy_button_time, 
                    view.on_joy_button_press, view.on_joy_button_hold)

    def redraw(self):
        self.active_view.draw()

    def stop_polling_input(self):
        self.polling = False

    def __check_for_press_or_hold(self, prev_val: bool, time_val: float, on_press: Callable[[], None], 
                                  on_hold: Callable[[], None]) -> float:
        # If not previously pressed - Call On Press
        if prev_val != 1:
            if on_press != None:
                on_press()

            # Update the time val by returning it's new value
            return time.time() + (KEY_INIT_CHG_WAIT_TIME - KEY_PRESSED_CHG_WAIT_TIME)
        elif on_hold != None: # Otherwise check for Hold
            time_diff = time.time() - time_val
            # If hold - Call Active View's On Joystick Button Hold
            if time_diff > KEY_PRESSED_CHG_WAIT_TIME:
                on_hold()
                return time.time() # Update time val by returning it's new value
        
        return time_val