---
description: NFC 名片进度看板：设计门槛、等外部输入、需要谁决策、工程化 TODO
last_updated: 2026-09-23
---

# 进度看板

**一句话状态（2026-09-23）**：PCB 与 CAD 设计已收口到"可以打样验证"——E16 板（三键、L 形板框、右边缘 USB、NFC 馈线与底层落点）的原生 DRC、逐引脚网表、连通性、制造包全部通过；外壳 V7 的几何、真实元件干涉与 STL 网格检查通过并可直接打印。**板上只剩 NFC 线圈本身没落铜**，其余都在等外部输入。

> **2026-09-23 方法论检查已确诊一项、新增一项**（覆铜导出补齐后 `ES-002` 从"无法裁决"变成机制清楚）：用 DRC 看不见的规则集（[规则索引](../../../docs/pcb-design-rules.md)、[pcb-methodology skill](../../../.agents/skills/pcb-methodology/SKILL.md)）离线扫了一遍，得到两项需要写盘的动作——**C3（充电器 BAT 引脚电容）离它要服务的引脚 24.49 mm**，以及 **USB/ESD 区域几乎没有地缝合**（J1 的 10 mm 内仅 1 个地过孔）。两者都躲过了原生 DRC、逐引脚网表、连通性与制造包四项检查。细节与实测数据见 [E16 记录 · 方法论检查](../hardware/pcb-e16-usb-right-mid.md#方法论检查emc--信号完整性2026-09-23)。

> **新会话从这里开始**：根 [README](../../../README.md) → [环境与常驻服务](../../../docs/environment.md)（工具链、桥接启动、五分钟自检）→ 本页（门槛、外部输入、TODO）→ "
        "[E16 记录](../hardware/pcb-e16-usb-right-mid.md)（全部细节与实测数据）。动手前先跑一遍自检，动铜箔前再跑连通性审计与 `check-proposed-route.py`。

"
        "> 机器可读的门槛与证据以 [pcb-e14-manufacturing-gates.json](../hardware/pcb-e14-manufacturing-gates.json) 为准（含工程 sha256），本页是给人看的视图；两者冲突时以 JSON 与 `check-e14-gates.py` 的输出为准。

## 设计门槛

| 门槛 | 状态 | 现在缺什么 | 证据入口 |
| --- | --- | --- | --- |
| 板框与 USB 开口 | ✅ 已闭合 | — | [E16 记录 · USB 缺口基准](../hardware/pcb-e16-usb-right-mid.md#j1-与板框基准复核2026-09-23已修正并复验) |
| 网表与电源布线 | ✅ 已完成 | — | 逐引脚 56 位号 / 234 引脚 / 0 差异；原生 DRC 只剩 24 项固有 J1 槽边告警 |
| NFC 天线与金属净空 | ⏳ 等实验 | 天线形式（板上线圈 or 贴纸/FPC）+ PN532 桌面实验 | [馈线与落点](../hardware/pcb-e16-usb-right-mid.md#nfc-天线馈线落铜2026-09-23)、[线圈候选设计](../hardware/pcb-e16-usb-right-mid.md#线圈候选设计已算好并离线校验等实验拍板) |
| 电芯交付包络 | ⏳ 等实测 | 电芯实物最大外形（含保护板/引线/胶带/鼓胀）与出线方向 | [电芯包络决策表](../hardware/pcb-e16-usb-right-mid.md#电芯包络决策表2026-09-23) |
| 可打印外壳 | ⏳ 等样件 | 打印三件并试装（键帽行程、屏幕贴合、0.4/0.5 mm 薄壁与 ±0.2 公差） | [外壳说明](../enclosure/README.md)、[打印网格报告](../enclosure/nfc-card-e16-print-meshes-report.json) |
| 供应商制造包 | ⏳ 依赖上面三项 | 确认后从同一版本重导并放行 | [制造包核对](../hardware/pcb-e16-usb-right-mid.md#制造包自动核对2026-09-23) |

## 等外部输入

- [ ] **电芯实物测量**（或供应商图纸）：对照边界表东 33.80 / 北 ~15.02 / 高 3.6 mm；超了要移按键列并重排约 8 条走线。
- [ ] **PN532 桌面实验**：读距与金属负载结论，决定天线形式；板上线圈按实测区 10.4 × 21.3 mm 算得 6 圈 1.12 µH / Q 139，匹配电容起点 100 pF + 15 pF。
- [ ] **打印 V7 三件**（下壳、上壳、三个键帽一次打）并试装反馈。
- [ ] **J1 到手核对**壳脚与板边，并确认插头插到底。

## 需要用户决策

- [ ] 线圈现在就画（板上线圈默认方案，落点两种天线都兼容；不利再撤）还是等实验结论？方案与校验工具已就位：[plan-nfc-coil.py](../scripts/plan-nfc-coil.py) 生成 [e16-nfc-coil-plan.json](../hardware/e16-nfc-coil-plan.json)，[check-proposed-route.py](../scripts/check-proposed-route.py) 离线校验（当前 `ok=true`，环间距 0.150 mm）。
- [ ] 装壳后 SWD 救援是否加底层镜像焊盘 + 下壳三个 Ø1.2 mm 探针孔（外观取舍）。
- [ ] 第三颗按键（SW2）的功能分配。
- [ ] 下单通道：嘉立创经济型 PCBA 单板（84 × 52 可直下）还是标准型拼板。

## 工程化 TODO

- [x] **补覆铜导出**（2026-09-23）：探测出 `pours` / `poured` / region 的真实结构（三处与假设不符，见 E16 记录），导出扩展后重导快照，**内容指纹与实况板逐字段一致**。新增 [analyze-e16-pour.py](../scripts/analyze-e16-pour.py) 与共享的 [pour_geometry.py](../scripts/pour_geometry.py)（带标定断言）。`ES-002` 由此确诊。
- [ ] **给 `GP-003/GP-004/BE-002` 补检查器**：已在 `analyze-e16-pour.py` 中实现，但 `GP-001`（信号跨越覆铜缺口）仍未实现——它是"干扰"最核心的一条，判据可按顶层走线下方底层覆铜的连续覆盖率。
- [ ] **把连通性审计的 `ground_reach` 修到可信**：目前报 2 个 GND 焊盘未到达覆铜，但都与手工验证的事实冲突（R13 的 GND 焊盘 0.050 mm 处就有 GND 过孔），标为 `trusted: false`、不参与门禁。修好后才能逐一验证 29+14 块覆铜区域与 GND 网络的连通性。
- [ ] **给 USB/ESD 区域补地缝合孔**（需客户端）：U5/U6 的 GND 焊盘旁各 ≥2 个，用 0.61/0.305 mm 避免落进加价档；落铜前跑 `check-proposed-route.py`，落铜后重跑原生 DRC + 连通性 + 制造包。
- [ ] **C3 处置**（需客户端）：充电器的 BAT 引脚电容搬回 U2 旁，牵动 `BAT_PACK_TBD` 约 20 mm 走线重布。
- [ ] **制造包放行前重新点数并记录过孔数**：门槛文件与散文都没有产物佐证（散文的 162 与新门槛文件的 168 不一致）。
- [x] 引入方法论设施：4 个上游 submodule（跟随 main）+ 仓库级[规则索引](../../../docs/pcb-design-rules.md) + [pcb-methodology skill](../../../.agents/skills/pcb-methodology/SKILL.md) + `check-e16-emc.py`（16 条规则）+ `tools/check-rule-coverage.py`（防止覆盖过度声明）（2026-09-23）。
- [x] artifacts 归档：23 个阶段目录进 `artifacts/archive/`，顶层只留当前产物（2026-09-23，提交 `63f35a5`）。
- [x] 目录命名改为"用途优先"（`manufacture/`、`cad/`、`review/`、`studies/routing-space/`；版本写在文件名里）。
- [x] 把文档引用的小文件（重开/DRC 记录、网表、检查脚本、渲染图册）搬进受管理目录：`hardware/records/`、`enclosure/`、`enclosure/renders/`。
- [x] `.gitignore` 改为 `**/artifacts/**` + 唯一例外 `artifacts/README.md` 索引；修复全仓相对链接（检查 0 断链）。
- [x] 桥接"从零重建"实测：`install-agent.sh` 重装后新 PID 起来、`/health` ok、崩溃计数 0。
- [x] 新增仓库级 [环境与常驻服务](../../../docs/environment.md)（工具链、服务、五分钟自检、常见故障）。
- [x] 制造包导出→归档的拷贝步骤脚本化：[collect-e16-manufacture.py](../scripts/collect-e16-manufacture.py) 按内容识别四件、拒绝跨批次混用（2026-09-23）。
- [x] 桥接改为**按需启动**：plist 去掉 `RunAtLoad`/`KeepAlive`，新增 `bridge-start.sh` / `bridge-stop.sh`，`--login-start` 才自启；本机已按此重装并实测 start/stop（2026-09-23）。
- [x] 桥接日志：`install-agent.sh --quiet` 可写入 `EDA_BRIDGE_QUIET=1`，超过 5 MB 自动轮转 `.1`；默认仍保留完整日志。
- [x] `~/Downloads` 清理：20 个 `.cn.lceda.pro.*` 旧批次导出、旧 Gerber zip（v1–v5）、解压目录与 21 MB 的 `NFC-E16-3D.txt` 已删除（释放约 29 MB）；有长期价值的 `E16-sch-netlist.txt` 存为 [hardware/records/e16-sch-netlist.enet](../hardware/records/e16-sch-netlist.enet)（sha256 与验证过的那份一致）。
- [x] `artifacts/archive/`：用户确认**全部保留**（体量可接受、索引可追溯），不删除。

## 这份看板怎么维护

1. **只改事实**：状态、门槛、TODO 勾选；细节写进对应项目文档，不在这里重复。
2. **收尾时更新**：每轮工作结束（提交前）把新完成项打勾、新增待办补上，并更新 `last_updated`。
3. **门槛以 JSON 为准**：设计门槛变化必须同时更新 [门槛文件](../hardware/pcb-e14-manufacturing-gates.json) 并跑 `check-e14-gates.py`。
