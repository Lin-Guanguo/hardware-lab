# NFC 名片硬件

## 当前确定方案

**2026-09-29 最新：A3 只作局部修复，必要地恢复，整板仍未完成。**入口：[A3 报告与前后实铜图](v4-option-a3-review.md)、[原生候选](kicad/v4-option-a3-local/README.md)。61 个地焊盘连通，GND 未连接 9→0，其它仍 7 项；ERC 0／parity 0，DRC 58。C25 ADC 与 CC 电阻组的局部改线、十处实铜地桥保留；破坏 C4 地的 TS/PG 方案撤回。连续几何证明当前 CC/BUSY/D− 出口围堵，但 CS 仍有连续通路，不能把网格失败当空间不足。下一步在命名局部组内共同处理控制、供电和信号返回；未继续整板自动布线，未执行最终 DFM。原生重开／增量重建已验证，电气、制造及回流待办未关闭。[A2 对照](v4-option-a2-review.md)、旧 A／失败板与 D、phase1/2/3 保留，采样和硬约束不变。

第二阶段对照为 [KiCad V4 phase2](kicad/v4-phase2/README.md)，联合通道、显示完整连接、原生检查和本版国内 DFM 见 [第二阶段报告](kicad-v4-phase2.md)，器件与电气输入见 [原厂核查](v4-design-inputs.md)。六根屏幕信号与 USB／供电已同版共存；SCK／USB 返回及 SWD 入口未通过，尚不具备整板详细设计或制造条件。保留 [第一阶段](kicad-v4-phase1.md)和冻结的 [D 工程](board-review-d.md)。下面是 R1 历史索引。

## R1 历史记录

Use the [R1 native project](../../../eda/NFC-Card-R1.eprj2) and [current project index](../README.md). The antenna/CC2 and battery-pad changes were checkpointed in `bee8846`. The [pre-order follow-up](r1-preorder.md) removes nominal 0.2 mm drills, improves USB stitching and corrects the C1/C8 service assignment. The CE/SCL reroute removes two vias; R3/R4 are corrected to 0 ohm. [USB/SWD recovery](r1-usb-swd-recovery.md) records the implemented 2.54 mm SWD row, physical clip trial fit, pending RESET decision and firmware tests. Vendor DFM and prototype tests remain open.

| Files | Purpose |
| --- | --- |
| [电路对照评审](r1-circuit-reference-review.md) | NTC 装配、屏幕电容规格、供电与关断验证，以及 muxcard 对照 |
| [production/r1/](production/r1/README.md) | Frozen vendor exports and portable project |
| [pcb-r1-delivery.md](pcb-r1-delivery.md) | Current engineering report and checks |
| [r1-design.json](r1-design.json) | Coordinated dimensional inputs |
| [records/r1-validation.json](records/r1-validation.json) | Consolidated verification; other `r1-*` files hold inputs and detailed evidence |
| [candidate-bom.md](candidate-bom.md), [component-options.md](component-options.md) | Component selection rationale; the exported BOM is authoritative for R1 |
| [battery-purchase-candidates.json](battery-purchase-candidates.json) | Purchased battery candidates and measurement uncertainty |
| [Historical hardware](../archive/pre-r1/hardware/) | E-series snapshots, placement studies and old manufacturing gates |

The native project is editable design data. Gerber describes board artwork and drilling; it does not contain the complete editable design, firmware or enclosure.
