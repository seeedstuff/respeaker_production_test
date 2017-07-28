import sys, os

import fix_import
import wave
import audioop
import pyaudio
from microphone import *


from fft import FFT


wav_file = './record.wav'

class Audio_Mic_test():
    def __init__(self):
        self.FRAMES = 1024
        self.fft = FFT(self.FRAMES)
        # self.wav = wave.open(wav_file, 'rb')
        self.wav = ""
        # self.channels = self.wav.getnchannels()
        self.channels = ""
        self.freq1 = 0
        self.freq2 = 0
        # self.freq1_max = 520 
        # self.freq1_min = 480 
        self.freq1_max = 530 
        self.freq1_min = 480
        self.freq2_max = 420 
        self.freq2_min = 380
        self.headphone_freq_left = 0
        self.headphone_freq_right = 0
        self.speaker_freq = 0
        self.isHeadphoneChannelLeft_OK = False
        self.isHeadphoneChannelRight_OK = False
        self.isSpeaker_OK = False

        
    def analyze(self):
        count = 0
        fn1_sum = 0
        fn2_sum = 0
        
        self.wav = wave.open(wav_file, 'rb')
        self.channels = self.wav.getnchannels()
        
        frames = self.wav.readframes(self.FRAMES)    
        if self.channels == 2:
            frames = audioop.tomono(frames, 2, 0.5, 0.5)
        while frames:
            F = self.fft.dft(frames)
            m1 = 0
            m2 = 0
            for v in F:
                if v > m1:
                    m2 = m1
                    m1 = v
                elif v > m2:
                    m2 = v
            # Assume amplitude = m1
            # frequency = F.index(m1) * wav.getframerate() / FRAMES
            fn1, y1 = F.index(m1) * self.wav.getframerate() / self.FRAMES, m1
            fn2, y2 = F.index(m2) * self.wav.getframerate() / self.FRAMES, m2
            
            if 100 < fn1 and fn1 < 2000:
                print fn1, y1
                print fn2, y2
                fn1_sum = fn1_sum + fn1
                fn2_sum = fn2_sum + fn2
                count = count + 1
                if count > 50:
                    break
            frames = self.wav.readframes(self.FRAMES)
            if self.channels == 2:
                frames = audioop.tomono(frames, 2, 0.5, 0.5)
        self.wav.close()
        
        if count != 0:
            self.freq1 = fn1_sum/count
            self.freq2 = fn2_sum/count

    def check_headphone_left(self):
        os.system("amixer sset Speaker 20%")
        os.system("amixer sset Headphone 90%,20%")
        os.system("./play_sound.sh")
        self.analyze()
        self.headphone_freq_left = self.freq1
        if  self.freq1_min < self.headphone_freq_left and self.headphone_freq_left < self.freq1_max:
            self.isHeadphoneChannelLeft_OK = True

    def check_headphone_right(self):
        os.system("amixer sset Speaker 20%")
        os.system("amixer sset Headphone 20%,90%")
        os.system("./play_sound.sh")
        self.analyze()
        self.headphone_freq_right = self.freq1
        if  self.freq1_min < self.headphone_freq_right and self.headphone_freq_right < self.freq1_max:
            self.isHeadphoneChannelRight_OK = True

    def check_speaker(self):
        os.system("amixer sset Speaker 90%")
        os.system("amixer sset Headphone 20%")
        os.system("./play_sound.sh")
        self.analyze()
        self.speaker_freq = self.freq1
        if self.freq1_min < self.speaker_freq and self.speaker_freq < self.freq1_max:
            self.isSpeaker_OK = True

    def check_array_mic(self):
        self.analyze()
        self.headphone_freq_right = self.freq1
        if  self.freq1_min < self.headphone_freq_right and self.headphone_freq_right < self.freq1_max:
            self.isHeadphoneChannelRight_OK = True


if __name__ == "__main__":
    headphone = Audio_Mic_test()
    headphone.check_array_mic()
    print "freq: ", headphone.headphone_freq_right, "test: ", headphone.isHeadphoneChannelRight_OK
