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

### 桥接稳定性（2026-09-22 诊断）

现场日志确认三件事：**bridge 现在没问题**（launchd 托管、单实例、只监听 127.0.0.1:49620，连续运行 30 分钟无重启）；**问题在扩展侧的连接行为**——30 分钟内 116 次连接 / 114 次注册 / 114 次断开，约每 16 秒重连一次，断开码 112 次是 1005；**每次重连都注册一个新的 windowId**，而服务端既不主动心跳也不清理死连接，于是出现"注册 2 个窗口但只开着 1 个 EasyEDA"的僵尸注册。当活动窗口指向刚断开的 socket 时，请求要么返回 `No EDA window connected`，要么（半死连接）30 秒超时。

按性价比的处理顺序：

1. 调用侧加固（已落地）：执行前先 `GET /eda-windows` 并 `POST /eda-windows/select` 选一个真实在线窗口，失败重选重试一次。仅此一项不足以解决半死连接的超时。
2. 服务端心跳与清理（待做）：每 ~15 秒向所有 EDA 连接 ping，超时未 pong 就关闭并摘除注册。注意 `bridge-server.mjs` 位于 `.agents/skills/easyeda-api/`（符号链接到 `upstreams/easyeda-api-skill` 子模块），按仓库约定**不改上游**，要在仓库内放一份打了补丁的本地副本或包装脚本来跑。
3. 客户端收敛（需用户操作）：只保留一个编辑器窗口/标签页。若同时开着两个图页标签，扩展很可能各注册一次连接，这正是 `count: 2` 的来源，也会让活动窗口频繁切换。

### 通道恢复 runbook

现象与判据（按顺序核对，避免把调用侧误判成扩展故障）：

1. `curl -s http://127.0.0.1:49620/health`：桥接是否在跑（`service: easyeda-bridge`）、`edaConnected` 是否为 true。桥接由 launchd 托管：`launchctl list | grep easyeda-bridge`；重启用 `launchctl remove easyeda-bridge` 再 `launchctl submit -l easyeda-bridge -o /tmp/easyeda-bridge.out -e /tmp/easyeda-bridge.err -- /bin/zsh -lc "cd <skill dir> && exec node scripts/bridge-server.mjs"`。
2. `curl -s http://127.0.0.1:49620/eda-windows`：窗口列表。**health 为 true 但列表为空**说明扩展刚断、注册已过期——这是最常见的假在线状态。
3. `node projects/nfc-business-card/scripts/eda-exec-wait.mjs <code.js> 90000`：等待式执行器会轮询到有真实窗口再发请求；如果它报 `no live window`，就是扩展侧没在连，不用再试调用姿势。
4. 扩展侧恢复：EasyEDA 里 **高级 → 扩展管理器 → Run API Gateway 先禁用再启用**（只重启应用有时不够），并确认"允许外部交互"仍是勾选状态；同时**只保留一个编辑器窗口/标签页**，两个图页标签会各注册一次连接。
5. 探针命令：`node scripts/eda-exec-wait.mjs /tmp/eda-ping.js 60000`，其中 ping 脚本内容为 `return { ok: true };`。拿到 `"ok":true` 才算通道可用。

### 客户端与启动命令

封装只读核对可使用 `sys_FileManager.getFootprintFileByFootprintUuid(uuid, libraryUuid, 'elibz2')` 导出库文件，解包后读取 `.elibu` 源数据；本机已验证 FPC-05FB-24PH20。系统库 `lib_Footprint.openInEditor()` 返回空值时可用此路径，无需为读焊盘反复新建测试工程。库导出不等于封装已通过制造审核；单位按 PCB 的 mil 换算，接口签名仍以当前 Skill 为准。

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

### 电子名片原理图草案（2026-09-20）

源文件：[`eda/NFC-Business-Card.eprj2`](../../../eda/NFC-Business-Card.eprj2)。在客户端“所有工程”的仓库 `eda` 目录刷新后打开，或使用“文件 → 打开工程”选择该文件。三页电路与检查范围见 [原理图草案记录](../hardware/schematic-draft.md)；27 个电路元件及 32 个命名网络已保存，另有一个排除 BOM/PCB 的 FPC 座候选。

实际验证了保存并重开工程、网表导出前后对照、SQLite `quick_check`、`.epro2` 导出包完整性，以及 PDF 三页预览。原理图 DRC 有 15 警告，未通过；这不等于 PCB/PCBA 验证。网表检查命令：

```sh
python3 projects/nfc-business-card/scripts/check-schematic-netlist.py projects/nfc-business-card/hardware/schematic-draft.enet
```

本机 3.2.203 与当前 API 文档还有以下差异；仅记录验证过的绕行方式，不修改上游 Skill：

- `dmt_Project.createProject()` 传离线目录后返回空值，未创建文件。改用一次客户端“文件 → 新建 → 工程”，明确保存到根 `eda/`，之后通过 API 画图。
- `sch_ManufactureData.getPngFile()` 不存在。实际使用 `getExportDocumentFile(..., 'PDF', ..., 'Current Schematic')` 导出三页 PDF；用 `dmt_EditorControl.getCurrentRenderedAreaImage()` 检查画布。
- 本机属性对象的 `toAsync()` / `done()` 出现坐标、字号重复转换，不能直接复用为文字格式批量修改。已用文档提供的 `sch_PrimitiveAttribute.modify()` 修正：属性字号传入 `0.08` 后，原始文档字号为 `8`；与 `sch_PrimitiveText.create()` 的字号参数不同。修改后必须保存、关闭图页再重开，避免旧渲染缓存掩盖结果，并以导出 PDF 再检查。
- 带网络名的导线会生成自己的 Name 属性；删除网络端口时可能清空该名称。当前工程用导线名称连接，改显示位置后重新导出网表核对。网络名在导出时会转大写，例如 `nRESET` 导出为 `NRESET`。
- 原理图 DRC 的详细数组返回属于较新版本。当前客户端用 `check(true, true, false)`，等检查结束后从 DRC 面板读取结果；不要将刚开始检查时的中间计数当最终结果。

本轮 API 执行记录、原始资料片段、PDF 与 `.epro2` 导出留在被忽略的 `artifacts/eda-draft/`。人工或 AI 继续编辑前先核对当前工程/图页、保存状态；不要原样重跑放置脚本造成重复元件。

### PCB 试布线验证（2026-09-20）

当前图页为 `Board1 → E6-302030 试布线 - 未完成`；[结果与限制](../hardware/pcb-routing.md)。本轮验证 `pcb_Document.autoRouting({RoutingNets: [...], existingPrimitiveMode: 'keep'})`：属性名是 `RoutingNets`，不是类文档例子中的 `nets`。返回成功数量不能代替 DRC，存在报告成功但仍有断点的情况。

铜线可用 `pcb_PrimitiveLine.create()`，铺铜边界用 `pcb_PrimitivePour.create()`，修改走线后逐个 `rebuildCopperRegion()` 再复查。`pcb_Drc.check(true, true, true)` 实际返回按类别分组的详细数组，可归档计数及未连接网络。工程规则未放宽；第一轮 DRC 53 条，第二轮 41 条，保存重开及 108 项网表检查通过。执行脚本、在线备份和完整快照分别见 `artifacts/eda-routing/` 与 `artifacts/eda-routing-refine/`。

第二轮接口经验：相邻线段可能在创建后合并，源数据中的最终 ID 不一定与每次 `create()` 返回 ID 一一对应。撤销某次试布线时应对比前后源数据，核对待删除对象及删除后的实际状态，不能只依赖返回成功或最初收集的 ID。本轮逐项删除并复核差异后完成清理。DRC 接口曾超时，保存并重开目标 PCB 图页后恢复；超时后先读取工程状态，不重复提交整批修改。

候选线路可先在离线脚本中计算，但网格精度、板边和圆形过孔的近似会影响间距；最终必须重新铺铜、运行原生 DRC，并保存重开核对。当前保留原有规则，新过孔采用 20.5 mil 外径、12.1 mil 孔径（约 0.521/0.307 mm），避免在规则阈值处受数值取整影响。当前连通性仍未通过，不能导出后直接下单。

### PCB 预布局验证（2026-09-20）

同一源工程的 `Board1 → E6-302030 预布局 - 未布线` 已保存，具体器件、板框、预览及 DRC 结果见 [PCB 预布局记录](../hardware/pcb-prelayout.md)。没有启动 FreeCAD，本轮只改 EDA；三维模型不会自动同步。

已验证的步骤：

1. 核对工程、PCB UUID 和现有内容，使用 SQLite 在线备份保存一致的改动前副本，不直接复制正在写入的数据库。
2. `pcb_Document.importChanges(schematicUuid)` 在本机只打开导入确认框；返回 `true` 不代表元件已落到 PCB。通过一次 UI 确认应用后，重新枚举得到 27 个元件。
3. PCB 元件 `toAsync()`、坐标/角度 setter、`await done()` 本轮可用，单位为 mil。板框与参考区用 `pcb_MathPolygon.createPolygon()` 和 `pcb_PrimitivePolyline.create()`；图形中使用有文档依据的命名枚举映射，因为本机运行上下文没有全局 `EPCB_LayerId`。
4. 本机 `pcb_PrimitiveLine.create()` 按当前文档调用仍报参数错误，改用有文档支持的折线接口；`sys_FileManager.setDocumentSource()` 写回 V3 文本返回 `false` / 格式错误，未用它修改板厚。板厚通过 **工具 → 图层管理器 → 物理堆叠 → 板厚 0.8 mm → 自动分配基板厚度 → 确认** 设置，之后从源数据读回约 0.800024 mm。
5. `sys_FileManager.getDocumentFootprintSources()` 本机返回空数组；改为依次只读打开工程内的封装、取得 `getDocumentSource()` 后关闭，并恢复 PCB。出现未关联器件的提示时取消，不修改库器件关联。
6. PCB 保存、关闭图页、重开；再导出网表、核对位置/网络和原生 DRC。显示设置会在重开时恢复部分默认值，270° 会规范化为 −90°，比较时须区分显示变化与实际设计变化。

本轮原生 DRC 为 122 条，未通过；网表 108 项关键引脚检查通过，145 个焊盘的网络与原理图一致。API 调用、原始封装、数据库备份、验证脚本和导出包保存在被忽略的 `artifacts/eda-prelayout/`。后续编辑应核对当前源工程并局部修改，不能原样重跑创建图形脚本，以免产生重复板框或标注。

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

## FreeCAD 脚本工作流

2026-09-20 已验证命令行生成/检查与脚本驱动的 GUI 预览。入口是 [freecad-study.py](../scripts/freecad-study.py)，内部工作脚本为 [freecad-worker.py](../scripts/freecad-worker.py)，建模仍复用 [pcba-layout.FCMacro](../enclosure/pcba-layout.FCMacro)。没有新增 MCP、插件或常驻服务。

### 日常命令

从仓库根目录执行。省略 `--output-dir` 时，每次自动创建独立的 `projects/nfc-business-card/artifacts/freecad/<动作>-<随机后缀>/`，命令会打印绝对路径：

```sh
# Build, save, reopen, check geometry, and export envelope STEP without a GUI.
python3 projects/nfc-business-card/scripts/freecad-study.py generate

# Check the saved model through an isolated copy without changing the source.
python3 projects/nfc-business-card/scripts/freecad-study.py check projects/nfc-business-card/enclosure/pcba-layout.FCStd

# Launch one temporary GUI process, apply appearance, capture two views, then exit.
python3 projects/nfc-business-card/scripts/freecad-study.py preview projects/nfc-business-card/enclosure/pcba-layout.FCStd
```

要检查/预览刚生成的新模型，将后两条命令的输入替换为生成目录中的 `pcba-layout.FCStd`。需要明确输出位置时追加 `--output-dir <新目录>`；已存在的目录会被拒绝，即使其中没有同名模型。**`generate` 和 `check` 不打开窗口；只有显式运行 `preview` 才临时打开 FreeCAD。** 平时集中完成建模与检查，再做一次预览，避免反复弹窗。

| 命令 | 输出 |
| --- | --- |
| `generate` | `.FCStd`、布局 SVG、生成报告、重新打开后的几何报告、`pcba-envelopes.step` |
| `check` | 磁盘输入副本 `input.FCStd`、重新计算后的几何报告 |
| `preview` | 输入副本、几何报告、`isometric.png`、`top.png`、保留显示属性的 `pcba-layout-view.FCStd` |
| 所有命令 | `job.json`、`source-audit.json`、`result.json`、`freecad.log` |

`pcba-envelopes.step` 只有简化物理器件和 PCB 包络，不含参考面/预留区；不是可制造 PCB、完整器件 STEP 或可打印外壳。预览生成的 `.FCStd` 仍可编辑。平时直接打开现有 [PCBA 模型](../enclosure/pcba-layout.FCStd)：

```sh
open -a FreeCAD projects/nfc-business-card/enclosure/pcba-layout.FCStd
```

### 环境与实现边界

- 本机验证版本：Homebrew FreeCAD **1.1.3 arm64**，内置 Python **3.11.14**；外层 `python3` 只负责调度，不直接导入 FreeCAD。脚本当前针对 macOS 应用路径，不宣称跨平台。
- 建模/几何检查调用 `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`。子进程的 `PYTHONHOME` 设为 `/Applications/FreeCAD.app/Contents/Resources`，`PYTHONPATH` 设为其 `lib/`；不改 shell 配置或全局 Python 环境。
- GUI 预览调用同目录的 `freecad`，通过临时 `.FCMacro` 入口执行 `FreeCADGui` API；无需菜单点击。独立 `--user-cfg` / `--system-cfg` 路径位于该次输出目录，不复用用户的配置文件。
- 预览需要 macOS 图形登录会话和可用 OpenGL，**不是纯无界面渲染**；会短暂出现窗口。脚本只退出自己的临时进程，不关闭用户已开的 FreeCAD。无图形环境时只使用 `generate` / `check`，SVG 可独立查看。
- 无 GUI 生成时，将颜色作为对象 `StudyColor` 属性持久化。预览显式恢复可见性、颜色、预留区透明度，隐藏前盖参考面，并设置外形线框。
- GUI 启动可能稍后恢复旧视角，视角切换也有动画：预览在事件循环内分阶段设视角和导图。检查 PNG 非空白及俯视角已到位，之后仍需实际看图。首次验证发现的空白图与错误视角已通过这些步骤修复。
- 本机 GUI 日志仍出现未安装 3Dconnexion 库、启动阶段 `Gui` 名称及退出时 Qt 线程存储提示。本轮没有安装驱动或更改应用；最终几何、视图保存和导出图均另行核验，不把退出码或日志无报错作为唯一成功标准。
- 外层脚本同时检查子进程结果与 `result.json`。FreeCAD 可能打印 Python 异常却返回 0，因此必须读取完成标记；异常、几何失败、缺失/空白预览均返回非零。单次子进程最多运行 90 秒，超时只终止该次进程。

### 六色屏与 302030 变体

同一生成宏新增 `e6-302030` 变体，默认不带参数仍生成旧版 `baseline`。`--variant` 仅用于生成；检查/预览读取输入模型自身的参数。

```sh
# Generate the six-color screen and 302030 battery study without opening a window.
python3 projects/nfc-business-card/scripts/freecad-study.py generate --variant e6-302030

# Inspect the archived sample layout without changing it.
python3 projects/nfc-business-card/scripts/freecad-study.py check projects/nfc-business-card/enclosure/pcba-e6-302030.FCStd

# Optional GUI preview; one temporary process, then exit.
python3 projects/nfc-business-card/scripts/freecad-study.py preview projects/nfc-business-card/enclosure/pcba-e6-302030.FCStd
```

生成目录内仍使用 `pcba-layout.FCStd` 等通用文件名。本次单独归档为 `enclosure/pcba-e6-302030.*`，没有替换旧版 `pcba-layout.*`。生成前的源文件审计根据变体选择对应的已保存模型，始终写新目录。

2026-09-20 实际验证记录位于 `artifacts/freecad-e6-302030/`：`generate-v1` 保存重开与几何检查通过；`baseline-regression` 确认旧布局坐标、尺寸、证据和叠层保持一致；`check-published` 检查已归档新模型通过。FPC 通道和过厚电池的两个错误副本分别产生预留区冲突、内腔越界，命令正确返回非零。导出 STEP 重读为 11 个有效实体，体积差小于 `1e-5 mm³`。

新增预留区通过模型属性 `CheckPhysicalClearance`、`AllowedComponents` 和 `KeepOutsideNfc` 控制检查，保存后重开仍有效。检查验证简化通道是否被其他实体占用，不验证真实柔性排线、电路布局或天线设计。

视觉检查采用完整 SVG 渲染和 `preview-v1/isometric.png`。该次 `top.png` 上部异常，不计为视觉通过；Quick Look 缩略图还会裁切 SVG 右侧，最终 PNG 使用 FreeCAD 自带的 Qt SVG 在 `QT_QPA_PLATFORM=offscreen` 下完整渲染。图像可见不等于比例正确，仍需对照模型尺寸检查。只运行了一次临时 FreeCAD GUI 预览，原有用户进程保留。

### 电池靠右、USB 下长边变体

`e6-bottom-usb` 生成新的独立方案，归档为 `enclosure/pcba-e6-bottom-usb.*`，没有覆盖旧模型。EDA 对应独立文件 `eda/NFC-Business-Card-Bottom-USB.eprj2`；原工程的试布线保留。

```sh
python3 projects/nfc-business-card/scripts/freecad-study.py generate --variant e6-bottom-usb
python3 projects/nfc-business-card/scripts/freecad-study.py check projects/nfc-business-card/enclosure/pcba-e6-bottom-usb.FCStd
python3 projects/nfc-business-card/scripts/freecad-study.py preview projects/nfc-business-card/enclosure/pcba-e6-bottom-usb.FCStd
```

本轮只执行一次 GUI 预览，其余生成和检查均调用 `freecadcmd`。`artifacts/bottom-usb/` 保存生成、检查、预览与 EDA API 记录；27 个简化形体的几何检查通过，完整 SVG、等轴测、顶视图和 EDA 画布分别目视检查。归档模型保留 GUI 显示属性，重新 `check` 通过。结构与 PCB 的具体验证边界见[排布记录](../hardware/pcb-bottom-usb.md)。

### 银行卡以内的紧凑变体

`e6-84x52` 为推荐的包络研究，归档至 `enclosure/pcba-e6-84x52.*`；`e6-83x51` 为更小的比较变体，生成结果留在临时目录。两者继续复用同一宏与工作流，尺寸包括假设壳壁，真实器件不缩放；当时未同步 EDA，后续细化版见下节。

```sh
python3 projects/nfc-business-card/scripts/freecad-study.py generate --variant e6-84x52
python3 projects/nfc-business-card/scripts/freecad-study.py generate --variant e6-83x51
python3 projects/nfc-business-card/scripts/freecad-study.py check projects/nfc-business-card/enclosure/pcba-e6-84x52.FCStd
# Optional: one temporary GUI process, then exit.
python3 projects/nfc-business-card/scripts/freecad-study.py preview projects/nfc-business-card/enclosure/pcba-e6-84x52.FCStd
```

本次运行记录在 `artifacts/compact-layout/`：两变体的 `generate` 和归档模型 `check` 均通过；旧 `e6-bottom-usb` 重新生成的报告与旧报告完全相同。只为 84 × 52 运行一次 GUI 预览，检查等轴测与顶视图后保存带颜色的模型；另用 Qt SVG 离屏渲染两方案平面图及比较图并目视检查。

`review.py` 使用此前 `artifacts/bottom-usb/pad-geometry.json` 的封装快照进行离线平移检查，不能当作 EDA DRC；本机可运行 `python3 projects/nfc-business-card/artifacts/compact-layout/review.py` 复核。该脚本和输入快照是本地检查产物，不随 Git 分发；建议坐标与检查结论归档在 `enclosure/compact-layout-review.json`，后续必须在新 EDA 工程重新验证。完整说明见[紧凑排布记录](../enclosure/compact-layout.md)。

### 84 × 52 实际封装细化

2026-09-21 新增 `e6-84x52-detail`，仍复用同一宏与命令。归档模型为 `enclosure/pcba-e6-84x52-detail.FCStd`，独立 EDA 为 `eda/NFC-Business-Card-84x52.eprj2`。相对旧比较版，使用 FH12A 候选本体上界并靠近屏幕，加入 U4/U5 包络及 8 个平面焊盘；未验证的插接、电路和制造项见[排布记录](../hardware/pcb-84x52.md)。

```sh
python3 projects/nfc-business-card/scripts/freecad-study.py generate --variant e6-84x52-detail
python3 projects/nfc-business-card/scripts/freecad-study.py check projects/nfc-business-card/enclosure/pcba-e6-84x52-detail.FCStd
# Optional: one temporary GUI process, then exit.
python3 projects/nfc-business-card/scripts/freecad-study.py preview projects/nfc-business-card/enclosure/pcba-e6-84x52-detail.FCStd
```

本轮 `generate` / 归档 `check` 均通过，36 个形体无已建模碰撞；一次 GUI 预览的等轴测与顶视、Qt 离屏 SVG 渲染和 EDA 画布分别查看。旧 `e6-84x52` 重生成的报告完全相同，既有 7 个 CAD/EDA 文件哈希不变。记录位于 `artifacts/compact-detail/`。

EDA 经 API 保存重开后检查 30 个元件、188 个焊盘；本机快照核对命令为 `python3 projects/nfc-business-card/artifacts/compact-detail/check-layout.py`，该脚本及输入是本地临时产物。持久检查结果见 `hardware/pcb-84x52.json`；134 条 DRC 尚未通过，不能据此生产。旧原理图尚未同步 J2/U4/U5 候选，下一轮先修改原理图再同步板图。

### 保护手工修改

1. 运行前记录既有模型的 SHA-256、Git 状态和已运行的 FreeCAD 进程。Git 修改状态不能区分手工编辑与此前生成，均当成应保留的工作。
2. **其他进程中的未保存编辑无法由 `freecadcmd` 直接读取。** 若要检查那些修改，先在原窗口另存到新路径，再把该文件传给 `check` / `preview`；未保存状态不算作已经验证。
3. 生成始终写入新目录；检查/预览先复制磁盘文件。结束后比较源文件 SHA-256；若用户同时保存导致其变化，命令报告失败，旧副本不能代表最新状态。
4. 两份 `.FCMacro` 都拒绝覆盖已有模型/报告。GUI 直接运行还检查当前进程是否已打开同名文档；这不等于跨进程锁。历史 `layout-study.*` 保留，不由新工作流重新生成。
5. 若要把实验结果采用为正式模型，先核对原窗口未保存状态，将手工版本另存，然后明确选择新文件；脚本不自动替换 `enclosure/`。手工改 `.FCStd` 不会回写宏，宏仍是默认研究布局的生成源。

需要调整默认排布时修改宏中的尺寸与坐标，再运行 `generate` 比较新目录结果。`StudyParameters` 只驱动已设置表达式的部分尺寸；PCB 轮廓、多数器件坐标和叠层分配并非自动联动，不应只改一个参数就宣称整体重新布局完成。

### 本机实际验证

本轮固定输出根为 `projects/nfc-business-card/artifacts/freecad-workflow-validation/`，以下目录已使用，重跑应换目录名或省略 `--output-dir`：

```sh
python3 projects/nfc-business-card/scripts/freecad-study.py generate --output-dir projects/nfc-business-card/artifacts/freecad-workflow-validation/generate
python3 projects/nfc-business-card/scripts/freecad-study.py check projects/nfc-business-card/enclosure/pcba-layout.FCStd --output-dir projects/nfc-business-card/artifacts/freecad-workflow-validation/check-existing
python3 projects/nfc-business-card/scripts/freecad-study.py preview projects/nfc-business-card/artifacts/freecad-workflow-validation/generate/pcba-layout.FCStd --output-dir projects/nfc-business-card/artifacts/freecad-workflow-validation/preview-ready
```

- **几何检查：通过。** 保存后重开，25 个几何实体有效；物理器件无碰撞、无超出假设内腔（USB 侧壁开口例外）、无侵入 NFC 平面预留区；PCB 为单一连通实体。几何检查读取模型本身，不沿用生成报告宣称成功。
- **STEP 导出：通过包络检查。** 用 `freecadcmd` 重新读取导出的 STEP，11 个物理实体有效，数量与体积和源模型一致；不代表制造文件验证。
- **视觉检查：通过本轮空间模型检查。** 已查看导出的等轴测和正俯视图，器件颜色、半透明预留区、隐藏前壁和外形线框正常，模型完整可见。几何通过不等于视觉通过，PNG 非空白检查也不能替代目视检查。
- **保护与失败路径：通过。** 复用输出目录和直接宏覆盖均被拒绝，原文件哈希不变；将主控移动到 NFC 区的隔离副本被 `check` 检出并返回失败。原有 FreeCAD 窗口与手工模型未被替换。
- **未覆盖：** 焊盘、布线、FPC 折弯、键帽、完整包体/线材、RF、ERC/DRC、制造与实物。检查器只适用于当前 PCBA 研究对象及 0.8 mm 侧壁假设，不是任意 CAD 文件的通用验证器。

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

## E6 电路工程的 API 验证记录（2026-09-21）

最新工程：[NFC-Business-Card-84x52-E6.eprj2](../../../eda/NFC-Business-Card-84x52-E6.eprj2)，[验证记录](../hardware/pcb-e6-84x52.md)。本机 3.2.203 + Run API Gateway 1.0.6 可创建/连接元件和试布线，但下列返回值不能直接作为验收依据：

- `pcb_Document.importChanges()` 返回成功可能只是打开“确认导入信息”，仍需核对差异并应用。独立检查全部元件引脚与封装焊盘网络；不要只看返回布尔值。
- 本次遇到原理图文字删除/部分属性更新在内存生效、保存后冷重开和 PDF 却仍为旧值；`save() === true` 不足以证明该类修改持久化。本页后续排查已通过原生删除解决旧文字恢复；此前 PDF 未重新验收，不能作为制造文档。
- 长时间自动布线可能超过桥接的 30 秒请求期限；超时不代表布线停止。检查客户端状态后再继续操作，最终以保存重开后的铜线、过孔、DRC 为准。
- 同一工程出现重复窗口时，显式指定已核对路径的 `windowId`；`openProject()` 后窗口标题/`prjPath` 可能仍指向旧工程，需用磁盘文件重新打开核验。避免并行修改同一文档。
- 网络赋值一致、几何检查、原生 DRC、视觉检查与实测是不同层面的结论，本版分别记录，不以任一项替代其余项。


### E6 保存与关联排查（2026-09-21）

本轮从磁盘重新打开唯一工程窗口后，原理图导出为 56 个元件，234 项引脚检查通过。此前仍响应 API、但 macOS 无可操作窗口的会话曾导出 30 个元件，并出现原理图/PCB 焦点不一致；重开后未复现，不能将该会话结果判为设计数据丢失。连接成功与 `getCurrentDocumentInfo()` 本身不足以证明导出上下文正常。

独立比较原理图与 PCB 的制造网表发现 **27 处 Unique ID 不同**：原理图 J2、U4 和屏幕外围使用 `gge57`–`gge83`，PCB 对应元件仍使用 `gge28`–`gge54`；位号、封装与引脚网络一致。这是实际的关联差异；已用 `IPCB_PrimitiveComponent.toAsync()`、`setState_UniqueId()`、`await done()` 将 PCB 对齐原理图，保存重开后 112 项关联/封装检查通过，原生 Netlist Error 消失。不能仅凭引脚检查通过就忽略关联差异。

`check-e6-netlist.py` 新增 `--pcb-netlist <PCB 导出的 .enet>`，比较元件集合、Unique ID、Footprint 和引脚网络。对修正前导出按预期失败，检出上述 27 项；修正后导出通过。正式 PCB 网表保存为 `hardware/e6-pcb.enet`；原有 `--pcb` 平面快照检查不包括关联 ID。API 原始记录、修改前 SQLite 在线备份及待执行的关联修正映射位于被忽略的 `artifacts/eda-persistence-review/`。

外部一手报告：[文字删除恢复 #36](https://github.com/easyeda/pro-api-sdk/issues/36)描述相同症状，并报告“API 选中 → 编辑器原生 Delete → 保存重开”有效；本机已复现可行路径：API 精确选中旧文字，再用原生“编辑 → 删除 → 已选”，保存并重开图页确认。第 3 页删除 13 条旧说明，第 1/2 页替换 4 条，均未恢复。单独发送 Delete 快捷键未生效，必须确认画布实际焦点或使用菜单。[网表比较 #39](https://github.com/easyeda/pro-api-sdk/issues/39)及其后续评论区分了 UUID 比较异常和原生导入更新状态；它不能代替本项目的网表审计，也不证明本项目告警是假阳性。

本轮结果：56 个元件位置和旋转保持不变，632 段铜线、103 个过孔、两块地铜数量不变；PCB DRC 从 74 降到 73（49 条连接、24 条 USB 槽边距），SQLite `quick_check` 为 `ok`。本轮未增加布线。接下来处理实际连接、电源与天线；后续同步需继续检查关联 ID，避免整批删除/重建器件造成位置和走线变化。

Skill 文档列出 `sch_ManufactureData.getSvgFile()`，但本机 3.2.203 运行时该方法不存在；本轮改用 `getCurrentRenderedAreaImage()` 检查第 3 页画布，不将视口截图当作完整制造图纸。


### E6 局部布线与过孔检查（2026-09-21）

本轮通过 `pcb_PrimitiveLine` / `pcb_PrimitiveVia` API 局部重布 BUSY 并接通三条屏幕短网络，记录于[布线说明](../hardware/pcb-e6-84x52.md#本轮局部布线2026-09-21)。先保留 SQLite 在线备份和原始图元，再离线检查候选路径；只在当前 PCB UUID 核对一致后写入。最终为 648 段线、107 个过孔，DRC 67 条（43 条连接、24 条槽边距）。

新建 4 个普通通孔后，DRC 曾额外报告 8 条接触该过孔的连接错误。对这 4 个过孔执行 `toAsync()`、重新赋予原网络 `setState_Net(...)`、`setState_DesignRuleBlindViaName(null)` 并 `await done()` 后，额外错误消失；保存重开后仍成立。两项设置同时执行，不能断定是哪项生效，也不能认定根因是盲孔类型；读取属性时，新旧过孔均为普通通孔且盲孔规则名为空。对原有过孔做同样刷新未减少剩余错误，不得据此忽略真实断点。官方 [create 接口](https://prodocs.lceda.cn/cn/api/reference/pro-api.pcb_primitivevia.create.html)说明空盲孔规则表示非盲埋孔；本地现象仅限本机版本。

每轮修改后重建铺铜，保存并关闭/重开 PCB，再导出网表、读取原生 DRC、核对元件位置与关联 ID。网表检查通过仅说明元件与引脚赋网一致；铜线是否连通仍以原生 DRC 为独立检查，电气性能需另行评审及实测。


### E6 功能块副本与恢复检查（2026-09-21）

当前 [E6-Blocks](../hardware/pcb-e6-84x52-blocks.md) 由 `getProjectFileByProjectUuid(..., 'epro2')` 导出，再以 `importProjectByProjectFile(..., {operation: 'New Project', ...})` 导入为独立工程。`openProject()` 切换后本机标题和 `prjPath` 仍指向旧文件；在副本修改前先关闭应用，从新 `.eprj2` 路径重新打开，核对窗口路径、工程 UUID 和 PCB 上下文。不要只根据 API 工程名判断正在编辑哪个磁盘文件。

本轮曾出现 DRC 请求超时而源数据读取、修改和保存仍正常的情况。超时不证明修改未执行，也不表示 DRC 通过：先读回元件坐标，避免重复执行删除/创建；保存后重新启动该工程，再复验。重启后 DRC 恢复并完成保存重开验证；未确定超时根因。原 E6 文件 SHA-256 保持不变，副本 `quick_check=ok`，234 项原理图引脚、234 项 PCB 焊盘和 112 项关联检查通过。
