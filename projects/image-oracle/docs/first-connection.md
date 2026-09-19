# 首次连接记录

## 2026-09-18：USB 识别与串口接收

- 用户提供的主板近照可辨认模组标记 `ESP32-S3-N16R8`，摄像头排线座在该照片中未插入排线。标记不能替代 Flash 与 PSRAM 容量实测。
- 用户连接 Mac 后，相比连接前新增一组 `/dev/cu.usbmodem…` 与 `/dev/tty.usbmodem…`，对应同一个串口。实际端口名每次连接时查询，不作为固定配置入库。
- `ioreg` 显示 USB 产品名称为 `USB Single Serial`，VID/PID 为 `0x1a86:0x55d3`，绑定 macOS 自带的 `AppleUSBACMData` 驱动。本次未额外安装驱动，未根据 USB ID 推定具体桥接芯片型号。
- 使用 Python 标准库 `os`、`termios`、`select`，以 115200 波特率、8 数据位、无校验、1 停止位打开串口，观察 6 秒，收到 36 字节：`50%R`、`50%G`、`50%B` 各出现两次。
- 上述输出提示预装程序可能在测试 RGB 灯；板上灯的颜色、亮度和输出含义尚未由实物观察或源码确认。
- 读取期间未发送应用数据、未主动触发复位；结束后恢复串口配置并关闭端口。没有下载或烧录固件，也没有验证摄像头、屏幕、按键或存储容量。

## 已执行的检查

- 通过 Python `glob` 比较连接前后的 `/dev/cu.*` 与 `/dev/tty.*`。
- `ioreg -r -c IOSerialBSDClient -l`：核对串口设备入口。
- `ioreg -r -c IOUSBHostDevice -l`：核对 USB 描述符与驱动。
- `lsof` 检查目标串口未被其他进程占用，再进行上述限时读取。
- PATH 中有 Python 3.12.12、`screen` 和 Homebrew；未找到 `arduino-cli`、`idf.py`、`esptool` 或 `pio`，当前 Python 中也未找到 `serial`、`esptool` 模块。此结果不代表磁盘上不存在其他环境。

## 2026-09-18：用户安装摄像头后识别预装固件

- 用户报告已断开供电、插入摄像头排线并重新连接 USB；尚未提供安装后的近照，排线方向、锁扣和摄像头型号仍未目视核对。
- 重连后串口仍可识别，115200、8N1 下读取 4 秒，收到 24 字节，仍为 RGB 测试输出。
- 通过 `screen` 连接，发送 Ctrl+C 后收到 `main.py` 第 18 行的 `KeyboardInterrupt` 和 MicroPython 提示符，确认预装固件为 **MicroPython v1.19.1（2022-06-18），ESP32S3 module with ESP32S3**。
- `help('modules')` 未列出 `camera`；直接执行 `import camera` 得到 `ImportError: no module named 'camera'`。这说明当前环境不能直接使用该模块测试摄像头，不是摄像头硬件故障的证据。
- 查询后发送 Ctrl+D，收到 `MPY: soft reboot`、`RGB Demo`，并恢复 `50%R/G/B` 循环输出。随后退出测试会话，`lsof` 确认串口无占用。
- 本轮没有安装工具链、写入板上文件或烧录固件，也没有初始化或采集摄像头图像。

### 可复现的查询操作

用户要求后续操作同时提供命令、用途和结果，区分 Mac 命令行与板上 Python 提示符。以下端口参数需替换为当次 `ls /dev/cu.*` 查到的实际路径。

在 Mac 终端中：

```sh
ls /dev/cu.*
screen -ls
lsof <PORT>
TERM=xterm-256color screen -S esp32-inspect <PORT> 115200
```

`TERM=xterm-256color` 为本次命令指定终端能力，避免工具终端缺少清屏能力；用户自己的正常终端通常不需要此设置。先检查占用，避免与已有串口会话争用。

进入 `screen` 后按 Ctrl+C，等板上出现 `>>>`，逐行执行：

```python
import sys, os
print(sys.implementation)
print(os.uname())
help('modules')
import camera
```

这些是发给板上 MicroPython 的代码，不是在 Mac 的 shell 中执行。查询后按 Ctrl+D，让 MicroPython 软重启并重新运行预装程序。

本次从另一个 Mac 命令行关闭查询会话：

```sh
screen -S esp32-inspect -X quit
lsof <PORT>
```

`lsof` 无输出表示未发现串口占用；退出 `screen` 不会断开 USB 供电。若仅按 Ctrl+A 再按 d，会话进入后台并继续占用串口，可用 `screen -r esp32-inspect` 返回。

## 下一步

1. 预装固件和 RGB 测试程序已识别；继续核对安装后的摄像头排线方向与型号，屏幕暂不连接。
2. 准备固件开发环境。优先复现商家 Arduino 相机例程，可通过 Arduino CLI 操作；固定工具链与依赖版本后先构建，再按项目约定确认目标设备和恢复方式后烧录。
3. 首次覆盖前备份现有固件并记录恢复方式；获得烧录授权后验证取帧，再核对并连接屏幕，最后加入按键。需要调整排线时先断电。

参考：[Espressif 串口连接与验证](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/establish-serial-connection.html)、[Arduino CLI 入门](https://docs.arduino.cc/arduino-cli/getting-started)。
