import fix_import
from spi import *

class SPI_Control():

    def __init__(self):
        self.dev = SPI()
        self.cmd_led_control = 0
        self.cmd_gpio_control = 1
        self.cmd_7688_test_result = 2
        self.cmd_main_task_control = 3
        self.cmd_main_task_power_test = 0xff
        self.led_mode_blink = 0
        self.led_mode_wheel = 1

    def send_cmd(self, data, len, prefix = 0xA5, addr = 0):
        crc = self.dev.crc8(data, len)
        content = [prefix, addr, len]
        content.append(data)
        content.append(crc)
        #print content
        self.dev.write(content)

    def arduino_gpio_control(self, pin, mode, state):
        data = [self.cmd_gpio_control, pin, mode, state]
        self.send_cmd(data, len(data))

    def arduino_task_id_control(self, task_id):
        data = [self.cmd_main_task_control, task_id]
        self.send_cmd(data, len(data))

    def arduino_test_result_update(self, obj, result):
        data = [self.cmd_7688_test_result, obj, result]
        self.send_cmd(data, len(data))

    # [cmd, mode, number, speed, color[3]]
    def arduino_rgb_led_control(self, mode, number, speed, R, G, B):
        speed_H = (speed / 256) & 0xFF
        speed_L = (speed % 256) & 0xFF
        data = [self.cmd_led_control, mode, number, speed_H, speed_L, R, G, B]
        self.send_cmd(data, len(data))

    def arduino_rgb_led_control2(self, led_index, speed, R, G, B):
        speed_H = (speed / 256) & 0xFF
        speed_L = (speed % 256) & 0xFF
        data = [self.cmd_led_control, led_index, speed_H, speed_L, R, G, B]
        self.send_cmd(data, len(data))    

if __name__ == "__main__":
    spi = SPI_Control()
    spi.arduino_task_id_control(spi.cmd_main_task_power_test)
