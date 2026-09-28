# R6：USB CC2 保护拓扑与间距修正

## 当前确定方案

[R6 独立工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R6.eprj2)从 R5 派生，将 USB CC2 的后级过孔移至 `(74.10,25.75)` mm，并只将数据保护件 U5 下移 0.02 mm 以保留相邻异网铜间距；USB 连接器、U6、天线、板框未动。一个中间试验曾绕过 U6 保护端，被独立断线检查发现并废弃；交付版的 CC2 保护拓扑检查通过。移动 U5 后 J1–U5 中心距约 5.267 mm，U5 到接地过孔约 0.919 mm，3 mm 内接地过孔数仍为 6。该位置证据仅用于本版几何评审，尚未实测 USB ESD 性能。

保存重开后原生 DRC 0，独立连通、NFC、0.15 mm 异网铜间距、板框与四槽检查通过；167 个过孔的最小实际钻孔约 0.30 mm，最小径向孔环 0.1016 mm。[本地验证](../../records/r1-layout-reset-r6-validation.json)与同版[Gerber](NFC-Card-R1-Layout-Reset-R6-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R6-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R6-cpl.csv)留作对照。

[线上 PCB/SMT DFM](vendor-dfm-2026-09-25.md)显示 R5 新增的焊盘距焊盘危险消失，但 U1 焊脚到孔仍有 2 条，其他孔环、槽、阻焊和贴片模型危险未消除。R7 已针对 U1 孔位继续修正；R6 不用于下单。
