#import mraa
import time
import os
from spi_control import *


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
        value = -1
        out = os.popen('cat /sys/class/gpio/gpio{}/value'.format(self.pin))
        tmp = int(out.read())
        if 0 == tmp  or 1 == tmp:
            value = tmp

        return value
            


def gpio_test():
    arduino_A1 = 19
    arduino_A4 = 22
    arduino_A5 = 23
    # gpio_46 <- A5(23)
    # gpio_45 <- A1(19)
    # gpio_13 <- A4(22)
    # gpio_12 <- gpio_41

    gpio_read_shift = 0
    spi = SPI_Control()

    # GPIO init
    os.system('mt7688_pinmux set uart0 gpio')
    os.system('mt7688_pinmux set uart1 gpio')
    
    #gpio_12 = GPIO(12, output=False)
    gpio_13 = GPIO(13, output=False)
    gpio_45 = GPIO(45, output=False)
    gpio_46 = GPIO(46, output=False)
    #gpio_41 = GPIO(41, output=True)  # Connect HP_SEL and GPIO_12

    # state 1
    spi.arduino_gpio_control(arduino_A5, 1, 1)  # arduino A5
    spi.arduino_gpio_control(arduino_A1, 1, 0)  # arduino A4
    spi.arduino_gpio_control(arduino_A4, 1, 1)  # arduino A1
    #gpio_41.write(0)
    gpio_read_shift |= gpio_46.read()
    gpio_read_shift |= gpio_45.read() << 1
    gpio_read_shift |= gpio_13.read() << 2
    #gpio_read_shift |= gpio_12.read() << 3
   
    # state 0
    spi.arduino_gpio_control(arduino_A5, 1, 0)  # arduino A5
    spi.arduino_gpio_control(arduino_A1, 1, 1)  # arduino A4
    spi.arduino_gpio_control(arduino_A4, 1, 0)  # arduino A1
    #gpio_41.write(1)
    gpio_read_shift |= gpio_46.read() << 3
    gpio_read_shift |= gpio_45.read() << 4
    gpio_read_shift |= gpio_13.read() << 5
    #gpio_read_shift |= gpio_12.read() << 7

    print "gpio_read_shift: ", bin(gpio_read_shift)

    #gpio_41.write(0)

    if 0b10101 == gpio_read_shift:
        return True

def power_button_test():
    gpio_18 = GPIO(18, output=False)
    gpio_40 = GPIO(40, output=True)
    gpio_40.write(0)
    value = gpio_18.read()
    while value == gpio_18.read():
        pass

    return True


def gpio_config(pin, direction, value):
    path = "/sys/class/gpio/gpio%d"%pin
    if(False == os.path.exists(path)):
        os.system("echo %d"%pin + " > /sys/class/gpio/export")
        time.sleep(0.1)
    os.system("echo " + direction + " > /sys/class/gpio/gpio%d"%pin + "/direction")
    time.sleep(0.1)
    if "out" == direction:
        os.system("echo %d"%value + " > /sys/class/gpio/gpio%d"%pin + "/value")

if __name__=="__main__":
    # gpio_18 = GPIO(18, output=False)
    # gpio_40 = GPIO(40, output=True)
    # gpio_40.write(0)
    # while True:
    #     value = gpio_18.read()
    #     print value
    #     if value == 0: 
    #         gpio_40.write(1)
    #         gpio_40.write(0)
    #     time.sleep(.1)

    if gpio_test():
        print "GPIO test: OK!"
    else:
        print "GPIO test: Failed!"

    ret = power_button_test()
    print "Power button test: ", ret