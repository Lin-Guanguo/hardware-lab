# R5：C9 与 USB CC2 局部修正记录

## 当前确定方案

[R5 独立工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R5.eprj2)从 R4 派生，移开 C9 焊盘内的 VDD_3V3 过孔，并局部修改 USB CC2。保存重开后的原生 DRC、独立连通、NFC、板框及 Gerber 钻孔检查通过，最小实际钻孔约 0.30 mm、径向孔环 0.1016 mm，异网铜对象间距审计无小于 0.15 mm 的配对。[线上 PCB DFM](vendor-dfm-2026-09-25.md)证实 R4 新增的盘到线、PTH 孔到线危险归零，但新的 CC2 过孔使焊盘距焊盘危险从 3 条增至 4 条；R5 保留为对照，不用于下单。R6 已修正这处回退。

同版文件：[Gerber](NFC-Card-R1-Layout-Reset-R5-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R5-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R5-cpl.csv)、[本地检查](../../records/r1-layout-reset-r5-validation.json)。SMT 上传虽匹配 29/29 组，该任务的 SMT 分析返回空白，不能解释为通过。
