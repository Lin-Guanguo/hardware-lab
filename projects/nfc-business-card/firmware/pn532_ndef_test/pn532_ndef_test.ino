#include <SPI.h>
#include <PN532_SPI.h>
#include <emulatetag.h>
#include <NdefMessage.h>

constexpr uint8_t kSckPin = 40;
constexpr uint8_t kMisoPin = 39;
constexpr uint8_t kMosiPin = 41;
constexpr uint8_t kCsPin = 42;
constexpr char kTestUrl[] = "https://example.com";

class ConfiguredPN532SPI : public PN532_SPI {
 public:
  using PN532_SPI::PN532_SPI;

  void begin() override {
    PN532_SPI::begin();
    SPI.setDataMode(SPI_MODE0);
    SPI.setBitOrder(LSBFIRST);
    SPI.setFrequency(1000000);
    digitalWrite(kCsPin, HIGH);
  }
};

ConfiguredPN532SPI transport(SPI, kCsPin);
EmulateTag tag(transport);
uint8_t ndefBuffer[120];
uint8_t uid[3] = {0x12, 0x34, 0x56};
bool ready = false;
uint32_t pn532Version = 0;
int16_t samResponse = -1;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(100);
  SPI.begin(kSckPin, kMisoPin, kMosiPin, kCsPin);

  NdefMessage message;
  message.addUriRecord(kTestUrl);
  const int size = message.getEncodedSize();
  if (size <= 0 || size > static_cast<int>(sizeof(ndefBuffer))) {
    Serial.println("NDEF_FAIL message_size");
    return;
  }

  message.encode(ndefBuffer);
  tag.setNdefFile(ndefBuffer, size);
  tag.setUid(uid);
  tag.setTagWriteable(false);
  PN532 probe(transport);
  probe.begin();
  pn532Version = probe.getFirmwareVersion();
  if (pn532Version == 0) {
    Serial.println("NDEF_FAIL no_pn532_response");
    return;
  }
  // The valid SAMConfiguration response has zero payload bytes; upstream SAMConfig() treats it as failure.
  const uint8_t samCommand[] = {PN532_COMMAND_SAMCONFIGURATION, 0x01, 0x14, 0x01};
  uint8_t response[8];
  if (transport.writeCommand(samCommand, sizeof(samCommand)) == 0) {
    samResponse = transport.readResponse(response, sizeof(response), 1000);
  }
  if (samResponse != 0) {
    Serial.println("NDEF_FAIL pn532_init");
    return;
  }

  ready = true;
  Serial.printf("NDEF_READY url=%s bytes=%d\n", kTestUrl, size);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "STATUS") {
      Serial.printf("NDEF_%s url=%s chip=0x%02lX firmware=%lu.%lu sam_response=%d\n",
                    ready ? "READY" : "FAIL", kTestUrl,
                    (pn532Version >> 24) & 0xFF, (pn532Version >> 16) & 0xFF,
                    (pn532Version >> 8) & 0xFF, samResponse);
    }
  }
  if (!ready) {
    delay(1000);
    return;
  }
  if (tag.emulate(1000)) {
    Serial.println("NDEF_SESSION");
  }
}
