# 电子名片桌面实验接线图册

## 当前确定方案

第一张图为 [PN532 → ESP32-S3-CAM SPI 接线图](pn532-esp32-spi.html)：采用原 Image Oracle 的 ESP32-S3-CAM N16R8，拆下 TFT 和按键，复用 GPIO40/41/42，新增 GPIO39 作 MISO。PN532 按用户到货照片与 ITEAD 同外形板资料画出正面、双排 26 针、SET0/SET1 和六根接线。ESP32 按已验证的 [Image Oracle 板卡针序](../../image-oracle/wiring-diagrams/display-pin-locations.html)画出完整左右排针丝印。

**验证边界：**按图接线、SET0=L、SET1=H 后，[PN532 探测固件](../firmware/pn532_probe/README.md)返回 `PROBE_OK chip=0x32 firmware=1.6`。随后[固定网址 NDEF 固件](../firmware/pn532_ndef_test/README.md)使手机弹出并正确打开 `https://example.com`。这验证了当前六线连接；双排针仍未逐针量通断，其他接口和最终名片板尚未验证。

| 图 | 内容 | 状态 |
| --- | --- | --- |
| [PN532 SPI 接线](pn532-esp32-spi.html) | 两块板外形、完整排针、PN532 1–26 物理针号、六根线逐根高亮 | SPI 探测和固定网址手机读取通过 |

可编辑图源位于 [sources/pn532-esp32-spi.html](sources/pn532-esp32-spi.html)，独立页面可直接在浏览器打开。详细接线表、依据与测试记录见 [NFC 桌面实验](../docs/nfc-bench-test.md#pn532-双排针与接线实测)。改线或拨动开关前先拔 USB。
