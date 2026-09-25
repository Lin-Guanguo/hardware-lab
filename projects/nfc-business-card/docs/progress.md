# R1 progress

## 当前确定方案

2026-09-25：[R17 USB4500 封装诊断](../hardware/production/r1-layout-reset-r17/README.md)从 R16 独立导出项目，在封装主数据里把 J1 的 12 个 SMT 焊盘中心从 113.2 改为 101.4 mil；导入、保存、关闭重开后位置保持。原生 DRC 新增 **12 条 J1 焊盘到缺口边缘错误**；独立连通、0.30 mm 钻孔、≥0.1016 mm 径向孔环、离散异网 0.15 mm 间距及板框／槽几何检查通过。[嘉立创 PCB／SMT DFM](../hardware/production/r1-layout-reset-r17/vendor-dfm-2026-09-25.md)的 VIA 孔到焊盘危险 12→6、焊盘距外型线危险 0→12；BOM 29/29 组匹配。J1 焊脚接触比约 0.35→0.50，但 **12 条 SMT 危险仍在**。下一步先按 GCT 图纸统一焊盘／槽／缺口／CPL 基准，明确这处板边铜是否符合普通制造与装配，再重布 USB；**R17 不可下单，R14 仍是 DRC 0 审核基线**。

2026-09-25：按七个功能区整理了[器件原厂参考与重排门槛](../hardware/r1-seven-zone-reference-plan.md)。USB、充电／稳压、屏幕供电、主控天线各有不能为整齐而打散的局部关系；按键和普通控制线有更多排布自由度。此前单焊盘 API 试验只改变实时坐标，未持久写入；R17 改为修改封装主数据并经重开验证。

2026-09-25：[R16 USB 缺口诊断](../hardware/production/r1-layout-reset-r16/README.md)把缺口最窄宽加至约 9.20 mm、内角 R0.20 mm，重开工程后原生 DRC 0、独立连通／NFC／间距／板框／钻孔检查通过。[线上 PCB／SMT DFM](../hardware/production/r1-layout-reset-r16/vendor-dfm-2026-09-25.md)显示焊盘距外型线危险 0，但 J1 接触比仍约 0.35、12 条装配危险未消；孔环、阻焊和槽宽问题仍在。R0.20 加工及装配公差尚未确认，**不可下单**。[双层中置接口参考](../hardware/usb-mid-mount-two-layer-references.md)已整理。

2026-09-25：[R15 USB4500 焊盘诊断](../hardware/production/r1-layout-reset-r15/README.md)当次 Gerber 将 12 个信号焊盘位移 0.29972 mm，[线上 DFM](../hardware/production/r1-layout-reset-r15/vendor-dfm-2026-09-25.md)显示 J1 接触比约 0.35→0.50，同时出现 12 条焊盘到缺口边 0 mm 危险。**事后重开原生工程发现焊盘位移未保存**，当次 Gerber 无法由保存工程复现；先修封装持久化，R15 仅作敏感性诊断，不下单。

2026-09-25：[R14 独立候选](../hardware/production/r1-layout-reset-r14/README.md)在 R12 上只移动 R1、C1、C8 和 SWDIO 附近四个过孔及短线；R13 的 R7 移孔因产生新焊盘间距危险已撤销。原生工程保存重开后 DRC 0；独立连通、NFC／板框、约 0.30 mm 钻孔、≥0.10 mm 径向孔环与异网 0.15 mm 间距检查通过。本地同网孔到焊盘薄间距的不同过孔 **8→4**；[嘉立创 PCB/SMT DFM](../hardware/production/r1-layout-reset-r14/vendor-dfm-2026-09-25.md)的 VIA 孔到焊盘危险 **20→12**，BOM **29/29** 组匹配。孔环 100、阻焊桥 43、USB 四槽、J1 焊脚相交 12 和 U1 板边 0.07 mm 危险仍在；[根因复盘](../hardware/production/r1-layout-reset-r14/dfm-root-cause-review-2026-09-25.md)将其归并为固定封装、局部过孔及线上图元／贴片模型问题，下一步先做原厂封装和成品层复核，**不下单**。

2026-09-25：[R12 独立候选](../hardware/production/r1-layout-reset-r12/README.md)从 R10 原生工程重新建立，只移动 R2、Q2 附近两孔和相连短线，保留 R10 顶层丝印。保存重开后原生 DRC 0；独立连通、NFC／板框、0.30 mm 钻孔、≥0.10 mm 径向孔环与异网 0.15 mm 间距检查通过。同网过孔压入焊盘 **2→0**；[嘉立创 PCB/SMT DFM](../hardware/production/r1-layout-reset-r12/vendor-dfm-2026-09-25.md)确认孔落焊盘警告 **4→0**、VIA 孔到焊盘危险 **24→20**，BOM 29/29 组匹配；孔环 100、阻焊桥 43、USB 四槽、J1 焊脚相交 12 和 U1 板边 0.07 mm 危险仍在，供应商未确认，**不下单**。

2026-09-25：[R10 独立候选](../hardware/production/r1-layout-reset-r10/README.md)从 R9 导入，只清理顶层封装外框，保留 D1–D3 阴极标记；铜、孔、装配、板框和天线不变。修正 Gerber 填充边界误计后，顶层外框触及焊盘线段 **3→0**，距焊盘 <0.13 mm 的线段 **78→68**。原生 DRC 0、独立连通、NFC／板框、0.30 mm 钻孔、≥0.10 mm 径向孔环检查通过。R10 Gerber/BOM/CPL 已上传嘉立创，29/29 组器件自动匹配；PCB DFM 的 VIA 孔到焊盘危险为 24，孔环 100、阻焊桥 43、USB 四槽等危险仍在。SMT DFM 后续返回 J1 焊脚相交 12 和 U1 板边 0.07 mm 危险，**不下单**。

2026-09-25：[R9 独立候选](../hardware/production/r1-layout-reset-r9/README.md)继承 R8 丝印清理，只移动 R15、Q3、R1 附近的 3 个 GND 过孔及短线。本地同网孔壁到焊盘铜边 <0.10 mm 的不同过孔 13→10，压入焊盘 4→2；保存重开的原生 DRC 0，独立连通、NFC/板框、0.30 mm 钻孔、≥0.10 mm 径向孔环和 0.15 mm 异网间距检查通过。Gerber 已上传嘉立创“我的文件”，线上结果页未打开，BOM/CPL 尚未上传到该任务；剩余孔距、封装外框丝印、孔环、阻焊、USB 槽及 J1/U1 装配危险待复核，**不下单**。

2026-09-25：[R8 独立丝印候选](../hardware/production/r1-layout-reset-r8/README.md)从 R7 导入，在顶层实物丝印隐藏 U4、U5、U6、L1、R21、R23、Q2、Q3 八个位号；保留装配资料中的位号及板上接口、极性标记。保存后的原生 DRC 0；Gerber 导出对比确认除顶层丝印外的制造层在导出精度内与 R7 等价。本地顶层文字距焊盘 <0.13 mm 的笔画 89→0，封装外框仍有 96 段过近。R8 Gerber 已上传嘉立创“我的文件”，线上结果页尚未打开，孔环、孔到焊盘、阻焊、USB 槽和 J1/U1 装配风险仍待处理；**不下单**。

2026-09-25：[R7 独立候选](../hardware/production/r1-layout-reset-r7/README.md)继承 R4 的显示供电分区及 R5/R6 的 C9、USB CC2 修正，最终只移动 U1 附近一颗 GND 过孔及其短线。保存重开后原生 DRC 0；独立铜箔连通、CC2 保护断线、NFC/板框、Gerber 钻孔与孔环、同版 BOM/CPL 检查通过。167 个过孔最小实际钻孔约 0.30 mm、最小径向孔环 0.1016 mm，异网铜对象无 <0.15 mm 配对。[R7 线上 PCB/SMT DFM](../hardware/production/r1-layout-reset-r7/vendor-dfm-2026-09-25.md)确认 U1 焊脚到孔 2→0 条危险，VIA 孔到焊盘 32→30 条；孔环 100、阻焊桥 43、USB 四槽、J1 焊脚重叠 12、U1 板边 1 等危险未消除。下一步按实物图纸和供应商工艺规则逐点处理及确认，**不下单**。

2026-09-25：[R4 初版](../hardware/production/r1-layout-reset-r4/README.md)完成显示供电区 15 个器件成组重排及布线，但线上 DFM 发现 C9 孔位、盘到线、PTH 孔到线危险；[R5](../hardware/production/r1-layout-reset-r5/README.md)消除这些新增危险但 CC2 焊盘间距回退，[R6](../hardware/production/r1-layout-reset-r6/README.md)修正 CC2 并确认保护拓扑，R7 继续修正 U1 孔位。各版独立工程和制造包保留用于回溯。

2026-09-24：[R2 独立候选](../hardware/production/r1-free-0p30-sense-ring-r2/README.md)在原电池采样候选上完成局部移孔和重布线，保留敏感器件、板框与天线不动。重开原生 DRC 0；最小钻孔 0.30226 mm、最小径向孔环 0.1016 mm；走线/焊盘/过孔异网间距审计未发现 <0.15 mm。Gerber/BOM/CPL 已从同一工程导出，本地独立连通、NFC、板框、四槽及 66/66 位号检查通过。[新版线上 PCB/SMT DFM](../hardware/production/r1-free-0p30-sense-ring-r2/vendor-dfm-2026-09-24.md)走线间距警告由 12 降至 1，盘到线及 PTH 孔到线危险清零；但孔环危险仍显示 100，VIA 孔到焊盘危险增至 32，SMT 新增 U1 焊脚到孔 2 条危险，J1/U1 原有问题未变。需继续局部处理和人工审核；原 R1 制造基准未变，未下单。

2026-09-24：[R3 独立重排试验](../hardware/production/r1-power-relayout-r3/README.md)将显示供电区与 USB/充电区分开，保留电池采样。66/66 引脚、重开原生 DRC、独立铜箔连通、屏幕/NFC 净空及 0.15 mm 异网间距在旧规则下本地检查通过。**自动布线产生 54 个约 0.25 mm 孔**；仅扩大至 0.30 mm／0.51 mm 外径的离线试验又有 29 对 <0.15 mm 的间距。当前工程已把过孔内径最小/默认设为 0.30 mm、外径最小/默认设为 0.50/0.55 mm；原生 DRC 据此报 54 条过孔尺寸错误。另已在嘉立创 EDA 保存同尺寸的双面板规则为新建 PCB 默认配置。命名焊盘复核发现 L1-1 到 C10-1 从 3.04 增至 7.37 mm，C11-1 到 L1-2 从 4.40 增至 10.29 mm，显示供电相对摆位需重做。本版标为布局起点与失败工艺试验，未送供应商 DFM，不可投产；R2 仍是低成本候选。下一步先优化敏感器件相对摆位，再以 0.30 mm 孔和 0.15 mm 目标约束布线。

[R2 线上 DFM 记录](../hardware/production/r1-free-0p30-sense-ring-r2/vendor-dfm-2026-09-24.md#接下来的处理顺序)列明下一步：先处理 U1 焊脚到孔与过孔贴近焊盘，再请工厂按实际 Gerber/器件图纸核实孔环、J1 槽和贴片模型、U1 工艺边。危险和费用未明确前不合入主分支作为制造版。

2026-09-24: checkpoint `ccf9f92` is committed. The [subsequent antenna/layout review](../hardware/pcb-r1-review.md) and battery-pad changes are saved in checkpoint `bee8846` at the user's request, alongside the separate enclosure studies. The subsequent drill/USB/routing review and 2.54 mm SWD/CAD synchronization are included in the current repository checkpoint at the user's request.

| Work | Status / next step |
| --- | --- |
| Source and file organization | R1 active files indexed; E-series history archived; manufacturing outputs tracked |
| Existing electrical checks | Saved/reopened native DRC 0; 58 components, 238 schematic pins matched; copper connectivity and winding cut proof pass |
| Screen protrusion perimeter | Corrected: no pours through the three exposed board edges; selected top B pads/routes are a narrow recorded exception |
| Coil appearance and edge offsets | Complete: five turns, 45° chamfers, equal 3 mm centreline offsets |
| Broader layout review | Review complete; CC2 branch corrected, exports refreshed. C1/C8 assignment corrected; no relocation required. Six nominal 0.2 mm drills eliminated; two GND stitches added, reducing worst USB via proximity from 3.66 to 2.62 mm. [DFM, assembly and remaining tests](../hardware/r1-preorder.md). |
| Control routing cleanup | CE 6 → 4 vias, 39.56 → 32.98 mm; SCL remains four vias and grows 1.70 mm. This step had 818 segments / 153 vias; the subsequent SWD adaptation has 819 / 153. Saved/reopened DRC and independent checks pass. |
| USB/SWD recovery | R3/R4 corrected to 0 ohm / C21189. [Hardware and recovery review](../hardware/r1-usb-swd-recovery.md): firmware and real USB tests pending; 2.54 mm 5P lands and cover access implemented under user-accepted generic clip assumptions; physical trial fit pending. User selected SWD programmer recovery on 2026-09-24; no hidden RESET switch or opening will be added for R1. |
| Enclosure | Nominal fit and meshes pass; physical assembly unverified |
| Packaging optimization | [Height handoff](../enclosure/r1-height-handoff.md) records regional heights and key motion. User deferred thickness/button process; active case remains 5.8 mm. |
| Battery B pads | Applied at (32.5,18.7)/(35.5,18.7) mm for upper-right lead exit; native DRC and copper checks pass. Frozen CAD wire/ferrite service volumes need later revision. |
| Redundant vias | Removed BAT/CC2/3V3 single-layer vias and one dead stub; all remaining vias contact copper on both faces. Audit rejects an injected redundant via. |
| RF and bring-up | User/agent must test the assembled board; provisional 220 pF tuning capacitors |
| 0.30 mm 低成本候选 | 改 TS 前的 Gerber 已完成[线上 DFM 任务 DFMP2609240514](../hardware/production/r1-free-0p30/vendor-dfm-2026-09-24.md)。孔环、镀铜槽、阻焊桥和 J1 SMT 告警尚未关闭；¥30 仅为裸板参数试算。制造前需在新版本补 TS/MR 10 kΩ 到地。供应商未正式接受，未下单。 |
| 0.30 mm＋电池采样前版 | [独立工程与文件](../hardware/production/r1-free-0p30-sense/README.md)已补 TS/MR 及采样；[线上 PCB/SMT DFM](../hardware/production/r1-free-0p30-sense/vendor-dfm-2026-09-24.md)完成，29 组器件匹配。薄孔环、槽、铜/阻焊、J1/U1 危险未关闭；其扩大孔环诊断 DRC 24，已由 R2 局部重布承接。 |
| R2 孔环与间距候选 | [独立工程与文件](../hardware/production/r1-free-0p30-sense-ring-r2/README.md)的本地检查通过，最小钻孔 0.30226 mm、最小径向孔环 0.1016 mm；独立对象间距审计无 <0.15 mm。[线上 PCB/SMT DFM](../hardware/production/r1-free-0p30-sense-ring-r2/vendor-dfm-2026-09-24.md)仍报孔环 100、VIA 到焊盘 32、U1 焊脚到孔 2、J1 焊脚重叠 12 条危险；需继续局部修改与工厂人工审核，不能作为下单包。 |
| R3 功能区重排 | [独立工程与预览](../hardware/production/r1-power-relayout-r3/README.md)已保存。电池采样保留，USB 保护/主控去耦/屏幕/NFC 未挪；本地几何连通检查通过。54 个小钻孔及显示供电回路扩大阻止其成为制板版；先做按工艺约束的下一轮布线。 |
| R4 已布线重排 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r4/README.md)已保存、重开；本地 DRC、连通、孔环与 0.15 mm 异网对象间距检查通过。[线上 PCB/SMT DFM](../hardware/production/r1-layout-reset-r4/vendor-dfm-2026-09-24.md)显示新增 C9 孔位、盘到线和 PTH 孔到线危险，另有孔环、J1/U1 和阻焊风险；下一版先局部修复，不可下单。 |
| R5／R6 局部修正 | [R5](../hardware/production/r1-layout-reset-r5/README.md)消除 C9 和部分 CC2 新危险；[R6](../hardware/production/r1-layout-reset-r6/README.md)修正 CC2 回退并完成线上 PCB/SMT 对照，U1 焊脚到孔仍有 2 条危险；保留对照，不可下单。 |
| R7 DFM 基线 | [同版工程与文件](../hardware/production/r1-layout-reset-r7/README.md)本地检查通过，[线上 DFM](../hardware/production/r1-layout-reset-r7/vendor-dfm-2026-09-25.md)确认 U1 焊脚到孔危险 0；孔环、过孔到焊盘、阻焊、四槽、J1/U1 模型危险仍待处理和工厂审核，不可下单。 |
| R8 丝印候选 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r8/README.md)已保存，原生 DRC 0，8 个过近顶层位号已隐藏；文字到焊盘近距笔画 89→0，封装外框与其他 DFM 危险仍待处理。Gerber 已上传，线上结果尚未读取，不可下单。 |
| R9 过孔局部修正 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r9/README.md)已保存并重开，原生 DRC 0；同网薄孔到焊盘 13→10，压入焊盘 4→2。Gerber 已上传，线上 PCB/SMT 结果尚未读取；继续局部处理并请供应商审核，不可下单。 |
| R10 顶层封装丝印 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r10/README.md)已保存，原生 DRC 0；修正审计器后触及焊盘铜边的丝印线段 3→0。线上 PCB/SMT DFM 仍有孔环、过孔到焊盘、阻焊、四槽及 J1/U1 装配危险，不可下单。 |
| R12 两孔局部修正 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r12/README.md)已保存重开，原生 DRC 0；孔落焊盘警告清零、过孔到焊盘危险 24→20。线上 PCB/SMT 仍报孔环、阻焊、四槽及 J1/U1 危险，待进一步局部修改与供应商审核，不可下单。 |
| R14 四孔局部修正 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r14/README.md)已保存重开，原生 DRC 0；过孔到焊盘危险 20→12，焊盘间距危险未增加。线上 PCB/SMT 其余危险列入供应商审核清单，不可下单。 |
| R15 USB 封装诊断 | [实时文件与线上 DFM](../hardware/production/r1-layout-reset-r15/README.md)显示焊盘位移会提高网站 SMT 接触比，但改动未持久保存到原生工程；不作为下单包。 |
| Battery | User measures protected pack and wires; nominal 31 × 12 × 3 mm |

No order placed. [Historical progress and experiments](../archive/pre-r1/readmes/projects/nfc-business-card/docs/progress.md) retain earlier findings and resolutions.
