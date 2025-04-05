from OSGlobals import get_polling, set_polling
from OSGlobals import get_current_view_controller
from OSGlobals import KEY_INIT_CHG_WAIT_TIME, KEY_PRESSED_CHG_WAIT_TIME
import time
import Display
from typing import Callable, Tuple

def polling_thread(sleep_time: float):
    # if self.active_view is None:
    #     raise TypeError("Active View is None (No View Was Presented) - Input Cannot Be Processed")

    set_polling()
    
    key_1_val = 0
    key_2_val = 0
    key_3_val = 0
    
    key_1_time = 0
    key_2_time = 0
    key_3_time = 0

    key_1_held = False
    key_2_held = False
    key_3_held = False
    
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

    joy_up_held = False
    joy_down_held = False
    joy_left_held = False
    joy_right_held = False
    joy_button_held = False
    
    prev_joy_up_val = 0
    prev_joy_down_val = 0
    prev_joy_left_val = 0
    prev_joy_right_val = 0
    prev_joy_button_val = 0
    
    disp = Display.disp
    
    while get_polling():
        time.sleep(sleep_time)

        vc = get_current_view_controller()
        
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
            key_1_time, ran_on_held = _check_for_press_or_hold(prev_key_1_val, key_1_time, 
                vc.on_key_1_press, vc.on_key_1_hold)
            # If it ran on_hold, set the key_1_held to true othwise keep it the same
            # On hold isn't always called (even on a hold) between times it calls it
            key_1_held |= ran_on_held
        # Check if Key 2 Pressed
        if key_2_val == 1:
            print("KEY 2 PRESSED")
            key_2_time, ran_on_hold = _check_for_press_or_hold(prev_key_2_val, key_2_time, 
                vc.on_key_2_press, vc.on_key_2_hold)
            # If it ran on_hold, set the key_2_held to true othwise keep it the same
            # On hold isn't always called (even on a hold) between times it calls it
            key_2_held |= ran_on_hold
        # Check if Key 3 Pressed
        if key_3_val == 1:
            print("KEY 3 PRESSED")
            key_3_time, ran_on_hold = _check_for_press_or_hold(prev_key_3_val, key_3_time, 
                vc.on_key_3_press, vc.on_key_3_hold)
            # If it ran on_hold, set the key_3_held to true othwise keep it the same
            # On hold isn't always called (even on a hold) between times it calls it
            key_3_held |= ran_on_hold
        # Check if Joystick Up Pressed
        if joy_up_val == 1:
            print("JOYSTICK - UP")
            joy_up_time, ran_on_hold = _check_for_press_or_hold(prev_joy_up_val, joy_up_time, 
                vc.on_joy_up_press, vc.on_joy_up_hold)
            # If it ran on_hold, set the joy_up_held to true othwise keep it the same
            # On hold isn't always called (even on a hold) between times it calls it
            joy_up_held |= ran_on_hold
        # Check if Joystick Down Pressed
        if joy_down_val == 1:
            print("JOYSTICK - DOWN")
            joy_down_time, ran_on_hold = _check_for_press_or_hold(prev_joy_down_val, joy_down_time, 
                vc.on_joy_down_press, vc.on_joy_down_hold)
            # If it ran on_hold, set the joy_down_held to true othwise keep it the same
            # On hold isn't always called (even on a hold) between times it calls it
            joy_down_held |= ran_on_hold
        # Check if Joystick Left Pressed
        if joy_left_val == 1:
            print("JOYSTICK - LEFT")
            print(vc.on_joy_left_press)
            joy_left_time, ran_on_hold = _check_for_press_or_hold(prev_joy_left_val, joy_left_time, 
                vc.on_joy_left_press, vc.on_joy_left_hold)
            # If it ran on_hold, set the joy_left_held to true othwise keep it the same
            # On hold isn't always called (even on a hold) between times it calls it
            joy_left_held |= ran_on_hold
        # Check if Joystick Right Pressed
        if joy_right_val == 1:
            print("JOYSTICK - RIGHT")
            joy_right_time, ran_on_hold = _check_for_press_or_hold(prev_joy_right_val, joy_right_time, 
                vc.on_joy_right_press, vc.on_joy_right_hold)
            # If it ran on_hold, set the joy_right_held to true othwise keep it the same
            # On hold isn't always called (even on a hold) between times it calls it
            joy_right_held |= ran_on_hold
            
        # Check if Joystick Button Pressed
        if joy_button_val == 1:
            print("JOYSTICK - BUTTON")
            joy_button_time, ran_on_hold = _check_for_press_or_hold(prev_joy_button_val, joy_button_time, 
                vc.on_joy_button_press, vc.on_joy_button_hold)
            # If it ran on_hold, set the key_1_held to true othwise keep it the same
            # On hold isn't always called (even on a hold) between times it calls it
            joy_button_held |= ran_on_hold
            
        # Check if Key 1 Released
        if prev_key_1_val == 1 and key_1_val == 0:
            print("KEY 1 RELEASED")
            vc.on_key_1_release(key_1_held)
            key_1_held = False
        # Check if Key 2 Released
        if prev_key_2_val == 1 and key_2_val == 0:
            print("KEY 2 RELEASED")
            vc.on_key_2_release(key_2_held)
            key_2_held = False
        # Check if Key 3 Released
        if prev_key_3_val == 1 and key_3_val == 0:
            print("KEY 3 RELEASED")
            vc.on_key_3_release(key_3_held)
            key_3_held = False
        # Check if Joystick Up Released
        if prev_joy_up_val == 1 and joy_up_val == 0:
            print("JOYSTICK - UP RELEASED")
            vc.on_joy_up_release(joy_up_held)
            joy_up_held = False
        # Check if Joystick Down Released
        if prev_joy_down_val == 1 and joy_down_val == 0:
            print("JOYSTICK - DOWN RELEASED")
            vc.on_joy_down_release(joy_down_held)
            joy_down_held = False
        # Check if Joystick Left Released
        if prev_joy_left_val == 1 and joy_left_val == 0:
            print("JOYSTICK - LEFT RELEASED")
            vc.on_joy_left_release(joy_left_held)
            joy_left_held = False
        # Check if Joystick Right Released
        if prev_joy_right_val == 1 and joy_right_val == 0:
            print("JOYSTICK - RIGHT RELEASED")
            vc.on_joy_right_release(joy_right_held)
            joy_right_held = False
        # Check if Joystick Button Released
        if prev_joy_button_val == 1 and joy_button_val == 0:
            print("JOYSTICK - BUTTON RELEASED")
            vc.on_joy_button_release(joy_button_held)
            joy_button_held = False

def _check_for_press_or_hold(prev_val: bool, time_val: float, on_press: Callable[[], None], 
                                on_hold: Callable[[], None]) -> Tuple[float, bool]:
    # Returns the time value to be used for the next check, and a bool for if it triggered on_hold

    # If not previously pressed - Call On Press
    if prev_val != 1:
        on_press()

        # Update the time val by returning it's new value
        return (time.time() + (KEY_INIT_CHG_WAIT_TIME - KEY_PRESSED_CHG_WAIT_TIME), False)
    else: # Otherwise check for Hold
        time_diff = time.time() - time_val
        # If hold - Call Active View's On Joystick Button Hold
        if time_diff > KEY_PRESSED_CHG_WAIT_TIME:
            on_hold()
            return (time.time(), True) # Update time val by returning it's new value
    
    return (time_val, False)