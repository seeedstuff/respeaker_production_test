import fix_import
import os, sys

# sys.path.append(os.path.join("/Media/SD-P1/respeaker_python_library/respeaker"))
# os.chdir('/Media/SD-P1/microphone_test')

from usb_hid import INTERFACE, usb_backend
from spi import SPI
from play import *
from audio_mic_test import *
import time
from spi_control import *

CRC8_TABLE = (
    0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15,
    0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d,
    0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
    0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d,
    0xe0, 0xe7, 0xee, 0xe9, 0xfc, 0xfb, 0xf2, 0xf5,
    0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
    0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85,
    0xa8, 0xaf, 0xa6, 0xa1, 0xb4, 0xb3, 0xba, 0xbd,
    0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
    0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea,
    0xb7, 0xb0, 0xb9, 0xbe, 0xab, 0xac, 0xa5, 0xa2,
    0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
    0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32,
    0x1f, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0d, 0x0a,
    0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
    0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a,
    0x89, 0x8e, 0x87, 0x80, 0x95, 0x92, 0x9b, 0x9c,
    0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
    0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec,
    0xc1, 0xc6, 0xcf, 0xc8, 0xdd, 0xda, 0xd3, 0xd4,
    0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
    0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44,
    0x19, 0x1e, 0x17, 0x10, 0x05, 0x02, 0x0b, 0x0c,
    0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
    0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b,
    0x76, 0x71, 0x78, 0x7f, 0x6a, 0x6d, 0x64, 0x63,
    0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
    0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13,
    0xae, 0xa9, 0xa0, 0xa7, 0xb2, 0xb5, 0xbc, 0xbb,
    0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8d, 0x84, 0x83,
    0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb,
    0xe6, 0xe1, 0xe8, 0xef, 0xfa, 0xfd, 0xf4, 0xf3
)


def crc8(data):
    result = 0
    for b in data:
        result = CRC8_TABLE[result ^ b]
    return result


class PixelRing:
    def __init__(self):
        self.hid = self.get_hid()
        if not self.hid:
            self.spi = SPI()

    @staticmethod
    def get_hid():
        interface = INTERFACE[usb_backend]
        if interface.isAvailable:
            boards = interface.getAllConnectedInterface()
            if boards:
                return boards[0]

    def off(self):
        self.set_color(rgb=0)

    def set_color(self, r=0, g=0, b=0, rgb=None):
        if rgb:
            self.write(0, [1, rgb & 0xFF, (rgb >> 8) & 0xFF, (rgb >> 16) & 0xFF])
        else:
            self.write(0, [1, b, g, r])

    def listen(self, direction=None):
        if direction is None:
            self.write(0, [7, 0, 0, 0])
        else:
            self.write(0, [2, 0, direction & 0xFF, (direction >> 8) & 0xFF])

    def wait(self):
        self.write(0, [3, 0, 0, 0])

    def speak(self, strength, direction):
        self.write(0, [4, strength, direction & 0xFF, (direction >> 8) & 0xFF])

    def set_volume(self, volume):
        self.write(0, [5, 0, 0, volume])

    @staticmethod
    def to_bytearray(data):
        if type(data) is int:
            array = bytearray([data & 0xFF])
        elif type(data) is bytearray:
            array = data
        elif type(data) is str:
            array = bytearray(data)
        elif type(data) is list:
            array = bytearray(data)
        else:
            raise TypeError('%s is not supported' % type(data))

        return array

    def write(self, address, data):
        data = self.to_bytearray(data)
        length = len(data)
        if self.hid:
            packet = bytearray([address & 0xFF, (address >> 8) & 0xFF, length & 0xFF, (length >> 8) & 0xFF]) + data
            self.hid.write(packet)
        else:
            crc = crc8(data)
            packet = bytearray([0xA5, address & 0xFF, length & 0xFF]) + data + bytearray([crc])
            self.spi.write(packet)

    def read(self, address, length, timeout=1):
        data = bytearray()
        if self.hid:
            address |= 0x8000
            packet = bytearray([address & 0xFF, (address >> 8) & 0xFF, length & 0xFF, (length >> 8) & 0xFF]) + data
            self.hid.Event.set()
            self.hid.write(packet)
            data = self.hid.read(timeout)
        return data

    def close(self):
        if self.hid:
            self.hid.close()

class ArrayTest():
    def __init__(self):
        self.record_file = "./record.wav"
        self.delete_record()
        self.spi = SPI_Control()

        self.ring = PixelRing()
        self.hp_sel = GPIO(41, output=True)
        self.player = Player(device='1')

        self.led_near_mic = [6, 7 , 9, 11, 1, 3, 5]
        self.microphone_state = 0
        self.enable_report_loop()

    def __del__(self):
        pass

    def enable_report_loop(self):
        os.system("echo start > /tmp/array_loop")

    def disable_report_loop(self):
        os.system("echo stop > /tmp/array_loop")
       
    def device_init(self):
        self.hp_sel.write(1)
        self.ring.write(0, [1])
        self.ring.set_color(rgb=0x050505)
        time.sleep(2)

    def test_micarray(self, timeout=30):
        state = False
        self.ring.write(0x02, [0, 0])
        self.player.play("./sound/1KHz_16k.wav")
        self.player.play("./sound/1KHz_16k.wav")
        print "Play sound over!"
        start = time.time()
        while time.time() - start < timeout:
            data = self.ring.read(0x02, 2)
            if data[0] != 2 or data[4] != 1:
                print "Shift wrong data"
            else:
                print "Test Result[{}]: {}".format(time.time(), data)
                if data[5] == 127:
                    state = True
                break
        self.microphone_state = data[5]
        return state

    def led_control(self, led, rgb=0):
        r, g, b = (rgb >> 16) & 0xff, (rgb >> 8) & 0xff, rgb & 0xff
        color = [b, g, r, 0]
        #self.ring.set_color(0)
        self.ring.write(0x0, [6])
        self.ring.write(0x03 + led, color)

    def microphone_clear_led(self):
        for i in range(12):
            self.led_control(i, rgb=0)

    def microphone_test_error_led(self, state):
        for bit in range(7):
            if (state >> bit) & 0x1:
                self.led_control(self.led_near_mic[bit], rgb=0x000500)
            else:
                self.led_control(self.led_near_mic[bit], rgb=0x050000)

    def led_control_test(self):
        for i in range(12):
            self.led_control(i, rgb=0x0f0f0f)

    def getPowerState(self):
        self.spi.arduino_task_id_control(self.spi.cmd_main_task_power_test)
        time.sleep(1)
        out = os.popen("cat ./states/power_state").read()
        if 0 == len(out):
            return 0
        state = int(out)
        os.system("echo 0 > ./states/power_state")
        return state

    def test_exit(self):
        self.ring.off()
        self.ring.close()
        os.system("killall arecord")

    def delete_record(self):
        if os.path.isfile(self.record_file):
            os.remove(self.record_file)

def main():
    try:
        # the end loop state
        array_loop = ""

        array_test = ArrayTest()
        array_test.delete_record()
        array_test.device_init()
        micArrayState = int()
        powerState = int()
        #micArrayState = True
        #powerState = True
        cnt = 0
        while cnt <= 3:
            micArrayState = array_test.test_micarray()
            if micArrayState:
                break
            cnt += 1
        powerState = array_test.getPowerState()
        print "micArrayState:", micArrayState
        print "powerState:", powerState

        if not micArrayState:
            array_test.microphone_clear_led()
            array_test.microphone_test_error_led(array_test.microphone_state)

        array_loop = os.popen("cat /tmp/array_loop").read()

        color = 0x05
        while "start" in array_loop:
            if micArrayState and powerState:
                array_test.ring.write(0, [1])
                array_test.ring.set_color(rgb=0x05)
                time.sleep(.5)
                array_test.ring.set_color(rgb=0x0500)
                time.sleep(.5)
                array_test.ring.set_color(rgb=0x050000)
                time.sleep(.5)
                array_test.ring.set_color(rgb=0x050505)
                os.system("aplay -D plughw:1 ./sound/lisa_ok.wav")
                
            if not micArrayState:
                os.system("aplay -D plughw:1 ./sound/lisa_micerror.wav")

            if not powerState:
                os.system("aplay -D plughw:1 ./sound/lisa_powerError.wav")

            array_loop = os.popen("cat /tmp/array_loop").read()
            print "array_loop: ", array_loop
            color = color << 8
            if color == 0x05000000:
                color = 0x05

    except Exception as e:
        print "Exception: ", e
        print "Exit"

def led_test():
    array_test = ArrayTest()
    while True:
        array_test.led_control_test()
        time.sleep(1)
        array_test.microphone_clear_led()
        time.sleep(1)

if __name__ == '__main__':
    led_test()
