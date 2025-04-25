import sounddevice as sd
import numpy as np
import queue
import threading
from ViewController import ViewController
from ControlView import ControlView

from typing import List, Union

from Components import RectangleComponent, TextComponent

class MicTestViewController(ViewController):
    def __init__(self):
        super().__init__()
        self.view = MicTestView()

        self._queues = [] # Queue to hold audio data for each microphone
        self.SCREEN_UPDATE_DELAY = 0.1 # Minimum Time between subsequent updates of the display
        self.BUFFER_SIZE = 750 # Size of the buffer to read from the InputStream
        self.THRESHOLD = 0.05 # Threshold for Tap

        self._stop = False

        self.present_view(self.view)

    def on_joy_right_press(self):
        self.pop_view_controller()

    def stop(self):
        self._stop = True

    def on_disappear(self):
        self.stop()

    def _audio_callback(self, indata, frames, time, status, index):
        if status:
            print(f"Status for mic {index}: {status}")
        self._queues[index].put(indata.copy())

    def _detect_spike(self, mic_index):
        while not self._stop:
            data = self._queues[mic_index].get()
            amplitude = np.max(np.abs(data))
            if amplitude > self.THRESHOLD:
                print("Mic " + str(mic_index) + ": " + str(amplitude))
                print(f"Spike detected in microphone {mic_index}")
                self.view.update_mic_tapped(mic_index)
            # Update the display with the current amplitude
            self.view.update_mic_amplitude(mic_index, amplitude)

    def on_appear(self):
        # Query all audio devices and initialize queues and streams
        devices = sd.query_devices()
        
        mic_ids = []
        self._mic_indices = []

        for i, d in enumerate(devices):
            name = d["name"]
            if d['max_input_channels'] > 0 and name.startswith("USB"):
                mic_ids.append(i)
                self._mic_indices.append(name[name.index("hw:")+3 : name.index(",")])
        
        self._queues = [queue.Queue() for _ in mic_ids]

        # List of InputStream objects
        streams = []
        for i in range(len(mic_ids)):
            index = mic_ids[i]

            stream = sd.InputStream(
                device=index,
                channels=1,  # Assuming each mic is mono
                callback=lambda indata, frames, time, status, index=i: self._audio_callback(indata, frames, time, status, index),
                blocksize=self.BUFFER_SIZE
            )
            streams.append(stream)

        # Start all InputStreams
        for stream in streams:
            stream.start()

        # Set stop to false
        self._stop = False

        # Set last tapped id to None
        self.view.update_mic_tapped(None)

        # Start spike detection threads
        threads = []
        for index in range(len(mic_ids)):
            thread = threading.Thread(target=self._detect_spike, args=(index,))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Wait until stopped
        for i in mic_ids:
            threads[i].join()
            streams[i].close()

class MicTestView(ControlView):
    DEF_BAR_WIDTH = 5
    DEF_BAR_ID_SPACE = 3
    
    def __init__(self, mic_indices: List[int], bar_width: int = DEF_BAR_WIDTH, bar_id_space: int = DEF_BAR_ID_SPACE):
        super().__init__(uses_keys_inp=False, right_text="Back")
        self._num_mics = len(mic_indices)
        self._mic_indices = mic_indices
        self._mic_components = [RectangleComponent(0,0,0,0) for _ in self._mic_indices]

        self.CHAR_WIDTH, self.CHAR_HEIGHT = TextComponent.get_text_size_of("0", spacing=self.LINE_SPACING)

        self._mic_name_components = [TextComponent(((idx + 0.5) * self._width / self._num_mics) + self._start_x - (self.CHAR_HEIGHT / 2),
                                                  self.SCREEN_HEIGHT - self.CHAR_WIDTH,str(idx)) for idx in self._mic_indices]
        self._mic_tapped_component = TextComponent(0, 0, "")
        
        self.bar_width = bar_width # Width of each mic bar on the screen
        self.bar_id_space = bar_id_space # Vertical Space (in pixels) between the Audio Bar and the ID Text

        self.add_components(self._mic_name_components)
        self.add_components(self._mic_components)
        self.add_component(self._mic_tapped_component)

        # Draw controls on image and get the view's frame (x, width)
        self._draw_controls_and_get_frame()

    def update_mic_tapped(self, mic_index: Union[int, None]):
        if mic_index is not None:
            tapped_text = "Mic Tapped: " + str(self._mic_indices[mic_index])
            tapped_text_width = self._get_text_width(tapped_text)
            self._mic_tapped_component.text = tapped_text
            self._mic_tapped_component.set_coordinate(((self._width - tapped_text_width) / 2) + self._start_x, 0)
        else:
            self._mic_tapped_component.text = ""
            self._mic_tapped_component.set_coordinate(0, 0)

    def update_mic_amplitude(self, mic_index, amplitude):
        rect_y = self.SCREEN_HEIGHT - self.CHAR_HEIGHT - self.bar_id_space
        rect_max_height = rect_y - self.CHAR_HEIGHT
        rect_start_x = ((mic_index + 0.5) * self._width / self._num_mics) - (self.bar_width / 2) + self._start_x
        self._mic_components[mic_index].set_rect(rect_start_x, rect_y - int(amplitude*rect_max_height), rect_start_x + self.bar_width, rect_y)

    def _draw_controls_and_get_frame(self):
        # Draw controls on image (and get our View's start and end x as well as width)
        self._start_x, self._end_x = self.draw_controls_on_image(self.__draw)
        self._width = self._end_x - self._start_x

    