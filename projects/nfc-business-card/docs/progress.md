# R1 progress

## 当前确定方案

2026-09-24：[R2 独立候选](../hardware/production/r1-free-0p30-sense-ring-r2/README.md)在原电池采样候选上完成局部移孔和重布线，保留敏感器件、板框与天线不动。重开原生 DRC 0；最小钻孔 0.30226 mm、最小径向孔环 0.1016 mm；走线/焊盘/过孔异网间距审计未发现 <0.15 mm。Gerber/BOM/CPL 已从同一工程导出，本地独立连通、NFC、板框、四槽及 66/66 位号检查通过。[新版线上 PCB/SMT DFM](../hardware/production/r1-free-0p30-sense-ring-r2/vendor-dfm-2026-09-24.md)走线间距警告由 12 降至 1，盘到线及 PTH 孔到线危险清零；但孔环危险仍显示 100，VIA 孔到焊盘危险增至 32，SMT 新增 U1 焊脚到孔 2 条危险，J1/U1 原有问题未变。需继续局部处理和人工审核；原 R1 制造基准未变，未下单。

2026-09-24：[R3 独立重排试验](../hardware/production/r1-power-relayout-r3/README.md)将显示供电区与 USB/充电区分开，保留电池采样。66/66 引脚、重开原生 DRC、独立铜箔连通、屏幕/NFC 净空及 0.15 mm 异网间距本地检查通过。**自动布线产生 54 个约 0.25 mm 孔**；仅扩大至 0.30 mm／0.51 mm 外径的离线试验又有 29 对 <0.15 mm 的间距。命名焊盘复核发现 L1-1 到 C10-1 从 3.04 增至 7.37 mm，C11-1 到 L1-2 从 4.40 增至 10.29 mm，显示供电相对摆位需重做。本版标为布局起点与失败工艺试验，未送供应商 DFM，不可投产；R2 仍是低成本候选。下一步先优化敏感器件相对摆位，再以 0.30 mm 孔和 0.15 mm 目标约束布线。

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
| Battery | User measures protected pack and wires; nominal 31 × 12 × 3 mm |

No order placed. [Historical progress and experiments](../archive/pre-r1/readmes/projects/nfc-business-card/docs/progress.md) retain earlier findings and resolutions.
