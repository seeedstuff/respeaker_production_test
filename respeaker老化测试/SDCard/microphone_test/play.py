"""
 ReSpeaker Python Library
 Copyright (c) 2016 Seeed Technology Limited.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import threading
import time
import wave
import os
import pyaudio

CHUNK_SIZE = 1024 * 2


class GPIO:
    def __init__(self, pin, output=False):
        self.pin = pin
        if not os.path.isfile('/sys/class/gpio/gpio{}/value'.format(self.pin)):
            os.system('echo {} > /sys/class/gpio/export'.format(self.pin))
            
        self.set_direction(output)
        
    def close(self):
        os.system('echo {} > /sys/class/gpio/unexport'.format(self.pin))
        
    def set_direction(self, output):
        direction = 'out' if output else 'in'
        os.system('echo {} > /sys/class/gpio/gpio{}/direction'.format(direction, self.pin))
        
    def write(self, level):
        level = 1 if level else 0
        os.system('echo {} > /sys/class/gpio/gpio{}/value'.format(level, self.pin))

    def read(self):
        out = os.popen('cat /sys/class/gpio/gpio{}/value'.format(self.pin))
        return out.read()

class Player():
    def __init__(self, pyaudio_instance=None, device=None):
        self.pyaudio_instance = pyaudio_instance if pyaudio_instance else pyaudio.PyAudio()
        self.event = threading.Event()
        # self.stream = self.pa.open(format=pyaudio.paInt16,
        #                            channels=1,
        #                            rate=16000,
        #                            output=True,
        #                            start=False,
        #                            # output_device_index=1,
        #                            frames_per_buffer=CHUNK_SIZE,
        #                            stream_callback=self.callback)
        self.device_index = 0
        if device:
            for i in range(self.pyaudio_instance.get_device_count()):
                dev = self.pyaudio_instance.get_device_info_by_index(i)
                name = dev['name'].encode('utf-8')
                print(i, name, dev['maxInputChannels'], dev['maxOutputChannels'])
                if name.lower().find(device.lower()) >= 0 and dev['maxOutputChannels'] > 0:
                    self.device_index = i
                    break
        
    def get_pyaudio(self):
        return self.pyaudio_instance

    def play(self, wav_file, block=True):
        self.wav = wave.open(wav_file, 'rb')
        self.event.clear()
        self.stream = self.pyaudio_instance.open(
            format=pyaudio.get_format_from_width(self.wav.getsampwidth()),
            channels=self.wav.getnchannels(),
            rate=self.wav.getframerate(),
            output=True,
            output_device_index=self.device_index,
            frames_per_buffer=CHUNK_SIZE,
            # stream_callback=self.wav_callback,
        )
        
        data = self.wav.readframes(CHUNK_SIZE)
        while data:
            self.stream.write(data)
            data = self.wav.readframes(CHUNK_SIZE)
            
        self.stream.close()

    def play_raw(self, raw_data, rate=16000, channels=1, width=2, block=True):
        self.raw = raw_data
        self.width = width
        self.channels = channels
        self.event.clear()
        self.stream = self.pa.open(format=self.pa.get_format_from_width(width),
                                   channels=channels,
                                   rate=rate,
                                   output=True,
                                   output_device_index=self.device_index,
                                   frames_per_buffer=CHUNK_SIZE,
                                   stream_callback=self.raw_callback)
        if block:
            self.event.wait()
            time.sleep(2)             # wait for playing audio data in buffer, a alsa driver bug
            self.stream.close()

    def wav_callback(self, in_data, frame_count, time_info, status):
        data = self.wav.readframes(frame_count)
        flag = pyaudio.paContinue
        if self.wav.getnframes() == self.wav.tell():
            data = data.ljust(frame_count * self.wav.getsampwidth() * self.wav.getnchannels(), '\x00')
            # flag = pyaudio.paComplete
            self.event.set()

        return data, flag

    def raw_callback(self, in_data, frame_count, time_info, status):
        size = frame_count * self.width * self.channels
        data = self.raw[:size]
        self.raw = self.raw[size:]
        flag = pyaudio.paContinue
        if not len(self.raw):
            data = data.ljust(frame_count * self.width * self.channels, '\x00')
            # flag = pyaudio.paComplete
            self.event.set()

        return data, flag

if __name__ == '__main__':
    # hp_sel = GPIO(41, output=True)
    # gpio_12 = GPIO(12, output=False)
    # hp_sel.write(1)
    # player = Player(device='1')
    # player.play("./sound/1KHz_16k.wav")
    # while True:
    #     print "gpio_12:", gpio_12.read()
    #     time.sleep(1)
    import sys

    argc = len(sys.argv)
    if argc < 2:
        print('Usage: python {} music.wav [card] [control]'.format(sys.argv[0]))
        sys.exit(1)
    
    if argc > 2:
        device = sys.argv[2]
    else:
        device = None
        
    if argc > 3:
        pin = GPIO(41, output=True)
        pin.write(int(sys.argv[3]))

    player = Player(device=device)
    player.play(sys.argv[1])
