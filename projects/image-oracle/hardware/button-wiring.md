# 五向按键：中心键与屏幕共地

## 已确认与待验证

2026-09-19，用户提供一块绿色导航按键板的近照；照片中排针从上到下为 `COM UP DWN LFT RHT MID SET RST`。中央按杆有四向和按下操作，另外有 SET、RST 两个独立按钮。COM／MID 接法已通过计数和定格交互验证；具体厂家、PCB 版本及其他触点尚未逐项核对。

当前主板为已验证的 ESP32-S3-CAM N16R8。GPIO14 未被相机、屏幕或原生 USB 占用；屏幕接线保持[原表](display-wiring.md)。方案采用 GPIO14 内部上拉，COM 接 GND，按下 MID 时预期读到 LOW。该接法不向按钮板连接 VCC，也不需要外接上拉电阻。

## 共地接线

先拔掉 USB。准备三根母对公杜邦线和一根母对母杜邦线：母头是带孔插座，套模块排针；公头露出金属针，插面包板。

1. 拆下原来直接连接主板 GND 与屏幕 GND 的母对母线，其余七根屏幕线保留。
2. 三根母对公线分别连接：主板 GND → a5、屏幕 GND → b5、按键 COM → c5。
3. 一根母对母线连接：按键 MID → 主板丝印 `14`。
4. 其他按键脚悬空；不要将主板 3V3 或 5V 插进这个共地孔组。

```text
主板 GND ── a5 ┐
屏幕 GND ── b5 ├── 同一块内部金属片：a5、b5、c5、d5、e5
按键 COM ── c5 ┘

按键 MID ───────── 主板 GPIO14
```

孔号只是便于说明：选择普通接线区任意一组相通的五孔即可，不需要使用两侧电源轨。典型 a～j 面包板中，同编号 a～e 相通；a5 与 a6 不通，e5 与跨中间沟的 f5 也不通。三根线插三个不同孔，不把线挤进同一个孔。实物编号或方向不同时，先对照孔组与中间沟。

主板若按金属屏蔽罩朝前、天线朝上、两个 USB 口朝下摆放，`14` 在左排倒数第二针，其下是 `5V`；仍以实物丝印为准。按键板的 RST 只是一个按钮触点，本实验不接主板 EN/RST。

## 程序与验收

[屏幕程序](../firmware/display_serial/README.md)已增加中心键计数：10 ms 消抖，每次按下加一，长按不连加，重启归零。2026-09-19 用户已实际操作按键，报告旧版快速连按漏计数、整屏刷新明显；基本按键路径已验证。

用户确认独立采样版计数不再丢失，但持续按压后画面延迟；已进一步烧录 `revision=button-counter-usb-nonblocking`，修正无串口读取端时 USB 日志阻塞绘图的问题。实机压力测试通过，接线不变；用户持续连按复测确认“始终跟手，问题解决”。长按不连加的实物专项验收仍待补充，详见[按键启动记录](../docs/button-bringup.md)。

原显示测试程序的源码和烧录文件保留于被忽略的 `artifacts/firmware/display-smoke-20260919/`，附 SHA-256 清单；完整原厂备份及相机基线仍保留。

当前板上运行第三个 [oracle_live](../firmware/oracle_live/README.md) 程序，沿用同一接线；MID 将左侧预览定格到右侧并更新答案，用户已确认交互正常。

## 依据

- 用户提供的按键正面丝印照片，以及项目现有相机与屏幕 GPIO 配置。
- [同类八针模块说明](https://sensorembedded.com/index.php?filename=5D+ROCKER+JOYSTICK.pdf&route=extension/module/document/download)：用于交叉核对 COM 与七个触点的含义，不作为实物 PCB 版本或实测结果。
- [Arduino-ESP32 GPIO 文档](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/gpio.html)：`INPUT_PULLUP` 与 `digitalRead()`。
- [SparkFun 面包板结构说明](https://learn.sparkfun.com/tutorials/how-to-use-a-breadboard/all)。
