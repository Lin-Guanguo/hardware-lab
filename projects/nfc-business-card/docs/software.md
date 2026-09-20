---
description: Homebrew 软件管理、FreeCAD 安装与后续工具范围
last_updated: 2026-09-20
---

# 软件与本机环境

2026-09-19 用户授权准备建模软件，并确认优先用 Homebrew 管理。**FreeCAD 1.1.3 arm64 已安装并启动，第一份空间研究模型已生成和检查。** 先研究器件排布和厚度；KiCad 与固件工具暂未安装。

2026-09-20 制造与 AI 工作流调研后，优先验证 **EasyEDA Pro 官方 AI API 工具链**。官方 Skill 和本地桥接依赖已在仓库内安装，用户自行安装的专业版 **3.2.203** 已连接 **Run API Gateway 1.0.6**；独立小型原理图通过保存重开、网表连接核对和工程包导出检查。继续使用此组合推进，KiCad 保留为备选；PCB 与制造文件导出尚未验证，详见 [PCBA 与 AI 设计流程调研](pcba-ai-workflow.md)。

## 仓库内 EDA Skill

用户要求外部上游仓库统一放在 `upstreams/`，采用 Git submodule 加符号链接，不使用全局 Skill 安装。

- 上游：[easyeda/easyeda-api-skill](https://github.com/easyeda/easyeda-api-skill)。版本 **1.1.36**，固定提交 **`ccfaf28a577b61a09ebc907f0a943d1e6c782def`**。
- 子模块：[`upstreams/easyeda-api-skill`](../../../upstreams/easyeda-api-skill)，保留上游原始文件。
- Skill 入口：[`.agents/skills/easyeda-api/SKILL.md`](../../../.agents/skills/easyeda-api/SKILL.md)；目录是指向 `../../upstreams/easyeda-api-skill` 的相对符号链接。
- 本地依赖放在子模块的 `node_modules/`；`.gitmodules` 使用 `ignore = untracked` 忽略未跟踪的运行依赖，仍会显示已跟踪源码的修改。npm 缓存放在仓库已有忽略规则覆盖的 `.cache/npm/`。
- 复用已有 Node.js **24.19.0**、npm **11.17.0**，安装锁文件中的 **ws 8.21.3**；未改全局 Skill、npm 包或 shell 配置。
- 上游示例的 `${CLAUDE_SKILL_DIR}` 在 Codex 中按实际 Skill 路径解释，适配约定写在根目录 AGENTS.md。此提交已附带 `references/`，其 README 中的文档构建、打包命令与当前 `package.json` 不一致，不执行这些旧命令。

从仓库根目录恢复依赖：

```sh
git submodule update --init --recursive
npm --prefix upstreams/easyeda-api-skill ci --omit=dev --ignore-scripts --no-audit --no-fund --cache "$PWD/.cache/npm"
```

需要连接 EDA 时，在独立终端从仓库根目录启动，结束后用 Ctrl-C 停止：

```sh
npm --prefix upstreams/easyeda-api-skill run server
```

桥接自动选择 `49620–49629` 的可用端口，仅监听 `127.0.0.1`。启动前先检查已有进程，避免重复运行；以下为本轮实际使用的端口，其他端口按启动输出替换：

```sh
curl --fail --silent http://127.0.0.1:49620/health
curl --fail --silent http://127.0.0.1:49620/eda-windows
```

官方 [`Run API Gateway`](https://jlc-ext.com/item/oshwhub/run-api-gateway) **1.0.6** 已经用户授权安装。在客户端 **高级 → 扩展管理器 → 已安装 → Run API Gateway → 配置** 中，已勾选“允许外部交互”和“显示在顶部菜单”。首次改权限后重新禁用/启用扩展，才成功连接；新编辑器窗口可看到 **API Gateway → 重新连接**。重连后窗口 ID 会变化，每次先读取 `/eda-windows` 并核对工程名。

已验证：`npm ci`、`node --check scripts/bridge-server.mjs`、`npm ls --omit=dev --depth=0` 通过；真实编辑器连接后 `/health` 返回 `edaConnected: true`。本轮桥接由手动后台进程运行，日志与 PID 留在被忽略的 `projects/nfc-business-card/logs/`；没有配置登录启动。后续终端启动的桥接可用 Ctrl-C 停止。

### 客户端与启动命令

- 应用：`/Applications/嘉立创EDA(专业版).app`，本轮界面确认版本 **3.2.203**、半离线模式。
- 用户执行 `setup-cli.command` 后，`/usr/local/bin/lceda-pro` 已可用；内容只通过 `open -F` 打开应用，**不是**原理图或 PCB 的命令行编辑接口。AI 操作通过上面的网关。
- 下次可运行 `lceda-pro`，再启动桥接或检查其是否已运行。挂载的安装镜像中也有同名应用，自动化应明确使用 `/Applications/` 下的已安装副本。

“所有工程”按客户端登记的工程目录加载；从其他路径打开的工程可以出现在“最近设计”，但不会因此自动加入左侧目录。2026-09-20 已验证登记测试产物目录后，左侧可显示 **AI-API-Smoke-Test**。按用户要求，所有项目的原始 `.eprj2` 工程现统一直接保存在仓库根目录 [eda/](../../../eda/README.md)，不使用工程文件符号链接。用户保存并退出客户端后，测试工程已移至 `eda/AI-API-Smoke-Test.eprj2`，迁移前后 SHA-256 一致，SQLite `PRAGMA quick_check` 通过。用户接下来在 **设置 → 客户端 → 数据路径 → 离线工程路径** 中将原测试目录替换为 `/Users/linguanguo/dev/hardware-lab/eda`，应用并重启；新路径的显示与打开待用户验证。后续工程直接保存到 `eda/`，无需逐一登记目录。这是本机客户端设置，不随 Git 克隆自动恢复。参见[官方客户端说明](https://prodocs.lceda.cn/cn/faq/client/)。

### 独立原理图验证（2026-09-20）

本轮只在新建本地工程 **AI-API-Smoke-Test** 中修改；用户打开的“示例工程_面板打印设计”保留在另一窗口。用两颗 **C25804 / 0603WAF1002T5E / R0603 / 10 kΩ** 电阻组成分压器，验证工具链，不作为电子名片的正式电路。

| 检查 | 结果 |
| --- | --- |
| 读取工程、搜索器件、放置和修改元件 | 通过，R1/R2 位号、阻值、料号与封装可读回 |
| 导线与网络端口 | 通过，建立 VIN、VMID、GND 三个网络 |
| 保存并从磁盘重开 `.eprj2` | 通过，元件、导线、端口与文字仍在 |
| `.epro2` 工程包导出 | 通过，文件已写入本地，ZIP 完整性检查通过 |
| 新版网表文件导出 | 通过，解析网表并断言 R1 的 2/1 脚为 VIN/VMID，R2 的 2/1 脚为 VMID/GND |
| PCB 布局、ERC/DRC、Gerber、BOM/坐标、实物 | 未验证 |

测试工程位于仓库根目录 `eda/`，其余导出产物保留在 `projects/nfc-business-card/artifacts/eda-smoke-test/`；此临时测试工程及产物均不入 Git：

- `eda/AI-API-Smoke-Test.eprj2`：可从 EDA 的“文件 → 打开工程”打开的本地原始工程。
- `AI-API-Smoke-Test-export.epro2`：导出的工程包；不能只改后缀当作 `.eprj2` 使用。
- `netlist.enet`、`verification.json`、`editor.png`：网表、核对结果和编辑器截图。

实际遇到的兼容性问题及已验证绕行方式：

1. 上游 Skill 1.1.36 的 `POST /eda-windows/select` 使用未定义的 `activeWindowId` 变量，导致响应报错并退出桥接进程。保留上游代码不变；改为每次 `POST /execute` 明确传入已核对工程的 `windowId`。重启桥接后重新发现窗口，不能复用旧 ID。
2. `sch_Netlist.getNetlist()` 已在文档标为废弃，本轮两次超时。改用 **`sch_ManufactureData.getNetlistFile()`** 后成功取得网表文件，并使用 `File.text()` 读回核对。
3. 器件搜索结果包含完整属性，但本轮按库 UUID 放置后部分附加属性为空；已显式补齐测试所需的阻值、精度与功率。正式 BOM 必须逐项核对，不能假定搜索结果的全部属性自动保留。

### 面板和 3D 外壳的范围

“面板打印设计”示例包含材料边界、开孔、透明控制、正面印刷和背胶等图层，用于设备正面的薄面板设计。专业版另支持简单的 3D 外壳图元，可导出上下盖 STL 用于打印，或导出 STEP/OBJ 继续建模；见[官方 3D 外壳导出说明](https://prodocs.lceda.cn/cn/pcb/export-3d-shell-file/index.html)。这些是独立的设计与下单流程，不能把面板示例或 PCB/PCBA 订单理解为已包含整机外壳和总装。名片的 ≤5 mm 厚度仍结合 FreeCAD 检查。

本项目选择 **嘉立创 EDA 专业版 Mac ARM64 客户端**，官网下载入口为 [软件下载](https://lceda.cn/page/download)。网页与桌面是运行形式，标准版与专业版是产品版本；[专业版也有网页版](https://prodocs.lceda.cn/cn/quick-start.html)。官方 Skill 声明桌面客户端为运行前提，先按此组合验证。Homebrew 的 `easyeda` 在本次查询中为 6.5.51，且已被禁用，不作为该客户端的安装入口。

## Homebrew 管理方式

桌面工具优先使用 Homebrew 官方 cask，避免同时维护手动安装和 cask 两份应用。FreeCAD 安装命令：

```sh
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew install --cask freecad
```

本次安装 FreeCAD 1.1.3 的 macOS arm64 版本，应用路径为 `/Applications/FreeCAD.app`。Homebrew 元数据与 [官方发布](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3) 的下载资产和 SHA-256 已交叉核对：

- 资产：`FreeCAD_1.1.3-macOS-arm64-py311.dmg`
- 大小：649,856,006 bytes
- SHA-256：`f5c0ece7cd7c932466d6effadc0fc6e179b0538a9d9a6a77a6769eae3af2667c`
- Homebrew 安装成功；`brew list --cask --versions freecad` 返回 `freecad 1.1.3`。
- `file /Applications/FreeCAD.app/Contents/Resources/bin/freecad` 确认为 arm64。
- `spctl --assess --type execute -vv /Applications/FreeCAD.app` 返回 accepted / Notarized Developer ID；没有修改系统安全设置。

日常查看版本及可用更新：

```sh
brew list --cask --versions freecad
brew outdated --cask freecad
```

将来需要时使用 `brew upgrade --cask freecad` 升级，或 `brew uninstall --cask freecad` 卸载；本轮没有执行升级或卸载。工程保存在本仓库，应用由 Homebrew 管理。升级前保存设计，重新执行模型验证后更新这里的版本记录。

## 打开和生成空间研究模型

直接用 FreeCAD 打开 [layout-study.FCStd](../enclosure/layout-study.FCStd)，即可选中对象调整尺寸与位置。前壁默认隐藏，外形目标以线框表示；各对象的 `Evidence` 属性记录尺寸来源和缺失项。

本轮已实际执行的生成方法：

1. 在 FreeCAD 中通过 `File → Open` 打开 [layout-study.FCMacro](../enclosure/layout-study.FCMacro)。
2. 确认需要保留的布局已经另存，关闭现有的研究模型文档。
3. 在宏编辑器激活时，选择 `Macro → Execute Macro`。宏会生成默认布局，保存 `.FCStd` 和同目录的 [JSON 检查报告](../enclosure/layout-study-report.json)。

运行宏会覆盖默认研究模型及报告。修改 `.FCStd` 不会自动回写宏；保留不同方案时另存文件，不要靠再次运行宏保存手动修改。JSON 是生成时的检查快照，后续手动移动器件不会自动更新报告。

本轮验证结果：宏在 FreeCAD 1.1.3 图形界面执行成功，模型显示与颜色已目视检查；另用应用内的 `freecadcmd` 重新打开保存文件并重算，确认 10 个几何实体有效、外形为 86 × 54 × 5 mm、已建模组件没有相互碰撞或超出假设内腔，主控区标称厚度余量为 0.2 mm。检查未包含未知器件和装配公差，不能视作可制造性通过。

命令行检查使用应用内的 `Contents/Resources/bin/freecadcmd`，并将 `PYTHONHOME`、`PYTHONPATH` 指向 `/Applications/FreeCAD.app/Contents/Resources`；已验证 `--help` 和临时检查脚本执行。普通打开模型使用 FreeCAD 图形界面即可。

## 安装前的本机检查（2026-09-17）

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
| **EasyEDA Pro + 官方 AI API 工具链** | 客户端 3.2.203、Gateway 1.0.6、Skill 1.1.36 已连接 | 独立原理图保存重开、工程导出与网表核对通过；PCB 制造流程待验证 |
| **KiCad 10.0.6** | EDA 备选，未安装 | 原理图、PCB、ERC/DRC、Gerber/STEP 导出；应用及符号/封装/3D 库会占用磁盘 |
| **FreeCAD 1.1.3 arm64** | 已安装并验证 | 参数化外壳、导入 PCB STEP、机械干涉与加工输出；通过 Homebrew 管理 |
| **Arduino IDE 或 Arduino CLI + Seeed nRF52 Boards** | EN04/XIAO 原型时二选一 | 官方 NFC 指南验证过 Boards 1.1.13，另需屏幕与 NFC 库；CLI 的实际复现命令尚未验证 |
| **nRF Util + SDK Manager + nRF Connect SDK v3.4.0 配套工具链** | 决定先做功能验证时安装 | 固件构建、依赖管理与板级开发；含大量源码和工具链，不能只安装一个编译器替代 |
| **SEGGER J-Link 软件** | 选定 DK/调试器后安装 | SWD 下载与调试，是否需要具体驱动以硬件与 Nordic 流程为准 |
| VS Code + Nordic 扩展 | 可选 | 图形化管理 SDK/构建/调试；如果继续使用 Codex 与 shell，可先不装 |

当前用 FreeCAD 研究外形，EDA 已通过 EasyEDA 官方 AI 接口的原理图基础验证。确定功能验证硬件后，再选择对应的板厂 Arduino 或 Nordic 工具。不宜在 USB、NFC 和电池约束验证前冻结 PCB。已安装的 FreeCAD 和 EDA 版本以上述实测记录为准；其余工具版本号为 2026-09-17 调研快照，安装时重新核对。板厂路线依据：[Seeed NFC 指南](https://wiki.seeedstudio.com/XIAO-BLE-Sense-NFC-Usage/)。

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

- EasyEDA Pro 与 KiCad 先选一套通过验证的工具，不同时维护两份原理图；制造商选择与 EDA 选择分别评估。
- OpenSCAD 可用于代码生成的简单外壳；涉及 PCB STEP、复杂台阶和装配检查时优先 FreeCAD。本轮不安装第二套机械 CAD。
- 旧 nRF5 SDK 不作为默认新增环境。采用板厂 Arduino BSP 时固定版本并验证 NFC/USB/屏幕共同工作；与 NCS 镜像的 Flash 布局和下载格式不能混用。
- 暂不需要 Docker、云端构建、手机 App 开发环境、平台服务或新的 Codex 插件。
