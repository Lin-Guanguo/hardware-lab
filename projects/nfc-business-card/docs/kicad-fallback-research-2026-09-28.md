# KiCad 备用工具链调研

## 当前决定与验证边界

2026-09-28 用户决定：**本轮继续使用嘉立创 EDA；若本轮仍不能完成，再转向 KiCad。随后授权安装软件并准备仓库工具链，暂不迁移产品工程。** 当前中沉 USB-C、0.8 mm 板厚、标准型 SMT 和薄壳方向见[项目 README](../README.md)，不因工具调研改变。用户计划付费生产，EDA 专属免费打样券不是本次选型目标。

KiCad 10.0.6 已由用户通过 Homebrew 安装；仓库新增 `kicad-workflow`、独立 Python 绑定环境、自检和样例脚本。基础 API 编辑、保存重开、DRC 与导出已验证，见[工具入口与记录](../../../tools/kicad/README.md)。未更新子模块或迁移产品 PCB；工具样例通过不等于本项目已验证可用。

## 本机与仓库现状

| 项目 | 2026-09-28 检查结果 |
| --- | --- |
| 系统 | Apple Silicon / arm64，macOS 26.3 |
| KiCad | 10.0.6，`/Applications/KiCad/KiCad.app`；CLI 为 `/opt/homebrew/bin/kicad-cli` |
| Python | `python3` 为 3.12.12，可复用，不需要为分析脚本再装一套 Python |
| 已启用 skill | `.agents/skills/easyeda-api`、`.agents/skills/pcb-methodology`、`.agents/skills/kicad-workflow` |
| 已有 KiCad 上游 | `upstreams/kicad-happy`，锁定 `a6bba1add1e18b89e3aa0824b9769ed1d9d79174`，规则参考及按需分析；PCB 解析脚本已用独立样例验证 |
| 已有流程上游 | `upstreams/pcba-design-skills`，锁定 `d41e9996f052016727403236cf0f7476f8f23a1b`，目前只作参考 |

上游判断基于上述本地提交，不将在线 main 的新功能视为已引入。自建 [pcb-methodology](../../../.agents/skills/pcb-methodology/SKILL.md) 继续负责敏感件、规则适用性和证据纪律。

## 软件组成与安装

| 组件 | 建议 | 用途与边界 |
| --- | --- | --- |
| KiCad 稳定版 | 已安装 **10.0.6** | 原理图、PCB、封装编辑，Gerber/3D 查看及 `kicad-cli`；恢复或升级时重新核实版本并记录 |
| 官方符号、封装和 3D 库 | 首次启动检查库初始化；关键器件另核原厂图纸 | 通用库不等于本项目料号已匹配，3D 模型也不代替机械尺寸核对 |
| `kicad-python` | 已安装 **0.8.0**，放仓库 `.cache/kicad-venv/` | 官方 IPC API 的 Python 绑定；本次实测后已在 `tools/kicad/requirements.txt` 锁定依赖 |
| 现有 Python | 复用 | `kicad-happy` 的安装说明要求 Python 3.10+，核心分析脚本使用标准库 |
| 第三方 MCP、自动布线器、制造插件 | 首轮不列为必需 | 先证明原生 API/CLI 能完成最小操作链；存在具体缺口后再评估，避免同时引入多个未验证层 |

沿用用户已有的 Homebrew 管理偏好。本次已执行的安装与版本检查命令：

```sh
brew install --cask kicad
kicad-cli version
```

也可使用 [KiCad 官方 macOS 下载页](https://www.kicad.org/download/macos/)；官方当前支持 macOS 12 及以上，Homebrew 使用 Universal DMG，适合本机架构。[Homebrew 软件包](https://formulae.brew.sh/cask/kicad)提供 CLI 链接；若 PATH 未找到，官方 macOS CLI 路径是 `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`。

首次启动按[官方入门说明](https://docs.kicad.org/10.0/en/getting_started_in_kicad/getting_started_in_kicad.html)初始化库，确认符号、封装及模型可解析。原有 FreeCAD 继续负责外壳与实体干涉，不需更换。

## Skill 怎么引入

建议沿用“方法论总控＋工具执行＋补充审查”，不全量安装另一套流程。

| 层次 | 入口 | 引入方式 |
| --- | --- | --- |
| 设计方法 | 现有 `pcb-methodology` | 继续使用；切换时补 KiCad 工具入口，不照搬 EasyEDA 的坐标和图元检查器 |
| KiCad 执行 | 自建仓库级 `kicad-workflow` | 已创建并完成工具样例验证，记录工程身份、版本、API 编辑、保存重开、原生检查和制造导出 |
| 分析审查 | `kicad-happy/skills/kicad`、按需 `emc` | 通过自建入口按需运行；PCB 解析已验证，EMC 未运行。不注册上游的宽泛触发描述；它们不是自动布局布线引擎 |
| BOM 与制造资料 | 同上游 `bom`、`jlcpcb` | 按需参考；`bom` 有写回原理图属性的工作流，不是纯只读检查；`jlcpcb` 含国际站费用和工艺假设，国内订单须另核 |
| 流程参考 | 已有 `pcba-design-skills` | 继续参考阶段证据与失效规则，不再叠加另一套总控或自动下单流程 |

仓库已有子模块，无需重复 clone 或全局安装。未来直接启用的上游 skill 以 `.agents/skills/<name>` 相对符号链接指向固定提交的子目录；仓库适配写在自建 skill，保持上游文件不变。启用前要读完整 skill 及其关联依赖：例如 `kicad` 在具备相应输入/工具时要求联动 EMC/SPICE，不应只安装一个入口便声称完成全部审查。

本次审阅其用途、依赖与部分实现入口，并在独立样例运行 `analyze_pcb.py --full`；未完成全仓代码审计或完整设计评审。可定位资料：[固定提交 README](https://github.com/aklofas/kicad-happy/blob/a6bba1add1e18b89e3aa0824b9769ed1d9d79174/README.md)、[KiCad 分析 skill](https://github.com/aklofas/kicad-happy/blob/a6bba1add1e18b89e3aa0824b9769ed1d9d79174/skills/kicad/SKILL.md)、[依赖说明](https://github.com/aklofas/kicad-happy/blob/a6bba1add1e18b89e3aa0824b9769ed1d9d79174/install-guidance.md)。

## AI 实际操作的路径与缺口

推荐：**AI 调用受控脚本 → 官方 IPC API 编辑 PCB → 保存重开 → CLI 原生检查/导出 → 补充分析与视觉核对**。

- KiCad 10 的 IPC API 需要运行中的 GUI，仅覆盖 PCB 编辑器；原理图自动化不能假设走同一接口。原理图优先导入已核对的设计，必要的后续编辑另做样例验证。公开文本格式便于检查，但不能由此推断直接批量改文件安全可靠。
- KiCad 10 的 IPC API 不提供绘图/制造导出，使用 `kicad-cli`。CLI 提供 ERC、DRC、原理图/PCB 一致性检查以及制造导出，可产出机器可读报告。
- 老 `pcbnew` SWIG API 已弃用，官方计划在 KiCad 11 移除。新工具优先 IPC；第三方插件如果仍依赖 SWIG，必须明确版本约束，不能因为能安装就当长期方案。
- 能创建线段和过孔，不代表能调用完整交互布线器，更不代表会规划。首轮必须验证局部布线、回流、规则拦截和保存一致性，暂不承诺全板自动布线。
- 自定义物理间距规则可覆盖同网络对象，但需限定对象与例外，避免把合法连接也误判。courtyard 检查依赖正确装配边界，第三方几何分析也需用已知样例标定。

依据：[IPC 状态与限制](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/)、[Python 绑定](https://pypi.org/project/kicad-python/)、[旧接口弃用](https://dev-docs.kicad.org/en/apis-and-binding/index.html)、[KiCad 10 CLI](https://docs.kicad.org/10.0/en/cli/cli.html)、[PCB 规则手册](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)。开发文档可能同时描述 KiCad 11；不得把其新增功能当作 10.0.6 已有能力。

## 本项目的迁移准备

先冻结迁移当时的最新嘉立创候选、网表、BOM、封装与机械约束，记录文件指纹；R21 只作历史对照，不能覆盖本轮中沉方案的新决定。

KiCad 10 官方 PCB 导入支持 EasyEDA Pro `.epro/.zip`，不等于能直接读取我们的 `.eprj2` 数据库。先测试嘉立创导出格式，再分别验证原理图、PCB 和库的导入。项目能打开只是第一步，须逐项核对：

- 位号、引脚网络、料号、DNP，以及原理图到封装的对应关系；不能只比较器件总数。
- 中沉 USB 的实际料号/槽口/焊盘、U1 官方 61 焊盘、J2 引脚顺序与正反面。
- NFC 连续线圈与原理图短接符的语义、BLE/NFC 禁铜区、阻焊/锡膏、铺铜连接及板框缺口。
- 坐标单位、原点、底层镜像和 CPL 角度；目前依赖 EasyEDA 快照及 mil 单位的脚本需适配后重标定。

若正式引入，建议原生 KiCad 工程放 `projects/nfc-business-card/hardware/kicad/`，首次有可用工程时才创建；纳入 `.kicad_pro`、`.kicad_sch`、`.kicad_pcb`、`.kicad_dru` 及实际用到的项目库/库表。临时锁文件、个人界面状态和可重建导出物忽略。工程内采用相对库路径；长期小证据继续放 `hardware/records/`，大产物放 `artifacts/`。这是目录建议，本次未创建空目录或变更忽略规则。

试验期保留当前嘉立创工程作为主工程；正式切换后指定唯一编辑来源，旧工程归档，不来回转换维护两份设计。

## 最小验收与停止条件

正式迁移前先用独立 USB/ESD/充电局部样例验证，再迁移整板。本次仅完成两焊盘工具样例的 API 写入/重开、未连接及线宽违规检测、基础导出；以下产品相关验收仍须完成：

1. 库、网络、板框和器件方向对账；另设 NFC 线圈/短接与净空专项样例。
2. API 移动一个器件、创建一段线和一个过孔后保存，关闭重开，几何及网络一致；恢复基线也可复现。
3. 故意注入短路、未连接、同网孔靠近焊盘及装配边界冲突，证明检查器能报出预期缺陷；修正后消失。未布通样例的预期未连接项单列，不能靠全局忽略获得“DRC 0”。
4. 按原厂关系做局部摆件和试布，确认接口与工具确实支持所需操作。
5. 从同一保存版本生成 Gerber、钻孔、BOM 和 CPL，核对国内嘉立创文件规范；实际上传验证时检查层、槽、坐标、极性与物料识别，不等于下单。

如果基础操作、保存或规则检测不能稳定复现，停在工具适配阶段，不把整板迁移当作排障手段。若本轮失败源于机械/工艺输入不闭合，迁移前仍需解决该输入；换 EDA 不会改变可制造性要求。

付费生产可走标准制造文件；[国内嘉立创 BOM/CPL 规范](https://www.jlc.com/portal/server_guide_48022.html)是本项目对接依据，国际站教程仅补充。EDA 专属免费券排除导入 PCB，见[官方说明](https://prodocs.lceda.cn/cn/faq/fabrication/)，不能把换软件等同于制造费用或优惠必然相同。

## 本次核查记录

- `uname -m`、`sw_vers`、Python 版本及常见安装路径探测：完成，只读。
- `git submodule status`、`.gitmodules`、现有 skill/上游说明阅读：完成，未更新子模块；新增本仓库工具 skill 与独立虚拟环境。
- 软件版本、macOS 下载、API/CLI、导入与制造规范：网络资料核查完成。
- KiCad 安装、库初始化、API 编辑与保存重开、DRC 正反例、Gerber/钻孔/坐标导出：独立样例通过，完整边界见[验证记录](../../../tools/kicad/README.md#2026-09-28-验证记录)。
- 工程转换、原理图 ERC、真实器件/规则专项、制造文件上传：未执行。
