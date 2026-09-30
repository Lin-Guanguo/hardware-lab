# AI Passport

探索 FoloToy AI Passport：一款集成屏幕、按键、电池和 NFC 标签的紧凑可编程装置。

## 当前确定方案

先验证已到货的 FoloToy AI Passport 的出厂功能和 USB 连接，核对版本后再复现对应官方固件、开发屏幕与按键应用；目前没有本地固件工程或已验证的构建入口。NFC 内容切换仍属探索，不能当作已实现功能。

2026-09-29 UI 方向确定为中文“个人终端”，正在比较三种视觉方案。当前交互示意为身份、工作、微信二维码三页；用户确认上键向前、下键向后，首尾循环。微信页使用用户此前在“硬件 测试”聊天提供的原始二维码，保留白底黑码和留白；个人二维码仅保留在本机对话预览中，不提交仓库。上述页面尚未实现或烧录到设备，工作状态均为演示数据。

- 2026-09-16，用户确认已经下单，计划到货后开始玩。
- 2026-09-28，用户确认 TRAE 版到货并通过 USB-C 连接 Mac；初始状态有充电灯、屏幕未亮，USB 未枚举。用户开机后识别到 Espressif USB Serial/JTAG，并成功读取出厂程序日志；日志显示 BLE 连接、通知订阅和时间同步成功。
- 2026-09-29，重新连接后 USB 及 `/dev/cu.usbmodem1101` 仍正常；按下述方式监听 12 秒收到 105 字节，包含“还没有传过全屏图”。用户描述当前为可通过蓝牙更新内容的简单玩法；未取得固件版本号，未刷写固件。
- 同日完成完整 8 MB Flash 备份及设备摘要校验；确认当前应用为 `trae_card 1.2.2`（2026-09-15 构建），芯片为 ESP32-C3 v1.1，Secure Boot 与 Flash 加密均未启用。备份位置和恢复命令见[备份与恢复记录](docs/factory-backup-2026-09-29.md)。尚未执行恢复写入。
- 尚未完成硬件版本核对、出厂功能验收、固件导入、工具链安装、构建或烧录。
- 后续随首份应用源码按需创建 `firmware/` 等目录。

## 目标与约束

- 先从屏幕、按键交互和一个实用的小应用开始。
- 探索在屏幕上选择名片、微信或小红书链接，再通过 NFC 让另一部手机打开选中的内容。
- 希望功耗较低，并在本地 Mac 上通过 shell 工具完成开发。
- 当前资料中的被动 NTAG213 没有 MCU 侧 BSP API。通过按键切换 NFC 内容仍是待研究的功能，尚未验证；固定 URL 加服务端切换跳转目标也是候选方案，但依赖网络，并受具体 App 链接行为限制。

## 下一步

1. 在已校验的完整备份基础上确定新 UI 或玩法，核对构建产物和 USB 下载路径后再替换固件；保留当前快照用于回退。
2. 验收出厂屏幕、三个功能键和内容同步；核对硬件版本、随附配件、出厂固件，检查实际 NFC 标签及其写保护状态。
3. 按仓库约定将匹配的官方工程作为 Git submodule 引入 `upstreams/`，保留许可证，记录上游 revision；本项目的应用源码按需放入 `firmware/`。
4. 复现构建流程，在下方记录具体环境准备、构建、烧录和日志命令，遵循导入工程的板卡专属说明。
5. 跑通最小的屏幕按键应用，再分别实验 NFC 和功耗。

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

已验证的备份/校验命令见[备份与恢复记录](docs/factory-backup-2026-09-29.md)；本项目构建及烧录尚未验证，不直接套用通用 ESP32-C3 开发板配置。

## 默认固件恢复（2026-09-29 核对）

[官方恢复教程](https://ai-passport.folotoy.cn/guides/restore-factory-firmware/)明确支持替换玩法后恢复默认固件：扫描自己设备背面的二维码，将设备专属完整链接私下转到电脑，用桌面 Chrome 或 Edge 打开；USB 连接并开机后，在页面底部进入“恢复默认固件”，连接并核对设备，再执行完整恢复。成功后设备自动重启。专属链接包含 SN 和 KEY，不写入仓库或公开记录。

官方恢复默认固件不等于还原当前全部个人设置。本轮已使用隔离的 `esptool==5.1.0` 读取全 Flash，并验证文件大小、SHA-256 和设备内容摘要；备份包含数据分区，可能含个人内容或设备凭据，仅保存在本机被忽略且限制权限的 `artifacts/` 目录。读取方法参考 [Espressif read-flash](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/esptool/basic-commands.html#read-flash-contents-read-flash)。

本轮实际状态：USB 自动进入下载模式、全容量备份和摘要比对已通过；没有写入固件。RTS 复位未退出 stub，改用 watchdog 复位后原应用重新启动，日志确认显示/LVGL、BLE 和音频初始化至 `99-ready`。设备专属恢复页、官方镜像和实际恢复写入尚未验证；应用禁用 USB 时本板的手动下载入口也待确认。不能据此承诺任何情况下都能无损恢复。

## 进阶玩法调研（2026-09-29）

以下仅核对公开源码和文档，未在本机编译或在设备上验收，也未确定开发方向：

- [Claude Buddy 分支](https://github.com/FoloToy/ai-passport/tree/9f5e2a43b7f8da9dda119174f0286ca8f2485795)：18 种像素角色、任务状态、近期消息和实体按键审批，通过加密 BLE 交换 JSON。分支说明称对接实验性 Claude Desktop Hardware Buddy；附带的[验证记录](https://github.com/FoloToy/ai-passport/blob/9f5e2a43b7f8da9dda119174f0286ca8f2485795/docs/validation/2026-08-11-claude-buddy-phase1.md)明确未做设备启动、桌面配对及持续连接验收，不能视为即刷即用。可参考其协议做 Mac 脚本状态屏；其他工具的桥接需另行实现。
- [离线宝可梦图鉴](https://github.com/FoloToy/ai-passport/blob/main/docs/reference/sunny0826/offline-pokedex/README.md)：社区归档记录包含 1,025 个条目、像素图和叫声，适合体验完整自定义应用。
- [声音钥匙扣](https://github.com/FoloToy/ai-passport/blob/main/docs/reference/shinku-chen/voice-keychain/README.md)与[双机 BLE 通信经验](https://github.com/FoloToy/ai-passport/blob/main/docs/reference/shinku-chen/two-device-ble-link.md)：分别可参考制作声音装置、双机对战或交换消息。
- 自建方向：Mac 脚本遥控器、服务器状态屏、Wi-Fi/BLE 信号观察器、按键语音终端。它们是候选设计，不能当作当前出厂固件已有功能。

官方 BSP 已覆盖屏幕、按键、音频、Wi-Fi/BLE 和 USB 日志；硬件指南记载 ESP32-C3、8 MB Flash、无 PSRAM。适合把交互放在卡片上，把大模型和重计算放在 Mac 或服务器。NTAG213 为被动标签且没有 MCU 侧 BSP API，不能据此承诺通过固件动态改 NFC 或模拟门禁卡。依据：[官方硬件指南](https://github.com/FoloToy/ai-passport/blob/main/docs/hardware-design/AI_HARDWARE_DEVELOPMENT_GUIDE.md)。

## 参考资料

- [官网](https://ai-passport.folotoy.cn/#diy)
- [官方 Codex 开发教程](https://ai-passport.folotoy.cn/guides/create-a-play-with-codex/)
- [官方固件安装工具](https://ai-passport.folotoy.cn/tools/web-flasher/)
- [官方源码](https://github.com/FoloToy/ai-passport)
- [购买与讨论归档](../../../CyberMnema/timeline/2026/09/W38/AI_Passport.20260916.md)
