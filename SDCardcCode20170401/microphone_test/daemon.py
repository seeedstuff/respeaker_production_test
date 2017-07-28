import os
from time import time, sleep

os.chdir("/Media/SD-P1/microphone_test")

class MicArrayTest():
    def __init__(self):
        self.is_array_on = False

    def isArrayOn(self):
        arrayIsOn = False
        if  os.path.exists("/dev/dsp1") and not self.is_array_on:
            self.is_array_on = True
            print "Array on"
            arrayIsOn = True
        elif not os.path.exists("/dev/dsp1") and self.is_array_on:
            self.is_array_on = False
            print "Array off"
            os.system("echo stop > /tmp/array_loop")

        return arrayIsOn

if __name__ == '__main__':
    array = MicArrayTest()
    while True:
        if array.isArrayOn():
            print "start main.py!"
            os.system("python ./main.py&")
            os.system("echo start > /tmp/array_loop")
        sleep(1)