# 第三个程序：实时预览、定格照片与 Boolean Oracle

## 当前确定方案

本目录是项目当前采用的整合基线：[oracle_live.ino](oracle_live.ino)，构建入口为 [build-oracle.sh](../../scripts/build-oracle.sh)。ESP32-S3-CAM N16R8、OV3660、ST7789 和 MID 中心键沿用既有接线：左侧预览，按 MID 定格到右侧，并按固定图像算法生成 TRUE/FALSE。

2026-09-19 已构建、烧录并获用户实物验收；后续在此继续开发，两个早期固件保留作单项基线。当前仍是开发板与模块的桌面原型，未完成定制 PCB 或外壳。

## 功能说明


这是独立于 `camera_serial` 和 `display_serial` 的第三个固件。前两个工程的源码与构建目录保持原样；本程序复用显示工程的 `button_debouncer.h`，构建时需保留仓库结构。

## 交互

- 左侧 `LIVE`：持续显示摄像头预览。
- 中心键 MID：将当前已经显示完整的左侧画面复制到右侧 `FROZEN`，左侧继续播放。
- 下方：根据右侧照片的像素显示 `TRUE` 或 `FALSE`，旁边显示该照片的哈希。
- 再次按 MID：替换右侧照片和答案。长按只触发一次；照片只保存在 RAM，重新上电清空。

两个画面各为 112×84，保持 4:3 比例。此处“定格”保存的是当前可见的缩略图，不会再拍一张稍晚的高分辨率照片；一次显示周期内的多个按下请求合并为保存当前最新画面，原始按下次数仍保留在诊断字段中。

## 环境与接线

- 开发板：已验证的 ESP32-S3-CAM N16R8，摄像头为 OV3660。
- Arduino CLI 1.5.1，ESP32 core 3.3.11，ESP-IDF 5.5.5，随工具链提供的 `esp32-camera` 与 `esp_jpeg` 1.3.1。
- Adafruit BusIO 1.17.4、GFX 1.12.6、ST7735/ST7789 1.11.0，与第二个程序相同。
- 16 MB Flash、OPI 8 MB PSRAM、Hardware CDC；相机取 160×120 JPEG，双帧缓冲及 `CAMERA_GRAB_LATEST`，XCLK 20 MHz。
- 屏幕 SPI mode 0、8 MHz；SCK40、MOSI41、RST21、DC47、CS42、BL38。
- 按键 MID14、COM 共地，其他按键脚不接；原生 USB 保留 GPIO19／20。

沿用[屏幕接线](../../hardware/display-wiring.md)、[中心键接线](../../hardware/button-wiring.md)和已验证的相机排线，不新增接线，不启用 SD、Wi-Fi 或音频。

## 构建、烧录与恢复

从仓库根目录执行：

```sh
bash projects/image-oracle/scripts/build-oracle.sh
```

产物生成到 `projects/image-oracle/build/oracle_live/`。构建不会自动烧录。

确认连接的是当前主板、已有恢复文件且串口未被占用后，正常模式下可尝试：

```sh
(
  cd projects/image-oracle/build/oracle_live
  uv tool run --offline --from esptool==5.1.0 esptool \
    --chip esp32s3 --port /dev/cu.usbmodem1101 \
    --before usb-reset --after watchdog-reset write-flash @flash_args
)
```

如果自动切换下载模式失败：拔 USB，按住 BOOT/IO0，插回靠 EN/RST 的原生 USB-C，再松开 BOOT。重新确认设备后，把上面 `--before usb-reset` 改为 `--before no-reset` 执行。烧录后若没有自动启动，保持接线，不按 BOOT，短按 EN/RST。

第二个程序的用户确认可用版本已备份到本地忽略目录 `artifacts/firmware/display-nonblocking-20260919/`，包括源码、烧录文件、`flash_args` 与 SHA-256 清单。需要恢复时将烧录工作目录换为该目录；相机工程和完整原厂备份也保留，见[相机启动记录](../../docs/camera-bringup.md)。

第三个程序验收后，也已归档到 `artifacts/firmware/oracle-live-20260919/`，8 个文件的 `SHA256SUMS` 校验通过。恢复方法相同；归档范围与后续两条路线见[阶段收尾记录](../../docs/prototype-milestone.md)。

## 在 Mac 查询、定格与导出

```sh
uv run --offline projects/image-oracle/scripts/oracle.py --port /dev/cu.usbmodem1101 STATUS
uv run --offline projects/image-oracle/scripts/oracle.py --port /dev/cu.usbmodem1101 SNAP
uv run --offline projects/image-oracle/scripts/oracle.py --port /dev/cu.usbmodem1101 EXPORT \
  --output projects/image-oracle/artifacts/photos/oracle-frozen.png
```

`SNAP` 与按 MID 的行为一致；`EXPORT` 只读取已经定格的右图，逐行校验并另存 PNG，不重新拍照、不覆盖已有文件。导出期间不要再次按 MID；若照片变化、像素哈希或答案不一致，脚本报错且不保存混合照片。客户端复用避免触发复位的 `NativeUsbSerial`。

这些命令属于第三个程序；第一个程序的 `capture.py` JPEG 协议与第二个程序的屏幕控制命令不能混用。

## 固定算法

算法版本：`RGB565-FNV1a32-MSB-v1`。

1. JPEG 解码为 160×120 RGB565，以最近邻采样缩到屏幕显示的 112×84。
2. 按键冻结该缩略图，逐行、从左到右处理像素；每个 16 bit 像素先处理高字节，再处理低字节。
3. FNV-1a 32 bit 初值 `2166136261`，每个字节执行 `hash = (hash XOR byte) × 16777619`，按无符号 32 bit 回绕。
4. 哈希最高位为 1 返回 `TRUE`，否则为 `FALSE`。

只使用冻结照片像素，不加入按键次数、时间、随机种子、序列号或上一张照片的结果。同一份像素必然得到同一答案，连续两次答案允许重复。光照、曝光和传感器噪声可能让同一场景的两次拍摄不同；这是确定性映射，不是图像语义判断或真实随机数。

固定测试向量与缩放测试：

```sh
mkdir -p projects/image-oracle/build
c++ -std=c++17 -Wall -Wextra -pedantic \
  projects/image-oracle/tests/oracle_image_test.cpp \
  -o projects/image-oracle/build/oracle_image_test
projects/image-oracle/build/oracle_image_test
```

例如完整绿色 RGB565 `0x07E0` 画面得到 `35D106C5 / FALSE`，完整红色 `0xF800` 得到 `DD591DC5 / TRUE`。这些是软件测试向量，不是要求拍摄实物色卡得到相同像素。

## 代码怎么读

- [oracle_live.ino](oracle_live.ino)：板卡配置、三个任务、页面绘制、按键和 USB 协议。
- [oracle_image.h](oracle_image.h)：缩放和答案算法，可在 Mac 上单独测试。
- [oracle.py](../../scripts/oracle.py)：控制、逐行导出、重算照片哈希及答案。

`capture_camera()` 在 core 0 取帧、解码、缩放，目标更新周期不短于约 50 ms；主循环在 core 1 读取最新画面，仅刷新左侧图像区域。共享帧用互斥锁短暂保护复制，锁内不执行取帧、解码或 SPI。`sample_button()` 在 core 1 以较高优先级每 1 ms 采样并进行 10 ms 消抖。

右侧照片由主循环单独保存，不被预览任务改写。USB 使用零发送等待和可跳过消息策略；`ROW <0..83>` 一次返回一行，避免大图片输出长时间阻塞交互。命令回复采用尽力发送，客户端超时会报错，不会自动重试有副作用的 `SNAP`。

主要诊断字段：`camera_frames`／`preview_frames` 是取帧和显示的累计帧数；`live_frame`／`frozen_frame` 是显示及冻结帧编号；`snapshots`、`hash`、`oracle` 描述右图；`camera_errors`、`frame_age_ms`、`capture_us`、`decode_us` 用于定位相机问题；`preview_draw_max_us`、`snapshot_draw_max_us`、`sample_gap_max_us`、`usb_write_max_us`、`usb_dropped`、`loop_gap_max_us` 用于观察响应性。字段 `_us` 以微秒计，`_ms` 以毫秒计。

## 验证状态

2026-09-19：固件构建通过，程序 408,244 字节、静态 RAM 35,784 字节；运行时图像缓冲、相机驱动和任务栈另行分配。固定哈希、重复性、两种答案及最近邻缩放的 Mac 测试通过。手动进入下载模式后烧录及四段摘要校验通过；不按按钮断电重插后正常启动，识别 OV3660。

实机预览约 20 FPS，冻结右图时左侧继续更新；USB 无读取端回归通过，相机错误为 0，采样间隔峰值 1.490 ms、USB 发送峰值 0.314 ms。右图已导出 PNG，Mac 重算 `232CB5A2 / FALSE` 与板上一致，图像已打开检查。用户移动摄像头并多次按 MID 后，确认预览、定格、答案、画面方向和颜色“都正常，效果符合预期”，本版本作为后续开发的可用基线。详见[整合记录与实测数据](../../docs/oracle-bringup.md)。

可运行下列实机回归测试；期间不要按 MID，脚本会主动定格两次，验证预览推进、定格状态不变及 USB 无读取端下的响应性：

```sh
uv run --offline projects/image-oracle/tests/oracle_smoke.py --port /dev/cu.usbmodem1101
```

## 参考

- 相机引脚复用本仓库 [camera_serial](../camera_serial/README.md)，屏幕配置和消抖复用 [display_serial](../display_serial/README.md)。
- [Espressif esp32-camera](https://github.com/espressif/esp32-camera)：JPEG 相机驱动，随固定 Arduino 工具链提供，许可证保留在依赖目录。
- [Espressif esp_jpeg](https://github.com/espressif/idf-extra-components/tree/master/esp_jpeg)：使用随工具链安装的 1.3.1；调用其有输出缓冲长度限制的解码 API。RGB565 不交换字节，供本机 `uint16_t` 读取，由 Adafruit SPI 写入时处理传输字节序。
- [已验证的响应性经验](../../docs/responsive-input-display.md)。
