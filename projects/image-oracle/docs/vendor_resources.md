---
description: 鹿小班 ESP32-S3-CAM 套装资料入口、本地下载、版本差异与首次实验顺序
last_updated: 2026-09-16
---

# 鹿小班套装资料与使用顺序

已找到与采购名称一致的 **ESP32S3-CAM 摄像头＋面包板＋1.54 寸彩屏**资料页，并下载相机测试程序、接线教程原文、技术图和小智固件。当前完成的是资料核对，尚未连接实物、编译或烧录。

今晚建议先做：**核对实物 → USB-UART 识别主板 → 摄像头串口测试 → 屏幕显示 → 五向按键**。摄像头已通过板载排线座连接，不需要自己用杜邦线连接全部摄像头信号。

## 1. 正确的资料入口

| 来源 | 用途与适用范围 |
| --- | --- |
| [芯路城资料分类页](https://www.xinlucity.com/?s=resource/index/cid/3.html) | 用户提供的总入口；同站混有多个不同板型 |
| [590：ESP32S3-CAM 摄像头＋1.54 寸彩屏套装](https://www.xinlucity.com/?s=resourcedetail/index/id/590.html) | 与采购名称一致，优先从这里进入 |
| [套装接线教程（飞书）](https://my.feishu.cn/wiki/HDWdwcVGUi3b3dk0IoycXR6pnOc) | 从套装页链接；摄像头、屏幕、麦克风、功放接线与小智固件 |
| [555：ESP32S3-CAM 摄像头开发板](https://www.xinlucity.com/?s=resourcedetail/index/id/555.html) | 摄像头测试程序、模组信号定义、USB 接口说明 |
| [168：1.54 寸 SPI 屏（灰排线）](https://www.xinlucity.com/?s=resourcedetail/index/id/168.html) | 相关屏幕资料，但 PDF 与套装参数图存在明确版本差异，只作候选参考 |

飞书教程此次获取的标题为“【最新】小智AI面包板带摄像头互动功能接线教程”，文档 revision 为 **819**。其中板卡标为 **ESP32-S3 N16R8 CAM＋OV3660**，也提及 OV2640、OV5640；实物摄像头型号仍需确认。

## 2. 已下载到哪里

原始资料放在本项目的 [downloads/xinlucity/](../downloads/xinlucity/)。共 14 个文件，含 3 个解压文件，约 **46.6 MiB**。下载目录被 Git 忽略；本说明、来源和 [SHA-256 下载清单](vendor_downloads.json) 纳入版本管理。以后重新 clone 仓库需要按清单重新获取本地资料。

| 本地资料 | 怎么用 |
| --- | --- |
| [相机测试 ZIP](../downloads/xinlucity/camera_TEST_V1_1.zip)／[已解压的 Arduino sketch](../downloads/xinlucity/extracted/camera_TEST_V1_1/camera_TEST_V1_1.ino) | 首次验证相机，串口输出 PID、型号、FPS、图像字节数；不依赖屏幕或 Wi-Fi |
| [套装接线教程原文](../downloads/xinlucity/kit_wiring_upstream.md) | 本地可读的 Markdown 原文；内嵌图片、视频和其他文档仍是在线引用，并非完整离线镜像 |
| [小智 v2.2.6 固件](../downloads/xinlucity/v2.2.6-bread-compact-wifi-s3cam-3660.bin) | 教程获取时标为最新的 OV3660 套装固件；保留供以后复现商家演示使用 |
| [套装屏幕参数图](../downloads/xinlucity/kit_display_parameters.png) | 对照屏幕背面丝印、排针名称、尺寸和供电 |
| [主控模组信号图](../downloads/xinlucity/board_pinout.png)／[摄像头接口图](../downloads/xinlucity/camera_pinout.png) | 查看芯片信号占用；模组信号图不是开发板排针的物理排列图 |
| [SD 接口图](../downloads/xinlucity/sd_pinout.png)／[USB 接口照片](../downloads/xinlucity/usb_ports.png) | 区分 SD 引脚和 USB-UART／USB-OTG 接口 |
| [屏幕原理图与尺寸图 PDF](../downloads/xinlucity/extracted/display/display_schematic.pdf) | **不同版本参考，不能直接照排针序号接线或据此设计外壳** |
| [ST7789 数据手册 PDF](../downloads/xinlucity/extracted/display/ST7789_datasheet.pdf) | 包内实际为 ST7789VW v1.0（2017/09）；仅在查驱动命令、时序时阅读 |
| [屏幕测试代码 RAR](../downloads/xinlucity/display_test_code.rar) | 6 套 STM32 工程，可参考初始化代码；没有 ESP32／Arduino 工程，不能直接烧到 S3 |
| [屏幕原理图原包](../downloads/xinlucity/display_schematic_dimensions.rar)／[数据手册原包](../downloads/xinlucity/display_specification.rar) | 保留原始下载，方便校验来源和重新解压 |

未下载历史小智固件、接线视频、Windows 工具安装包和无关板卡资料。原始代码保持不变，尚未导入 `firmware/`。

## 3. 必须区分的版本和引脚

### 主板与摄像头

采购和套装教程写的是 **N16R8**，通常对应 16 MB Flash、8 MB PSRAM；但商家主控信号图下方写的是 **N8R8**。目前不能把图上的容量当作实物确认结果。首次连接时应同时核对模组丝印、Flash 识别结果与 PSRAM 初始化日志。

商家相机 sketch 与摄像头接口图中的 GPIO 定义相符：

| 相机信号 | ESP32-S3 GPIO |
| --- | --- |
| XCLK | 15 |
| SCCB SDA／SCL（配置摄像头） | 4／5 |
| D0～D7（例程称 Y2～Y9） | 11、9、8、10、12、18、17、16 |
| VSYNC／HREF／PCLK | 6／7／13 |
| PWDN／RESET | 例程均为 `-1`，表示不分配独立 GPIO |

这是**商家板型参考**，不是实测接线表。若实物一致，这些信号已在主板和排线座内连接，启用摄像头时不要再分配给按钮或屏幕。插拔、调整摄像头排线前先断开供电。

### 套装屏幕与商家原配接线

套装参数图写的是 **`1.54TFT-SPI-ST7789 Ver:1.1`**，240×240，标称 2.8～3.3 V，模块尺寸 32×43.7×2.58 mm。图中排针为 `GND VCC SCL SDA RST DC CS BL`。这些规格仅描述商家图中的版本，尺寸最终以实物测量为准。

以下抄录自套装飞书教程，仅在核对实物名称、型号后用于复现配套固件；以后自己的固件可以重新规划 GPIO：

| 屏幕丝印 | 商家教程连接 | 含义 |
| --- | --- | --- |
| GND | GND | 共地 |
| VCC | 3V3 | 屏幕供电；不要因为主板用 USB 5 V，就把这个屏幕接到 5 V |
| SCL | GPIO19 | SPI 时钟 SCK |
| SDA | GPIO20 | SPI 数据 MOSI |
| RST | GPIO21 | 屏幕复位 |
| DC | GPIO47 | 数据／命令选择 |
| CS | GPIO45 | 片选 |
| BL／教程写 BLK | GPIO38 | 背光控制 |

这里的 **SCL、SDA 是屏幕 SPI 信号，不是 I2C 接口**。接线看丝印名称，不按另一块板子的针脚位置数过去。

关键限制：

- **GPIO19/20 同时是原生 USB 信号。** 使用上表屏幕接线时，编程和看串口优先走板上 **USB-UART** 接口，不把 USB-OTG 当作可同时使用的数据接口。按丝印判断，不凭“左口／右口”。
- **GPIO45 是 strapping pin。** 商家用它作 CS；若实物屏幕的上下拉不同，应先检查启动条件，不能默认任意屏幕都能直接替换。
- 商家图中 SD 使用 GPIO38/39/40，与这里的屏幕背光及教程中的部分音频引脚重叠。首次实验先不插 SD 卡，不默认这些功能可以同时启用。
- Flash／PSRAM 占用的引脚不能随意再用；尤其不要从普通 S3 例程照抄 GPIO35/36/37 的分配。

GPIO 限制依据：[Espressif ESP32-S3 GPIO 官方说明](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/gpio.html)。

### 为什么屏幕 PDF 不能直接照用

已逐页查看下载的两页 PDF：其模块为 **31.62×45.95 mm**，排针标为 `3V3 GND SCK GND SDI DC CS BL`，复位使用板上 RC 电路；与套装图的 **32×43.7 mm、带 RST 排针**版本不同。保留它便于参考，但不据此安排电源位置、接线顺序或外壳开孔。

另外，[普通 ESP32-S3 页面 61](https://www.xinlucity.com/?s=resourcedetail/index/id/61.html) 并非 CAM 专用资料，其通用示例存在 ADC／触摸引脚说明不准确等问题。确认能力以芯片官方文档为准，确认板上连接以对应版本原理图及实物为准。

## 4. 今晚怎么开始

### 第一步：只确认主板和串口

1. 核对主板、摄像头排线、屏幕背面的丝印；暂时不用把喇叭、麦克风和所有传感器都接上。
2. 确认摄像头排线在断电时插牢。用能传数据的 USB 线连接 Mac 与 **USB-UART**，先只用这一路 USB 供电。
3. 在插线前后对比串口列表：

   ```sh
   ls /dev/cu.*
   ```

4. 记录新增端口名，不能把教程的 Windows `COMxx` 直接用于 Mac。如果没有新端口，先检查线和接口，再按实际 USB-UART 芯片确认是否需要 macOS 驱动；不预先安装所有驱动。
5. 先查看出厂程序的串口输出和现有行为；需要覆盖固件时，再确认目标设备并考虑备份出厂 Flash。

### 第二步：先验证摄像头

优先从已下载的 `camera_TEST_V1_1.ino` 建立最小测试。它属于 Arduino framework，但不要求使用 Arduino IDE；可以用 **VS Code＋Arduino CLI** 完成编译、上传和串口监控。选择该路径是为了先复现现成相机例程，正式项目仍可使用 ESP-IDF。

商家给出的配置参考为 **ESP32S3 Dev Module、16 MB Flash、OPI PSRAM、串口 115200**，实际存储容量须按实物确认。通过 USB-UART 调试时，还需检查 Arduino 的 `Serial` 输出配置，避免日志被配置到原生 USB CDC。

测试通过的观察标准是：相机初始化成功，出现传感器 PID／型号，持续取帧并输出 FPS 和字节数。当前例程为 JPEG、QVGA（320×240）、两个位于 PSRAM 的帧缓冲。**能输出帧大小只证明能取到帧，图像是否正常还需随后查看。**

导入项目时要先处理原始代码里的两个问题：

- `camera_config_t config;` 没有清零，应改为 `camera_config_t config = {};`，避免未赋值字段受驱动版本影响。
- 初始化失败时 `setup()` 直接 `return`，但 Arduino 仍会执行 `loop()`；应增加初始化成功状态检查，失败时不继续取帧。

原文件仍保持上游内容。本次未安装工具链、固定 Arduino core 版本、编译或验证上传命令，因此这里不把它称为“已验证可运行工程”。

### 第三步：屏幕、图像和按键逐个加入

1. 确认屏幕版本和引脚后，先显示纯色、文字，验证 SPI 初始化、背光和方向。
2. 再显示相机照片；JPEG 需要解码，320×240 的图像还需考虑在 240×240 屏幕上的缩放或裁剪。
3. 最后加入五向按键，用剩余 GPIO 实现拍照、切换画面和确认。当前还没有最终按钮引脚分配。
4. 然后实现“固定图像输入 → 固定算法 → 固定答案”，并用保存的同一张图验证结果可复现。

ST7789 的底层初始化不必从头手写；Arduino 可复用对应屏幕库，ESP-IDF 可使用 `esp_lcd`。具体库和版本在建立固件工程时确定。摄像头驱动参考 [Espressif esp32-camera](https://github.com/espressif/esp32-camera)，屏幕接口参考 [ESP-IDF LCD 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/lcd/index.html)。

## 5. 下载的小智固件什么时候用

`v2.2.6-bread-compact-wifi-s3cam-3660.bin` 是配套“小智 AI”应用，适合以后检查整套语音、相机、屏幕的商家演示。它不是 Image Oracle 的项目固件，也不是可直接修改的源码。若实物不是 OV3660，不能仅凭板名就认定这个二进制适配。

飞书教程引用的 [烧录说明](https://my.feishu.cn/wiki/Zpz4wXBtdimBrLk25WdcXzxcnNS) 需在使用该二进制前核对。本次没有验证其合并镜像布局和写入地址，**不提供猜测的 `write-flash 0x0` 命令**。

教程指向的小智源码是 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32/)，当时说明要求 ESP-IDF 5.5.3 以上、目标 `esp32s3`、板型 `Bread Compact WiFi + LCD +Camera`、屏幕 `ST7789 240*240`。这是该小智版本的构建说明，不代表 Image Oracle 必须使用同一工程或版本。源码仓库本次未克隆，后续使用时应固定 revision。

## 6. 下次继续的入口

- 对照实物确认主板、摄像头、屏幕三个版本，解决上述 N8R8／N16R8 和屏幕 PDF 差异。
- 读取现有串口输出，确认 USB-UART 端口与存储规格。
- 在 `firmware/` 建立经过小修正的相机最小工程，固定依赖，记录真实构建／烧录／验证命令。
- 相机与屏幕验证后，在 `hardware/` 记录最终接线；此前本文件的表格都只是商家参考。

本次已检查下载大小和 SHA-256、ZIP 完整性、RAR 目录及 PDF 内容。实物型号、供电稳定性、固件兼容性和所有功能尚未实测。
