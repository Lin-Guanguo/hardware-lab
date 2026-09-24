# Programmable NFC Business Card

## 当前确定方案

**最新先摆位候选：**[R4 独立工程与对照图](hardware/production/r1-layout-reset-r4/README.md)从 R2 新建，显示供电区 15 个器件成组重排，保持七对敏感焊盘的相对距离，另 51 个器件及板框／天线未动；工程内过孔规则为 0.30 mm 钻孔、默认约 0.55 mm 外径。R4 的走线与覆铜仍为旧位置，重开原生 DRC 有 62 条间距错误和 36 条断连，当前仅是布局检查点，**不可投产**。下一步先复核封装包络，再局部拆线重布；R2 仍是最新低成本制造候选。

**最新低成本制板候选：**[R2 独立工程与制造检查文件](hardware/production/r1-free-0p30-sense-ring-r2/README.md)继承了 TS/MR 10 kΩ 到地及可关断的电池 ADC 采样，在显示供电、USB 扇出及充电区局部重布。重开工程后原生 DRC 为 0，最小实际钻孔 0.30226 mm、最小径向孔环 0.1016 mm；独立走线/焊盘/过孔审计未发现小于 0.15 mm 的异网铜间距。[新版线上 PCB/SMT DFM](hardware/production/r1-free-0p30-sense-ring-r2/vendor-dfm-2026-09-24.md)仍列孔环、过孔到焊盘、USB 槽及 J1/U1 贴装危险，**尚不可投产**；原 R1 是未投产的制造基准。

**独立布局重排试验：**[R3 工程与诊断](hardware/production/r1-power-relayout-r3/README.md)把显示供电器件移到右上功能区，保留屏幕、NFC、USB 保护及电池采样。旧规则下保存重开后的 DRC、连通与 0.15 mm 异网间距检查通过；但自动布线生成了 **54 个约 0.25 mm 过孔**，简单放大至 0.30 mm 又出现 29 对窄间距。现已把当前工程的过孔内径最小/默认改为 0.30 mm，原生 DRC 据此报 54 条过孔尺寸错误；新建 PCB 的默认双面板规则也已保存。C10–L1–Q1 布局代理面积仍偏大。此版是下一轮按工艺约束重布的起点，**不是低成本制造候选，不可下单**；R2 仍是最新低成本候选。

**3.0 mm 内腔研究：**按用户反馈电池最厚处可卡入 3 mm，已完成 [4.6 mm 总厚诊断](enclosure/r1-cavity-3mm-study/README.md)。现有 USB、主控、FPC 座和按键运动存在干涉；局部深腔与平整外表两条路线已有尺寸预算，尚无可打印的 3 mm 内腔方案。电池 3.0 mm 仅用于本次研究，打包版不变。

**最新减薄候选：**[3.6 mm 内腔／5.2 mm 总厚度](enclosure/r1-usb-height-5.2/README.md)已生成。保持电池 3.4 mm 包络及 PCB 安装高度，调整键帽中央压柱后，静止无预压干涉、完整行程几何通过；USB-C 顶部名义余量约 0.11 mm，打印公差和实物回弹仍未验证。5.8 mm 打包版保持不变。

**减薄方向更新：**以 USB-C 安装高度为约束的 [5.4 mm 圆角候选](enclosure/r1-usb-height-5.4/README.md)已生成。键帽底面局部挖空后完整行程几何检查通过，仍保留 3.4 mm 电池包络；键帽局部薄壁、回弹公差与可拆底盖待解决，尚未替换 5.8 mm 打包版。

**CAD 最新接口同步：**[2.54 mm SWD 圆角候选](enclosure/r1-rounded-rear-soft-swd254/README.md)沿用 5.8 mm 厚度，仅更新底盖五孔：Ø1.60 mm、孔口 R0.05，表面最窄连桥 0.84 mm。用户接受通用夹具假设，实物试夹待完成。可拆底盖与按钮减薄仍在设计中。

**外壳工艺评审：**[SLA 打印与 SWD 烧录说明](enclosure/r1-rounded-rear-soft/manufacturing-review.md)已完成，保留五个调试孔。圆角候选仍需解决薄底盖、胶接定位、涂层配合和按键轴向公差；首选向嘉立创 3D 询价，备选 PCBWay。成品板固件尚未开发；首次 bootloader 由用户通过 SWD 写入，不安排工厂代烧。

**最新圆角候选：**[加大圆角的上壳与底盖](enclosure/r1-rounded-rear-soft/README.md)已生成，正面／背面／俯视四角为 R1.2／R0.7／R3.2 mm；外尺寸与 PCB 不变，装入几何检查通过。仍待底盖固定与实物工艺验证。

**外壳方向更新，2026-09-24：**用户选择正面＋侧壁一体、独立底盖、背面内移接缝和外露圆角。[独立 CAD 候选与剖面](enclosure/r1-rounded-rear-study/README.md)保持原外尺寸，PCB 对上壳的装入路径检查通过；底盖固定、胶接工艺和实际装配仍待验证，尚未替换现有 CAD 或制造文件。

**R1 is the current editable engineering prototype.** Three front keys and a front e-paper display; rear NFC coil; right-centred recessed USB-C; two-layer 0.8 mm PCB; transparent printed enclosure, 85.2 × 53.2 × 5.8 mm. The selected battery is nominally 31 × 12 × 3 mm.

**Reviewed prototype checkpoint, 2026-09-24:** the perimeter GND rim is removed, the rear coil has 45° corners and equal offsets to the three exposed edges, and USB CC2 now branches at its protection pad. DRC/connectivity checks pass. **The C1 finding was retracted after identifying C8 as the existing charger input capacitor.** [Review and discussion items](hardware/pcb-r1-review.md). RF tuning, battery measurements and physical assembly remain unverified. The earlier archive checkpoint is `ccf9f92`; the PCB and enclosure study checkpoint is `bee8846`. Subsequent drill/return-path changes are described in the [pre-order review](hardware/r1-preorder.md).

**Latest electrical review:** CE/SCL routing now uses two fewer vias and 4.88 mm less combined trace; saved/reopened DRC and independent copper checks pass. R3/R4 changed to 0 ohm / C21189. [USB update/logging and SWD recovery plan](hardware/r1-usb-swd-recovery.md) records the implemented 2.54 mm SWD row, its synchronized cover access and the user-selected SWD programmer recovery path. The selected generic 5P clip is accepted on nominal dimensions; actual contact is a prototype check. Current manufacturing files are refreshed; the user confirmed on 2026-09-24 that R1 needs no hidden RESET switch or side opening. Next: [production verification handoff](hardware/r1-preorder.md#next-task-handoff).

**低成本制板试验：**[R1 0.30 mm 钻孔候选](hardware/production/r1-free-0p30/README.md)已另存并完成本地检查，且已做[嘉立创线上 DFM](hardware/production/r1-free-0p30/vendor-dfm-2026-09-24.md)。它消除了 0.25 mm 钻孔，但最窄孔环约 0.076 mm；孔环、镀铜槽和 USB-C 贴片模型仍需供应商确认。电路评审还确定需补 TS/MR 10 kΩ 到地，当前候选制造包尚未合入；原 R1 仍是当前制造基准。

![Actual front and rear copper](enclosure/renders/r1-routed-front-rear.png)

**Battery follow-up:** battery pads are routed at the user-selected **B position beneath the screen**, with the pack lead exit toward the upper right; both pads were subsequently shifted **1.5 mm right**, to (32.5,18.7)/(35.5,18.7) mm. Three redundant signal vias and one unused stub were removed; reopened DRC and independent copper checks pass. [Regional height/button handoff](enclosure/r1-height-handoff.md) records the accepted 3.4 mm battery and 0.25 mm ferrite assumptions. Thickness/button work is deferred; the active case remains **5.8 mm**. Its old wire/ferrite service bodies need revision for the new pads.

## R1 file index

| Entry | Purpose |
| --- | --- |
| [Native EDA project](../../eda/NFC-Card-R1.eprj2) | Primary editable source: one PCB and one four-page schematic |
| [Ring and clearance R2 candidate](hardware/production/r1-free-0p30-sense-ring-r2/README.md) | 最新独立工程、Gerber/BOM/CPL、本地验证与新版线上 DFM；不可投产 |
| [R3 layout reset trial](hardware/production/r1-power-relayout-r3/README.md) | 独立重排与诊断导出；小孔和供电回路待解决，不可下单 |
| [R4 placement-first trial](hardware/production/r1-layout-reset-r4/README.md) | 独立工程、元件摆位与重开记录；旧走线未重布，不可下单 |
| [Previous battery-sensing cost candidate](hardware/production/r1-free-0p30-sense/README.md) | 前版线上 DFM 与薄孔环诊断基线 |
| [Manufacturing files](hardware/production/r1/README.md) | Gerber for bare PCB; BOM and CPL for assembly; PDF, STEP and portable EDA backup |
| [Design and verification](hardware/pcb-r1-delivery.md) | Design decisions, checks, limits and reproduction commands |
| [USB/SWD recovery](hardware/r1-usb-swd-recovery.md) | Electrical checks, UF2/CDC plan, clip dimensions and selected SWD recovery |
| [Design inputs](hardware/r1-design.json) | PCB, screen, flex, battery and enclosure dimensions |
| [Clear enclosure](enclosure/README.md) | Editable CAD, assembled STEP and printable tray/lid/three-key meshes |
| [Evidence](hardware/records/r1-validation.json) | Saved DRC, netlist, physical copper, winding and export checks |
| [Scripts](scripts/README.md) | Current export, verification and package commands |
| [Progress](docs/progress.md) | Remaining engineering and physical work |
| [Complete local ZIP](artifacts/NFC-Card-R1-prototype.zip) | Rebuildable handoff containing PCB, CAD and checks; do not upload it as a Gerber ZIP |
| [Historical archive](archive/README.md) | E-series designs, experiments, old indexes and migration map |

## Physical validation still required

- Measure the complete protected battery, sealed edges and wires against the assumed 32.5 × 14 × 3.4 mm envelope.
- Fit the fully inserted display flex, printed enclosure, keys and USB plug; check screen-to-aperture alignment and adhesive retention.
- Bring up the assembled PCB and tune NFC with the final screen and enclosure. C23/C24 = 220 pF is provisional.

[Bench experiments](docs/nfc-bench-test.md) and [firmware](firmware/pn532_probe/) are separate from production-board qualification. No order has been placed.
