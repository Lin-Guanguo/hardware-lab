# USB 串口相机测试

用于鹿小班／芯路城 ESP32-S3-CAM N16R8 套装的最小相机工程：初始化摄像头，接收 `SNAP` 命令，通过原生 USB 返回一张 320×240 JPEG。无需 Wi-Fi、屏幕或按键。

## 固定环境

- Arduino CLI 1.5.1，macOS ARM64。
- `esp32:esp32` core 3.3.11（基于 ESP-IDF 5.5.5），使用其随附的 `esp32-camera` 驱动。
- 板型 `esp32s3`，16 MB Flash、OPI PSRAM，分区选项 `app3M_fat9M_16MB`。
- `USBMode=hwcdc,CDCOnBoot=cdc`；程序使用 `Serial`，经芯片原生 USB 的 Hardware CDC 通信。主机串口参数为 115200、8N1，实际数据经 USB 传输。
- 原生 USB 使用 GPIO19／20，与当前摄像头引脚不冲突；测试时这两个引脚不可再接屏幕。商家屏幕例程使用了这两个引脚，接入屏幕前需重新分配或改用 USB-UART。
- Mac 接收脚本使用 Python ≥3.10、pyserial 3.5，通过 `uv run` 的脚本依赖声明固定版本。

所有构建命令均可从仓库根目录运行：

```sh
bash projects/image-oracle/scripts/setup.sh
bash projects/image-oracle/scripts/build.sh
```

`setup.sh` 下载并校验固定版本 CLI，再安装固定版本 ESP32 core；`arduino.sh` 将工具数据、包缓存和用户库目录限定在本项目的 `downloads/arduino/`。`build.sh` 中保留完整的 `arduino-cli compile` 命令及板卡参数，输出位于 `projects/image-oracle/build/camera_serial/`。

2026-09-19 已构建、烧录并取得 OV3660 的 320×240 JPEG，实物验证与恢复方法见[启动记录](../../docs/camera-bringup.md)。构建不等于烧录，覆盖现有固件前需完成备份并确认恢复方式。

## 协议

Mac 发送 ASCII `SNAP\n`。初始化失败或取帧失败时，固件返回以 `ERROR ` 开头的一行。相机已初始化时先输出 `INFO` 行，包含传感器 PID、Flash 和 PSRAM 字节数；取帧成功后依次返回：

1. ASCII 头：`JPEG <bytes> <width> <height>\n`。
2. 恰好 `<bytes>` 字节的 JPEG 数据。
3. ASCII 尾：`\nEND\n`。

`capture.py` 打开串口、等待启动、发送拍照命令，按长度收取数据，并检查结束标记及 JPEG 首尾标记；协议错误或超时不保存照片，不覆盖已有文件。针对当前 macOS 原生 USB 接口，脚本跳过 pyserial 的 DTR／RTS 更新，并关闭 termios 的 HUPCL，防止打开或关闭端口时触发复位。依赖固定为 pyserial 3.5，钩子实现与问题证据见启动记录。脚本识别到 ROM 的 `waiting for download` 时，会提示退出下载模式。

```sh
uv run projects/image-oracle/scripts/capture.py \
  --port <PORT> \
  --output projects/image-oracle/artifacts/photos/capture.jpg
```

`<PORT>` 需替换为本次 `ls /dev/cu.*` 查到的原生 USB 端口，插口靠 EN/RST。执行前关闭占用它的 `screen` 会话。

## 来源与修改

- 摄像头信号分配与初始化参数参考商家 `camera_TEST_V1_1.ino` 和相机接口图；采用项目原有的板型配置，不套用其他 ESP32-CAM 板。
- 来源页：<https://www.xinlucity.com/?s=resourcedetail/index/id/555.html>。
- 原包：<https://testxinlu.oss-cn-beijing.aliyuncs.com/static/upload/file/warehouse/2026/07/30/1785404353371499.zip>。
- ZIP SHA-256：`9f0c232f1793610ced4ff316ed82cdaf40cd7f2e9606204c560c641e47707531`。
- 原 sketch SHA-256：`178fca0ff71e0094fac157865b438effe3ce17d72e70fbbe09836b2c98bc5459`。商家未给出 Git revision，以上哈希固定所参考版本；来源与图像哈希另见 [下载清单](../../docs/vendor_downloads.json)。
- 商家 ZIP 只有原 sketch，未附许可证文件；原始文件保存在忽略目录中，不补造上游许可声明。工程中的串口请求／JPEG 传输和 Mac 接收逻辑为本仓库新增代码。
- 对初始化结构清零、检查 PSRAM 与初始化状态；失败时不继续取帧。复用驱动原有的传感器识别，收到命令后才向串口发送照片。
- [Arduino ESP32 3.3.11](https://github.com/espressif/arduino-esp32/releases/tag/3.3.11) 和 [Arduino CLI 1.5.1](https://github.com/arduino/arduino-cli/releases/tag/v1.5.1) 的原始许可证随工具包保留。
