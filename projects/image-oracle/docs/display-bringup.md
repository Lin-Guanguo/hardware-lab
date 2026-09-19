# 屏幕首次启动记录

## 目标与实物状态

2026-09-19：用户报告已按[接线表](../hardware/display-wiring.md)连接八针屏幕，授权继续操作。主板正常插入靠 EN/RST 的原生 USB-C 口，未按 BOOT。

- 屏幕排针顺序由用户确认：`GND VCC SCL SDA RST DC CS BL`，与套装资料一致。
- 供电按套装 3.3 V，SCK40、MOSI41、RST21、DC47、CS42、BL38。
- 没有新增实物接线／背面照片，具体 PCB 版本未独立核对；用户随后目视确认屏幕已显示测试画面。
- 电脑识别原生 USB JTAG/serial debug unit，VID/PID `303a:1001`，设备序列号与此前同一主板一致；当前端口 `/dev/cu.usbmodem1101`。

## 烧录前检查

原厂 16 MiB 备份重新计算 SHA-256，与此前验证记录一致：

```sh
shasum -a 256 projects/image-oracle/artifacts/backups/factory-20260918.bin
```

结果：`d73b6dd5a15e469a30629798664fb6e9e5c0ee30ef2679d75858d97a72b6fb15`。相机基线的源码、固件和原厂恢复路径仍保留；没有重新读取完整 Flash。

接好屏幕后，原相机固件成功拍照，说明当前供电、相机与原生 USB 仍能工作，但不证明屏幕接线无误：

```sh
uv run projects/image-oracle/scripts/capture.py \
  --port /dev/cu.usbmodem1101 \
  --output projects/image-oracle/artifacts/photos/display-wiring-check.jpg
```

收到 OV3660、16 MB Flash、8 MB PSRAM 信息，保存 320×240 JPEG，5311 字节。提取公共原生 USB 连接类后再拍一张 `display-usb-helper-check.jpg`，4869 字节，确认连接行为仍可用；照片均不入 Git。

## 屏幕固件

独立工程为 [display_serial](../firmware/display_serial/README.md)，复用已有 Arduino CLI／ESP32 core，新增固定版本 Adafruit 显示库。应用上电显示色块、白框和文字，USB 命令支持纯色、测试页和背光开关。摄像头基线工程未加入显示依赖。

构建通过，程序占用 341,532 字节，静态 RAM 24,456 字节，应用二进制 341,680 字节。生成的分区表与相机基线逐字节一致。

通过原生 USB 自动进入下载模式，写入启动程序、分区表、OTA 引导数据和应用，各段摘要校验全部通过。`--after watchdog-reset` 本次成功自动进入应用，无需用户再按按钮或断电。

```sh
bash projects/image-oracle/scripts/build-display.sh
(
  cd projects/image-oracle/build/display_serial
  uv tool run --from esptool==5.1.0 esptool \
    --chip esp32s3 --port /dev/cu.usbmodem1101 \
    --before usb-reset --after watchdog-reset \
    write-flash @flash_args
)
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 STATUS
```

首次状态回复：`firmware=display_serial configured=ST7789 size=240x240 ready=1 backlight=1 uptime_ms=5572 flash=16777216 psram=8388608 sck=40 mosi=41 rst=21 dc=47 cs=42 bl=38 spi_hz=8000000`。这确认主板应用正在运行，并按配置发起显示操作。

随后独立重开客户端，`STATUS` 的 uptime 增至 85,627 ms，确认打开／关闭 USB 未让程序复位；重画测试页返回 `OK TEST`。

用户在测试页显示后反馈“确实显示了”，基本显示验证通过。没有收到新照片；颜色顺序、四边是否完整和旋转方向未逐项检查，背光开关命令也尚未单独目视验证。当前保留测试页，下一步确认按键模块后做按键计数实验。

## 验证命令

```sh
bash -n projects/image-oracle/scripts/build-display.sh
python3 -m py_compile projects/image-oracle/scripts/capture.py \
  projects/image-oracle/scripts/native_usb.py \
  projects/image-oracle/scripts/display.py
git diff --check
```

上述脚本语法和差异检查已通过。屏幕没有 MISO，串口状态或命令成功不能代替对实际画面的检查。
