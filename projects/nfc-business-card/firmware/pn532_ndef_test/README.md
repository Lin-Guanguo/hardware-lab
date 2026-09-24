# PN532 NDEF 网址模拟测试

## 当前确定方案

本工程复用已通过 SPI 探测的 ESP32-S3-CAM 与 PN532 六线接法，模拟只读 NFC Type 4 标签。上电默认提供 `https://example.com`；串口可发送 `URL <地址>` 临时切换到其他 HTTPS 地址或实验用的 `weixin://` 地址，无需反复烧录。当前程序尚未接入实体按键或墨水屏。接线与 SET0=L、SET1=H 见 [NFC 桌面实验](../../docs/nfc-bench-test.md#pn532-双排针与接线实测)。

使用 [Seeed-Studio/PN532](../../../../upstreams/seeed-pn532) 的 `arduino` 分支和 [don/NDEF](../../../../upstreams/ndef) 的 `master` 分支，分别锁定 `e44820e4ecbffbae00419b404b655fd269582741`、`838d3b68a62c5b95158b4ab4bdeabb3a5225001f`；许可证在各子模块中。源文件没有复制到本项目。使用仓库中 Image Oracle 的 Arduino CLI 1.5.1 与 ESP32 core 3.3.11。

从仓库根目录构建：

```sh
bash projects/image-oracle/scripts/arduino.sh compile \
  --fqbn 'esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=opi' \
  --library upstreams/seeed-pn532 --library upstreams/ndef \
  --build-path projects/nfc-business-card/build/pn532_ndef_test \
  --warnings default \
  projects/nfc-business-card/firmware/pn532_ndef_test
```

烧录到已确认的 ESP32-S3-CAM：

```sh
(
  cd projects/nfc-business-card/build/pn532_ndef_test
  uv tool run --offline --from esptool==5.1.0 esptool \
    --chip esp32s3 --port /dev/cu.usbmodem1101 \
    --before usb-reset --after watchdog-reset write-flash @flash_args
)
```

串口发送 `STATUS\n` 可读取 PN532 状态及当前地址；发送 `URL https://example.org\n`，看到 `NDEF_URL_SET` 后再用 `STATUS` 确认新地址。地址必须以 `https://` 或 `weixin://` 开头，编码后的 NDEF 消息不得超过 120 字节；非法或过长地址返回 `NDEF_URL_REJECTED`，原地址继续有效。切换前先移开手机，切换后再碰卡。串口选择只保存在 RAM 中，ESP32 重启后恢复默认地址。手机靠近板载天线时，程序在读卡会话结束后输出 `NDEF_SESSION`。USB 口使用靠 EN/RST 的原生 USB-C；通过 `NativeUsbSerial` 打开可避免串口控制线引发复位，做法见 [USB/UART 记录](../../../image-oracle/docs/usb-uart-notes.md)。

Seeed 库的 `PN532::SAMConfig()` 将有效的零载荷响应视为失败；本工程直接通过传输接口确认 `SAMConfiguration` 的完整响应，`sam_response=0` 表示成功。SPI 实例在库初始化后显式设置为 MODE0、低位先传、1 MHz，以匹配当前板卡。未修改子模块源码。

2026-09-24 构建、烧录及写入摘要校验通过；实机 `STATUS` 返回 `NDEF_READY url=https://example.com chip=0x32 firmware=1.6 sam_response=0`，证明固件与 PN532 初始化成功。用户将手机靠近后，串口出现 `NDEF_SESSION`；用户报告手机弹出“是否打开链接”，打开后确认网址是 `https://example.com`。手机型号与系统版本未记录；不同手机的系统提示仍需分别实测。

2026-09-25 增加串口 `URL` 临时切换，用于逐一测试用户提供的小红书主页短链、微信个人二维码解析出的 HTTPS 地址，以及未有官方个人跳转保证的 `weixin://` 形式。个人微信二维码的完整地址不写入仓库；本工程上电默认不会发布个人账号信息。构建与烧录通过，实机切到小红书短链后 `STATUS` 返回 `NDEF_READY`。用户手机先提示网址，点击后经浏览器打开正确的小红书主页；直接进入 App 尚未验证。个人微信二维码解析出的 `https://u.wechat.com/...` 也成功发布，但手机经浏览器打开微信下载页，没有进入个人加好友页。`weixin://addfriend/...` 出现应用选择卡片，选择微信后没有进一步页面；换用另一人的微信号后也未进入加好友页。实验结束时已切回小红书链接，重启后仍恢复默认地址。详细比较见 [NFC 桌面实验](../../docs/nfc-bench-test.md#个人主页与微信入口实测2026-09-25)。
