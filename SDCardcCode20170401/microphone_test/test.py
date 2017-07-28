from main import *
from time import time, sleep
import threading
import play

player = Player(device='1')
ring = PixelRing()
cnt = 0

def test(timeout=30):
    state = False
    ring.write(0x02, [0,0])
    print "listening..."
    player.play("./sound/1KHz_16k.wav")    
    player.play("./sound/1KHz_16k.wav")    
    start = time()
    while time() - start < timeout:
        data =  ring.read(0x02, 2)
        if data[0] != 2 or data[4] != 1:
            #print data[0:5]
            print "Shift wrong data..."
        else:
            print "Test Result[{}]: {}".format(cnt, data)
            if data[5] == 127:
                state = True
            break
    return state

try:
    print "Test result: {}".format(test())
except KeyboardInterrupt, SystemExit:
    _exit = True
    exit(0)

