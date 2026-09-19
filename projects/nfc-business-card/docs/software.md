---
description: macOS 工具检查、推荐软件与尚未执行的安装范围
last_updated: 2026-09-17
---

# 软件与本机环境

**本轮只检查和研究，没有安装软件。** 用户要求安装前讨论；下列版本为 2026-09-17 调研快照，正式安装前再次确认包、架构和所需权限。

## 已检查的本机状态

| 项目 | 结果 |
| --- | --- |
| 操作系统 | macOS 26.3，arm64 |
| Git | `/usr/bin/git`，2.50.1 Apple Git |
| Python | pyenv Python 3.12.12 |
| CMake | `/opt/homebrew/bin/cmake`，4.4.3 |
| Homebrew | 已安装；已查看 formula/cask 清单 |
| 阅读资料 | 已有 Poppler / `pdftotext`、`pdftoppm`，本轮用于核对原厂 PDF |
| CAD | PATH、`/Applications`、`~/Applications` 中未发现 KiCad、FreeCAD、OpenSCAD |
| Nordic 开发 | PATH 中未发现 `nrfutil`、`west`、`ninja`、`arm-none-eabi-gcc`；常见安装目录未发现 Nordic/SEGGER 工具 |
| 其他嵌入式环境 | 常见位置未发现 PlatformIO、Arduino CLI 或相关应用 |

这是常见路径与包清单检查，不是全盘扫描，也不排除用户另存的工具。Homebrew 查询时刷新了 API 元数据，没有安装 formula/cask。已有的全局 Python/CMake 不代表满足 Nordic 固定 SDK 所需的配套版本。

## 推荐安装组合

USB 需求加入后，功能样机有两种软件入口：**EN04/XIAO 可先用板厂 Arduino 路线**，或 **nRF52840 DK 使用 Nordic SDK**。先选硬件和 USB bootloader，再选一套首轮工具，不同时默认安装两套。日常 USB 上传不需要每次运行 SWD；J-Link 用于 DK 调试、定制板首烧或救援。

| 软件 | 当前建议 | 作用与安装范围 |
| --- | --- | --- |
| **KiCad 10.0.6** | CAD 阶段安装 | 原理图、PCB、ERC/DRC、Gerber/STEP 导出；应用及符号/封装/3D 库会占用磁盘 |
| **FreeCAD 1.1.3 arm64** | CAD 阶段安装 | 参数化外壳、导入 PCB STEP、机械干涉与加工输出；官方 arm64 DMG 可用 |
| **Arduino IDE 或 Arduino CLI + Seeed nRF52 Boards** | EN04/XIAO 原型时二选一 | 官方 NFC 指南验证过 Boards 1.1.13，另需屏幕与 NFC 库；CLI 的实际复现命令尚未验证 |
| **nRF Util + SDK Manager + nRF Connect SDK v3.4.0 配套工具链** | 决定先做功能验证时安装 | 固件构建、依赖管理与板级开发；含大量源码和工具链，不能只安装一个编译器替代 |
| **SEGGER J-Link 软件** | 选定 DK/调试器后安装 | SWD 下载与调试，是否需要具体驱动以硬件与 Nordic 流程为准 |
| VS Code + Nordic 扩展 | 可选 | 图形化管理 SDK/构建/调试；如果继续使用 Codex 与 shell，可先不装 |

建议分两步讨论：先决定功能验证硬件，再安装对应的板厂 Arduino 或 Nordic 工具；进入电路/外壳设计时增加 KiCad + FreeCAD。也可以先安装两个 CAD 工具做外形研究，但不宜在 USB、NFC 和电池约束验证前冻结 PCB。板厂路线依据：[Seeed NFC 指南](https://wiki.seeedstudio.com/XIAO-BLE-Sense-NFC-Usage/)。

官方入口：[KiCad macOS](https://www.kicad.org/download/macos/)、[FreeCAD 1.1.3](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3)、[Nordic 安装说明](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/installation/install_ncs.html)、[SDK v3.4.0](https://github.com/nrfconnect/sdk-nrf/releases/tag/v3.4.0)、[nRF Util](https://www.nordicsemi.com/Products/Development-tools/nRF-Util)。

## Nordic 环境的注意点

当前官方流程使用 `nrfutil sdk-manager` 或 VS Code 扩展，不默认照旧教程安装 Desktop Toolchain Manager。`latest` 文档目前显示 3.4.99 开发版本，工程锁定的是发布标签 v3.4.0；安装时以该版本的匹配工具链和支持矩阵为准。

当前安装文档的 macOS SDK Manager 路径为 `/opt/nordic/ncs`，不保证能自由改到本项目目录。项目只保存自身源码、配置和版本说明，不把 SDK 整棵复制进仓库。系统路径写入、磁盘占用、可能的权限提示在安装前说明；不自行绕过 Gatekeeper。

以下是官方命令形态的计划示例，**尚未执行**，不是已经验证的本机安装步骤：

```sh
nrfutil install sdk-manager
nrfutil sdk-manager search
nrfutil sdk-manager install v3.4.0
```

先通过官方渠道安装 nRF Util，再核对本机 arm64、SDK 版本与工具支持。系统对固件构建和配套工具的支持等级可能不同；不能只因为 macOS 26 出现在表中就保证每个 J-Link/扩展版本完全兼容。第一次构建用官方样例做烟雾验证，记录实际 `west`、SDK、工具链和调试器版本。

## 不必同时安装的替代方案

- EasyEDA 可以作为贴片供应链集成优先时的 EDA 备选；本项目默认 KiCad，便于本地源文件和 shell 工作流，不同时维护两份原理图。
- OpenSCAD 可用于代码生成的简单外壳；涉及 PCB STEP、复杂台阶和装配检查时优先 FreeCAD。本轮不安装第二套机械 CAD。
- 旧 nRF5 SDK 不作为默认新增环境。采用板厂 Arduino BSP 时固定版本并验证 NFC/USB/屏幕共同工作；与 NCS 镜像的 Flash 布局和下载格式不能混用。
- 暂不需要 Docker、云端构建、手机 App 开发环境、平台服务或新的 Codex 插件。
