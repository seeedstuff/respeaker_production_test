import os, sys

os.chdir("/Media/SD-P1/production_test")

from spi_control import *
from wifi_test import *
from gpio_test import *
import subprocess, time
from audio_mic_test import *
#import threading


test_obj = {
  'mt7688_gpio_state': 0,
  'wifi_state': 0,
  'audio_mic_state': 0,
  'power_button_state': 0
}

test_obj_array = []

arduino_main_task_begin = 0
arduino_main_task_detect_console = 1
arduino_main_task_check_is_fw_upgraded = 2
arduino_main_task_is_udisk_exist = 3
arduino_main_task_reboot = 4
arduino_main_task_choose_boot_operation = 5
arduino_main_task_fw_upgrade_Start = 6
arduino_main_task_fw_reading = 7
arduino_main_task_fw_writting = 8
arduino_main_task_fw_upgrade_done = 9
# arduino_gpio include adc test
arduino_main_task_hw_test_arduino_gpio = 10
arduino_main_task_hw_test_arduino_adc = 11
arduino_main_task_check_is_sdcard_installed = 12
arduino_main_task_hw_test_wait_for_7688_cmd = 13
arduino_main_task_end = 14
arduino_main_task_mark_test_state_to_7688 = 15
arduino_main_task_wait_for_power_button = 16

# Test obj index
test_result_index_arduino_gpio = 6
test_result_index_arduinio_adc = 7
test_result_index_MT7688_gpio = 8
test_result_index_MT7688_WiFi = 9
test_result_index_MT7688_audio_mic = 10
test_result_index_POWER_button = 11

try:
    os.remove("./test.wav")
except:
    pass

spi = SPI_Control()

# 1.WiFi test
def test_obj_wifi():
    if wifi_test():
        test_obj['wifi_state'] = 1
    print 'wifi test: ', test_obj['wifi_state']
    spi.arduino_test_result_update(test_result_index_MT7688_WiFi, test_obj["wifi_state"])
    

# 2.mt7688 gpio test
def test_obj_gpio():
    if gpio_test():
        test_obj['mt7688_gpio_state'] = 1        
        print "GPIO test: OK!"
    else:
        test_obj['mt7688_gpio_state'] = 0
        print "GPIO test: Failed!"
    spi.arduino_test_result_update(test_result_index_MT7688_gpio, test_obj["mt7688_gpio_state"])

# 3.audio&mic test
def test_obj_audio_mic():
    #test_headphone_left = Audio_Mic_test()
    #ttest_headphone_right = Audio_Mic_test()
    test_speaker = Audio_Mic_test()

    #test_headphone_left.check_headphone_left()
    #test_headphone_right.check_headphone_right()
    test_speaker.check_speaker()

    # print 'headphone freq: ', test_headphone_left.headphone_freq_left, test_headphone_right.headphone_freq_right
    # print 'headphone test: ', test_headphone_left.isHeadphoneChannelLeft_OK, test_headphone_right.isHeadphoneChannelRight_OK
    # print 'speaker freq: ', test_speaker.speaker_freq
    # print 'speaker test:', test_speaker.isSpeaker_OK
    
    if test_speaker.isSpeaker_OK:
        test_obj["audio_mic_state"] = 1
        print "audio_mic_test OK!"
    else:
        print "audio_mic_test Failed!"
    spi.arduino_test_result_update(test_result_index_MT7688_audio_mic, test_obj["audio_mic_state"])

# 4.power button test
def test_obj_power_button():
    ret = power_button_test()
    print "Power button test: ", ret
    if ret:
        test_obj["power_button_state"] = 1
        spi.arduino_rgb_led_control2(11, 200, 0, 5, 0)
    else:
        spi.arduino_rgb_led_control2(11, 200, 5, 0, 0)
    spi.arduino_test_result_update(test_result_index_POWER_button, test_obj["power_button_state"])
    

def gpio_config(pin, direction, value):
    path = "/sys/class/gpio/gpio%d"%pin
    if(False == os.path.exists(path)):
        os.system("echo %d"%pin + " > /sys/class/gpio/export")
        time.sleep(0.5)
    os.system("echo " + direction + " > /sys/class/gpio/gpio%d"%pin + "/direction")
    time.sleep(0.5)
    if "out" == direction:
        os.system("echo %d"%value + " > /sys/class/gpio/gpio%d"%pin + "/value")



if __name__=="__main__":

    try:
        os.chdir("/Media/SD-P1/production_test")
        os.system("/etc/init.d/mopidy stop")
        #os.system("/etc/init.d/upmpdcli stop")
        #os.system("/etc/init.d/mopidy disable")
        # 1.Arduino gpio test
        # 2.Arduino ADC test
        spi.arduino_task_id_control(arduino_main_task_hw_test_arduino_gpio)    
        spi.arduino_task_id_control(arduino_main_task_hw_test_wait_for_7688_cmd)


        # 3.7688 gpio test
        test_obj_gpio()

        # 4.WiFi test
        test_obj_wifi()

        # 5.audio&mic test
        test_obj_audio_mic()
        #spi.arduino_test_result_update(test_result_index_MT7688_audio_mic, 0)

        test_obj_array.append(test_obj["mt7688_gpio_state"])
        test_obj_array.append(test_obj["wifi_state"])
        test_obj_array.append(test_obj["audio_mic_state"])
        test_obj_array.append(test_obj["power_button_state"])
        

        for index in range(len(test_obj_array)):
            #print obj
            if 1 == test_obj_array[index]:
                spi.arduino_rgb_led_control2(index + 8, 200, 0, 5, 0)
                time.sleep(.2)
            else:
                spi.arduino_rgb_led_control2(index + 8, 200, 5, 0, 0)
                time.sleep(.2)

        spi.arduino_task_id_control(arduino_main_task_mark_test_state_to_7688)
        
        os.system("amixer sset Headphone 90%,90%")
        os.system("amixer sset Speaker 20%")
        #os.system("aplay ./sound/Coldplay.wav&")
        os.system("aplay -M ./sound/left_right_voice_woman.wav&")

        # 6.power button test
        test_obj_power_button()
        os.system("/etc/init.d/mopidy start")
        #os.system("/etc/init.d/upmpdcli start")
        

    except (KeyboardInterrupt, SystemExit):
        pass
