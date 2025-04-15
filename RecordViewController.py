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
from MicTestViewController import MicTestView

from TimeUtils import get_duration_text

from USBDriveManager import is_pendrive_connected, create_recordings_dir

# Constants
MAX_FILE_RECORD_TIME = 3600 # 1 hr

error_view = TitleView()
mic_test_view = MicTestView()

class RecordViewController(ViewController):
    def __init__(self, rec_duration: int):
        self.rec_duration = rec_duration
        self.stop_recording = False

        self.view = ControlView()
        self.view.key2_text = "Stop"

        self.present_view(self.view)

    def start(self):
        self.stop_recording = False
        
        actual_time = self.rec_duration
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
                    while time.time() - start_time < duration and not self.stop_recording:
                        file.write(q.get())
            
            print("Done" + date_time)
            
        def count_down(cnt_time):
            '''
            cnt_time to count down from in seconds
            '''
            while cnt_time >= 0 and not self.stop_recording and threading.current_thread() is cnt_thread:
                time_str = "time left:\n" + get_duration_text(cnt_time)
                
                self.view.view_text = time_str
                # view_controller.redraw()
                
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

            if self.stop_recording:
                break
            
            actual_time -= duration
            rec_cnt += 1
            
            if duration > actual_time:
                duration = actual_time
        
        # If stopping don't wait for counter to get out of sleep (could take a minute)
        # Instead let it finish later - where it should just instantly stop
        cnt_thread.join(0.5 if self.stop_recording else None)

        # Show done and then present select view again
        self.view.key_controls_en = False
        self.view.view_text = "Stopped" if self.stop_recording else "Done!"
        # view_controller.redraw()
        
        time.sleep(1)
        
        self.view.key_controls_en = True
        self.pop_view_controller()

    def on_appear(self):
        # Check if Pendrive is connected (if not display error text and try again)
        while not is_pendrive_connected(PENDRIVE_MOUNT_POINT):
            error_view.text = "Pendrive not Found"
            self.present_view(error_view)
            # Delay before checking again
            time.sleep(1)

        create_recordings_dir()
        self.start()

    def on_key_2_press(self):
        self.view.view_text = "Stopping"
        self.view.key_controls_en = False

        self.stop_recording = True

    def on_disappear(self):
        # On disappear stop all threads
        self.stop_recording = True