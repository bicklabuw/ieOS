import sounddevice as sd
import numpy as np
import queue
import threading
from PIL import Image, ImageDraw
from ControlView import ControlView
import time
import Display

class MicTestView(ControlView):
    def __init__(self):
        super().__init__(uses_keys_inp=False, right_text="Back")
        
        self.__queues = [] # Queue to hold audio data for each microphone
        self.SCREEN_UPDATE_DELAY = 0.1 # Minimum Time between subsequent updates of the display
        self.BUFFER_SIZE = 750 # Size of the buffer to read from the InputStream
        self.THRESHOLD = 0.05 # Threshold for Tap
        self.BAR_WIDTH = 5 # Width of each mic bar on the screen
        self.BAR_ID_SPACE = 3 # Vertical Space (in pixels) between the Audio Bar and the ID Text

        self.__stop = False
        self.__draw_lock = threading.Lock()

        self.__last_draw_time = time.time() - self.SCREEN_UPDATE_DELAY
        self.__last_tapped_id = None

        # Reset the image
        self.__reset_image()

        # Draw controls on image and get the view's frame (x, width)
        self.__draw_controls_and_get_frame()

        # On Disappear stop all threads
        self.on_disappear = self.__on_disappear

    def __audio_callback(self, indata, frames, time, status, index):
        if status:
            print(f"Status for mic {index}: {status}")
        self.__queues[index].put(indata.copy())

    def __detect_spike(self, mic_index):
        while not self.__stop:
            data = self.__queues[mic_index].get()
            amplitude = np.max(np.abs(data))
            if amplitude > self.THRESHOLD:
                print("Mic " + str(mic_index) + ": " + str(amplitude))
                print(f"Spike detected in microphone {mic_index}")
                self.__last_tapped_id = mic_index
            # Update the display with the current amplitude
            self.__update_display(mic_index, amplitude)

    def __update_display(self, mic_index, amplitude):
        num_mics = len(self.__queues)

        rect_y = self.SCREEN_HEIGHT - self.CHAR_HEIGHT - self.BAR_ID_SPACE
        rect_max_height = rect_y - self.CHAR_HEIGHT
        rect_start_x = ((mic_index + 0.5) * self.__width / num_mics) - (self.BAR_WIDTH / 2) + self.__start_x
        self.__draw.rectangle([rect_start_x, rect_y, rect_start_x + self.BAR_WIDTH, rect_y - int(amplitude*rect_max_height)], fill=0)

        with self.__draw_lock:
            if time.time() - self.__last_draw_time >= self.SCREEN_UPDATE_DELAY:
                self.draw()
            

    def draw(self):
        num_mics = len(self.__queues)
        for i in range(num_mics):
            id_x = ((i + 0.5) * self.__width / num_mics) + self.__start_x - (self.CHAR_WIDTH / 2)
            self.__draw.text((id_x, self.SCREEN_HEIGHT - self.CHAR_HEIGHT), str(self.__mic_indices[i]), fill=0)

        if self.__last_tapped_id != None:
            tapped_text = "Mic Tapped: " + str(self.__last_tapped_id)
            tapped_text_width = self._get_text_width(tapped_text)
            self.__draw.text((((self.__width - tapped_text_width) / 2) + self.__start_x, 0), tapped_text, fill=0)
        
        Display.disp.ShowImage(Display.disp.getbuffer(self.__image))

        self.__last_draw_time = time.time()

        self.__reset_image()
        self.__draw_controls_and_get_frame()

    def __reset_image(self):
        self.__image = Image.new('1', (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), self.TEXT_COLOR)
        # Get drawing object to draw on image.
        self.__draw = ImageDraw.Draw(self.__image)

    def __draw_controls_and_get_frame(self):
        # Draw controls on image (and get our View's start and end x as well as width)
        self.__start_x, self.__end_x = self.draw_controls_on_image(self.__draw)
        self.__width = self.__end_x - self.__start_x

    def run(self):
        # Query all audio devices and initialize queues and streams
        devices = sd.query_devices()
        
        mic_ids = []
        self.__mic_indices = []

        for i, d in enumerate(devices):
            name = d["name"]
            if d['max_input_channels'] > 0 and name.startswith("USB"):
                mic_ids.append(i)
                self.__mic_indices.append(name[name.index("hw:")+3 : name.index(",")])
        
        self.__queues = [queue.Queue() for _ in mic_ids]

        # List of InputStream objects
        streams = []
        for index in mic_ids:
            stream = sd.InputStream(
                device=index,
                channels=1,  # Assuming each mic is mono
                callback=lambda indata, frames, time, status, index=index: self.__audio_callback(indata, frames, time, status, index),
                blocksize=self.BUFFER_SIZE
            )
            streams.append(stream)

        # Start all InputStreams
        for stream in streams:
            stream.start()

        # Set stop to false
        self.__stop = False

        # Set last tapped id to None
        self.__last_tapped_id = None

        # Start spike detection threads
        threads = []
        for index in mic_ids:
            thread = threading.Thread(target=self.__detect_spike, args=(index,))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Wait until stopped
        for i in mic_ids:
            threads[i].join()
            streams[i].close()

    def stop(self):
        self.__stop = True

    def __on_disappear(self):
        self.stop()
        self.__last_tapped_id = None