#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_ST7789.h>
#include <stdarg.h>
#include "button_debouncer.h"

constexpr int LCD_SCK = 40;
constexpr int LCD_MOSI = 41;
constexpr int LCD_RST = 21;
constexpr int LCD_DC = 47;
constexpr int LCD_CS = 42;
constexpr int LCD_BL = 38;
constexpr uint32_t LCD_SPI_HZ = 8000000;
constexpr int BUTTON_MID = 14;
constexpr uint32_t BUTTON_DEBOUNCE_MS = 10;
constexpr int COUNTER_WIDTH = 180;
constexpr int COUNTER_HEIGHT = 24;

class Display : public Adafruit_ST7789 {
 public:
  using Adafruit_ST7789::Adafruit_ST7789;

  void begin(uint32_t = 0) override {
    // init() calls begin() internally; also limit initialization on jumper wires.
    Adafruit_ST7789::begin(LCD_SPI_HZ);
  }
};

Display display(&SPI, LCD_CS, LCD_DC, LCD_RST);
GFXcanvas16 counter_canvas(COUNTER_WIDTH, COUNTER_HEIGHT);
bool display_ready = false;
bool backlight_on = false;
bool counter_visible = false;
bool button_ready = false;
uint32_t press_count = 0;
uint32_t counter_draw_us = 0;
uint32_t counter_draw_max_us = 0;
uint32_t page_draw_us = 0;
uint32_t usb_write_max_us = 0;
uint32_t usb_messages_dropped = 0;
uint32_t loop_gap_max_us = 0;

struct ButtonSnapshot {
  uint32_t count = 0;
  uint32_t max_sample_gap_us = 0;
  bool pressed = false;
};

ButtonSnapshot button_state;
portMUX_TYPE button_mux = portMUX_INITIALIZER_UNLOCKED;

void send_usb(const char *format, ...) {
  const uint32_t start_us = micros();
  char message[768];
  va_list args;
  va_start(args, format);
  const int length = vsnprintf(message, sizeof(message), format, args);
  va_end(args);
  // A missing or slow USB reader must never delay the screen.
  if (length <= 0 || length >= static_cast<int>(sizeof(message)) || Serial.availableForWrite() < length) {
    ++usb_messages_dropped;
  } else if (Serial.write(reinterpret_cast<const uint8_t *>(message), length) != static_cast<size_t>(length)) {
    ++usb_messages_dropped;
  }
  const uint32_t elapsed_us = micros() - start_us;
  if (elapsed_us > usb_write_max_us) usb_write_max_us = elapsed_us;
}

ButtonSnapshot read_button_state() {
  portENTER_CRITICAL(&button_mux);
  const ButtonSnapshot snapshot = button_state;
  portEXIT_CRITICAL(&button_mux);
  return snapshot;
}

void sample_button(void *) {
  ButtonDebouncer button(BUTTON_DEBOUNCE_MS, digitalRead(BUTTON_MID) == LOW, millis());
  TickType_t next_wake = xTaskGetTickCount();
  uint32_t previous_sample_us = micros();
  for (;;) {
    const uint32_t now_us = micros();
    const uint32_t gap_us = now_us - previous_sample_us;
    previous_sample_us = now_us;
    const bool pressed = button.update(digitalRead(BUTTON_MID) == LOW, millis());
    portENTER_CRITICAL(&button_mux);
    if (pressed) ++button_state.count;
    button_state.pressed = button.pressed();
    if (gap_us > button_state.max_sample_gap_us) button_state.max_sample_gap_us = gap_us;
    portEXIT_CRITICAL(&button_mux);
    vTaskDelayUntil(&next_wake, pdMS_TO_TICKS(1));
  }
}

void draw_counter_value() {
  const uint32_t start_us = micros();
  counter_canvas.fillScreen(ST77XX_BLACK);
  counter_canvas.setTextWrap(false);
  counter_canvas.setTextColor(ST77XX_GREEN);
  counter_canvas.setTextSize(3);
  counter_canvas.setCursor(0, 0);
  counter_canvas.print(press_count);
  display.drawRGBBitmap(24, 90, counter_canvas.getBuffer(), COUNTER_WIDTH, COUNTER_HEIGHT);
  counter_draw_us = micros() - start_us;
  if (counter_draw_us > counter_draw_max_us) counter_draw_max_us = counter_draw_us;
}

void draw_counter() {
  const uint32_t start_us = micros();
  display.fillScreen(ST77XX_BLACK);
  display.drawRect(0, 0, 240, 240, ST77XX_WHITE);
  display.setTextWrap(false);
  display.setTextColor(ST77XX_WHITE);
  display.setTextSize(2);
  display.setCursor(24, 28);
  display.print("BUTTON COUNTER");
  display.setTextColor(ST77XX_WHITE);
  display.setTextSize(1);
  display.setCursor(24, 166);
  display.print("Press the stick: +1");
  display.setCursor(24, 190);
  display.print("MID -> GPIO14");
  display.setCursor(24, 208);
  display.print("COM -> GND");
  draw_counter_value();
  counter_visible = true;
  page_draw_us = micros() - start_us;
}

void draw_test_pattern() {
  counter_visible = false;
  display.fillScreen(ST77XX_BLACK);
  display.fillRect(0, 0, 80, 64, ST77XX_RED);
  display.fillRect(80, 0, 80, 64, ST77XX_GREEN);
  display.fillRect(160, 0, 80, 64, ST77XX_BLUE);
  display.drawRect(0, 0, 240, 240, ST77XX_WHITE);
  display.setTextWrap(false);
  display.setTextSize(2);
  display.setTextColor(ST77XX_WHITE);
  display.setCursor(10, 24);
  display.print("R");
  display.setTextColor(ST77XX_BLACK);
  display.setCursor(90, 24);
  display.print("G");
  display.setTextColor(ST77XX_WHITE);
  display.setCursor(170, 24);
  display.print("B");
  display.setTextSize(4);
  display.setCursor(24, 85);
  display.print("HELLO!");
  display.setTextSize(2);
  display.setCursor(24, 140);
  display.print("ESP32-S3");
  display.setTextSize(1);
  display.setCursor(24, 175);
  display.print("ST7789 240x240 / SPI 8MHz");
  display.setCursor(24, 197);
  display.print("SCK40 MOSI41 RST21");
  display.setCursor(24, 211);
  display.print("DC47 CS42 BL38");
}

void handle_command(const char *command) {
  if (strcmp(command, "STATUS") == 0) {
    const ButtonSnapshot button = read_button_state();
    send_usb("STATUS firmware=display_serial configured=ST7789 size=240x240 "
                  "ready=%d backlight=%d uptime_ms=%lu flash=%u psram=%u "
                  "sck=40 mosi=41 rst=21 dc=47 cs=42 bl=38 spi_hz=%lu "
                  "revision=button-counter-usb-nonblocking button_gpio=14 raw_mid=%d mid=%d count=%lu "
                  "button_ready=%d debounce_ms=%lu sample_gap_max_us=%lu "
                  "counter_draw_us=%lu page_draw_us=%lu counter_draw_max_us=%lu "
                  "usb_write_max_us=%lu usb_dropped=%lu loop_gap_max_us=%lu\n",
                  display_ready, backlight_on, millis(), ESP.getFlashChipSize(),
                  ESP.getPsramSize(), LCD_SPI_HZ, digitalRead(BUTTON_MID),
                  button.pressed ? LOW : HIGH, static_cast<unsigned long>(button.count),
                  button_ready, static_cast<unsigned long>(BUTTON_DEBOUNCE_MS),
                  static_cast<unsigned long>(button.max_sample_gap_us),
                  static_cast<unsigned long>(counter_draw_us), static_cast<unsigned long>(page_draw_us),
                  static_cast<unsigned long>(counter_draw_max_us), static_cast<unsigned long>(usb_write_max_us),
                  static_cast<unsigned long>(usb_messages_dropped), static_cast<unsigned long>(loop_gap_max_us));
    return;
  }
  if (!display_ready) {
    send_usb("ERROR display initialization failed\n");
    return;
  }
  if (strcmp(command, "COUNTER") == 0) {
    if (counter_visible) draw_counter_value();
    else draw_counter();
  } else if (strcmp(command, "TEST") == 0) {
    draw_test_pattern();
  } else if (strcmp(command, "RED") == 0) {
    counter_visible = false;
    display.fillScreen(ST77XX_RED);
  } else if (strcmp(command, "GREEN") == 0) {
    counter_visible = false;
    display.fillScreen(ST77XX_GREEN);
  } else if (strcmp(command, "BLUE") == 0) {
    counter_visible = false;
    display.fillScreen(ST77XX_BLUE);
  } else if (strcmp(command, "WHITE") == 0) {
    counter_visible = false;
    display.fillScreen(ST77XX_WHITE);
  } else if (strcmp(command, "BLACK") == 0) {
    counter_visible = false;
    display.fillScreen(ST77XX_BLACK);
  } else if (strcmp(command, "LIGHT_ON") == 0) {
    digitalWrite(LCD_BL, HIGH);
    backlight_on = true;
  } else if (strcmp(command, "LIGHT_OFF") == 0) {
    digitalWrite(LCD_BL, LOW);
    backlight_on = false;
  } else {
    send_usb("ERROR unknown command; use STATUS COUNTER TEST RED GREEN BLUE WHITE "
             "BLACK LIGHT_ON LIGHT_OFF\n");
    return;
  }
  send_usb("OK %s\n", command);
}

void setup() {
  Serial.setTxBufferSize(1024);
  Serial.setTxTimeoutMs(0);
  Serial.begin(115200);
  pinMode(BUTTON_MID, INPUT_PULLUP);
  // Keep sampling above loopTask priority while SPI drawing or USB output blocks.
  button_ready = xTaskCreatePinnedToCore(sample_button, "button", 2048, nullptr, 2,
                                       nullptr, ARDUINO_RUNNING_CORE) == pdPASS;
  if (!button_ready) {
    send_usb("ERROR button task creation failed\n");
    return;
  }
  pinMode(LCD_BL, OUTPUT);
  digitalWrite(LCD_BL, LOW);
  if (!counter_canvas.getBuffer()) {
    send_usb("ERROR counter canvas allocation failed\n");
    return;
  }
  if (!SPI.begin(LCD_SCK, -1, LCD_MOSI, LCD_CS)) {
    send_usb("ERROR SPI initialization failed\n");
    return;
  }
  display.init(240, 240, SPI_MODE0);
  display.setRotation(0);
  draw_counter();
  digitalWrite(LCD_BL, HIGH);
  backlight_on = true;
  display_ready = true;
  send_usb("READY display_serial button-counter-usb-nonblocking; MID=14; visual check required\n");
}

void loop() {
  static uint32_t previous_loop_us = micros();
  const uint32_t now_us = micros();
  const uint32_t gap_us = now_us - previous_loop_us;
  previous_loop_us = now_us;
  if (gap_us > loop_gap_max_us) loop_gap_max_us = gap_us;
  static char command[32];
  static size_t length = 0;
  static bool overflow = false;
  while (Serial.available()) {
    const char ch = Serial.read();
    if (ch == '\r') continue;
    if (ch == '\n') {
      if (overflow) {
        send_usb("ERROR command too long\n");
      } else if (length > 0) {
        command[length] = '\0';
        handle_command(command);
      }
      length = 0;
      overflow = false;
    } else if (length < sizeof(command) - 1) {
      command[length++] = ch;
    } else {
      overflow = true;
    }
  }
  const ButtonSnapshot button = read_button_state();
  if (button.count != press_count) {
    press_count = button.count;
    if (display_ready) {
      if (counter_visible) draw_counter_value();
      else draw_counter();
    }
    send_usb("EVENT MID count=%lu\n", static_cast<unsigned long>(press_count));
  }
  delay(1);
}
