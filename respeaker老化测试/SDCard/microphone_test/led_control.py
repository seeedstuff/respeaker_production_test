from main import *


ring = PixelRing()

def led_control(led, r, g, b):
    color = [r, g, b]
    ring.set_color(0)
    ring.write(0x0, [6])
    ring.write(0x03 + led, color)



if __name__=="__main__":
  while True:
    for i in range(12):
        led_control(i, 0x05, 0x05, 0x05)

