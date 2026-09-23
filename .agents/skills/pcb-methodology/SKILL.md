---
name: pcb-methodology
description: 本仓库的 PCB 设计方法论总控：约束层级、电气敏感件变更门禁、证据纪律、规则适用性判定，以及该查哪个上游参考。在改布局/布线/板框/器件位号、评审设计、准备制造包、判断某条规则是否适用于本板、或担心"这个做法是不是 best practice"时使用。与 easyeda-api（读写 EDA 工程）配合；不替代它，也不替代原生 DRC。
---

# PCB 设计方法论（总控）

## 这份 skill 解决什么

DRC 只回答"几何有没有撞上"。它不回答：

- 这颗去耦电容该在哪
- 这个开关回路的面积会不会辐射
- 这次为了美观的挪动有没有动到电气敏感件
- 这条从网上看来的规则，对**这块板子**到底成不成立

本 skill 是这几类判断的执行体。规则清单、阈值与一手来源见仓库级 [docs/pcb-design-rules.md](../../../docs/pcb-design-rules.md)，本页负责**流程与门禁**。

## 约束层级

把每个设计决定放进下面三层；**可交易目标永远不能静默降低硬约束或电气目标**。

| 层 | 内容 | 性质 |
| --- | --- | --- |
| 硬约束 | 板厂最小间距与槽边、连接器配合几何、天线净空、焊盘支撑、装配可达、载流宽度、板框与挖空 | 不可交易。任何一项冲突就停下来说清楚 |
| 排名目标 | 回流路径连续性、去耦局部性、开关热回路面积、差分几何、器件去耦到引脚的距离 | 可交易，但**交易必须显式**：记录换来了什么、放弃了什么 |
| 自由目标 | 外观对称、排布美观、丝印清晰、成本档位、走线长度次优 | 可以在这一层内自由决定 |

判断口诀：**先问"我要动的东西属于哪一层"，再问"这次改动的代价记在哪一层"。** 用户提出"为了好看"时，不要回答"美观不重要"，要回答"这件事落在哪一层、代价是什么"。

## 电气敏感件门禁（改布局前必做）

任何移动、旋转、重排之前，把要动的每个器件对照下表分类。命中后两类时，**必须附命名证据**才能提交。

| 类别 | 本仓库典型器件 | 门禁 |
| --- | --- | --- |
| 自由区 | 按键 SW*、丝印、测试点 TP*、指示灯、机械框、非关键接插件 | 可直接为美观/装配移动 |
| 带规则 | 去耦电容（须在供电脚逃逸路径上）、开关变换器的输入电容与电感热回路、USB 串阻与 ESD 阵列（保护必须在分支之前）、晶振与反馈网络、电流检测、分压电阻 | 移动必须附证据：DC-001/DC-003 距离、SW-002/SW-003 回路面积，或写明为何不适用 |
| 必须重新推导 | 天线净空区几何、连接器与板框配合基准、板框缺口与挖空、关键网络的换层与参考、地覆铜连通性 | 不能"顺手挪"。重新走一遍几何检查 + 连通性审计 + 原生 DRC 对比 |

写进文档的判据要区分**实测 / 图纸推导 / 推断**三种，不要混成一句"已确认"。

## 适用性判定（用规则之前）

上游规则是按"多层板 + 高速接口"写的。对本仓库这类板子（2 层、0.8 mm、USB 全速、射频在模块内），**必须先判 适用 / 不适用 再动手**：

- 前提不成立就标"不适用"并写明为什么。例：`GP-002` 只针对 ≥4 层板；`SU-001/002/003` 假设存在平面对；`DP-004` 假设有内层可用。
- 前提成立但阈值口径不同就写明。例：`XT-001` 的 3H 在 0.8 mm 介质下是 2.4 mm，比本板多数走线间距都宽，必须按攻击者类别筛；`RP-001` 的 max(2H, 1.0 mm) 在 2 层板上是 1.6 mm，而 2 层板没有平面对，回流在两面地覆铜之间跳。
- **写明"不适用"和写明"适用"同样有价值**：否则会花力气修一个不存在的问题（USB 全速等长就是这一类，实测余量约 480 倍）。

## 证据纪律

1. **测量，不要推断。**"大概是"不是发现。决定是否继续做下去的说法必须有数字，并标明是实测、图纸推导还是推断。
2. **先验证工具，再验证结果。** 任何新的几何检查器先用已知非对称物体标定。本项目实际踩过：DRC 计数口径、24 项与 12 项的分类差异、客户端 `null.map` 报错。
3. **不要信任手抄的数字。** 从机器导出的快照重新生成计数；散文里的数字会漂（已发生：文档写 781 段铜 / 242 焊盘 / 162 过孔，快照实际 798 / 244 / 168）。
4. **一个变量一次，记录完整门禁向量。** 改完同时记录：原生 DRC 分类计数、连通性审计、焊盘/过孔/线计数、几何检查。只报"DRC 没变多"不算验证。
5. **检查器要独立于被测对象。** 能与 EDA 导出对账的第二条路径才有价值；同一个来源自证不算验证。

## 该查哪个上游

上游以 Git submodule 固定在 `upstreams/`，按需跟随 main（`git submodule update --remote`）。**只读不装**：这些仓库假设 KiCad/MCP 或各自的目录布局，不接入 `.agents/skills/`，避免与自建桥接冲突、也避免第三方脚本对着我们在乎的设计执行。

| 要回答的问题 | 上游 | 读哪里 |
| --- | --- | --- |
| DRC 抓不到的电气规则、阈值、一手来源 | [kicad-happy](../../../upstreams/kicad-happy) | `skills/emc/references/pcb-emc-rules.md` |
| EMC 公式、协议偏斜限值、发射限值 | kicad-happy | `skills/emc/scripts/emc_formulas.py`（纯 stdlib，需同目录 `skills/kicad/scripts/kicad_utils.py`） |
| 监管限值（FCC / CISPR / MIL） | kicad-happy | `skills/emc/references/emc-standards.md`、`emc-methodology.md` |
| 门禁组织、产物失效规则、实验记录格式 | [pcba-design-skills](../../../upstreams/pcba-design-skills) | `.agents/skills/pcb-layout-review/SKILL.md`、`references/layout-review-checklist.md` |
| 同工具链（EasyEDA Pro + MCP）的陷阱、装配纪律 | [pcb-skill](../../../upstreams/pcb-skill) | `skills/pcb/SKILL.md`、`docs/case-study.md` |
| 独立于 EDA 的验证脚本思路 | pcb-skill | `scripts/verify/README.md`、`scripts/placement/README.md` |
| 逐引脚/逐器件证据式审查、嘉立创 EDA `.epro2` 解析 | [hw-review](../../../upstreams/hw-review) | `SKILL.md`、`parse_epro2.py`、`templates/` |

引用上游内容时同时标出**规则 ID 与文件名**：上游 README 的规则计数与实际文档不一致（声称 44 条 / 18 类，`pcb-emc-rules.md` 实际 42 条 / 17 类，且 `ML-001` 有实现无条目）。

## 本仓库工具链入口

```bash
# 桥接按需启动（不是开机自启；状态/停止同名脚本）
tools/easyeda-bridge/bridge-start.sh

# 导出 E16 实时快照（经桥接；输出 hardware/e16-right-mid-snapshot.json）
node projects/nfc-business-card/scripts/eda-exec-wait.mjs \
     projects/nfc-business-card/scripts/eda-export-e16-snapshot.js 60000
```

| 用途 | 入口 |
| --- | --- |
| 环境、五分钟自检、常见故障 | [docs/environment.md](../../../docs/environment.md) |
| DRC 看不见的规则索引与板级适用性 | [docs/pcb-design-rules.md](../../../docs/pcb-design-rules.md) |
| EMC / 信号完整性只读检查 | `projects/nfc-business-card/scripts/check-e16-emc.py` |
| 铜箔连通性（动铜箔后必跑） | `projects/nfc-business-card/scripts/check-e16-copper-connectivity.py` |
| 落铜前逐点校验 | `projects/nfc-business-card/scripts/check-proposed-route.py` |
| 逐引脚网表一致性 | `check-netlist-consistency.py` + `eda-export-pcb-pins.js` |
| 制造包核对 | `check-e16-manufacture.py`、`collect-e16-manufacture.py` |
| 进度与门槛 | `projects/*/docs/progress.md`、`hardware/pcb-e14-manufacturing-gates.json` |

**覆铜几何已补齐**（2026-09-23）：导出脚本原先读 region 上不存在的 `polygon` / `rule`，两个字段被静默丢弃，铜箔对象则完全没采集。现已补齐 `pours` / `poured` 并通过内容指纹与实况板核对。两点必须记住，否则会量出自信的错数：

- 填充坐标的**单位与快照其余对象不同**，1 单位 = 0.254 mm；`pours`、走线、焊盘、外形都是 mil。
- `fills[]` 是混合列表：≥3 顶点的环是覆铜多边形（首环外轮廓、后续为孔），**2 点退化线段是散热辐条**——它才是把地焊盘接到覆铜的东西。

这两点由 `pour_geometry.py` 承载，并带**标定断言**（解析出的覆铜必须落在铜箔边框内 1 mm，否则拒绝出结论）。`ground_reach`（GND 焊盘是否到达覆铜）目前标为 `trusted: false`，**不参与门禁**：它与手工验证的事实冲突，属于线索而非发现。

## 变更与实验循环

1. **冻结输入**：记录当前 SHA、快照、DRC 分类计数作为对照基线。
2. **一次一个连贯的改动**，命名候选状态（如 `e17-coil-landed`），保留成对文件以便回退。
3. **测完整门禁向量**，与当前最佳安全候选对比。**大板或加层只有在消除一个已测量的阻塞且不回退其他门禁时才成立。**
4. **接受标准**：不得新增断网、真实 DRC 错误、电源不连通或已核实的制造缺陷。
5. **不重复已否定的方法**——除非条件发生了实质变化（记录里要写明变的是什么）。
6. 改动牵动网络/器件/封装/布局/走线/BOM/CPL 时，下游门禁失效，需重新验证。

失败也要记录：本项目历史上"两层布局做不出 USB-C 数据扇出"的结论就是被后续"多层板规则 + 0.3/0.2 mm 小孔 + 焊盘端部错列"推翻的。

## 什么时候停下来问用户

- 改动会落在硬约束层（板框、连接器基准、天线净空、器件料号）而不只是自由层
- 两个目标真的要冲突，需要用户在成本/外观/性能之间取舍
- 要下单、要烧录、要向外部发消息
- 发现的问题需要"重新生成"而不是局部修补——把代价和收益讲清楚再动手

其余情况按本 skill 直接推进，把假设和证据写在文档里。
