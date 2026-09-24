#include <Adafruit_PN532.h>

constexpr uint8_t kSckPin = 40;
constexpr uint8_t kMisoPin = 39;
constexpr uint8_t kMosiPin = 41;
constexpr uint8_t kCsPin = 42;

Adafruit_PN532 pn532(kSckPin, kMisoPin, kMosiPin, kCsPin);
bool spiStarted = false;

void printStatus() {
  Serial.printf("PN532_PROBE_READY pins_idle=%u\n", !spiStarted);
}

void setup() {
  pinMode(kSckPin, INPUT);
  pinMode(kMisoPin, INPUT);
  pinMode(kMosiPin, INPUT);
  pinMode(kCsPin, INPUT);
  Serial.begin(115200);
  Serial.setTimeout(250);
  printStatus();
}

void loop() {
  if (!Serial.available()) {
    delay(10);
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command == "STATUS") {
    printStatus();
    return;
  }

  if (command != "PROBE") {
    Serial.println("ERROR expected STATUS or PROBE");
    return;
  }

  Serial.println("PROBE_START");
  spiStarted = true;
  if (!pn532.begin()) {
    Serial.println("PROBE_FAIL spi_init");
    return;
  }

  const uint32_t version = pn532.getFirmwareVersion();
  if (version == 0) {
    Serial.println("PROBE_FAIL no_pn532_response");
    return;
  }

  Serial.printf("PROBE_OK chip=0x%02lX firmware=%lu.%lu\n",
                (version >> 24) & 0xFF, (version >> 16) & 0xFF,
                (version >> 8) & 0xFF);
}
