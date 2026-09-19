#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_ST7789.h>
#include <stdarg.h>
#include "esp_camera.h"
#include "jpeg_decoder.h"
#include "oracle_image.h"
#include "../display_serial/button_debouncer.h"

constexpr int LCD_SCK = 40, LCD_MOSI = 41, LCD_RST = 21;
constexpr int LCD_DC = 47, LCD_CS = 42, LCD_BL = 38, BUTTON_MID = 14;
constexpr uint32_t LCD_SPI_HZ = 8000000;
constexpr size_t CAMERA_WIDTH = 160, CAMERA_HEIGHT = 120;
constexpr size_t IMAGE_WIDTH = 112, IMAGE_HEIGHT = 84;
constexpr size_t IMAGE_PIXELS = IMAGE_WIDTH * IMAGE_HEIGHT;
constexpr size_t IMAGE_BYTES = IMAGE_PIXELS * sizeof(uint16_t);
constexpr int LIVE_X = 6, FROZEN_X = 122, IMAGE_Y = 48;

class Display : public Adafruit_ST7789 {
 public:
  using Adafruit_ST7789::Adafruit_ST7789;
  void begin(uint32_t = 0) override { Adafruit_ST7789::begin(LCD_SPI_HZ); }
};

struct CameraState {
  bool initialized = false;
  esp_err_t error = ESP_OK;
  uint16_t sensor_pid = 0;
  uint32_t frames = 0, frame_ms = 0, errors = 0;
  uint32_t capture_us = 0, decode_us = 0;
};

struct ButtonState {
  uint32_t presses = 0, sample_gap_max_us = 0;
  bool pressed = false;
};

Display display(&SPI, LCD_CS, LCD_DC, LCD_RST);
GFXcanvas16 answer_canvas(224, 56);
uint16_t *decoded_pixels = nullptr, *camera_pixels = nullptr, *shared_pixels = nullptr;
uint16_t *live_pixels = nullptr, *frozen_pixels = nullptr;
SemaphoreHandle_t frame_mutex = nullptr;
CameraState camera_state;
ButtonState button_state;
portMUX_TYPE button_mux = portMUX_INITIALIZER_UNLOCKED;
bool display_ready = false, tasks_ready = false, has_snapshot = false;
uint32_t live_frame = 0, frozen_frame = 0, snapshots = 0, frozen_hash = 0;
uint32_t preview_frames = 0, preview_draw_max_us = 0, snapshot_draw_max_us = 0;
uint32_t usb_write_max_us = 0, usb_dropped = 0, loop_gap_max_us = 0;
uint32_t consumed_presses = 0;

void send_usb(const char *format, ...) {
  const uint32_t started = micros();
  char message[896];
  va_list args;
  va_start(args, format);
  const int length = vsnprintf(message, sizeof(message), format, args);
  va_end(args);
  if (length <= 0 || length >= static_cast<int>(sizeof(message)) || Serial.availableForWrite() < length) {
    ++usb_dropped;
  } else if (Serial.write(reinterpret_cast<const uint8_t *>(message), length) != static_cast<size_t>(length)) {
    ++usb_dropped;
  }
  const uint32_t elapsed = micros() - started;
  if (elapsed > usb_write_max_us) usb_write_max_us = elapsed;
}

ButtonState read_button() {
  portENTER_CRITICAL(&button_mux);
  const ButtonState state = button_state;
  portEXIT_CRITICAL(&button_mux);
  return state;
}

CameraState read_camera() {
  if (!frame_mutex) return {};
  xSemaphoreTake(frame_mutex, portMAX_DELAY);
  const CameraState state = camera_state;
  xSemaphoreGive(frame_mutex);
  return state;
}

void sample_button(void *) {
  ButtonDebouncer button(10, digitalRead(BUTTON_MID) == LOW, millis());
  TickType_t next_wake = xTaskGetTickCount();
  uint32_t previous_us = micros();
  for (;;) {
    const uint32_t now_us = micros();
    const uint32_t gap = now_us - previous_us;
    previous_us = now_us;
    const bool press = button.update(digitalRead(BUTTON_MID) == LOW, millis());
    portENTER_CRITICAL(&button_mux);
    if (press) ++button_state.presses;
    button_state.pressed = button.pressed();
    if (gap > button_state.sample_gap_max_us) button_state.sample_gap_max_us = gap;
    portEXIT_CRITICAL(&button_mux);
    vTaskDelayUntil(&next_wake, pdMS_TO_TICKS(1));
  }
}

void capture_camera(void *) {
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 11; config.pin_d1 = 9; config.pin_d2 = 8; config.pin_d3 = 10;
  config.pin_d4 = 12; config.pin_d5 = 18; config.pin_d6 = 17; config.pin_d7 = 16;
  config.pin_xclk = 15; config.pin_pclk = 13; config.pin_vsync = 6; config.pin_href = 7;
  config.pin_sccb_sda = 4; config.pin_sccb_scl = 5;
  config.pin_pwdn = -1; config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QQVGA;
  config.jpeg_quality = 12;
  config.fb_count = 2;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;
  const esp_err_t result = esp_camera_init(&config);
  xSemaphoreTake(frame_mutex, portMAX_DELAY);
  camera_state.initialized = result == ESP_OK;
  camera_state.error = result;
  if (result == ESP_OK) camera_state.sensor_pid = esp_camera_sensor_get()->id.PID;
  xSemaphoreGive(frame_mutex);
  if (result != ESP_OK) {
    vTaskDelete(nullptr);
    return;
  }

  for (;;) {
    const uint32_t started_ms = millis();
    const uint32_t capture_started = micros();
    camera_fb_t *frame = esp_camera_fb_get();
    const uint32_t capture_us = micros() - capture_started;
    bool valid = frame && frame->format == PIXFORMAT_JPEG &&
                 frame->width == CAMERA_WIDTH && frame->height == CAMERA_HEIGHT;
    const uint32_t decode_started = micros();
    if (valid) {
      esp_jpeg_image_cfg_t jpeg = {};
      jpeg.indata = frame->buf;
      jpeg.indata_size = frame->len;
      jpeg.outbuf = reinterpret_cast<uint8_t *>(decoded_pixels);
      jpeg.outbuf_size = CAMERA_WIDTH * CAMERA_HEIGHT * sizeof(uint16_t);
      jpeg.out_format = JPEG_IMAGE_FORMAT_RGB565;
      jpeg.out_scale = JPEG_IMAGE_SCALE_0;
      esp_jpeg_image_output_t output = {};
      valid = esp_jpeg_decode(&jpeg, &output) == ESP_OK &&
              output.width == CAMERA_WIDTH && output.height == CAMERA_HEIGHT;
      if (valid) resize_rgb565(decoded_pixels, CAMERA_WIDTH, CAMERA_HEIGHT,
                               camera_pixels, IMAGE_WIDTH, IMAGE_HEIGHT);
    }
    const uint32_t decode_us = micros() - decode_started;
    if (frame) esp_camera_fb_return(frame);
    // Hold the mutex only for publishing pixels and metadata, never camera or SPI I/O.
    xSemaphoreTake(frame_mutex, portMAX_DELAY);
    camera_state.capture_us = capture_us;
    camera_state.decode_us = decode_us;
    if (valid) {
      memcpy(shared_pixels, camera_pixels, IMAGE_BYTES);
      ++camera_state.frames;
      camera_state.frame_ms = millis();
    } else {
      ++camera_state.errors;
    }
    xSemaphoreGive(frame_mutex);
    const uint32_t elapsed_ms = millis() - started_ms;
    vTaskDelay(pdMS_TO_TICKS(elapsed_ms < 50 ? 50 - elapsed_ms : 1));
  }
}

void draw_answer() {
  answer_canvas.fillScreen(ST77XX_BLACK);
  answer_canvas.setTextWrap(false);
  answer_canvas.setTextSize(1);
  answer_canvas.setTextColor(ST77XX_WHITE);
  answer_canvas.setCursor(0, 0);
  answer_canvas.print("ORACLE");
  if (has_snapshot) {
    const bool answer = oracle_answer(frozen_hash);
    answer_canvas.setTextSize(4);
    answer_canvas.setTextColor(answer ? ST77XX_GREEN : ST77XX_YELLOW);
    answer_canvas.setCursor(0, 16);
    answer_canvas.print(answer ? "TRUE" : "FALSE");
    answer_canvas.setTextSize(1);
    answer_canvas.setTextColor(ST77XX_WHITE);
    answer_canvas.setCursor(144, 16);
    answer_canvas.print("IMAGE HASH");
    answer_canvas.setCursor(144, 32);
    answer_canvas.printf("%08lX", static_cast<unsigned long>(frozen_hash));
  } else {
    answer_canvas.setTextSize(2);
    answer_canvas.setCursor(0, 20);
    answer_canvas.print("PRESS TO ASK");
  }
  display.drawRGBBitmap(8, 152, answer_canvas.getBuffer(), 224, 56);
}

void draw_layout() {
  display.fillScreen(ST77XX_BLACK);
  display.setTextWrap(false);
  display.setTextColor(ST77XX_WHITE);
  display.setTextSize(2);
  display.setCursor(48, 8);
  display.print("IMAGE ORACLE");
  display.setTextSize(1);
  display.setTextColor(ST77XX_GREEN);
  display.setCursor(LIVE_X, 32);
  display.print("LIVE");
  display.setTextColor(ST77XX_CYAN);
  display.setCursor(FROZEN_X, 32);
  display.print("FROZEN");
  display.drawRect(LIVE_X - 1, IMAGE_Y - 1, IMAGE_WIDTH + 2, IMAGE_HEIGHT + 2, ST77XX_WHITE);
  display.drawRect(FROZEN_X - 1, IMAGE_Y - 1, IMAGE_WIDTH + 2, IMAGE_HEIGHT + 2, ST77XX_WHITE);
  display.setTextColor(ST77XX_WHITE);
  display.setCursor(LIVE_X + 20, IMAGE_Y + 38);
  display.print("STARTING...");
  display.setCursor(FROZEN_X + 26, IMAGE_Y + 38);
  display.print("PRESS MID");
  display.drawFastHLine(8, 144, 224, 0x4208);
  display.setCursor(60, 224);
  display.print("PRESS MID TO FREEZE");
  draw_answer();
}

void take_snapshot() {
  if (!display_ready || !live_frame) {
    send_usb("ERROR preview not ready\n");
    return;
  }
  const uint32_t started = micros();
  // Freeze exactly the completed preview, not a newer frame from the camera task.
  memcpy(frozen_pixels, live_pixels, IMAGE_BYTES);
  frozen_frame = live_frame;
  frozen_hash = oracle_hash(frozen_pixels, IMAGE_PIXELS);
  ++snapshots;
  has_snapshot = true;
  display.drawRGBBitmap(FROZEN_X, IMAGE_Y, frozen_pixels, IMAGE_WIDTH, IMAGE_HEIGHT);
  draw_answer();
  const uint32_t elapsed = micros() - started;
  if (elapsed > snapshot_draw_max_us) snapshot_draw_max_us = elapsed;
  send_usb("SNAP snapshot=%lu frame=%lu hash=%08lX oracle=%s\n",
           static_cast<unsigned long>(snapshots), static_cast<unsigned long>(frozen_frame),
           static_cast<unsigned long>(frozen_hash), oracle_answer(frozen_hash) ? "TRUE" : "FALSE");
}

void handle_command(const char *command) {
  if (strcmp(command, "STATUS") == 0) {
    const CameraState camera = read_camera();
    const ButtonState button = read_button();
    send_usb("STATUS firmware=oracle_live revision=1 ready=%d tasks=%d camera=%d camera_error=%d "
             "sensor_pid=%04X uptime_ms=%lu camera_frames=%lu preview_frames=%lu camera_errors=%lu "
             "live_frame=%lu frozen_frame=%lu snapshots=%lu hash=%08lX oracle=%s "
             "frame_age_ms=%lu capture_us=%lu decode_us=%lu preview_draw_max_us=%lu snapshot_draw_max_us=%lu "
             "button_presses=%lu sample_gap_max_us=%lu usb_write_max_us=%lu usb_dropped=%lu loop_gap_max_us=%lu\n",
             display_ready, tasks_ready, camera.initialized, camera.error, camera.sensor_pid, millis(),
             camera.frames, preview_frames, camera.errors, live_frame, frozen_frame, snapshots, frozen_hash,
             has_snapshot ? (oracle_answer(frozen_hash) ? "TRUE" : "FALSE") : "NONE",
             camera.frames ? millis() - camera.frame_ms : 0, camera.capture_us, camera.decode_us,
             preview_draw_max_us, snapshot_draw_max_us, button.presses, button.sample_gap_max_us,
             usb_write_max_us, usb_dropped, loop_gap_max_us);
  } else if (strcmp(command, "SNAP") == 0) {
    take_snapshot();
  } else if (strncmp(command, "ROW ", 4) == 0) {
    char *end = nullptr;
    const long row = strtol(command + 4, &end, 10);
    if (!has_snapshot || end == command + 4 || *end || row < 0 || row >= static_cast<long>(IMAGE_HEIGHT)) {
      send_usb("ERROR invalid row or no snapshot\n");
      return;
    }
    char pixels[IMAGE_WIDTH * 4 + 1];
    const char hex[] = "0123456789ABCDEF";
    for (size_t x = 0; x < IMAGE_WIDTH; ++x) {
      const uint16_t pixel = frozen_pixels[row * IMAGE_WIDTH + x];
      for (size_t digit = 0; digit < 4; ++digit) pixels[x * 4 + digit] = hex[(pixel >> (12 - digit * 4)) & 15];
    }
    pixels[IMAGE_WIDTH * 4] = '\0';
    send_usb("ROW snapshot=%lu y=%ld pixels=%s\n", snapshots, row, pixels);
  } else {
    send_usb("ERROR use STATUS SNAP or ROW <0..83>\n");
  }
}

void setup() {
  Serial.setTxBufferSize(1024);
  Serial.setTxTimeoutMs(0);
  Serial.begin(115200);
  pinMode(LCD_BL, OUTPUT);
  digitalWrite(LCD_BL, LOW);
  pinMode(BUTTON_MID, INPUT_PULLUP);
  if (!psramFound()) { send_usb("ERROR PSRAM unavailable\n"); return; }
  decoded_pixels = static_cast<uint16_t *>(ps_malloc(CAMERA_WIDTH * CAMERA_HEIGHT * sizeof(uint16_t)));
  camera_pixels = static_cast<uint16_t *>(ps_malloc(IMAGE_BYTES));
  shared_pixels = static_cast<uint16_t *>(ps_malloc(IMAGE_BYTES));
  live_pixels = static_cast<uint16_t *>(ps_malloc(IMAGE_BYTES));
  frozen_pixels = static_cast<uint16_t *>(ps_malloc(IMAGE_BYTES));
  frame_mutex = xSemaphoreCreateMutex();
  if (!decoded_pixels || !camera_pixels || !shared_pixels || !live_pixels || !frozen_pixels ||
      !frame_mutex || !answer_canvas.getBuffer()) { send_usb("ERROR allocation failed\n"); return; }
  if (!SPI.begin(LCD_SCK, -1, LCD_MOSI, LCD_CS)) { send_usb("ERROR SPI initialization failed\n"); return; }
  display.init(240, 240, SPI_MODE0);
  display.setRotation(0);
  draw_layout();
  display_ready = true;
  digitalWrite(LCD_BL, HIGH);
  const bool button_started = xTaskCreatePinnedToCore(sample_button, "button", 2048, nullptr, 2,
                                                     nullptr, ARDUINO_RUNNING_CORE) == pdPASS;
  const bool camera_started = xTaskCreatePinnedToCore(capture_camera, "preview", 8192, nullptr, 1,
                                                     nullptr, 0) == pdPASS;
  tasks_ready = button_started && camera_started;
  send_usb("READY oracle_live tasks=%d; MID freezes the visible preview\n", tasks_ready);
}

void loop() {
  static uint32_t previous_us = micros();
  const uint32_t now_us = micros();
  const uint32_t gap = now_us - previous_us;
  previous_us = now_us;
  if (gap > loop_gap_max_us) loop_gap_max_us = gap;
  static char command[32];
  static size_t length = 0;
  static bool overflow = false;
  for (int budget = 0; budget < 64 && Serial.available(); ++budget) {
    const char ch = Serial.read();
    if (ch == '\r') continue;
    if (ch == '\n') {
      if (overflow) send_usb("ERROR command too long\n");
      else if (length) { command[length] = '\0'; handle_command(command); }
      length = 0;
      overflow = false;
    } else if (length < sizeof(command) - 1) command[length++] = ch;
    else overflow = true;
  }
  const ButtonState button = read_button();
  if (consumed_presses != button.presses) {
    // Multiple presses between displayed frames request the same latest frozen view.
    consumed_presses = button.presses;
    take_snapshot();
  }
  if (display_ready && frame_mutex) {
    bool changed = false;
    xSemaphoreTake(frame_mutex, portMAX_DELAY);
    if (camera_state.frames != live_frame) {
      memcpy(live_pixels, shared_pixels, IMAGE_BYTES);
      live_frame = camera_state.frames;
      changed = true;
    }
    const esp_err_t camera_error = camera_state.error;
    xSemaphoreGive(frame_mutex);
    if (changed) {
      const uint32_t started = micros();
      display.drawRGBBitmap(LIVE_X, IMAGE_Y, live_pixels, IMAGE_WIDTH, IMAGE_HEIGHT);
      const uint32_t elapsed = micros() - started;
      if (elapsed > preview_draw_max_us) preview_draw_max_us = elapsed;
      ++preview_frames;
    }
    static bool error_shown = false;
    if (camera_error != ESP_OK && !error_shown) {
      display.fillRect(LIVE_X, IMAGE_Y, IMAGE_WIDTH, IMAGE_HEIGHT, ST77XX_BLACK);
      display.setTextColor(ST77XX_RED);
      display.setTextSize(1);
      display.setCursor(LIVE_X + 20, IMAGE_Y + 38);
      display.print("CAM ERROR");
      error_shown = true;
    }
  }
  delay(1);
}
