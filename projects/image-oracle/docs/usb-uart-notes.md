# 两个 USB-C 接口、UART 与固件通信

记录日期：2026-09-19。适用于本项目已核对的 ESP32-S3-CAM N16R8 开发板；接口位置以按钮丝印为准。

## 两个接口的区别

| 接口 | 数据路径 | 已核对的 USB 产品名称 |
| --- | --- | --- |
| 靠 BOOT／IO0 | 电脑 USB → 板载 USB 转 UART 芯片 → ESP32-S3 的 UART | `USB Single Serial` |
| 靠 EN／RST | 电脑 USB → ESP32-S3 内置 USB 控制器 | `USB JTAG/serial debug unit` |

两个口均可供电、烧录，数据经过的硬件不同。USB-C 只是连接器外形，不能单凭外形判断协议、速率或用途。

若将开发板摆成金属盖朝自己、天线朝上、两个 USB-C 朝下，则左口靠 EN／RST，是原生 USB；右口靠 BOOT／IO0，是 USB 转 UART。仍应按实物丝印核对。

## 串口是什么

这里的串口具体指 UART（Universal Asynchronous Receiver/Transmitter，通用异步收发器）：把字节拆成逐位的电信号，按双方约定的速度发送。

- `TX`：发送；一方的 TX 对接另一方的 RX。
- `RX`：接收。
- `GND`：共用电压参考。
- UART 没有单独的时钟线，因此双方需要约定波特率和帧格式，例如 `115200、8N1`，即 115200 波特、8 数据位、无校验、1 停止位。

接 USB 转 UART 口时，USB 线连接的是电脑与转换芯片；转换芯片再通过板内的 TX／RX 线路与 ESP32 通信。

原生 USB 可以向电脑提供类似串口的软件接口。因此两种通道都可能出现在 Mac 的 `/dev/cu.*` 下，也能被串口工具打开；设备路径相似不代表底层都经过 UART。

## 从哪个口烧录，与运行后在哪个口通信

烧录时运行的是芯片内置的 ROM 下载程序；正常启动后运行的是 Flash 中的应用固件。这两者不是同一个程序。

从哪一个口烧录，不会自动决定应用从哪个口输出。应用的通信通道由源码和编译配置决定：可以从 USB 转 UART 口烧录，再让应用通过原生 USB 传照片，也可以在程序中同时启用两条通道。

本项目的相机与屏幕工程使用以下 Arduino 编译配置：

```text
USBMode=hwcdc,CDCOnBoot=cdc
```

在这组配置下，程序的 `Serial` 使用原生 USB Hardware CDC。名称 `Serial` 本身不能脱离编译配置来判断对应的硬件。具体代码与配置见[相机工程](../firmware/camera_serial/README.md)和[屏幕工程](../firmware/display_serial/README.md)。

原生 USB 的 Hardware Serial/JTAG 是固定功能控制器；将设备做成 USB 键盘、鼠标或大容量存储设备，需要改用 USB OTG 控制器及相应固件配置，并非只修改 `Serial` 输出内容。

## 为什么有时选 UART，有时选原生 USB

| 场景 | 选择依据 |
| --- | --- |
| 日志、简单命令、Python REPL | 两种通道都可胜任，按固件配置使用 |
| 照片、大量二进制数据 | 原生 USB 吞吐潜力较高，本项目拍照采用此方式 |
| 调试复位、休眠或 USB 配置问题 | USB 转 UART 芯片独立于 ESP32；它仍供电时，电脑端串口通常可保持存在 |
| 制作 USB 键盘、鼠标或 U 盘类设备 | 原生 USB OTG 承担设备功能，UART 可另作调试通道 |
| 业务数据和调试日志分开传输 | 程序可同时使用两条通道，例如原生 USB 传照片、UART 输出日志 |

原生 USB 会受芯片自身状态影响，例如深度休眠或错误重配 GPIO19／20 都可能使设备从电脑端消失。USB 转 UART 口保持可见，也不等于 ESP32 中的程序一定仍在运行。

两路同时通信是可实现的程序设计，本项目尚未进行双通道并行实测。已有相机与屏幕实验使用单个原生 USB 连接。

## “快速口／慢速口”只是粗略记法

- UART 在 `115200、8N1` 下，每个有效字节通常占 10 个传输位，理论有效数据速率为 `115200 ÷ 10 = 11520 字节/秒`，约 **11.5 KB/s**。UART 可以提高波特率，实际稳定上限取决于芯片、转换器、线路与软件。
- ESP32-S3 原生 USB 支持 Full-speed，总线速率为 **12 Mbps**，折合原始带宽 **1.5 MB/s**；这不是应用可保证达到的文件传输速度，也不是 USB 2.0 High-speed 的 480 Mbps。
- 原生 USB 虚拟串口界面中填写 `115200`，不意味着 USB 总线会按 UART 的 115200 位/秒传输。
- 读取数据、协议往返、缓冲和程序处理都会影响实际速度。本项目曾经通过原生 USB 备份 16,777,216 字节 Flash，用时 1461 秒，约 11.5 KB/s；这是当次备份结果，不是原生 USB 的吞吐上限，也不能当作照片传输测速结果。

屏幕与 ESP32 之间走 SPI，按钮走 GPIO；电脑连接哪个 USB 口，本身不会直接决定屏幕的 SPI 刷新速度。

## 日常连接与模式切换

日常运行正常插入 USB，不需要按 BOOT。按住 BOOT 上电或复位，是请求进入 ROM 下载模式；它本身不擦除固件。真正写入 Flash 的烧录操作才会改变固件。

更完整的复位、下载模式与实际命令见[摄像头操作复盘](camera-bringup.md)，Mac 的设备查看与 `screen` 操作见[首次连接记录](first-connection.md)。这些文档记录的是相应实验阶段，当前设备状态以[项目 README](../README.md)为准。

## 参考

- [Espressif：USB Serial/JTAG 控制台、功能与限制](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/usb-serial-jtag-console.html)
- [Espressif：USB Device Stack](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html)
- [ESP32-S3 技术参考手册：USB Serial/JTAG 的 Full-speed 速率](https://documentation.espressif.com/esp32-s3_technical_reference_manual_en.pdf)
