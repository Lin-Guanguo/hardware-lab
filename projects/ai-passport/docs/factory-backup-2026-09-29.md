# 出厂固件备份与恢复

## 当前确定方案

更换玩法前保留当前设备的完整 Flash 备份。2026-09-29 已完成全容量读取和设备端摘要校验；未执行恢复写入，也未替换固件。官方另有设备专属恢复入口，但本轮未验证该设备的专属网页或下载镜像。

## 实测结果

| 项目 | 结果 |
| --- | --- |
| 芯片 | ESP32-C3 QFN32，revision v1.1 |
| Flash | 8 MB，XMC，manufacturer `20` / device `4017` |
| 安全状态 | Secure Boot Disabled；Flash Encryption Disabled |
| 应用名称 / 版本 | `trae_card` / `1.2.2`，从备份内 app descriptor 读取 |
| 构建时间 / SDK | `Sep 15 2026 11:35:38` / ESP-IDF `v5.5.3` |
| 本机备份 | `projects/ai-passport/artifacts/backups/factory-20260929-205821/factory-full-921600.bin` |
| 文件大小 | 8,388,608 字节 |
| SHA-256 | `745978d062156ebf667d79f645eb8360370df3a92c9a7942775291a5c2053e1c` |
| 设备比对 | `verify-flash`：`Verification successful (digest matched)` |

备份包括 bootloader、分区表、应用和全部数据区域。分区表包含 `nvs`、`phy_init`、`factory`、`imgstore`、`imgframe`、`cardid`、`imguser`、`audio`、`imgava`；未解析或公开个人内容和设备凭据。备份目录权限为 `0700`，镜像为 `0600`，均被 Git 忽略。同目录保留 SHA256SUMS、分区元数据和读取/校验日志。

完整备份不包含芯片 eFuse。后续实验不烧写 eFuse、不启用 Secure Boot 或 Flash 加密、不禁用下载接口，并保留原生 USB Serial/JTAG。尚未核对本板在应用禁用 USB 时的物理下载入口，不能把软件备份当作任何故障下都可恢复的保证。

## 本次执行的读取和校验

以下命令使用隔离的固定版本工具，不是烧录操作。进入下载模式会暂时中断应用；本次通过 USB 自动复位成功，无需操作板上引脚。

```sh
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32c3 --port /dev/cu.usbmodem1101 \
  --before usb-reset --after no-reset --connect-attempts 3 flash-id

uv tool run --from esptool==5.1.0 esptool \
  --chip esp32c3 --port /dev/cu.usbmodem1101 \
  --before no-reset --after no-reset --connect-attempts 3 get-security-info

uv tool run --from esptool==5.1.0 esptool \
  --chip esp32c3 --port /dev/cu.usbmodem1101 --baud 921600 \
  --before usb-reset --after no-reset --connect-attempts 3 \
  read-flash 0 ALL \
  projects/ai-passport/artifacts/backups/factory-20260929-205821/factory-full-921600.bin

uv tool run --from esptool==5.1.0 esptool \
  --chip esp32c3 --port /dev/cu.usbmodem1101 --baud 921600 \
  --before no-reset --after no-reset --connect-attempts 3 \
  verify-flash 0 \
  projects/ai-passport/artifacts/backups/factory-20260929-205821/factory-full-921600.bin
```

默认 115200 读取过慢，主动中断了首次读取；中断后的退出握手报错，不能使用该次产物。随后重新进入下载模式，以 921600 完整读取，耗时 98.2 秒，退出码 0；验证退出码 0。未来重新备份应使用新的目录，避免覆盖本次已校验镜像。

校验后执行 `--before no-reset --after hard-reset read-mac`，RTS 复位未退出 stub：后续仍显示 `Stub flasher is already running`。改用下面的 watchdog 复位后成功返回原应用，串口读到 2,729 字节启动日志，含显示/LVGL、BLE、音频初始化、`99-ready` 和 `Returned from app_main()`。这不写 Flash；屏幕仍需用户目视确认。

```sh
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32c3 --port /dev/cu.usbmodem1101 \
  --before no-reset --after watchdog-reset --connect-attempts 2 read-mac
```

## 需要恢复时

### 官方默认固件

按[官方恢复教程](https://ai-passport.folotoy.cn/guides/restore-factory-firmware/)，扫描自己设备背面的二维码，将完整链接私下转到电脑，用桌面 Chrome 或 Edge 打开。设备连接并开机后，在专属页底部进入“恢复默认固件”，连接并核对设备，再执行完整恢复。链接包含 SN 和 KEY，不提交到仓库或公开分享。

官方恢复可能提供另一版本的默认固件；它不等同于恢复本次备份中的个人设置。

### 本机快照恢复（命令已整理，尚未执行）

先核对仍为同一台设备、串口未变、镜像 SHA-256 与上表一致，并检查当前安全状态。下面操作会覆盖完整 Flash，以备份时的内容替换此后所有修改；只在明确需要回退时执行，不额外执行 `erase-flash`，也不使用 `--force`。

```sh
uv tool run --from esptool==5.1.0 esptool \
  --chip esp32c3 --port /dev/cu.usbmodem1101 --baud 921600 \
  --before usb-reset --after watchdog-reset --connect-attempts 3 \
  write-flash --flash-mode keep --flash-freq keep --flash-size keep 0 \
  projects/ai-passport/artifacts/backups/factory-20260929-205821/factory-full-921600.bin
```

恢复后检查启动日志、屏幕、按键与小程序连接。工具内置写入校验通过仍不能替代这些功能验收。参考：[Espressif 读取与写入说明](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/esptool/basic-commands.html)。
