# V4 A4 GPIO 与固件接口（失败布局候选专用）

## 当前确定方案

2026-09-30：此映射已经同步 A4 的原理图和 PCB，并通过 256 个器件引脚对账、ERC 及原理图／PCB parity。**A4 布线被否决；映射只标识这个诊断工程，不是已验证硬件接口，也不应覆盖 A3。** 本仓库尚无这块 nRF52840 名片的固件工程；现有 PN532 例程运行于 ESP32-S3-CAM，不能混用。没有修改、构建或烧录 ESP32 固件。

## 原厂依据与限制

- [Raytac MDBT50Q Rev.L 本地原厂 PDF](../downloads/raytac_mdbt50q_rev_l.pdf)，§2.5，PDF／印刷页 14–17；§2.6 p17。SHA-256：`61fec8c0c9f8c33175be2237a8ebba73c6cfc0a3572fe3835fd341079c103d03`。从 [Raytac 文档入口](https://www.raytac.com/document/index.php?index_m_id=17)核对 Rev.L。
- [Nordic SPIM](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/spim.html)，Pin configuration、Instances／Configuration：GPIO 用 PSEL 选择；外设禁用时配置，同一个 GPIO 不能同时由两个外设驱动。SPIM2 不提供硬件 CS/DCX，最高 8 Mbps 是该实例能力，**不是本屏幕或本布线已验证的工作频率**。
- [Nordic TWIM](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/twim.html)，Master pin configuration、PSEL.SCL/SDA：支持端口／引脚选择；启用前配置开漏 GPIO 与正确输入状态。
- 模块上受射频影响的引脚只推荐 standard drive、low frequency；Rev.L 把低频定义到 10 kHz，并明确 SPI/I2C/UART/PWM 不属于这类用途。本次新分配的 SPI/I2C 引脚不在这些受限引脚中。不能由“有 GPIO 名称”推导任意可互换。
- P0.00/P0.01 保留外部低频晶振选择；P0.18 保留复位；USB D±、VBUS、VDD/VDDH、DCCH、SWD、NFC、ADC 和按键没有重分配。
- P1.09 的 TRACEDATA3 与 P0.11 的 TRACEDATA2 是复用功能。使用它们作屏幕 MOSI／EN 时不得同时启用对应硬件 trace 输出；正常 SWD 调试脚仍保留。

## 已写入 A4 的映射

| 网络 | A3 模块脚／GPIO | A4 模块脚／GPIO | 固件角色 |
| --- | --- | --- | --- |
| CHG_SCL | 16 / P0.27 | 36 / P0.14 | TWIM SCL，开漏 |
| CHG_SDA | 19 / P0.26 | 37 / P0.13 | TWIM SDA，开漏 |
| CHG_INT_N | 20 / P0.04 | 39 / P0.15 | 输入，保留外部上拉 |
| CHG_PG_N | 21 / P0.05 | 38 / P0.16 | 输入，保留外部上拉 |
| CHG_CE_N | 22 / P0.06 | 41 / P0.17 | 输出；保持现有低有效逻辑 |
| EPD_SCK_TBD | 36 / P0.14 | 24 / P0.08 | SPIM SCK |
| EPD_MOSI_TBD | 37 / P0.13 | 26 / P1.09 | SPIM MOSI；禁用同脚 trace |
| EPD_CS_N_TBD | 38 / P0.16 | 22 / P0.06 | 普通 GPIO 输出片选 |
| EPD_DC_TBD | 39 / P0.15 | 20 / P0.04 | 普通 GPIO 输出 |
| EPD_RESET_N_TBD | 41 / P0.17 | 19 / P0.26 | 普通 GPIO 输出复位 |
| EPD_BUSY_TBD | 24 / P0.08 | 16 / P0.27 | 输入；保持 R18 支路 |
| EPD_EN_TBD（未改） | 27 / P0.11 | 27 / P0.11 | U4 负载开关；禁用同脚 trace |

21 脚改为显式 NC，26 脚由 NC 改为 MOSI；没有修改库符号的物理引脚编号／名称。R5 是 SDA 上拉、R6 是 SCL 上拉；不要按位号排序猜信号。

后续固件可选 SPIM2 + TWIM0，以不同外设实例地址避开 SPIM0/TWIM0 共享资源。使用 GPIO 控制 CS/DC；MISO 不接。具体时钟、屏幕初始化、BQ25186 寄存器、充电允许条件及安全启动顺序仍须在真正的名片固件中实现和验证；本文件不是已完成驱动。

## 布局否决与下一次接口变更

电气兼容性没有证明路径排列正确。A4 把 MCU 上沿由左到右排成 MOSI、SCK、CS、DC、RESET、BUSY，而本次向左转入 J2 的折线构造使束内相交，详见 [A4 评审](v4-option-a4-review.md)。若重新分配顺序，必须再次同步工程与本接口文档，不能直接在固件里修补 PCB 网络差异。
