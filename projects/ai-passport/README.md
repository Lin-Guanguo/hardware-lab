# AI Passport

探索 FoloToy AI Passport：一款集成屏幕、按键、电池和 NFC 标签的紧凑可编程装置。

## 当前确定方案

先验证已到货的 FoloToy AI Passport 的出厂功能和 USB 连接，核对版本后再复现对应官方固件、开发屏幕与按键应用；目前没有本地固件工程或已验证的构建入口。NFC 内容切换仍属探索，不能当作已实现功能。

- 2026-09-16，用户确认已经下单，计划到货后开始玩。
- 2026-09-28，用户确认 TRAE 版到货并通过 USB-C 连接 Mac；初始状态有充电灯、屏幕未亮，USB 未枚举。用户开机后识别到 Espressif USB Serial/JTAG，并成功读取出厂程序日志；日志显示 BLE 连接、通知订阅和时间同步成功。
- 尚未完成硬件版本核对、出厂功能验收、固件导入、工具链安装、构建或烧录。
- 后续随首份固件或实验记录，按需创建 `firmware/`、`docs/` 等目录。

## 目标与约束

- 先从屏幕、按键交互和一个实用的小应用开始。
- 探索在屏幕上选择名片、微信或小红书链接，再通过 NFC 让另一部手机打开选中的内容。
- 希望功耗较低，并在本地 Mac 上通过 shell 工具完成开发。
- 当前资料中的被动 NTAG213 没有 MCU 侧 BSP API。通过按键切换 NFC 内容仍是待研究的功能，尚未验证；固定 URL 加服务端切换跳转目标也是候选方案，但依赖网络，并受具体 App 链接行为限制。

## 下一步

1. 验收出厂屏幕、三个功能键和内容同步；核对硬件版本、随附配件、出厂固件和恢复方式，检查实际 NFC 标签及其写保护状态。
2. 按仓库约定将匹配的官方工程作为 Git submodule 引入 `upstreams/`，保留许可证，记录上游 revision；本项目的应用源码按需放入 `firmware/`。
3. 复现构建流程，在下方记录具体环境准备、构建、烧录和日志命令，遵循导入工程的板卡专属说明。
4. 跑通最小的屏幕按键应用，再分别实验 NFC 和功耗。

## 常用命令

2026-09-28 已执行以下只读检查：

```sh
ioreg -p IOUSB -w 0
ioreg -r -c IOSerialBSDClient -l -w 0 | rg 'IOCalloutDevice|IODialinDevice|IOTTYDevice'
```

首次检查未枚举到设备；用户开机后复查结果如下：

- USB 名称：`USB JTAG/serial debug unit`，厂商 `Espressif`，VID:PID 为 `303A:1001`。
- 本次串口：`/dev/cu.usbmodem1101`（重插后可能变化）。
- 使用 Python 标准库 `os` / `termios` / `select`，以 115200、8N1 打开串口并监听 12 秒，收到 1043 字节日志。未发送串口命令，未主动设置 DTR/RTS；清除 `HUPCL` 避免关闭时挂断控制线。
- 日志显示应用运行，BLE 已连接、MTU 协商为 256、通知特征已订阅，并接收时间消息，报告“系统时钟已同步”。BLE 对端身份未从日志确认。
- 已验证 USB 枚举和设备到电脑的日志传输，观察到出厂程序的 BLE 数据接收；未刷写或复位固件，尚未完成屏幕、按键、电池或 NFC 的完整验收。

固件命令尚未建立；不直接套用通用 ESP32-C3 开发板配置。

## 参考资料

- [官网](https://ai-passport.folotoy.cn/#diy)
- [官方 Codex 开发教程](https://ai-passport.folotoy.cn/guides/create-a-play-with-codex/)
- [官方固件安装工具](https://ai-passport.folotoy.cn/tools/web-flasher/)
- [官方源码](https://github.com/FoloToy/ai-passport)
- [购买与讨论归档](../../../CyberMnema/timeline/2026/09/W38/AI_Passport.20260916.md)
