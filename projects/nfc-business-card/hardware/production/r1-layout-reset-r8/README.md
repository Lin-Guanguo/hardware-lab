# R8：重叠丝印清理候选

## 当前确定方案

[R8 独立工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R8.eprj2)从 [R7](../r1-layout-reset-r7/README.md)导入，只隐藏顶层实物丝印中与焊盘过近的 U4、U5、U6、L1、R21、R23、Q2、Q3 位号。其他位号、按钮与接口标识、B+/B- 极性及背面 SWD 标识保留；器件位号仍在工程和装配资料中。未移动器件、过孔、布线、板框或天线。

保存后的原生 DRC 为 **0 条**。[R7/R8 Gerber 比较](../../records/r1-layout-reset-r8-gerber-compare.json)表明铜层、钻孔、板框、阻焊、钢网和底层丝印在导出精度内等价，顶层丝印改变，所以比较文件的整体 `ok` 为 `false`；BOM/CPL 与 R7 逐字节相同。按 [Gerber 丝印笔画与焊盘铜边的近似审计](../../records/r1-layout-reset-r8-dfm-preflight.json)，顶层**文字**笔画小于 0.13 mm 的数量从 R7 的 89 降为 0；顶层**封装外框**仍有 96 段小于 0.13 mm，其中 21 段触及焊盘铜边。该计算按铜边而非阻焊开窗，且不等于供应商线上告警数量。

R8 Gerber 已于 2026-09-25 17:11 上传到嘉立创 DFM“我的文件”；网页显示文件条目，但本次浏览器操作未打开其分析结果，**没有新版线上 PCB/SMT 结论**。BOM/CPL 尚未上传到 R8 在线任务，未下单或付款。R7 的孔环、VIA 孔到焊盘、阻焊、USB 槽和 J1/U1 装配危险仍按[原线上记录](../r1-layout-reset-r7/vendor-dfm-2026-09-25.md)待处理，R8 **不能投产**。

## 同版文件与下一步

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R8-gerber.zip)，SHA-256 `c0f7f154d1d7027a285dc063fdb7fa053e64180de249e5b0b2669f38bf556001`；[BOM](NFC-Card-R1-Layout-Reset-R8-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R8-cpl.csv)。
- [R7/R8 本地审计](../../records/r1-layout-reset-r7-dfm-preflight.json)记录 13 个同网过孔孔壁距焊盘铜边 <0.10 mm，R8 尚未移动这些孔。先逐点避开焊盘且保持短回流和保护拓扑，再重跑原生 DRC、独立连通及制造包检查。
- 复核 96 段封装外框靠近焊盘的实物丝印，优先删除会被阻焊开窗截断的非功能性外框，保留器件方向和极性标记。重新导出并核对顶、底层丝印。
- 打开 R8 嘉立创 DFM 任务并核对丝印、孔环、阻焊、USB 槽，再上传同版 BOM/CPL 复核 SMT；供应商人工确认剩余制造与装配项后才能考虑下单。
