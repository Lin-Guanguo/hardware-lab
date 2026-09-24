---
description: NFC 名片进度看板：当前状态、NFC 线圈交接、工具边界、外部输入与待决策
last_updated: 2026-09-24
---

# 进度看板

## Current R1 handoff — 2026-09-24

Use the clean [NFC-Card-R1.eprj2](../../../../../../../../eda/NFC-Card-R1.eprj2), project UUID `70e4734137fc61bb6eab88e382fc9a6084e6f570f3396f1502e4f4e9dc906821`, PCB UUID `8033127c48771f3b`. The old project shares the PCB UUID; guard both identities. [Delivery and evidence](../../../../../../hardware/pcb-r1-delivery.md).

| Work item | Status | Next action and owner |
| --- | --- | --- |
| Clean project and accepted placement | Complete | One board/PCB, four schematic pages; all 58 component placements and outline retained. |
| Routing, ground and screen exclusion | Complete | Saved/reopened DRC 0; 238 pin nets matched; no split nets, dead ends or foreign copper in the complete screen area. |
| Rear five-turn NFC coil/feed | Routed and topology checked | User and agent validate resonance/read range with the final screen/case; adjust provisional C23/C24 and ferrite if needed. |
| Gerber, drill, BOM, CPL, PDF and STEP | Exported and cross-checked | Engineering prototype package; vendor placement/DFM review and powered bring-up still apply. |
| Clear 5.8 mm case and debug access | Nominal geometry and closed meshes pass | User tests printed fit, USB access, keys, screen alignment and adhesive closure. |
| Complete battery envelope | Nominal 31 × 12 × 3 mm selected | User measures received protected pack, sealed edges and lead exit; agent checks against the assumed maximum envelope. |

No order has been placed. The routed engineering handoff is complete; RF, powered hardware behaviour and physical assembly remain untested. Historical E14 manufacturing gates and E16–E20D results below apply to their own revisions, not the R1 handoff.

## Historical E16–E19 status

The following results refer to the older routed boards and do not qualify E20 for manufacture.

**一句话状态（2026-09-23）**：E16 无线圈基线、E17 六圈线圈和 E18 六圈加双侧电容均保留；独立的 **`Board1_5` / E19** 将右上角线圈外框扩大到 **20.2 × 21.3 mm、五圈**，现为 **58 元件 / 248 焊盘 / 825 线 / 174 过孔**。E18/E19 的网表、物理分支、铜连通和 V7 名义 CAD 检查通过，原生 DRC 仍有 24 项 J1 槽边告警。**二次整板审查发现导出 Gerber 板框歧义，增强后的制造包检查失败；RF、尺寸公差与实物装配也未闭环，不能下单。**详见 [整板复核](../../../../hardware/pcb-e19-independent-review.md)。

> **2026-09-23 方法论检查：两项都已修复。** 用 DRC 看不见的规则集（[规则索引](../../../../../../../../docs/pcb-design-rules.md)、[pcb-methodology skill](../../../../../../../../.agents/skills/pcb-methodology/SKILL.md)）离线扫出两处缺陷并已落盘复验：**USB/ESD 区域几乎没有地缝合**（`ES-002` 各 0 → 4 个过孔）与 **C3（充电器 BAT 引脚电容）离它要服务的引脚 24.49 mm**（`DC-001` CRITICAL → 通过）。两者原本都躲过了原生 DRC、逐引脚网表、连通性与制造包四项检查。细节见 [E16 记录 · 方法论检查](../../../../hardware/pcb-e16-usb-right-mid.md#方法论检查emc--信号完整性2026-09-23)。

> **新会话从这里开始**：根 [README](../../../../../../../../README.md) → [环境与常驻服务](../../../../../../../../docs/environment.md) → 本页 → [E19 线圈面积与工艺记录](../../../../hardware/nfc-coil-area-process-review.md)；双侧电容拓扑见 [E18 记录](../../../../hardware/pcb-e18-matching-study.md)，E16/E17 历史见对应硬件记录。动铜箔前跑连通性审计与 `check-proposed-route.py`，动 NFC 铜线后还要跑 `check-e18-nfc-branches.py`。机器可读的门槛与证据以 [pcb-e14-manufacturing-gates.json](../../../../hardware/pcb-e14-manufacturing-gates.json) 为准（含工程 sha256）。

---

## 交接：E19 放大线圈已落板，RF 实测待完成

此前卡在“两个网络无法用一段连续铜线连接”。本地 API 参考中的 `sch_PrimitiveComponent.createShortCircuitFlag` 正是遗漏的入口；在候选原理图页 `(605,565,90,false)` 放置后，U1 两个 NFC 引脚合为 `NFC1_TBD`，候选 PCB 的馈线、落点和螺旋也统一到该网。**不需要用户再在 GUI 放符号。**工程源文件内的负 y 与 API 正 y 不同，旧坐标放置会悬空。实验路径和完整验证见 [E17 记录](../../../../hardware/pcb-e17-coil-study.md)。

E16 的定制 net tie 封装和无网络铜箔分别新增 12、6 项真实 DRC，仍然是被否决的历史尝试。E17 以原理图短接符合网后，原生 PCB DRC 新增项为 0。E18 已按双侧拓扑落 C23/C24 焊位。用户指出线圈面积偏小后，复核发现原 USB 金属壳净空限制过严；E19 独立放大为五圈，并通过断线圈一段铜线的检查证明两端未被支路旁路。现阶段要对比两版实物调谐与读距，再据实测确定电容值。

---

## 工具边界与踩坑记录（避免重复推导）

1. **DRC 明细可读**：`pcb_Drc.check(strict, userInterface, true)` 返回违规数组。**不要相信布尔值**——`check(..., false)` 因为 24 项槽边基线恒为 `false`，对改动没有分辨力。此前我误记"DRC 只有布尔值"，代价是带着 6 项真实违规落盘却报告"0 违规"。
2. **封装文档的坐标是 mil**，尽管它的 `CANVAS` 声明 `"unit":"mm"`。按 mm 建会差 **39.37 倍**——这个错误是落板后在 PCB 快照（mil）里量出来的，不是看声明看出来的。
3. **器件会复制封装，不跟随封装更新**：改完封装必须删掉器件重建，否则落板仍是旧几何。
4. **库写入需要先存在个人库**（GUI 起始页「新建元件库」，或 `文件 > 新建 > 库`）。此前六项库操作全部失败，根因就是 `~/Documents/LCEDA-Pro/libraries/` 为空。建库后封装可建，但自定义符号创建与器件返回值仍不稳定，必须用 `search` 复核。**内置短接符可直接调用 `sch_PrimitiveComponent.createShortCircuitFlag`，无需建库。**
5. **直接落封装会抛错**：`pcb_PrimitiveComponent.create({libraryType: 4, ...})` 报 `Cannot read properties of null (reading 'attrsMap')`，并且会把客户端搞到起始页。要**通过器件**落。
6. **单位陷阱**：PCB 文档与快照是 **mil**；覆铜 `fill` 坐标是 **0.254 mm/单位**；`pour_geometry.MIL = 0.0254`（mm per mil）而 `check-e16-copper-connectivity.py` 的 `MIL = 39.37`（mil per mm）——**同名互为倒数**。
7. **`check-proposed-route.py` 已有 `pads` 模式**，可校验"被移动元件的焊盘 vs 既有铜箔"。它**已对 DRC 校准**：复算已知违规的 C3 原位得 4.34 / 4.08 mil，DRC 报 4.3 / 4.0。移动元件前先跑它。
8. **过孔孔径下限 7.9 mil**（0.2007 mm），且**规则按网络生效**：板上 30 个 7.8 mil 孔径只有 GND 上那 2 个（我加的）被报错，信号网络上的同规格未被约束。
9. **建多边形要走两跳**：先 `pcb_MathPolygon.createPolygon(source)` 得到 `IPCB_Polygon`，再 `pcb_PrimitivePolyline.create(net, layer, polygon, width)`；直接把坐标数组传给后者会报"参数不正确"。
10. **客户端会在保存时卡住**，留下一个不动的进度条（常见 `1%`）。判据：`/health` 仍在、文档 API 有响应、**工程文件 sha256 与门槛记录一致 → 改动已落盘**，可以放心重启。桥接会报 `AbortError` 并重试，那是界面卡住不是数据损坏。
11. **过孔创建参数顺序**：`pcb_PrimitiveVia.create(net, x, y, holeDiameter, diameter, ...)`——**孔径在前**。
12. **线圈可用板级走线画**——官方[线圈生成器扩展](https://github.com/easyeda/eext-coil-creator)调用 `pcb_PrimitiveLine.create`；本项目用原理图短接符解决两端网名，再以普通走线落板，并通过原生 DRC 验证。

---

## 设计门槛

**本轮工作顺序已调整：先查原厂／同型号参考设计，先确定布局，再详细布线。**旧走线不固定器件位置，U1 本体投影内的走线数量不能用来证明放不下。USB 是标准沉板产品；以前选择的“多层板工艺”是 DRC 规则名称，实际设计仍为双层 0.8 mm。复核还纠正了高度口径：J1 到 V7 上壳实体最小距离约 **0.34 mm**，原 0.13 mm 只是到统一参考平面的高度差。详见[参考与复核](../../../../hardware/pcb-e19-independent-review.md)。

| 门槛 | 状态 | 现在缺什么 | 证据入口 |
| --- | --- | --- | --- |
| 板框与 USB 开口 | ⏳ 原厂／参考封装与工艺适配待核 | J1 铜到槽边约 0.20 mm，满足公开最小值；继续核锣刀圆角、壳脚和实际插头，不能由 0.0007 mm 差值推断可靠性 | [整板复核](../../../../hardware/pcb-e19-independent-review.md) |
| 网表与电源布线 | ✅ 已完成 | — | 逐引脚 56 位号 / 234 引脚 / 0 差异；原生 DRC 只剩 24 项固有 J1 槽边告警 |
| **NFC 天线与匹配** | ⏳ **E18/E19 两种线圈与双侧电容焊位已完成，RF 未闭环** | 装配后比较谐振与读距，确定线圈版和 C23/C24 最终值 | [面积与工艺复核](../../../../hardware/nfc-coil-area-process-review.md) |
| 电芯交付包络 | ⏳ 等实测 | 电芯实物最大外形（含保护板/引线/胶带/鼓胀）与出线方向 | [电芯包络决策表](../../../../hardware/pcb-e16-usb-right-mid.md#电芯包络决策表2026-09-23) |
| 可打印外壳 | ⏳ 等样件 | 打印三件并试装（键帽行程、屏幕贴合、0.4/0.5 mm 薄壁与 ±0.2 公差） | [外壳说明](../../../../../../enclosure/README.md)、[打印网格报告](../../../../enclosure/nfc-card-e16-print-meshes-report.json) |
| 供应商制造包 | ❌ 当前导出板框检查失败 | 清掉 GKO 多余开放路径和 GME 冲突矩形，从同一版重导再核 | [整板复核](../../../../hardware/pcb-e19-independent-review.md) |

### 下单前必须核对的板厂约束（已查实）

| 项 | 板厂要求 | 本板 |
| --- | --- | --- |
| **线圈线宽线距** | 嘉立创线圈专门规则：1 oz 盖油 ≥0.15/0.15 mm；开窗 ≥0.25/0.25 mm | E18/E19 均为 **0.25/0.15 mm，线圈盖阻焊**。开窗需重画并改表面处理，见[工艺复核](../../../../hardware/nfc-coil-area-process-review.md) |
| **Gerber 板框** | 仅保留一个明确的闭合成品轮廓，去掉无关机械线 | 当前 GKO 两条路径、GME 另一个完整矩形，**不能上传下单**，见[整板复核](../../../../hardware/pcb-e19-independent-review.md) |
| 锣边到铜 | **≥0.2 mm** | J1 焊盘 **约 0.20 mm，名义满足**；差值不是成品机械公差，须按标准连接器封装与制造要求整体核对 |
| 过孔孔到孔 | ≥0.2 mm | 最差 0.385 mm ✓ |
| 免费裸板打样表面处理 | 先前查到的优惠选项为 OSP/沉金，具体以当次下单页为准 | **不能套用到经济型 PCBA**；0.8 mm 绿板经济型 PCBA 能力表列的是 HASL |
| 下单沟通 | 设计在 Gerber 里；表面处理等是页面选项；**关键环节是"生产稿确认"**；只有非常规要求才写下单备注 | 不需要预先找客服。求助渠道：下单页「技术咨询」、PCB 技术支持 QQ `3001741855`、官网「服务指引 → 人工服务」 |

## 等外部输入

- [ ] **电芯实物测量**（或供应商图纸）：对照边界表东 33.80 / 北 ~15.02 / 高 3.6 mm；超了要移按键列并重排约 8 条走线。
- [ ] **PN532 桌面实验与 E18/E19 样板 RF 对比**：开发板先测 NFC 功能；两种 PCB 线圈需实物测装壳谐振、读距、方向和金属负载。现有电感/Q 均为粗估，C23/C24 的 220 pF 是起始值，见 [E19 复核](../../../../hardware/nfc-coil-area-process-review.md)。
- [ ] **打印 V7 三件**（下壳、上壳、三个键帽一次打）并试装反馈。
- [ ] **J1 到手核对**壳脚与板边，并确认插头插到底。

## 需要用户决策

- [x] **NFC 线圈和匹配焊位的落铜方式**：E17 已解决原理图短接符与线圈落铜，E18 加两侧电容，E19 扩大线圈且验证支路分离。下一步是两版样板 RF 实测，不再需要 GUI 协助。
- [ ] 装壳后 SWD 救援是否加底层镜像焊盘 + 下壳三个 Ø1.2 mm 探针孔（外观取舍）。
- [ ] 第三颗按键（SW2）的功能分配。
- [ ] 下单通道：嘉立创经济型 PCBA 单板（84 × 52 可直下）还是标准型拼板。

## 工程化 TODO

- [ ] **把连通性审计的 `ground_reach` 修到可信**：目前报 2 个 GND 焊盘未到达覆铜，但都与手工验证的事实冲突（R13 的 GND 焊盘 0.050 mm 处就有 GND 过孔），标为 `trusted: false`、不参与门禁。**修好后才能逐一验证 27+16 块覆铜区域与 GND 网络的连通性。**
- [ ] **校准 `GP-001`（信号跨越覆铜缺口）**：已实现（`analyze-e16-pour.py`），按"采样点到最近参考铜箔的距离 ≤ 0.5 mm"判覆盖率，结果是 48 个信号网络里 **45 个低于 95%**——**该结论不可信**且已标为参考项。走廊宽度 0.5 mm 是本仓库自定（上游只给 95% 阈值），且该指标分不清"真实平面开槽"与"平面被同层其它走线的间距穿孔"。**要校准到一块已知有问题的板子才能用。**
- [x] **原生 DRC 明细可读**（2026-09-23）：`pcb_Drc.check(_, _, true)`；由此抓出并修复了 C3 造成的 6 项真实违规。
- [x] **给 USB/ESD 区域补地缝合孔**（2026-09-23）：4 个 GND 过孔 + 5 条拉线，重铺两块地覆铜；`ES-002` 各 0 → 4；U6 到最近底层覆铜 2.318 → 0.256 mm。
- [x] **C3 处置**（2026-09-23）：搬到 (48.60, 22.75) rot 180，`DC-001` 通过（最近同网络焊盘 0.82 mm）。顺带删掉 12 段绕行与 4 个孤立过孔——删除后连通性一度报 1 处断网，正是那 4 个过孔造成的。
- [ ] **修复制造包轮廓**：旧检查器只核顶点，误报 `ok=true`；增强后 E16/E18/E19 均因 GKO 多路径 + GME 冲突矩形而失败。修正源图/导出后重导并复核；钻孔/BOM/CPL 数量一致性本身仍成立。
- [x] **验证可复现的板框清理方法**：限定结构的审查脚本只改 GKO、删 GME，E19 清理包经完整性检查 `ok=true`，其余 15 个 Gerber 成员逐字节不变；源图/正式导出仍需修，详见[整板复核](../../../../hardware/pcb-e19-independent-review.md)。
- [x] **建线圈封装 `HL_NFC_COIL_E16`**（库 `hardware-lab`）：29 段螺旋 + 2 个换层过孔 + 2 个焊盘；**但本工具的 DRC 不接受它作为 net tie**，见交接节。
- [x] 引入方法论设施：4 个上游 submodule（跟随 main）+ 仓库级[规则索引](../../../../../../../../docs/pcb-design-rules.md) + [pcb-methodology skill](../../../../../../../../.agents/skills/pcb-methodology/SKILL.md) + `check-e16-emc.py`（16 条规则）+ `tools/check-rule-coverage.py`。
- [x] 新增仓库级 [环境与常驻服务](../../../../../../../../docs/environment.md)（工具链、服务、五分钟自检、常见故障；含"库 API 失败 = 缺个人库"与"保存卡住"两条判据）。
- [x] 桥接改为**按需启动**；日志轮转；`artifacts/` 归档与 `.gitignore` 收敛；`collect-e16-manufacture.py` 按内容识别四件、拒绝跨批次混用。

## 这份看板怎么维护

1. **只改事实**：状态、门槛、TODO 勾选；细节写进对应项目文档，不在这里重复。
2. **收尾时更新**：每轮工作结束（提交前）把新完成项打勾、新增待办补上，并更新 `last_updated`。
3. **门槛以 JSON 为准**：设计门槛变化必须同时更新 [门槛文件](../../../../hardware/pcb-e14-manufacturing-gates.json) 并跑 `check-e14-gates.py`。
4. **交接给别的 Agent 时**：重点看上面三节——「交接：NFC 线圈」「工具边界与踩坑记录」「下单前必须核对的板厂约束」。**工具边界那一节是几十次实测换来的，不要跳过。**
