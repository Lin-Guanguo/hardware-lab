# AI Passport

探索 FoloToy AI Passport：一款集成屏幕、按键、电池和 NFC 标签的紧凑可编程装置。

## 当前确定方案

先使用已下单的 FoloToy AI Passport，核对到货版本后复现对应官方固件，再做屏幕与按键应用；目前没有本地固件工程或已验证的构建入口。NFC 内容切换仍属探索，不能当作已实现功能。

- 2026-09-16，用户确认已经下单，计划到货后开始玩。
- 本项目尚未进行实物验货、固件导入、工具链安装、构建、烧录或实机测试。
- 后续随首份固件或实验记录，按需创建 `firmware/`、`docs/` 等目录。

## 目标与约束

- 先从屏幕、按键交互和一个实用的小应用开始。
- 探索在屏幕上选择名片、微信或小红书链接，再通过 NFC 让另一部手机打开选中的内容。
- 希望功耗较低，并在本地 Mac 上通过 shell 工具完成开发。
- 当前资料中的被动 NTAG213 没有 MCU 侧 BSP API。通过按键切换 NFC 内容仍是待研究的功能，尚未验证；固定 URL 加服务端切换跳转目标也是候选方案，但依赖网络，并受具体 App 链接行为限制。

## 到货后的下一步

1. 核对硬件版本、随附配件、出厂固件和恢复方式，检查实际 NFC 标签及其写保护状态。
2. 将匹配的官方工程导入 `firmware/`，保留许可证，在 `docs/` 中记录上游 revision。
3. 复现构建流程，在下方记录具体环境准备、构建、烧录和日志命令，遵循导入工程的板卡专属说明。
4. 跑通最小的屏幕按键应用，再分别实验 NFC 和功耗。

## 常用命令

尚未建立。后续只添加已在本项目源码和工具链上验证的命令，不直接套用通用 ESP32-C3 开发板配置。

## 参考资料

- [官网](https://ai-passport.folotoy.cn/#diy)
- [官方 Codex 开发教程](https://ai-passport.folotoy.cn/guides/create-a-play-with-codex/)
- [官方固件安装工具](https://ai-passport.folotoy.cn/tools/web-flasher/)
- [官方源码](https://github.com/FoloToy/ai-passport)
- [购买与讨论归档](../../../CyberMnema/timeline/2026/09/W38/AI_Passport.20260916.md)
