#include <Arduino.h>
#include "esp_camera.h"

bool camera_ready = false;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.printf("Image Oracle camera test; Flash=%u PSRAM=%u\n",
                 ESP.getFlashChipSize(), ESP.getPsramSize());

  if (!psramFound()) {
    Serial.println("ERROR PSRAM unavailable; check the board configuration");
    return;
  }

  // Xinlucity ESP32-S3-CAM camera connector, checked against the vendor sketch.
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 11;
  config.pin_d1 = 9;
  config.pin_d2 = 8;
  config.pin_d3 = 10;
  config.pin_d4 = 12;
  config.pin_d5 = 18;
  config.pin_d6 = 17;
  config.pin_d7 = 16;
  config.pin_xclk = 15;
  config.pin_pclk = 13;
  config.pin_vsync = 6;
  config.pin_href = 7;
  config.pin_sccb_sda = 4;
  config.pin_sccb_scl = 5;
  config.pin_pwdn = -1;
  config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 2;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;

  esp_err_t result = esp_camera_init(&config);
  if (result != ESP_OK) {
    Serial.printf("ERROR camera initialization failed: 0x%x\n", result);
    return;
  }

  sensor_t *sensor = esp_camera_sensor_get();
  const char *model = "unknown";
  switch (sensor->id.PID) {
    case OV2640_PID: model = "OV2640"; break;
    case OV3660_PID: model = "OV3660"; break;
    case OV5640_PID: model = "OV5640"; break;
  }
  camera_ready = true;
  Serial.printf("READY sensor=%s PID=0x%04x; send SNAP to capture\n",
                 model, sensor->id.PID);
}

void loop() {
  static char command[16];
  static size_t length = 0;
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\r') {
      continue;
    }
    if (ch != '\n') {
      if (length < sizeof(command) - 1) {
        command[length++] = ch;
      }
      continue;
    }

    command[length] = '\0';
    length = 0;
    if (strcmp(command, "SNAP") != 0) {
      Serial.println("ERROR expected SNAP");
      continue;
    }
    if (!camera_ready) {
      Serial.println("ERROR camera is not initialized; reset to inspect startup logs");
      continue;
    }

    Serial.printf("INFO sensor_pid=0x%04x flash=%u psram=%u\n",
                  esp_camera_sensor_get()->id.PID,
                  ESP.getFlashChipSize(), ESP.getPsramSize());
    camera_fb_t *frame = esp_camera_fb_get();
    if (frame == nullptr) {
      Serial.println("ERROR capture failed");
      continue;
    }
    if (frame->format != PIXFORMAT_JPEG) {
      esp_camera_fb_return(frame);
      Serial.println("ERROR expected a JPEG frame");
      continue;
    }

    Serial.printf("JPEG %u %u %u\n", static_cast<unsigned>(frame->len),
                   static_cast<unsigned>(frame->width),
                   static_cast<unsigned>(frame->height));
    Serial.write(frame->buf, frame->len);
    Serial.print("\nEND\n");
    Serial.flush();
    esp_camera_fb_return(frame);
  }
  delay(10);
}
