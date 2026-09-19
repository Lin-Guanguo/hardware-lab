# 中心按键与屏幕计数

本页记录实际操作与验证；技术原理和后续复用方法见[按键与屏幕响应知识笔记](responsive-input-display.md)。

## 接线与目标

2026-09-19，用户确认已按此前方案接好按键并连接 USB：COM 与主板、屏幕共地，MID 接 GPIO14。接线依据见[按键接线表](../hardware/button-wiring.md)，其他六个按键信号暂不接。

本轮验证中心键每按一次，屏幕计数加一；长按只计一次，松开后再次按下才继续计数。重新上电归零。摄像头保持原有接线，但本测试固件不启用拍摄。

## 构建与烧录

以下命令从仓库根目录执行。先枚举 USB，确认 `/dev/cu.usbmodem1101` 为此前同一主板的原生 USB JTAG/serial debug unit，VID/PID `303a:1001`；旧程序 `STATUS` 仍返回显示测试版本。

```sh
uv run --with pyserial==3.5 python -m serial.tools.list_ports -v
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 STATUS
bash projects/image-oracle/scripts/build-display.sh
```

原厂完整 16 MiB 备份及显示基线的 7 个文件重新计算 SHA-256，与已有清单一致。恢复资料见[相机启动记录](camera-bringup.md)及 `artifacts/firmware/display-smoke-20260919/`，文件未改动。

构建通过：程序占用 342,340 字节，静态 RAM 24,464 字节，应用二进制 342,496 字节。确认没有其他进程占用串口后执行：

```sh
(
  cd projects/image-oracle/build/display_serial
  uv tool run --from esptool==5.1.0 esptool \
    --chip esp32s3 --port /dev/cu.usbmodem1101 \
    --before usb-reset --after watchdog-reset \
    write-flash @flash_args
)
```

启动程序、分区表、OTA 引导数据和应用四段写入均通过摘要校验，watchdog 自动复位进入应用。

## 状态与实物验证

```sh
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 STATUS
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 COUNTER
```

烧录后的回复包含 `revision=button-counter button_gpio=14 raw_mid=1 mid=1 count=0`，同时 `ready=1 backlight=1`、Flash 为 16 MiB、PSRAM 为 8 MiB；重画计数页返回 `OK COUNTER`。这确认新固件运行和当前 GPIO 读数，屏幕画面仍需用户目视确认。

已请用户短按 3 次、长按约 2 秒再松开、最后短按 1 次，预期计数依次到 3、4、5，长按期间不重复增加。用户操作结果待回报。测试期间通过共用的 `NativeUsbSerial` 每 250 ms 查询状态并接收按键事件；原始串口记录保存在被 Git 忽略的 `logs/button-mid-*.log`。

## 快速连按漏计数与刷新修正

用户随后报告快速连按会漏计数，并能看到明显的从上到下刷新；旧固件查询时已有 `count=25`，基本按键到屏幕路径已由实际操作验证，但上述固定次数的验收未得到明确回报。

原因是旧版在同一循环里读取按键、调用 `fillScreen()` 清屏并重画全部文字。SPI 8 MHz 下，单次 240×240、16 bit 全屏像素传输的理论下限就是 `240 × 240 × 16 / 8000000 = 115.2 ms`，加上其他绘图更慢；绘图期间主循环不再读按键。旧版还要求电平稳定 30 ms，进一步限制了快速按压。

这次改动保留现有引脚和 8 MHz SPI：

1. 使用独立 FreeRTOS 任务，每 1 ms 采样并累计按下次数；通过短临界区与绘图循环共享快照。
2. 消抖阈值改为 10 ms，按下和松开都需要达到稳定时间；长按不重复计数。
3. 只刷新 180×24 的数字区域。先在内存画好数字及黑色背景，再一次写入对应矩形，避免先清空整个可见画面。

内存画布与局部重绘的依据见 [Adafruit 减少重绘闪烁说明](https://learn.adafruit.com/adafruit-gfx-graphics-library/minimizing-redraw-flicker)。此处没有加入屏幕扫描同步，不能据此保证所有情况下都无撕裂。

### 验证结果

2026-09-19，同一块开发板、同一端口测试：

| 项目 | 结果 |
| --- | --- |
| 旧版 `COUNTER` 命令往返，3 次 | 152.39、152.49、152.48 ms |
| 新版计数页 `COUNTER` 命令往返，4 次 | 10.93、10.44、10.33、11.00 ms |
| 新版固件内测得的数字绘图耗时 | 9.55～9.59 ms |
| 新版完整计数页绘图 | 约 159 ms，仅进入页面时执行 |
| 采样最大间隔，包含 `TEST` 和完整计数页切换 | 1.362 ms |
| 消抖行为测试 | 抖动、长按、100 次快速按压、计时回绕、上电按住均通过 |
| 固件构建 | 程序 344,428 字节，静态 RAM 24,520 字节；不含运行时分配的画布／任务栈 |
| 烧录 | 四段写入摘要校验通过，watchdog 自动复位 |
| 启动状态 | `revision=button-counter-partial ready=1 button_ready=1 count=0` |

命令往返包含 USB 与任务调度，不能直接当作纯 SPI 耗时。完整页面仍需约 159 ms，但这时采样任务继续工作。原始测量记录位于本地忽略目录 `logs/display-partial-benchmark-20260919.log`。

本次构建及行为测试命令见[工程说明](../firmware/display_serial/README.md#编译)。烧录仍使用上文命令，已缓存依赖时实际使用 `uv tool run --offline --from esptool==5.1.0 ...`。查看固件内计时可直接执行：

```sh
uv run --offline projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 COUNTER
uv run --offline projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 STATUS
```

实物复测：从 0 开始快速短按 10 次，再长按约 2 秒并松开，预期到 11，同时观察数字更新是否还出现整屏扫刷。用户结果待回报；模拟测试通过和采样间隔测量不能替代真实按压验收。

修改前的整屏计数固件、源码及 SHA-256 清单已存入本地 `artifacts/firmware/display-counter-20260919/`，用于回退；原厂、相机与 `HELLO!` 显示基线仍保留。

## 连续按压后变慢：USB 日志阻塞

用户随后确认局部重绘版不再丢计数，但出现“刚开始跟手，连续按压后几次合并刷新，停一会儿又恢复”。上一轮测量时电脑持续读取串口，未覆盖关闭读取端的情况。

检查固定版本 Arduino-ESP32 3.3.11 的 `HWCDC.cpp`：默认 TX 缓冲为 256 字节，每轮发送等待 100 ms，连续失败上限 20 次。USB 连接仍在但主机停止取数据时，一次写入可等待约 2 秒。依据为本地固定版本源码与[上游对应版本](https://github.com/espressif/arduino-esp32/blob/3.3.11/cores/esp32/HWCDC.cpp)。`Serial.printf("EVENT MID ...")` 在绘图所在主循环执行，所以日志等待会推迟下一次绘图；独立按键任务仍会累计，恢复后直接显示最新总数。

### 修复及对照实验

先只增加计时，保留原有阻塞发送行为，烧录 `button-counter-usb-probe` 临时诊断版本。再对比正式修复版 `button-counter-usb-nonblocking`：所有应用层 USB 输出共用 `send_usb()`，发送等待设为 0，TX 缓冲不足容纳整条消息时跳过，并累计 `usb_dropped`。缓冲扩至 1,024 字节以容纳完整 `STATUS`；关键是零等待和跳过策略，单纯扩大缓冲只会延后堵塞。

两版均运行 [usb_backpressure.py](../tests/usb_backpressure.py)：先切到 `TEST` 页，排队八条 `STATUS` 请求，关闭 Mac 串口读取端 20 秒，再重新连接查询。`TEST` 的绘图耗时让脚本有时间在状态回复产生前关闭端口；结束后恢复计数页。测试不生成虚拟按压。

| 实机指标 | 保留阻塞发送 | 不等待发送 |
| --- | --- | --- |
| 单次 USB 输出最大耗时 | 1,999.978 ms | 0.212 ms |
| 局部数字绘图最大耗时 | 9.574 ms | 9.580 ms |
| 主循环最大间隔 | 16,195.000 ms | 196.002 ms |
| 按键采样最大间隔 | 1.146 ms | 1.172 ms |
| 未完整发送／主动跳过消息数 | 8 | 6 |
| 回归测试 | 按预期失败：USB 等待超过 50 ms | 通过 |

主循环的 16 秒来自压力测试连续排队的多条阻塞回复，不代表每次物理按键都等待 16 秒；修复后的约 196 ms 来自测试特意触发的完整彩色页面绘图。两版数字绘制均约 9.6 ms，实测慢点是 USB 发送，未发现屏幕绘图随次数增加而变慢。

构建通过：程序 345,912 字节、静态 RAM 24,584 字节；启动程序、分区表、OTA 引导数据和应用四段写入均通过校验，自动复位成功。原始对照日志保存在本地 `logs/usb-backpressure-before-20260919.log` 与 `logs/usb-backpressure-after-20260919.log`。修复前的局部重绘固件及 SHA-256 清单保存在 `artifacts/firmware/display-partial-20260919/`，同目录另存了临时诊断源码 `usb-probe.ino`。

实际使用的构建、烧录及测试命令如下，从仓库根目录执行；运行测试前关闭其他串口客户端，建议正常复位以清空历史计时峰值：

```sh
bash projects/image-oracle/scripts/build-display.sh
(
  cd projects/image-oracle/build/display_serial
  uv tool run --offline --from esptool==5.1.0 esptool \
    --chip esp32s3 --port /dev/cu.usbmodem1101 \
    --before usb-reset --after watchdog-reset write-flash @flash_args
)
uv run --offline projects/image-oracle/tests/usb_backpressure.py --port /dev/cu.usbmodem1101
uv run --offline projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 STATUS
```

其中 `usb_dropped` 是跳过的诊断消息数，真实按键总数仍由独立任务保存；电脑不读取时允许丢日志，之后重新查询 `count` 即可。

2026-09-19，用户针对关闭串口读取端、连续快速按约 15 秒、停顿后再按的复测，明确反馈“始终跟手，问题解决”。持续连按后延迟与合并刷新的实物验收通过，`button-counter-usb-nonblocking` 作为当前按键与屏幕交互基线。该反馈不替代此前固定次数和长按不连加的专项验收。

## 代码阅读入口

源代码为 [display_serial.ino](../firmware/display_serial/display_serial.ino)：

- `setup()` 用 `pinMode(BUTTON_MID, INPUT_PULLUP)` 启用内部上拉；松开预期读到 HIGH，按下接地后读到 LOW。
- `sample_button()` 独立采样，通过 [ButtonDebouncer](../firmware/display_serial/button_debouncer.h) 要求电平稳定 10 ms。只有新的稳定按下才计数；长按不重复触发。
- `draw_counter()` 绘制完整页面，`draw_counter_value()` 仅绘制数字。`loop()` 发现累计次数变化后更新画面；采样任务在此期间继续运行。
- `STATUS` 的 `raw_mid` 是即时电平，`mid` 是消抖后的电平，`count` 是累计按下次数；`counter_draw_us` 和 `sample_gap_max_us` 用于观察耗时。
- `send_usb()` 发送状态、命令回复和 `EVENT MID count=...`；缓冲满时跳过整条消息，`usb_write_max_us` 记录耗时峰值。事件日志可能合并或跳过，总数以 `STATUS` 为准。

普通 `STATUS` 客户端退出后，板上程序仍然继续读取按键和绘图。不要同时用多个串口客户端读取同一端口。
