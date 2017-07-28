/**
 * Use Arduino (atmega32u4) as a SPI slave
 *
 * by Seeed Studio (http://seeedstudio.com)
 * 
 * Change log:
 * 
 * 2017-04-01
 * Issue： 麦克风矩阵测试治具突然不能测试，7688启动进入复位死循环
 * Solution： 在setup（）最后增加延时5秒，让7688过了启动过程后再输入Enter检测是否启动完毕。
 */

#include <SPI.h>
#include "respeaker.h"

#define DEBUG_ENABLE 1

#define PIXELS_SPACE        128
#define LED_NUM             12
#define COLOR_RED          0x110000
#define COLOR_GREEN        0x001100
#define COLOR_BLUE         0x000011
#define COLOR_YELLOW       0x0a0a00
#define COLOR_WHITE        0x0a0a0a 

#define TEST_BOJS          6

char spi_buf[64];
volatile byte spi_buf_index = 0;
volatile byte spi_event = 0;
volatile byte pixels_state = 0;

volatile uint32_t UARTtimeStart;
volatile bool UARTtimecnt_start = true;
const char *str_console_activated = "root@ReSpeaker:";
const char *str_reboot = "reboot -f";
const char *str_bootOperation = "9: Load Boot Loader code then write to Flash via TFTP.";
const char *str_readingFW = "reading lks7688.img";
const char *str_writingFW = "writing lks7688.img to flash";
const char *str_fwUpgrade_done = "Done!";
const char *str_autorunfile = "autorun.sh";
const char *str_sdcard_exist = "audio_mic_test.py";
const char *str_isTestPass = "TEST_PASS";

typedef struct {
  uint8_t led_index;
  uint32_t color;
}TEST_RESULT_LED;

// Setting 6 RGB leds by color: \
  arduino gpio, arduino adc,      MT7688 gpio, \
  MT7688 wifi,  MT7688 audio mic, power button, \
  arduino FW upgrade
volatile uint32_t test_result_colors[LED_NUM] = {0}; 
TEST_RESULT_LED test_result_led = {
  .led_index = 0,
  .color = 0,
};

typedef struct {
  // mode 1 blink, mode 0 wheel
  uint8_t mode;
  // Max number 12
  uint8_t number;
  // Blink or rotate speed
  uint16_t speed;
  // 16 bits RGB color
  uint32_t color;
}RGB_LED_State;

RGB_LED_State rgb_led_state = {
  .mode = 1,
  //.number = 0,
  .number = 12,
  .speed = 500,
  .color = 0x000000,
};

enum test_obj_id {
  test_id_arduino_gpio = 6,
  test_id_arduinio_adc,
  test_id_MT7688_gpio,
  test_id_MT7688_WiFi,
  test_id_MT7688_audio_mic,
  test_id_POWER_button
};

typedef struct{
  uint8_t arduino_gpio;
  uint8_t arduinio_adc;
  uint8_t MT7688_gpio;
  uint8_t MT7688_WiFi;
  uint8_t MT7688_audio_mic;
  uint8_t POWER_button;
}TEST_OBJ_RESULTS;

TEST_OBJ_RESULTS test_obj_results = {
  .arduino_gpio = 0,
  .arduinio_adc = 0,
  .MT7688_gpio = 0,
  .MT7688_WiFi = 0,
  .MT7688_audio_mic = 0,
  .POWER_button = 0
};

enum test_obj_led_num {
  led_num_arduino_gpio = 6,
  led_num_arduinio_adc = 7,
  led_num_MT7688_gpio = 8,
  led_num_MT7688_WiFi = 9,
  led_num_MT7688_audio_mic = 10,
  led_num_POWER_button = 11,
};

enum board_test_spi_cmd {
  spiCmd_array_power_test = 3,
};

enum main_task{
  main_task_begin = 0,
  main_task_detect_console,
  main_task_check_is_sdcard_installed,
  main_task_end,
  main_task_power_test,
};

volatile int main_task_id = main_task_begin;
volatile bool main_task_execute_once = false;

// void touch_event(uint8_t id, uint8_t event) {
//     // id - touch sensor id (0 ~ 7), event - 1: touch, 0: release
// }

void detect_console_timeout()
{

} 

// Send "Enter" to detect console
void detcet_console()
{
  static uint32_t timeoutcnt = millis();

  // Setting timeout 20 seconds
  if(20000 < millis() - timeoutcnt) {
    detect_console_timeout();
  }

  MT7688_send_Enter();
}

/**
  * @brief: Send command to 7688 console
  */
void MT7688_send_Enter(void)
{
  delay(500);
  Serial1.println("");
}

void MT7688_send_fw_upgrade(void)
{
  Serial1.write('5');
  //Serial1.println("sysupgrade /Media/SD-P2/openwrt-c1.bin");
  //Serial1.println("sysupgrade /Media/USB-A1/lks7688.img");
}

void MT7688_send_reboot(void)
{
  Serial1.println(str_reboot);
}

void MT7688_check_is_borad_tested(void)
{
  Serial1.println("cat /etc/test_pass");
}

void MT7688_check_is_fw_upgraded(void)
{
  Serial1.println("ls /root");
  //MT7688_send_Enter();
}

void MT7688_check_is_sdcard_installed()
{
  Serial1.println("ls /Media/SD-P1/microphone_test/");
}

void MT7688_run_test_script(void) 
{
  Serial1.println("python /Media/SD-P1/production_test/main.py");
}

void MT7688_test_pass_mark(void)
{
  Serial1.println("cp /Media/SD-P1/production_test/test_pass /etc");
}

void MT7688_delete_test_pass(void)
{
  Serial1.println("rm /etc/test_pass");
}

void MT7688_run_test_task(void)
{
  Serial1.println("python /Media/SD-P1/microphone_test/daemon.py &");
}

void MT7688_disable_mopidy(void)
{
  Serial1.println("/etc/init.d/mopidy stop"); 
}

void MT7688_disable_upmpdcli(void)
{
  Serial1.println("/etc/init.d/upmpdcli stop"); 
}

/* Send command to 7688 console */

// @brief Compare Seiral steam byte by byte
// @return 0, not found
//         1, found string
int parseStrFromSerial(const char* str, uint16_t len)
{
  char c;
  uint16_t index = 1;

  if(Serial1.available()) {
    c = Serial1.read();
    Serial.write(c);
    if(str[0] == c) {
      while(1) {
        while(!Serial1.available());
        c = Serial1.read();
        Serial.write(c);
        if(str[index] == c) {
          if(index >= len - 1) {
            MT7688_send_Enter();
            return 1;
          }
          index++;
        }
        else {
          return 0;
        }  
      }
    }
  }

  return 0;
}

/**
 * Led action identify 
 */

uint32_t led_num2bits(uint8_t num)
{
  uint32_t bits = 0;
  for (int i = 0; i < num; i++) {
    bits <<= 1;
    bits |= 1;
  }

  return bits;
}

// @brief: Setting led strip by lighting up num of leds and making some fade.
void simple_ledstrip(uint16_t num, uint32_t color, uint32_t led_data)
{
  respeaker.pixels().clear();
  for (uint16_t i = 0; i < num; i++) {
    if((led_data >> i) & 0x1) {
      respeaker.pixels().set_color(i, color);
    } 
    else {
      respeaker.pixels().set_color(i, 0);
    }
  }
  respeaker.pixels().update();
}

void LEDActoinID_begin(void)
{
  simple_ledstrip(12, COLOR_WHITE, 0xFFF);
  delay(3000);
  respeaker.pixels().clear();
}

/* @brief: This is a rotating ledstrip function
 *
 */

void LEDstripWheel(uint16_t led_num, uint32_t color, uint32_t ledOn_bits)
{
  volatile uint32_t data;
  static   uint32_t i = 0;

  data = ledOn_bits << i;
  data |= data >> LED_NUM;

  simple_ledstrip(led_num, color, data);

  if((led_num - 1) < ++i){
    i = 0;
  }
}

void LEDstripBlink(uint32_t led_num, uint32_t color, uint32_t ledOn_bits)
{
  static byte state = 1;
  volatile uint32_t data;

  state ^= 1;
  state ? data = ledOn_bits : data = 0;
  simple_ledstrip(led_num, color, data);
}

void LEDActoinID_loop(void)
{
  if (0 == rgb_led_state.mode) {
    LEDstripWheel(LED_NUM, rgb_led_state.color, led_num2bits(rgb_led_state.number));
  } else {
    LEDstripBlink(LED_NUM, rgb_led_state.color, led_num2bits(rgb_led_state.number));
  }
  
}

void LEDActoinID_color_wheel(void)
{
  static uint32_t wheel_color = 0x05;

  simple_ledstrip(LED_NUM, wheel_color, 0xfff);

  wheel_color <<= 8;
  if(wheel_color == 0x05000000) {
    wheel_color = 0x05;
  }
}

void LEDActoinID_HW_testing(void)
{
  if(0 == rgb_led_state.mode) {
    LEDstripBlink(LED_NUM, rgb_led_state.color, led_num2bits(rgb_led_state.number));
  } else {
    LEDstripWheel(LED_NUM, rgb_led_state.color, led_num2bits(rgb_led_state.number));  
  }
  
}


// volatile byte test_result_colors[6] = {0};  // Setting 6 RGB leds by color
// struct TEST_RESULT_LED test_result_led = {
//   .led_index = 0,
//   .color = 0,
// };
/**
  * @brief: RGB LED blink
  * @param: led_index, color
  */
void LEDActoinID_HW_Testing(void)
{
  static byte state = 1;
  uint16_t i;

  if (1 == state) 
  {
    // Serial.print("Test Color aray: ");
    for (i = 0; i < LED_NUM; i ++) 
    {
      // Serial.print("0x");
      // Serial.print(test_result_colors[i], HEX);
      // Serial.print(" ");
      respeaker.pixels().set_color(i, test_result_colors[i]);
    }
    // Serial.println("");
    respeaker.pixels().update();
  } 
  else 
  {
    respeaker.pixels().clear();
  }

  state ^= 1;
}

void LEDActoinID_WaitFor_HW_Test(void)
{
  LEDstripWheel(LED_NUM, COLOR_YELLOW, led_num2bits(6));
}

void LEDActoinID_wait_for_power_button(void)
{
  LEDstripBlink(LED_NUM, COLOR_BLUE, led_num2bits(LED_NUM));
}
/* Led action identify */

/**
 * HW test functions
 */
void arduino_gpio_test(void)
{
  uint16_t gpio_test_ret = 0;
  const uint16_t group_len = 5;
  int a, b;
  //int pins[8] = {10, 13, 9, 8, 3, 4, 2, 6};
  //int pins[4][2] = {{10, 9}, {13, 8}, {4, 2}, {12, A3}};
  int pins[group_len][2] = {{10, 9}, {13, 8}, {4, 2}, {3, 6}, {12, A3}};


  for(int i = 0; i < group_len; i++) {
    pinMode(pins[i][0], INPUT);
    pinMode(pins[i][1], OUTPUT); 

    digitalWrite(pins[i][1], HIGH);
    a = digitalRead(pins[i][0]);
    digitalWrite(pins[i][1], LOW);
    b = digitalRead(pins[i][0]);

    if(a == 1 && b == 0) {
      gpio_test_ret |= 0x1 << i;
    } else {
      gpio_test_ret &= ~(0x1 << i);
    }
  }

#if DEBUG_ENABLE
  Serial.print("GPIO Test: 0x");
  Serial.println(gpio_test_ret, HEX); 
  // Serial.print("ADC test, A0: ");
  // Serial.println(analogRead(A0));
#endif

  gpio_test_ret == 0x1F ? test_obj_results.arduino_gpio = 1 : test_obj_results.arduino_gpio = 0;
  

  if (test_obj_results.arduino_gpio) {
    test_result_colors[test_id_arduino_gpio] = 0x000500;
  } else {
    test_result_colors[test_id_arduino_gpio] = 0x050000;
  }

}

void arduino_adc_test(void) 
{
  uint16_t value = analogRead(A0);

#if DEBUG_ENABLE
  Serial.print("ADC test, A0: ");
  Serial.println(value); 
#endif

  if(150 < value && value < 190){
    test_obj_results.arduinio_adc = 1;
    test_result_colors[test_id_arduinio_adc] = 0x000500;
  }else {
    test_obj_results.arduinio_adc = 0;
    test_result_colors[test_id_arduinio_adc] = 0x050000;
  }

}

void mark_board_test_state(void)
{
  if(test_obj_results.arduino_gpio && \
    test_obj_results.arduinio_adc && \
    test_obj_results.MT7688_gpio && \
    test_obj_results.MT7688_WiFi && \
    test_obj_results.MT7688_audio_mic && \
    test_obj_results.POWER_button)
  {
    MT7688_test_pass_mark();
  }
  else {
    MT7688_delete_test_pass();
  }

  Serial.print("test result: ");
  Serial.print(test_obj_results.arduino_gpio);
  Serial.print(test_obj_results.arduinio_adc);
  Serial.print(test_obj_results.MT7688_gpio);
  Serial.print(test_obj_results.MT7688_WiFi);
  Serial.print(test_obj_results.MT7688_audio_mic);
  Serial.println(test_obj_results.POWER_button);
}

/* HW test functions */

/** 
 * @brief: Function to execute another function periodically。
 */
void loop_event_1(void (*p_none_block_loop_event) (void), uint32_t duration_ms)
{
  static uint32_t loop_event_timer = 0;

  if(duration_ms < millis() - loop_event_timer) {
    loop_event_timer = millis();
    p_none_block_loop_event();
  }
}

void loop_event_2(void (*p_none_block_loop_event) (void), uint32_t duration_ms)
{
  static uint32_t loop_event_timer = 0;

  if(duration_ms < millis() - loop_event_timer) {
    loop_event_timer = millis();
    p_none_block_loop_event();
  }
}

void gpio_control(uint8_t pin, uint8_t direction, uint8_t state)
{
  pinMode(pin, direction);
  if(OUTPUT == direction) {
    digitalWrite(pin, state);
  }
}

void board_test_handle(uint8_t *data, uint8_t len)
{
  switch (data[0]) {
    case spiCmd_array_power_test:   // [payload]
      if (0xff == data[1]) {
        main_task_id = main_task_power_test;
      }
      break;

    default: break;
  }
}

#if 1
/** 
  * @brief: SPI Event
  *
  */
void spi_handle_event(uint8_t addr, uint8_t *data, uint8_t len)
{
  if (0 == addr) {
#if DEBUG_ENABLE
    Serial.println("Receive SPI data!");
#endif
    // Handle spi data for board testing
    board_test_handle(data, len); 
  }
}
#endif


uint16_t a3, a4;
uint16_t a3_value_max = 850;
uint16_t a3_value_min = 830;
uint16_t a4_value_max = 270;
uint16_t a4_value_min = 250;


uint8_t microphone_power_test()
{
  uint8_t test_state = 0;
  a3 = analogRead(A3);
  a4 = analogRead(A4);

  Serial.print("A0, A1: ");
  Serial.print(a3);
  Serial.print(" ");
  Serial.println(a4);

  if(a3_value_min < a3 && a3 < a3_value_max && a4_value_min < a4 && a4 < a4_value_max) {
    test_state = 1;
    Serial1.println("echo 1 > /Media/SD-P1/microphone_test/states/power_state");
    delay(100);
    Serial1.println("echo 1 > /Media/SD-P1/microphone_test/states/power_state");
    delay(100);
    Serial1.println("echo 1 > /Media/SD-P1/microphone_test/states/power_state");
    delay(100);
  }
  else {
    test_state = 0;
    Serial1.println("echo 1 > /Media/SD-P1/microphone_test/states/power_state");
    delay(100);
    Serial1.println("echo 1 > /Media/SD-P1/microphone_test/states/power_state");
    delay(100);
    Serial1.println("echo 1 > /Media/SD-P1/microphone_test/states/power_state");
    delay(100);
    //Serial1.println("echo 0 > /Media/SD-P1/microphone_test/states/power_state");
  }

  return test_state;
}

void setup (void)
{
  respeaker.begin(1,1,1);
  respeaker.attach_spi_handler(spi_handle_event);
  delay(5000);
}

void loop(void)
{
  int ret;

  // while (1) {
  //   microphone_power_test();
  //   delay(1000);
  // }

  switch(main_task_id) {

    case main_task_begin:
      rgb_led_state.color = COLOR_BLUE;
      rgb_led_state.number = 4;
      rgb_led_state.mode = 0;
      rgb_led_state.speed = 100;
      main_task_id = main_task_detect_console;
      break;

    case main_task_detect_console:
      respeaker._loop(); 
      loop_event_1(LEDActoinID_loop, rgb_led_state.speed);
      loop_event_2(MT7688_send_Enter, 1000);
      ret = parseStrFromSerial(str_console_activated, strlen(str_console_activated));
      if (1 == ret) {
        rgb_led_state.color = COLOR_GREEN;
        rgb_led_state.number = 4;
        rgb_led_state.speed = 50;
        main_task_id = main_task_check_is_sdcard_installed;
      }

      break;

    case main_task_check_is_sdcard_installed:
      respeaker._loop();
      loop_event_1(LEDActoinID_loop, rgb_led_state.speed);
      loop_event_2(MT7688_check_is_sdcard_installed, 1000);

      ret = parseStrFromSerial(str_sdcard_exist, strlen(str_sdcard_exist));
      if (1 == ret) {
        MT7688_disable_mopidy();
        delay(500);
        MT7688_disable_upmpdcli();
        delay(500);
        MT7688_run_test_task();
        rgb_led_state.color = COLOR_WHITE;
        rgb_led_state.number = 4;
        rgb_led_state.speed = 50;
        main_task_id = main_task_end;

      }
      break;

    case main_task_end:
      respeaker._loop();
      loop_event_1(LEDActoinID_loop, rgb_led_state.speed);
      break;

    case main_task_power_test:
      microphone_power_test();
      main_task_id = main_task_end;
      break;

    default:
      break;
  }


}
