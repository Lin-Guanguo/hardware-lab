# 摄像头首次启动记录

## 目标与当前进度

2026-09-18：用户选择先验证摄像头。目标是备份原固件，构建包含 `esp32-camera` 驱动的 Arduino 固件，通过原生 USB 拍摄一张 JPEG 并在 Mac 查看。

- 原固件为 MicroPython v1.19.1，运行 `RGB Demo`；`import camera` 返回模块不存在。
- `esptool 5.1.0 flash-id` 识别 ESP32-S3 revision v0.2、16 MB Flash；应用初始化报告 8,388,608 字节 PSRAM，并成功使用 PSRAM 帧缓冲取图。尚未进行独立的全容量压力测试。
- 用户断电安装的摄像头已被驱动识别为 OV3660，PID `0x3660`，与发货单一致。
- 2026-09-19，原生 USB 完整备份成功：16,777,216 字节，用时 1461 秒；`verify-flash` 摘要比对通过，前 64 KiB 与 USB-UART 独立读取结果一致。备份为 `artifacts/backups/factory-20260918.bin`，校验记录为同目录 `factory-20260918.json`，均不入 Git。
- 工具链安装和原生 USB 版固件构建通过：程序 378,476 字节，静态 RAM 34,000 字节。烧录成功，各镜像均通过写入校验；设备查询显示 Secure Boot 和 Flash Encryption 未启用，没有修改 eFuse。
- 2026-09-19，不按按钮断电重插后，使用不切换串口控制线的 POSIX 读写方式，取得第一张 320×240 JPEG，3725 字节。已解码查看，可见显示器边角和周围环境。
- 正式 `capture.py` 随后调整为打开端口时不操作 DTR／RTS，关闭时不使用 HUPCL 挂断控制线；连续两次独立运行成功保存 4154、4289 字节的 JPEG，后一张已解码查看。照片位于忽略目录 `artifacts/photos/`。
- shell 语法检查、Python 编译检查、`git diff --check` 通过。接收逻辑通过伪终端验证：分段二进制数据完整接收，错误结束标记导致失败且不落盘，ROM 下载提示可明确报错；随后完成上述实物拍照验证。

## 操作复盘：模式、固件与工具

需要分清三层：ROM 下载器是芯片内置的；Flash 保存可替换的固件；`screen`、`esptool`、`capture.py` 是运行在 Mac 上、通过 USB 与板子通信的工具。

| 名称 | 属于哪一层 | 本次用途 |
| --- | --- | --- |
| ROM 下载模式 | 芯片启动模式 | 运行内置下载器，读取备份或写入 Flash；此时不运行灯效或相机应用 |
| 正常应用启动 | 芯片启动模式 | 从 Flash 加载引导程序和应用，执行当前保存的固件 |
| MicroPython REPL | 原固件提供的交互界面 | `>>>` 在板子上解释执行 Python；不是 ROM 下载器，也不是 Mac 本机 Python |
| 相机命令循环 | 新固件的应用逻辑 | Arduino/C++ 程序接收 `SNAP`，调用 `esp32-camera`，返回 JPEG |

本次经历的流程是：

1. **识别原程序。** Mac 识别串口后，`screen` 在 115200 下显示 RGB 灯效日志。`Ctrl+C` 中断 MicroPython 的 `main.py` 并回到 REPL，`Ctrl+D` 软重启 MicroPython。它们都不是切换到 ROM 下载模式。
2. **确认缺少相机支持。** 原固件 `import camera` 失败。选择使用包含 `esp32-camera` 的 Arduino 工程；驱动作为固件的一部分编译，未在原 Python REPL 中执行 `pip install`。
3. **进入下载模式并备份。** 按住 BOOT 插电，原灯效停止；这是运行下载器的结果，按 BOOT 本身不会擦除固件。USB-UART 高速读取失败后换到原生 USB，执行 `read-flash 0 ALL`，再用 `verify-flash` 校验完整 16 MiB 备份。
4. **在 Mac 构建。** `setup.sh` 安装固定工具链，`build.sh` 把 C++ 源码和驱动编译成 `.bin`。构建只生成电脑上的文件，还没有改动板子。
5. **写入 Flash。** `write-flash @flash_args` 将引导程序、分区表和相机应用写入板子并校验。这一步才用新固件替换原来的 MicroPython 运行环境；原固件保留在 Mac 的备份中。
6. **退出下载模式并拍照。** 本次最终通过不按任何按钮断电重插，配合不切换控制线的接收方式启动成功。随后正式 `capture.py` 连续两次完成拍照。

### 按键、快捷键和断开连接的区别

| 操作 | 作用 | 会改变 Flash 中的固件吗？ |
| --- | --- | --- |
| 按住 BOOT 上电，或按住 BOOT 再按 EN/RST | 请求进入 ROM 下载模式 | 不会 |
| 不按 BOOT，断电重插 | 重新启动当前 Flash 中的固件 | 不会 |
| 短按 EN/RST | 硬件复位；完整复位时重新判读启动状态 | 不会 |
| MicroPython 中按 `Ctrl+C` | 中断 Python 程序，返回旧固件的 REPL | 不会 |
| MicroPython REPL 中按 `Ctrl+D` | 软重启 MicroPython，再执行启动脚本 | 不会 |
| `screen` 中按 `Ctrl+A`、`D` | 只分离 Mac 上的会话，串口仍可能被占用 | 不会 |
| `screen -S <SESSION> -X quit` | 关闭指定的 Mac 会话并释放端口；控制线变化可能影响板子运行状态 | 不会 |
| `esptool write-flash ...` | 将文件内容写入指定 Flash 地址 | 会 |

**复位不会恢复原厂程序。** 现在 Flash 中是相机固件，重启仍会运行它；要回到原来的 Python REPL，需要重新烧录原固件备份。当前相机程序没有 RGB 闪灯循环，也没有 Python REPL，因此不能通过“灯是否闪”或 `Ctrl+C` 是否出现 `>>>` 判断它是否正常。

## 两个接口与 BOOT

按用户照片中天线在左、USB 接口在右的方向：靠 BOOT/IO0 的接口连接板载 USB-UART；靠 EN/RST 的接口连接 ESP32-S3 原生 USB。换口后的 USB 枚举已验证此区别：前者为 `USB Single Serial`，后者为 `USB JTAG/serial debug unit`。

BOOT 连接启动配置引脚 GPIO0。按住 BOOT 上电或复位，让芯片进入 ROM 下载模式，电脑可读取和写入 Flash。它本身不擦除 Flash；灯效停止是因为此时没有运行原来的应用程序。EN/RST 用于复位；不按 BOOT 复位通常回到 Flash 中的应用。

备份或烧录期间不要拔线、按复位或另开串口工具。完成后再按步骤切换运行模式。

参考：[Espressif 启动模式说明](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html)。

## 备份命令与恢复方法

以下命令从仓库根目录执行。`<PORT>` 替换为本次检测到的串口，不要原样输入尖括号；换接口后路径可能变化。

```sh
ls /dev/cu.*
screen -ls
```

`screen -ls` 列出会话；`Ctrl+A`、`D` 只分离会话，仍可能占用串口。需要释放端口时，先确认目标会话，再执行 `screen -S <SESSION> -X quit`。

手动进入下载模式：拔 USB，按住 BOOT，插入原生 USB 接口，再松开 BOOT。查询芯片和 Flash：

```sh
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32s3 --port <PORT> --before no-reset --after no-reset \
  flash-id
```

`uv tool run` 使用隔离的固定版本工具；`--before no-reset` 保留手动进入的下载状态，`--after no-reset` 让读取完成后继续留在下载环境。备份命令：

```sh
mkdir -p projects/image-oracle/artifacts/backups
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32s3 --port <PORT> --before no-reset --after no-reset \
  read-flash 0 ALL projects/image-oracle/artifacts/backups/factory-20260918.bin
```

`0 ALL` 表示从地址 0 开始读取检测到的全部 Flash；此命令只读取设备。现有同名备份应保留，重复备份需换文件名。备份、校验文件和日志均在 Git 忽略目录内。

读取成功后检查字节数和 SHA-256，再通过设备校验：

```sh
wc -c projects/image-oracle/artifacts/backups/factory-20260918.bin
shasum -a 256 projects/image-oracle/artifacts/backups/factory-20260918.bin
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32s3 --port <PORT> --before no-reset --after no-reset \
  verify-flash 0 projects/image-oracle/artifacts/backups/factory-20260918.bin
```

完整文件应为 16,777,216 字节。SHA-256 标识本地文件内容；`verify-flash` 将其与设备 Flash 比对。

**下面是需要回到原厂程序时的恢复命令，不是当前备份流程的一步。** 它覆盖设备 Flash，执行前应确认目标为同一块板、备份校验通过，并按上述 BOOT 步骤重新进入下载模式：

```sh
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32s3 --port <PORT> --before no-reset --after hard-reset \
  write-flash 0 projects/image-oracle/artifacts/backups/factory-20260918.bin
```

### 已遇到的读取问题

- USB-UART、921600 baud：约 4.6 MB 时数据流中断，未生成完整备份。
- USB-UART、460800 baud：约 332 KB 时收到不足 4096 字节的数据块，读取失败。
- USB-UART、115200 baud：64 KiB 小范围读取成功。
- 切换原生 USB 后可连接同一芯片；完整 16 MiB 读取与设备摘要校验均通过。

前 64 KiB 中的原厂分区表：

| 分区 | 起始地址 | 大小 |
| --- | --- | --- |
| nvs | `0x9000` | `0x6000` |
| phy_init | `0xf000` | `0x1000` |
| factory | `0x10000` | `0x1f0000` |
| vfs | `0x200000` | `0x600000` |

## 构建与拍照

```sh
bash projects/image-oracle/scripts/setup.sh
bash projects/image-oracle/scripts/build.sh
```

第一条安装固定版本工具链，第二条编译固件；均不会自动烧录。具体版本、板型参数、源码来源和传输协议见[相机工程说明](../firmware/camera_serial/README.md)。

构建生成的 `build/camera_serial/flash_args` 已核对：ESP32-S3、DIO、80 MHz、16 MB Flash，分别在 `0x0`、`0x8000`、`0xe000`、`0x10000` 写入引导程序、分区表、OTA 初始数据与应用。使用该文件可避免手工复制偏移量。

以下烧录步骤已在完成备份校验后执行成功。复现时先确认目标设备、备份和恢复方式；板子进入下载模式后，从仓库根目录运行：

```sh
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32s3 --port <PORT> --before no-reset --after no-reset \
  get-security-info

(
  cd projects/image-oracle/build/camera_serial
  uv tool run --from esptool==5.1.0 esptool \
    --chip esp32s3 --port <PORT> --before no-reset --after hard-reset \
    write-flash @flash_args
)
```

`get-security-info` 只查询安全启动与 Flash 加密状态，不修改 eFuse。`@flash_args` 从构建产物读取烧录参数与文件列表；括号中的 `cd` 只影响该组命令，不改变当前终端目录。`write-flash` 会覆盖相应 Flash 区域，成功后工具尝试自动复位。

### 手动下载模式的退出

本次通过 BOOT 上电进入下载模式，烧录后的 `--after hard-reset` 未让应用运行。原生 USB 的普通复位只重置内核，不重新采样启动配置引脚，因此仍保留下载模式状态。这与烧录数据是否正确是两件事。

尝试过以下软件完整复位命令，但此板在后续串口读取中仍报告下载模式，不能将它记为已验证的退出方法：

```sh
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32s3 --port <PORT> --before no-reset --after watchdog-reset \
  flash-id
```

本次已验证的退出操作是：**拔掉 USB，等待 2 秒，不按任何按钮，再插回原生 USB 接口**，随后使用修正后的 `capture.py`。理论上不按 BOOT、短按 EN/RST 也可退出；此前尝试受串口控制线操作干扰，不能据此断言按钮失效。参考：[Espressif：退出 USB-Serial/JTAG 下载模式](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/troubleshooting.html#leaving-download-mode-in-usb-serial-jtag-mode)。

### Mac 串口控制线问题

早期脚本主动设置 DTR／RTS，打开端口后收到 `rst:0x15 (USB_UART_CHIP_RESET)` 和 `waiting for download`，说明通信操作又触发了芯片复位。改为 pyserial 默认控制线状态仍没有解决。断电重插后，不执行调制解调器控制线 ioctl 的原始 POSIX 读写立即成功取图，定位到主机连接方式。

最终脚本保留 pyserial 3.5 的读写和超时处理，专门覆盖其 `_update_dtr_state`、`_update_rts_state` 钩子以跳过控制线修改，并清除 termios 的 `HUPCL`，避免关闭端口时挂断控制线。这是针对当前 Mac 与原生 USB 接口的实现；不要将该连接行为直接套用到其他需要控制线的串口设备。已用两次独立启动脚本验证连接、取帧和关闭流程。

### 日常拍照

相机程序通过 `Serial` 使用原生 USB，备份、烧录和拍照均可使用靠 EN/RST 的同一个接口；日常启动普通插入即可，不按 BOOT。该程序没有 Python REPL，也没有 RGB 闪灯循环，灯不闪不能据此判断烧录失败。

原生 USB 使用 GPIO19／20，当前摄像头不占用它们。商家屏幕接线使用这两个引脚，之后连接屏幕前必须调整屏幕引脚或将固件改为 USB-UART 通信。

```sh
uv run projects/image-oracle/scripts/capture.py \
  --port <PORT> \
  --output projects/image-oracle/artifacts/photos/my-photo.jpg
```

此脚本发送 `SNAP`，打印传感器与内存信息，接收 JPEG，并检查长度和协议标记；已有照片不会被覆盖，每次拍照需使用新文件名。当前端口为 `/dev/cu.usbmodem1101`，重插或换 Mac 接口后先用 `ls /dev/cu.*` 核对。可用以下命令打开新照片：

```sh
open projects/image-oracle/artifacts/photos/my-photo.jpg
```

已验证 320×240 单帧 JPEG；更高分辨率、视频流、屏幕和按键尚未测试。
