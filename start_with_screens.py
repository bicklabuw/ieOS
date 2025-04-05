import sounddevice as sd
import threading
import soundfile as sf
from datetime import datetime
import time
# import numpy  # Make sure NumPy is loaded before it is used in the callback
# assert numpy  #
import queue
import sys
import os
import Display

from ViewController import ViewController

from TitleView import TitleView
from ControlView import ControlView
from MicTestView import MicTestView

# Constants
PENDRIVE_MOUNT_POINT = "/mnt/usb0"
PENDRIVE_RECORDINGS_DIR = "/WAV"
PENDRIVE_RECORDINGS_PATH = PENDRIVE_MOUNT_POINT + PENDRIVE_RECORDINGS_DIR

MAX_FILE_RECORD_TIME = 3600 # 1 hr

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

view_controller = ViewController()

title_view = TitleView()
error_view = TitleView()
select_view = ControlView()
connection_view = ControlView()
mic_test_view = MicTestView()
record_view = ControlView()

selected_duration = DEF_DURATION

stop_recording = False

upload_allowed = False
upload_inited = False
upload_files = False

try:
    import AudioUpload
    from AudioUpload import AudioType 

    AUDIO_TYPE = AudioType.wav
except:
    upload_allowed = False

def init():
    # Draw Init Text
    title_view.text = "Insect Eavesdropper"
    view_controller.present_view(title_view)
    
    time.sleep(1)

    if (os.path.isdir(PENDRIVE_MOUNT_POINT) and not os.path.isdir(PENDRIVE_RECORDINGS_PATH)):
        os.makedirs(PENDRIVE_RECORDINGS_PATH)
    
    # Check if Pendrive is connected (if not display error text and try again)
    err_cnt = 0
    while (is_pendrive_connected(PENDRIVE_MOUNT_POINT) == False):
        err_str = "" if err_cnt == 0 else " (" + (err_cnt + 1) + ")"
        error_view.text = "Pendrive not found" + err_str
        view_controller.present_view(error_view)
        # Delay before checking again
        time.sleep(1)

def is_pendrive_connected(mount_point):
    return os.path.isdir(mount_point)

def start(actual_time):
    global record_view
    global select_view
    global stop_recording

    stop_recording = False
    
    duration = actual_time
    if(actual_time > MAX_FILE_RECORD_TIME):
        duration = MAX_FILE_RECORD_TIME

    now = datetime.now()
    date_time = now.strftime("_%m_%d_%Y_%H_%M_%S")

    file_name = "Pi1"+date_time
    file_paths_to_upload = []
    #setduration of each rec in seconds, each file will be this duration
    ##SAve
    ##SAve
    # define the number of channels and sample rate for the audio recording
    
    num_channels = 1
    sample_rate = 44100
    devices = sd.query_devices()
    print(devices)
    mic_indices = []
    mic_ids = []
    for i in devices:
        name = i["name"]
        if i['max_input_channels'] > 0 and name.startswith("USB"):
            mic_ids.append(i['index'])
            mic_indices.append(name[name.index("hw:")+3 : name.index(",")])
     
    print("IDs:")
    print(mic_ids)
    print("Indices: ")
    print(mic_indices)
        
    # start recording audio from the selected microphones
    def record(id,index,rectime,q):
        global PENDRIVE_RECORDINGS_PATH
        def callback(indata, frames, time, status):
            if status:
                print(frames)
                print("ERROR: ")
                print(status, file=sys.stderr)
            q.put(indata.copy())
 #   sd.wait()
    #setfilename
        file_path = f"{PENDRIVE_RECORDINGS_PATH}/{file_name}mic{index}hour{rectime}.wav" #+ AUDIO_TYPE.name  # name the file based on the microphone number
 #   sf.write(file_name, recording, sample_rate)
#    gc.collect()
        with sf.SoundFile(file_path, mode='x', samplerate=sample_rate,
                      channels=num_channels, subtype='PCM_24') as file:
            file_paths_to_upload.append(file_path)
            with sd.InputStream(samplerate=sample_rate, blocksize=750, device=id,
                            channels=num_channels, callback=callback):
                start_time = time.time()
                while time.time() - start_time < duration and not stop_recording:
                    file.write(q.get())
        
        print("Done" + date_time)
        
    def count_down(cnt_time):
        '''
        cnt_time to count down from in seconds
        '''
        while cnt_time >= 0 and not stop_recording and threading.current_thread() is cnt_thread:
            time_str = "time left:\n" + get_duration_text(cnt_time)
            
            record_view.view_text = time_str
            view_controller.redraw()
            
            #print(f"{mins % 60}" if mins > 0 else "")
            #print(f"Mins: {mins}")
            #print(f"Secs: {secs}")
            #print(time_str)
            
            if cnt_time == 0:
                return
            elif cnt_time <= 60:
                time.sleep(1)
                cnt_time -= 1
            else:
                time.sleep(60)
                cnt_time -= 60
        
            print("HI - WE'RE DONE")
            print(threading.current_thread())
            print("CNT TIME: " + str(cnt_time))

    rec_cnt = 0
    
    # Add count down thread
    cnt_thread = threading.Thread(target=count_down, args=[actual_time])
    cnt_thread.start()
    while actual_time > 0:
        mic_threads = []
        for i in range(len(mic_ids)):
            q = queue.Queue()
            t = threading.Thread(target=record,args=[mic_ids[i],mic_indices[i],rec_cnt,q])
            mic_threads.append(t)
        
        # wait for the recording to finish
        print(len(mic_threads))
        for i in mic_threads:
            i.start()
            
        for i in mic_threads:
            i.join()

        if stop_recording:
            break
        
        actual_time -= duration
        rec_cnt += 1
        
        if duration > actual_time:
            duration = actual_time
    
    # If stopping don't wait for counter to get out of sleep (could take a minute)
    # Instead let it finish later - where it should just instantly stop
    cnt_thread.join(0.5 if stop_recording else None)
    
    # Upload Files
    if upload_allowed and upload_inited and upload_files and not stop_recording:
        for path in file_paths_to_upload:
            AudioUpload.upload(path, AUDIO_TYPE)

    # Show done and then present select view again
    record_view.key_controls_en = False
    record_view.view_text = "Stopped" if stop_recording else "Done!"
    view_controller.redraw()
    
    time.sleep(1)
    
    record_view.key_controls_en = True
    view_controller.present_view(select_view)

def get_duration_text(duration):
    secs = duration
    mins = secs // 60
    hours = mins // 60
    days = hours // 24
    
    time_str = f"{days}d " if days > 0 else ""
    time_str += f"{(hours % 24)}h " if hours > 0 else ""
    time_str += f"{mins % 60}m " if mins > 0 else ""
    time_str += f"{secs % 60}s " if mins == 0 else ""
    
    return time_str

def update_select_view(duration: int, redraw: bool = True):
    global select_view
    
    select_view.view_text = f"Duration:\n{get_duration_text(duration)}"

    # Assumes View Controller Active View is Select View
    if redraw:
        view_controller.redraw()
    
def update_connection_view(redraw: bool = True):
    global upload_files
    global upload_allowed
    global upload_inited
    global connection_view
    
    on_str = "On"
    off_str = "Off"
    
    if upload_allowed:
        if upload_inited:
            upload_str = "Upload: " + (on_str if upload_files else off_str)
            connection_view.key2_text = off_str if upload_files else on_str
        else:
            upload_str = "Upload Setup Failed"
            connection_view.key2_text = "Retry"
    else:
        upload_str = "Upload Not Allowed or Not Implemented"
    # Update text for current state and show inactive option for key help text
    connection_view.view_text = upload_str

    # Assumes View Controller Active View is Connection View
    if redraw:
        view_controller.redraw()
    
    print(upload_str)

def sel_on_key_1_press():
    global selected_duration
    selected_duration += BUTTON_CHG_AMT
    update_select_view(selected_duration)

def sel_on_key_1_hold():
    global selected_duration
    selected_duration += (KEY_HOLD_INCR_HIGH_AMT - (selected_duration % KEY_HOLD_INCR_HIGH_AMT)
                        if selected_duration > KEY_HOLD_LOW_HIGH_SEPARATOR
                        else KEY_HOLD_INCR_LOW_AMT - (selected_duration % KEY_HOLD_INCR_LOW_AMT))
    update_select_view(selected_duration)

def sel_on_key_2_press():
    global selected_duration
    selected_duration -= BUTTON_CHG_AMT if selected_duration >= MIN_TIME + BUTTON_CHG_AMT else selected_duration - MIN_TIME
    update_select_view(selected_duration)

def sel_on_key_2_hold():
    global selected_duration
    if selected_duration > KEY_HOLD_LOW_HIGH_SEPARATOR:
        mod_val = selected_duration % KEY_HOLD_INCR_HIGH_AMT
        selected_duration -= mod_val if mod_val != 0 else KEY_HOLD_INCR_HIGH_AMT
    else:
        mod_val = selected_duration % KEY_HOLD_INCR_LOW_AMT
        selected_duration -= mod_val if mod_val != 0 else KEY_HOLD_INCR_LOW_AMT
    
    if selected_duration < MIN_TIME:
        selected_duration = MIN_TIME
    update_select_view(selected_duration)

def sel_on_key_3_press():
    global record_view
    print("start")
    #draw_text(f" Started for {selected_duration}s")
    view_controller.present_view(record_view)

def sel_on_joy_up_press():
    global selected_duration
    selected_duration += JOY_CHG_AMT
    update_select_view(selected_duration)

def sel_on_joy_up_hold():
    global selected_duration
    selected_duration += (JOY_HOLD_INCR_HIGH_AMT - (selected_duration % JOY_HOLD_INCR_HIGH_AMT)
                        if selected_duration > JOY_HOLD_LOW_HIGH_SEPARATOR
                        else JOY_HOLD_INCR_LOW_AMT - (selected_duration % JOY_HOLD_INCR_LOW_AMT))
    update_select_view(selected_duration)

def sel_on_joy_down_press():
    global selected_duration
    selected_duration -= JOY_CHG_AMT if selected_duration >= MIN_TIME + JOY_CHG_AMT else selected_duration - MIN_TIME
    update_select_view(selected_duration)

def sel_on_joy_down_hold():
    global selected_duration
    if selected_duration > JOY_HOLD_LOW_HIGH_SEPARATOR:
        mod_val = selected_duration % JOY_HOLD_INCR_HIGH_AMT
        selected_duration -= mod_val if mod_val != 0 else JOY_HOLD_INCR_HIGH_AMT

        if selected_duration < JOY_HOLD_LOW_HIGH_SEPARATOR:
            selected_duration = JOY_HOLD_LOW_HIGH_SEPARATOR
    else:
        mod_val = selected_duration % JOY_HOLD_INCR_LOW_AMT
        selected_duration -= mod_val if mod_val != 0 else JOY_HOLD_INCR_LOW_AMT
    
    if selected_duration < MIN_TIME:
        selected_duration = MIN_TIME
    update_select_view(selected_duration)

def sel_on_joy_left_press():
    global mic_test_view
    view_controller.present_view(mic_test_view)

def sel_on_joy_right_press():
    global connection_view
    update_connection_view(False)
    print(connection_view.on_joy_left_press)
    view_controller.present_view(connection_view)

def sel_on_joy_button_press():
    global selected_duration
    selected_duration = DEF_DURATION
    update_select_view(selected_duration)

def conn_on_key_2_press():
    global upload_files
    global upload_inited
    global upload_allowed

    if upload_allowed:
        if upload_inited:
            upload_files = not upload_files
        else:
            try:
                AudioUpload.init()
                upload_inited = True
            except:
                upload_inited = False
        update_connection_view()

def conn_on_joy_left_press():
    global select_view
    print("PRESENTING")
    view_controller.present_view(select_view)

def mic_test_on_joy_right_press():
    global select_view
    view_controller.present_view(select_view)

def rec_on_appear():
    global selected_duration
    start(selected_duration)

def rec_on_key_2_press():
    global record_view
    global stop_recording

    record_view.view_text = "Stopping"
    record_view.key_controls_en = False
    view_controller.redraw()

    stop_recording = True

def rec_on_disappear():
    # On disappear stop all threads
    stop_recording = True

def main():
    global state
    global upload_inited
    global upload_allowed
    global select_view
    global connection_view
    global selected_duration
    global record_view
    
    init()
    
    if upload_allowed:
        try:
            AudioUpload.init()
            upload_inited = True
        except:
            upload_inited = False

        select_view.right_text = "Wifi"#"Upload"
        select_view.on_joy_right_press = sel_on_joy_right_press
    
    select_view.up_text = "+10"
    select_view.down_text = "-10"
    select_view.left_text = "Mics"
    select_view.button_text = "RST"
    
    select_view.key1_text = "+"
    select_view.key2_text = "-"
    select_view.key3_text = "Go"

    connection_view.left_text = "Back"

    record_view.key2_text = "Stop"

    select_view.on_key_1_press = sel_on_key_1_press
    select_view.on_key_1_hold = sel_on_key_1_hold
    select_view.on_key_2_press = sel_on_key_2_press
    select_view.on_key_2_hold = sel_on_key_2_hold
    select_view.on_key_3_press = sel_on_key_3_press

    select_view.on_joy_up_press = sel_on_joy_up_press
    select_view.on_joy_up_hold = sel_on_joy_up_hold
    select_view.on_joy_down_press = sel_on_joy_down_press
    select_view.on_joy_down_hold = sel_on_joy_down_hold
    select_view.on_joy_left_press = sel_on_joy_left_press
    select_view.on_joy_button_press = sel_on_joy_button_press

    connection_view.on_key_2_press = conn_on_key_2_press
    connection_view.on_joy_left_press = conn_on_joy_left_press

    mic_test_view.on_joy_right_press = mic_test_on_joy_right_press
    mic_test_view.on_appear = mic_test_view.run

    record_view.on_appear = rec_on_appear
    record_view.on_key_2_press = rec_on_key_2_press
    record_view.on_disappear = rec_on_disappear

    update_select_view(selected_duration, False)
    view_controller.present_view(select_view)

    try:
        view_controller.start_polling_input()
    except IOError as e:
        print(e)
        error_view.text = "Failed - IOError"
        view_controller.present_view(error_view)
        raise e
        
    except KeyboardInterrupt:    
        print("ctrl + c:")
        Display.disp.RPI.module_exit()
        exit()
    
    
if __name__ == "__main__":
    main()
