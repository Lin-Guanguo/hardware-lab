# KiCad 工具入口

## 当前确定方案

2026-09-29，NFC 名片第四版已获用户明确授权使用 KiCad，完成[原生迁移与关键区试布](../../projects/nfc-business-card/hardware/kicad-v4-phase1.md)。嘉立创 D 保留作独立诊断对照；其它项目不自动迁移。设计方法见 [pcb-methodology](../../.agents/skills/pcb-methodology/SKILL.md)，KiCad 执行入口为 [kicad-workflow](../../.agents/skills/kicad-workflow/SKILL.md)。

2026-09-28 已安装 **KiCad 10.0.6**，初始化官方库并启用 IPC；仓库虚拟环境为 Python 3.12.12 / `kicad-python` 0.8.0。独立样例的 API 编辑、保存关闭重开、原生 DRC 和文件导出均已验证，详细范围见下方记录。

本轮沿用现有版本自检，没有重装或升级。真实导入新增限制：`kicad-python 0.8.0` 移动／旋转本次 EasyEDA Pro 导入的含圆弧 `fp_poly` 后曾改变局部图形，必须核对封装库差异；本轮关闭编辑器后恢复不变量并经重开验证。全局标签转换须包含 `Intersheetrefs` 属性，并通过原生保存规范化。不能只用基础样例的成功推断复杂导入完全兼容。

## 安装与恢复

从仓库根目录运行：

```sh
brew install --cask kicad
python3 -m venv .cache/kicad-venv
.cache/kicad-venv/bin/python -m pip install -r tools/kicad/requirements.txt
python3 tools/kicad/health.py
```

`requirements.txt` 固定本次 Python 3.12 / macOS 环境的绑定与传递依赖；Homebrew 软件版本另由 `kicad-cli version` 核实。切换主版本后先跑工具样例，不将“包安装成功”当接口兼容验证。CLI 不在 PATH 时可用 `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`。

Homebrew cask 安装示例到 `/Library/Application Support/kicad/demos` 时可能要求管理员密码，由用户在本机终端输入。安装期间不要手动挂载缓存 DMG；若报 `hdiutil: Resource busy`，先检查并卸载同一镜像的临时挂载，再重试。本次已清理临时挂载，最终通过 Homebrew 安装。

首次打开初始化官方符号/封装库，并确认模型路径。PCB Editor 的偏好设置中启用 IPC API Server 后，API 才能连接。它使用本机 socket，不需要另装 MCP 或常驻 HTTP 服务。

```sh
python3 tools/kicad/health.py --ipc --board /absolute/path/board.kicad_pcb
```

`health.py` 不写设计；它检查版本、绑定、上游提交，并在指定 `--board` 时核对完整路径。默认连接 `/tmp/kicad/api.sock`；多个实例时使用目标实例的 `KICAD_API_SOCKET`，不能编辑连接到的第一块未知板。

GUI 文件选择框等模态窗口打开时，本机出现过 IPC 超时；关闭对话框、等板加载完成，再重跑身份自检。无 PCB Editor 时出现连接拒绝属于预期。API 插件的解释器路径须指向已安装应用或有效虚拟环境，不能留下已卸载 DMG 中的路径。

## 原生检查与导出

下面的 `PROJECT` 和 `OUT` 是要替换的路径，不是本仓库产品工程的默认目标。

```sh
kicad-cli sch erc --format json --exit-code-violations -o OUT/erc.json PROJECT.kicad_sch
kicad-cli pcb drc --format json --schematic-parity --refill-zones --save-board --exit-code-violations -o OUT/drc.json PROJECT.kicad_pcb
kicad-cli pcb export gerbers --output OUT/gerbers/ PROJECT.kicad_pcb
kicad-cli pcb export drill --output OUT/gerbers/ PROJECT.kicad_pcb
kicad-cli pcb export pos --format csv --units mm --output OUT/positions.csv PROJECT.kicad_pcb
```

先保存并关闭正在编辑的工程再运行会保存板子的检查命令，避免 GUI 旧内存覆盖文件。`--schematic-parity` 用于同版原理图齐全的正式工程；纯 PCB 工具样例不使用它。DRC 退出码 `5` 表示发现违规，其他非零码可能是运行错误。报告中的违规、未连接和一致性结果均需检查。

以上是通用命令入口，不是嘉立创最终导出预设。实际导出应按订单指定层、坐标原点、槽孔与格式；例如国内嘉立创的 Gerber 接收要求应单独核对，不能直接照搬国际站默认值。BOM 用 `kicad-cli sch export bom --help` 核对字段导出；CPL 表头和旋转仍须按[国内规范](https://www.jlc.com/portal/server_guide_48022.html)对账。

## 独立 IPC 样例

该样例为两颗测试焊盘、两段跨层线和一个过孔，不是电子名片电路。输出目录必须在本仓库 `.cache/` 内，且 `create` 拒绝覆盖已有目录。

```sh
python3 tools/kicad/smoke-test.py create .cache/kicad-smoke-NEW
open -a /Applications/KiCad/KiCad.app/Contents/Applications/pcbnew.app .cache/kicad-smoke-NEW/ipc-smoke.kicad_pcb
.cache/kicad-venv/bin/python tools/kicad/smoke-test.py edit .cache/kicad-smoke-NEW
```

关闭样例板，再用同一 `open` 命令重开，然后运行：

```sh
.cache/kicad-venv/bin/python tools/kicad/smoke-test.py verify .cache/kicad-smoke-NEW
kicad-cli pcb drc --format json --exit-code-violations -o .cache/kicad-smoke-NEW/drc.json .cache/kicad-smoke-NEW/ipc-smoke.kicad_pcb
```

`edit` 用 IPC 移动 J2 并创建走线/过孔，保存后断言坐标、网络、层和尺寸；`verify` 只读取并重复这些断言。调用者必须真正关闭重开，脚本自身不声称完成此动作。可恢复的事务只覆盖当前编辑操作，不替代候选文件备份。

## 2026-09-28 验证记录

小证据保存在 [validation-2026-09-28.json](validation-2026-09-28.json)，可重建文件留在被忽略的 `.cache/kicad-smoke-2026-09-28/`。

- `brew list --cask --versions kicad`、`health.py --ipc --board ...`：10.0.6，目标板路径匹配。
- `smoke-test.py edit` 后关闭 PCB Editor，重新启动并打开同一文件，再运行 `verify`：J2 从 (15, 5) 移至 (16, 5) mm；两段 0.3 mm 跨层线、一个 0.6/0.3 mm 过孔和 TEST 网络均一致。
- `kicad-cli pcb drc --format json --exit-code-violations`：未连接基线退出 5 / 1 项未连接；API 完成布线后的文件退出 0 / 0 违规 / 0 未连接。前者在最终安装前使用同版本镜像内 CLI 验证。
- 在独立副本旁放置同名 `.kicad_pro` 和 `.kicad_dru`，规定最小线宽 0.5 mm：DRC 退出 5，准确报告两项 `track_width`。此规则用于检测器验证，不是产品设计规则。
- CLI 导出 7 层非 X2 Gerber、Excellon 钻孔与 CSV 坐标表成功；坐标表 J1/J2 的 X 为 5/16 mm，Y 为 -5 mm，体现导出坐标约定，不能未经转换直接当作国内 CPL。
- 固定提交的 `analyze_pcb.py --full` 正确提取板框、器件坐标、两段线和一个过孔；分析及导出前后源文件 SHA-256 一致，子模块无修改。

原生 DRC 采用默认检查配置，忽略项保留在 JSON 中；没有通过新增忽略项消除错误。本次没有原理图，因此未验证 ERC、原理图一致性或 BOM；也未覆盖同网间距/装配冲突专项、真实器件库、整板迁移、制造商上传审核。以上只证明基础工具链可用。

## 现有上游的使用

`upstreams/kicad-happy` 已作为子模块固定版本，无需重新 clone 或全局安装。本仓库通过 `kicad-workflow` 按需执行分析脚本；上游过宽的触发描述和整套采购流程不直接注册为项目 skill。

```sh
python3 upstreams/kicad-happy/skills/kicad/scripts/analyze_pcb.py BOARD.kicad_pcb --full --output OUT/pcb-analysis.json
```

输出目录先创建并放入任务 `artifacts/` 或本地 `.cache/`。分析器可写缓存/报告，不能对源文件零修改作未经验证的承诺；运行前后可对源文件做哈希对账。原理图、Gerber、EMC、热和 SPICE 分析按实际评审范围使用，详见上游说明。启发式分析不替代原生 ERC/DRC、器件数据手册或工厂审核。

## 官方依据

- [macOS 下载](https://www.kicad.org/download/macos/)、[Homebrew](https://formulae.brew.sh/cask/kicad)
- [KiCad 10 CLI](https://docs.kicad.org/10.0/en/cli/cli.html)
- [IPC API 与版本限制](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/)
- [kicad-python](https://pypi.org/project/kicad-python/)

KiCad 10 IPC 依赖 GUI，主要覆盖 PCB 编辑；导出走 CLI。开发版文档中的 headless API、原理图 IPC 不能视为稳定版已有能力。旧 SWIG `pcbnew` 接口已弃用，新脚本优先官方 IPC。
