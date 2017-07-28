import wave
import audioop
import pyaudio
import sys

from fft import FFT

FRAMES = 2048
#wav_file = '100_150Hz.wav' 
#wav_file = 'doubleSin300Hz_400Hz.wav'
#wav_file = 'record.wav'
wav_file = 'test.wav'

fft = FFT(FRAMES)


def check_result(func, 
            freq1_max = 180, 
            freq1_min = 120, 
            freq2_max = 480, 
            freq2_min = 420):
    def _decorator():
        channel_a = True
        channel_b = True
        objs = func()
        if freq1_max < objs[0] or objs[0] < freq1_min:
            channel_a = False
        if freq2_max < objs[1] or objs[1] < freq2_min:
            channel_b = False
        print channel_a, channel_b
    return _decorator
        

def analyze():
    fn1_sum = 0
    fn2_sum = 0
    num = 0

    wav = wave.open(wav_file, 'rb')
    channels = wav.getnchannels()

    frames = wav.readframes(FRAMES)    

    if channels == 2:
            frames = audioop.tomono(frames, 2, 0.5, 0.5)

    while frames:         
        F = fft.dft(frames)

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
        fn1, y1 = F.index(m1) * wav.getframerate() / FRAMES, m1
        fn2, y2 = F.index(m2) * wav.getframerate() / FRAMES, m2
        if 100 < fn1 and fn1 < 500:
            num = num + 1
            if num > 50:
                break
            fn1_sum = fn1_sum + fn1
            fn2_sum = fn2_sum + fn2
        #break

        frames = wav.readframes(FRAMES)
        if channels == 2:
            frames = audioop.tomono(frames, 2, 0.5, 0.5)

        

    wav.close()

    # The first and second high amplitude frequency
    return fn1_sum/num, fn2_sum/num

analyze()