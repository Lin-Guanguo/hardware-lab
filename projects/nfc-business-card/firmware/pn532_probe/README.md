# PN532 SPI 探测固件

## 当前确定方案

本工程用于已有 ESP32-S3-CAM N16R8 与到货 PN532 的第一轮桌面通信检查，只读取 PN532 芯片型号和固件版本；**不进行手机卡模拟或名片链接测试**。上电启动后不会初始化或驱动 PN532 的四根 SPI 引脚。USB 串口收到 `PROBE` 后才开始访问模块；`STATUS` 只确认当前固件，无需连接 PN532。

使用 Image Oracle 已验证的本地 Arduino CLI 1.5.1、ESP32 core 3.3.11，以及通过 Arduino 库管理器安装的 Adafruit PN532 1.3.4、Adafruit BusIO 1.17.4。上游库：[Adafruit PN532](https://github.com/adafruit/Adafruit-PN532)，许可证随本地包保留。构建与烧录使用与 Image Oracle 相同的 ESP32-S3、16 MB Flash、OPI PSRAM 和 Hardware CDC 配置。

从仓库根目录构建：

```sh
bash projects/image-oracle/scripts/arduino.sh lib install --no-deps \
  'Adafruit BusIO@1.17.4' 'Adafruit PN532@1.3.4'
bash projects/image-oracle/scripts/arduino.sh compile \
  --fqbn 'esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=opi' \
  --build-path projects/nfc-business-card/build/pn532_probe \
  --warnings default \
  projects/nfc-business-card/firmware/pn532_probe
```

刷写前确认 `PN532` 尚未连接、目标串口确为原 Image Oracle 主板，且原程序恢复包的 `SHA256SUMS` 校验通过。烧录不会自动擦掉整片 Flash，只覆盖本程序所需区域。借用既有恢复流程：

```sh
(
  cd projects/nfc-business-card/build/pn532_probe
  uv tool run --offline --from esptool==5.1.0 esptool \
    --chip esp32s3 --port /dev/cu.usbmodem1101 \
    --before usb-reset --after watchdog-reset write-flash @flash_args
)
```

若设备不自动进下载模式，按 [Image Oracle 烧录说明](../../../image-oracle/firmware/oracle_live/README.md#构建烧录与恢复)手动进入 BOOT 模式；不要执行整片擦除。烧录后用 USB 串口发送 `STATUS\n`，应返回 `PN532_PROBE_READY pins_idle=1`。然后拔 USB，按[桌面实验的拟接线表](../../docs/nfc-bench-test.md#pn532-双排针与拟接线未通电验证)核对并连接 PN532，接回 USB 后发送 `PROBE\n`。只有收到 `PROBE_OK chip=0x32 ...` 才算 SPI 基本通信通过；仍不代表手机可读取 NDEF。

如果需要恢复 Image Oracle，用已校验的 `projects/image-oracle/artifacts/firmware/oracle-live-20260919/` 中 `flash_args` 按同一方法烧录，断电后按原接线接回 TFT。
