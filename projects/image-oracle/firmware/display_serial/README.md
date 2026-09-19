# ST7789 屏幕、中心键计数与 USB 命令测试

用于 ESP32-S3-CAM N16R8 和套装 1.54 寸、240×240 SPI 屏幕。接线见[屏幕接线表](../../hardware/display-wiring.md)和[中心键共地接线](../../hardware/button-wiring.md)，本工程不启用摄像头或 SD。

当前源码上电显示 `BUTTON COUNTER` 和计数 0；中心键每按一次加一，10 ms 消抖，长按不连加，重启归零。GPIO14 使用 `INPUT_PULLUP`，松开预期为 HIGH，按下接通 COM/GND 后为 LOW。通过原生 USB 发送命令可切换计数页、纯色、测试页和背光；切换页面后再次按键会回到计数页。

2026-09-19：已验证独立按键采样和数字局部重绘，局部绘图约 9.6 ms。用户随后确认计数不再丢失，但连续按压后画面合并更新；补测发现 USB 日志在电脑不读取时可等待约 2 秒。当前固件为 `revision=button-counter-usb-nonblocking`，将 USB 输出改为不等待、缓冲满时跳过消息；压力测试通过，用户持续连按复测确认“始终跟手，问题解决”，作为当前交互基线。验证记录见[按键启动记录](../../docs/button-bringup.md)。此前的 `HELLO!`、整屏计数和局部重绘版本均有本地备份。屏幕没有连接 MISO，串口 `ready=1`／`OK` 只表示程序已执行初始化或发送操作；本次显示与交互效果由用户目视确认。

## 按键与刷新方式

- `sample_button()` 是优先级 2 的 FreeRTOS 任务，在 Arduino 所用核心上每 1 ms 采样一次；高于绘图所在 `loopTask` 的优先级 1。采样任务只读取 GPIO、消抖和累计次数，不调用屏幕或串口。
- `button_debouncer.h` 要求按下和松开各自稳定至少 10 ms，只有新的稳定按下才加一。短于此阈值的电平变化会被过滤；真实触点的高速表现仍需实测。
- 主循环通过短临界区取得次数。数字先画到 180×24 的 `GFXcanvas16`，再整体写入屏幕对应区域，像素缓冲占 8,640 字节。标题、说明与边框只在进入计数页时绘制。
- 绘图期间按键任务继续累计；主循环可以一次显示最新总数，因此 `EVENT MID count=...` 是累计值通知，不保证每次按下都有单独一行日志。
- `send_usb()` 共用于事件、状态和命令回复。发送等待设为 0，先检查整条消息能否放入 TX 缓冲，放不下就跳过并累计 `usb_dropped`；不会为补发日志而等待。TX 缓冲设为 1,024 字节，以容纳一条完整状态回复，扩大缓冲本身不是解决阻塞的方法。
- 被跳过的是诊断消息，按键总数独立保存，可随时用 `STATUS` 查询。电脑不读取或持续发送大量命令时，命令回复也可能被跳过；恢复读取后重新发送所需命令。无需一直开着串口监视器来保证屏幕流畅。
- SPI 保持 8 MHz。切换 `TEST`／纯色页面或从其他页面回到计数页仍需整页绘图，耗时不代表按键停止采样。

## 固定配置与依赖

- Arduino CLI 1.5.1、ESP32 core 3.3.11，安装方式复用项目 `scripts/setup.sh`。
- 16 MB Flash、OPI 8 MB PSRAM、原生 Hardware CDC；分区与相机基线相同。
- GPIO：SCK40、MOSI41、RST21、DC47、CS42、BL38；MISO 不连接。
- 按键：MID14、COM/GND；其余六个按键信号悬空。
- SPI mode 0、8 MHz。上游 `init()` 会内部调用默认 32 MHz 的 `begin()`，因此用一个小派生类把初始化和绘图都限制在 8 MHz，适合先用杜邦线验证。
- 背光先拉低，完成测试图后拉高。该极性依据套装 GPIO 背光接法，仍需实物验证。

| 依赖 | 版本 | 上游来源 |
| --- | --- | --- |
| Adafruit ST7735 and ST7789 Library | 1.11.0 | [源码 tag](https://github.com/adafruit/Adafruit-ST7735-Library/tree/1.11.0) |
| Adafruit GFX Library | 1.12.6 | [源码 tag](https://github.com/adafruit/Adafruit-GFX-Library/tree/1.12.6) |
| Adafruit BusIO | 1.17.4 | [源码 tag](https://github.com/adafruit/Adafruit_BusIO/tree/1.17.4) |

库通过 Arduino Library Manager 安装在被 Git 忽略的 `downloads/arduino/user/libraries/`，保留上游源码及许可证，不复制进本工程。使用 `--no-deps` 后逐项指定所需版本；上游元数据中其他示例使用的 seesaw 和 SD 不在本 sketch 的依赖路径中。

## 编译

以下命令均从仓库根目录执行。

```sh
bash projects/image-oracle/scripts/build-display.sh
```

脚本先安装固定版本的三个库，再生成 `build/display_serial/` 下的固件。只编译，不烧录。

修改消抖逻辑后，可在 Mac 上运行行为测试（无需接板子）：

```sh
mkdir -p projects/image-oracle/build
c++ -std=c++17 -Wall -Wextra -pedantic \
  projects/image-oracle/tests/button_debouncer_test.cpp \
  -o projects/image-oracle/build/button_debouncer_test
projects/image-oracle/build/button_debouncer_test
```

测试覆盖按下／松开抖动、长按、100 次快速按压、毫秒计时回绕和上电时已按住。快速按压用例每次按下 15 ms、松开 15 ms，以 1 ms 步长模拟；这不替代实物测试。

连接实物后，可运行 USB 无读取端回归测试，约需 20 秒。建议先正常复位，因为诊断峰值从启动起累计。脚本临时切到 `TEST` 页面并排队八条状态回复，关闭串口读取端，让发送缓冲填满，再恢复读取与计数页；不生成虚拟按键计数。

```sh
uv run --offline projects/image-oracle/tests/usb_backpressure.py --port /dev/cu.usbmodem1101
```

通过条件：确实出现被跳过的 USB 消息；USB 输出和局部绘图峰值均小于 50 ms；主循环间隔小于 300 ms（包含约 196 ms 的完整测试页绘制）；按键采样间隔小于 10 ms。不要同时打开其他串口客户端。

## 烧录

先正常连接靠 EN/RST 的原生 USB-C 口，确认端口及设备身份，关闭其他占用串口的程序。当前端口通常为 `/dev/cu.usbmodem1101`，重新连接后仍需核对：

```sh
ls /dev/cu.*
uv run --with pyserial==3.5 python -m serial.tools.list_ports -v
```

原厂完整备份和恢复方法见[摄像头启动记录](../../docs/camera-bringup.md)。确认目标和备份后执行：

```sh
(
  cd projects/image-oracle/build/display_serial
  uv tool run --from esptool==5.1.0 esptool \
    --chip esp32s3 --port /dev/cu.usbmodem1101 \
    --before usb-reset --after watchdog-reset \
    write-flash @flash_args
)
```

`usb-reset` 请求进入下载模式；`@flash_args` 指定构建产生的地址和文件；写入完成会校验摘要，再尝试通过 watchdog 复位进入程序。如果仍停在下载模式，拔 USB，等 2 秒，不按任何按钮再插回。

若自动进入下载模式失败，先拔线、按住 BOOT 插入原生 USB，再松开 BOOT；重新确认端口后把命令中的 `--before usb-reset` 换成 `--before no-reset`。

## 在 Mac 控制屏幕

```sh
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 STATUS
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 RED
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 GREEN
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 BLUE
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 TEST
```

其余命令：`COUNTER`、`WHITE`、`BLACK`、`LIGHT_OFF`、`LIGHT_ON`。`TEST` 重画彩色测试页；`COUNTER` 显示当前计数而不清零，已在计数页时只刷新数字。背光若被关闭，需先发 `LIGHT_ON`。

新版 `STATUS` 包含 `revision=button-counter-usb-nonblocking`、即时读数 `raw_mid`、消抖后读数 `mid` 和累计值 `count`。附带诊断字段：

| 字段 | 含义 |
| --- | --- |
| `button_ready` | 按键采样任务是否创建成功 |
| `debounce_ms` | 电平稳定阈值，当前为 10 ms |
| `sample_gap_max_us` | 本次启动以来相邻两次按键采样的最大间隔 |
| `counter_draw_us` | 最近一次数字区域绘制耗时，包含内存绘制与 SPI 写入 |
| `counter_draw_max_us` | 本次启动以来数字区域绘制的最大耗时 |
| `page_draw_us` | 最近一次完整计数页绘制耗时，包含数字区域 |
| `usb_write_max_us` | 本次启动以来单次 `send_usb()` 最大耗时，包含格式化、缓冲检查与发送 |
| `usb_dropped` | 因缓冲不足、格式超长或未完整写入而跳过的 USB 消息数，不是漏掉的按键数 |
| `loop_gap_max_us` | 本次启动以来相邻两次主循环开始时刻的最大间隔，完整页面绘制也计入 |

所有 `_us` 字段单位为微秒，除以 1,000 得到毫秒。

两个 Python 客户端共用 `scripts/native_usb.py`：跳过 DTR／RTS 控制线操作，关闭 `HUPCL`，避免打开或关闭端口时把芯片重新送入下载模式。此连接方式适用于本次 macOS 原生 USB 场景，不能直接当作其他串口设备的通用设置。不要同时运行 `screen` 等另一个串口客户端。

## 切回相机基线

相机源码和构建产物保留在 `firmware/camera_serial/`、`build/camera_serial/`。需要恢复时运行原相机构建脚本，将烧录命令中的工作目录改为 `build/camera_serial`，烧录成功后再使用 `capture.py`。屏幕测试程序不响应 `SNAP`；复位本身不会切回相机程序。

实测进展见[屏幕启动记录](../../docs/display-bringup.md)。
