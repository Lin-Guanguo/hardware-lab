# R1 progress

## 当前确定方案

2026-09-24：独立 [0.30 mm＋电池采样候选](../hardware/production/r1-free-0p30-sense/README.md)补齐 TS/MR 电阻和直接电池 ADC 采样，原生 DRC、独立连通、NFC/板框及 Gerber 检查通过；[新版线上 DFM 任务 DFMP2609240604](../hardware/production/r1-free-0p30-sense/vendor-dfm-2026-09-24.md)再次暴露孔环、USB 镀铜槽、阻焊和 J1/U1 贴装危险。全部扩大薄孔环的诊断由 64 条 DRC 降至 24 条，仍未得到可投产的孔环修订版。继续局部重布并重新 DFM；原 R1 制造基准未变，未下单。

[下一步按屏幕供电、USB 扇出、充电/全板间距、全量验证、供应商复查推进](../hardware/production/r1-free-0p30-sense/next-steps.md)；每区有明确通过条件，未完成前不合入主分支作为制造版。

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
| 0.30 mm＋电池采样新版 | [独立工程与文件](../hardware/production/r1-free-0p30-sense/README.md)已补 TS/MR 及采样；[线上 PCB/SMT DFM](../hardware/production/r1-free-0p30-sense/vendor-dfm-2026-09-24.md)完成，29 组器件匹配。孔环、槽、铜/阻焊、J1/U1 危险未关闭；整体扩孔环试验剩 24 条 DRC。下一步局部移孔/改线，核实器件实物封装，再以修订版重跑全部检查和工厂审核。 |
| Battery | User measures protected pack and wires; nominal 31 × 12 × 3 mm |

No order placed. [Historical progress and experiments](../archive/pre-r1/readmes/projects/nfc-business-card/docs/progress.md) retain earlier findings and resolutions.
