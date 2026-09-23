---
description: 本机工具链、常驻服务与目录约定：新接手的人或 AI 从零跑起来 + 五分钟自检
last_updated: 2026-09-23
---

# 环境与常驻服务

这份文档回答三个问题：**这台机器上都有什么、怎么从零重建、怎么确认它现在是好的**。项目本身的状态与下一步在各项目 README 与 [NFC 名片进度](../projects/nfc-business-card/docs/progress.md)里。

## 工具链

| 组件 | 位置 / 版本 | 用途 |
| --- | --- | --- |
| Node.js | `/Users/linguanguo/.nvm/versions/node/v24.19.0/bin/node`（nvm） | 桥接服务、EDA 脚本执行器 |
| EasyEDA（嘉立创EDA）专业版 | 3.2.203 + **Run API Gateway** 扩展（启用步骤与排障见[软件说明](../projects/nfc-business-card/docs/software.md#客户端与启动命令)） | 原理图/PCB 的唯一编辑环境 |
| FreeCAD | `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`（1.1.3） | 外壳建模、几何/干涉/网格检查、STEP/STL 导出 |
| Python | `python3`（3.12，pyenv）+ [scripts/requirements.txt](../projects/nfc-business-card/scripts/requirements.txt)（`openpyxl`、`Pillow`、`numpy`） | 快照分析、制造包核对、审查图渲染 |

EDA 扩展与桥接之间是 WebSocket；桥接只监听 `127.0.0.1:49620`，不对外暴露。

## 常驻服务：EDA 桥接

| 项 | 值 |
| --- | --- |
| launchd 作业 | `com.hardwarelab.easyeda-bridge`（`~/Library/LaunchAgents/com.hardwarelab.easyeda-bridge.plist`，按需模式：`RunAtLoad=false`、无 `KeepAlive`；`--login-start` 才会改成自启+保活） |
| 服务本体 | [tools/easyeda-bridge/bridge-server.mjs](../tools/easyeda-bridge/bridge-server.mjs)（仓库自有补丁副本，不是上游子模块） |
| 日志 | [logs/easyeda-bridge.out](../logs/) / `.err`（被 Git 忽略） |
| 健康检查 | `bash tools/easyeda-bridge/bridge-status.sh`（一条命令给出进程、运行时长、`/health`、在线窗口、崩溃与重连计数、日志大小和结论行） |

**桥接默认按需启动**：安装只登记作业，不开机自启；做 EDA 前手动开，做完可以关。

```sh
git submodule update --init --recursive          # upstreams/ 里的 API 文档子模块
python3 -m pip install -r projects/nfc-business-card/scripts/requirements.txt   # 脚本用到的三个包
tools/easyeda-bridge/install-agent.sh            # 渲染 plist → bootout/bootstrap（仅登记，不启动）
tools/easyeda-bridge/bridge-start.sh             # 需要时启动，并打印自检
tools/easyeda-bridge/bridge-stop.sh              # 用完停止（作业保留）
bash tools/easyeda-bridge/bridge-status.sh       # 随时查状态；期望 verdict: bridge up and EDA connected
tools/easyeda-bridge/install-agent.sh --login-start   # 只有需要开机自启时才用这个
```

`install-agent.sh` 是幂等的：重复执行不会产生多余备份（`.bak-*` 只保留最近 2 份），`node_modules` 软链缺失时会自动重建，日志超过 5 MB 会轮转一份 `.1`。**不要**手动 `nohup node bridge-server.mjs`，会和 LaunchAgent 抢 49620。

常用维护动作：

```sh
tools/easyeda-bridge/install-agent.sh --quiet   # 写入 EDA_BRIDGE_QUIET=1，日志只留关键行
: > logs/easyeda-bridge.out                     # 手动截断日志（安装脚本也会在超过 5 MB 时轮转）
```

## 目录与"什么进 Git"

| 路径 | 是否入库 | 说明 |
| --- | --- | --- |
| `eda/` | **是** | 嘉立创 EDA 原始 `.eprj2` 工程与阶段备份；客户端只登记这一个目录 |
| `upstreams/`、`.agents/skills/` | **是** | submodule 固定上游提交 + 相对符号链接供技能发现 |
| `projects/<项目>/` | **是** | 项目文档、硬件资料、脚本、可编辑 CAD（含小图册） |
| `**/artifacts/**` | 否（唯一例外：[artifacts/README.md](../projects/nfc-business-card/artifacts/README.md)） | 本机产物与历史阶段输出；索引说明布局与重建方式 |
| `downloads/`、`logs/`、`*.log` | 否 | 原厂资料缓存（有 `docs/download_manifest.json` 清单）与运行日志 |

长期需要引用的证据不放 `artifacts/`：EDA 重开/DRC 记录在 `projects/nfc-business-card/hardware/records/`，外壳模型与渲染图在 `enclosure/` 与 `enclosure/renders/`。

## 五分钟自检

```sh
cd /Users/linguanguo/dev/hardware-lab
bash tools/easyeda-bridge/bridge-status.sh                         # 桥接健康 + 是否有在线 EDA 窗口
python3 projects/nfc-business-card/scripts/check-e14-gates.py      # 工程 sha256、sqlite quick_check、门槛清单
python3 projects/nfc-business-card/scripts/check-e16-copper-connectivity.py   # 每个网络单一铜簇、无死铜端
python3 projects/nfc-business-card/scripts/check-e16-manufacture.py           # 制造包与快照逐点一致
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
  projects/nfc-business-card/scripts/check-e16-print-meshes.py                # 三个 V7 STL 是否可打印
```

期望：桥接 `verdict` 为 `bridge up and EDA connected`（**EDA 客户端没开时会是 `bridge up but no EDA window`，这不算故障**）、四个检查都 `ok`。

## 常见故障与判据

| 现象 | 原因与处理 |
| --- | --- |
| 状态行 `bridge down`（按需模式） | 正常：服务没启动。用 `tools/easyeda-bridge/bridge-start.sh` 开 |
| `bridge up but no EDA window` | EDA 客户端没开、扩展没启用，或编辑器标签页被关掉。打开客户端并确认扩展启用，扩展会在十几秒内重连 |
| 客户端刚启动、`/health` 已报 `edaConnected: true`，但**所有图元 API 返回 null**（连 `pcb_PrimitiveLine.getAll()` 都报 `Cannot read properties of null (reading 'map')`） | 冷启动停在起始页、**没有打开任何工程**。`dmt_SelectControl.getCurrentDocumentInfo()` 会显示 `documentType: -1`、`tabId: tab_page1`。先跑 `node projects/nfc-business-card/scripts/eda-exec-wait.mjs projects/nfc-business-card/scripts/eda-open-e16.js 180000`：它用 `dmt_Project.openProject()` 打开 E16 所在工程，并用**内容指纹**（56 元件 / 244 焊盘 / 798 线 / 168 过孔）确认身份，不依赖 API 报出的工程名 |
| 重操作（`pcb_Drc.check`、制造包导出）报 30 s 超时 | 走的是客户端界面线程：Mac 锁屏或窗口里有模态框时会超时。解锁并关掉对话框/重启客户端即可；轻量 API 不受影响 |
| **保存/导出时客户端界面卡住**，底部或窗口里留一个不动的进度条（常见 `1%`） | 反复出现（用户 2026-09-23 反馈"经常卡在触发保存，点一下就好"）。走界面线程的重操作会卡住等待，**轻量 API 仍然正常**，所以桥接会报 `AbortError` / `gave up waiting for a responsive EDA window` 并重试多次——**这是界面卡住，不是桥接或数据损坏**。点一下窗口让它继续即可；进度条不消失本身是外观问题。判据：`/health` 仍在、`dmt_SelectControl.getCurrentDocumentInfo()` 有响应、工程文件 SHA-256 与门槛记录一致，说明**改动已落盘**，可以放心重启客户端 |
| `/eda-windows` 里有“已连接”但实际只有 1 个窗口 | 扩展每十几秒重连一次并注册新 windowId，桥接会保留僵尸注册。执行器 [eda-exec-wait.mjs](../projects/nfc-business-card/scripts/eda-exec-wait.mjs) 每次先选在线窗口并重试 |
| `~/Downloads/.cn.lceda.pro.*` 堆积 | EDA 导出的临时落盘口（隐藏随机名）。用 `projects/nfc-business-card/scripts/collect-e16-manufacture.py` 归纳到 `artifacts/manufacture/`，其余可清 |
| 桥接进程反复退出 | 先看 `logs/easyeda-bridge.err` 是否有崩溃栈；`crashes (ERR_HTTP_HEADERS_SENT)` 计数长期为 0 才是正常 |
| 所有 `lib_*.create` / `copy` / `modify` / `openInEditor` 失败（`Error: null` / `[object Object]`），但 PCB 的读写全部正常 | **本机没有个人库**。判据：`lib_LibrariesList.getAllLibrariesList()` 返回 `[]`、`getPersonalLibraryUuid()` 返回 `null`/`undefined`，且 `~/Documents/LCEDA-Pro/libraries/` 是空目录。客户端处于 `HALF_OFFLINE` 模式（官方推荐模式，无需登录），个人库本地可写但**必须先在 GUI 建一个**：起始页「新建库」按钮，或打开文档后顶部菜单 `文件 > 新建 > 库`。建完再重试 API 写入 |

## 相关文档

- 项目状态与 TODO：[NFC 名片进度](../projects/nfc-business-card/docs/progress.md)
- EDA/FreeCAD 脚本工作流：[软件说明](../projects/nfc-business-card/docs/software.md)
- 桥接本体与安装细节：[tools/easyeda-bridge/README.md](../tools/easyeda-bridge/README.md)
- artifacts 布局与重建方式：[artifacts/README.md](../projects/nfc-business-card/artifacts/README.md)
