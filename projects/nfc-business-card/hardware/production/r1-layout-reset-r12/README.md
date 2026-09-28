# R12：同网过孔局部移位候选

## 当前确定方案

[R12 独立工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R12.eprj2)从已保存的 [R10](../r1-layout-reset-r10/README.md)原生工程导出并重新导入，保留其顶层丝印清理。只将 R2 附近 GND 过孔及 Q2 附近 BAT_PACK_TBD 过孔各移约 0.18／0.13 mm，调整相连的短线并重新铺铜；器件、焊盘、板框、天线、USB 保护拓扑均未改动。[可复现编辑脚本](../../../scripts/eda-r12-move-vias.js)记录了图元 ID 和旧／新坐标。中途 R11 试验误用了旧的 R10 临时导出，丝印回退，因此未作为候选交付；R12 已从 R10 原生工程重新建立并核对丝印。

保存、关闭、重开后原生 DRC **0 条**；独立连通、NFC 回路、板框／四个 USB 槽和 CC2 保护断开检查通过。167 个过孔最小实际钻孔约 **0.30 mm**，最小径向孔环 **0.1016 mm**；本地对象审计未发现 <0.15 mm 的异网铜间距。同网过孔孔壁到焊盘铜边 <0.10 mm 的不同过孔 **10→8**，压入焊盘铜边的 **2→0**。R10 的丝印清理仍在：顶层封装线段触及焊盘铜边为 0。

[嘉立创 R12 PCB/SMT DFM](vendor-dfm-2026-09-25.md)已完成：PCB 的孔落在焊盘上警告 **4→0**，VIA 孔到焊盘危险 **24→20**；孔环 100、阻焊桥 43、USB 槽 4 及 J1/U1 装配危险仍在。**R12 不是可直接投产文件；未下单或付款。**

## 同版文件与检查

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R12-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R12-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R12-cpl.csv)均从 R12 原生 PCB 导出；66 个 CPL 位号、29 组 BOM 与 R10 一致。
- [完整校验](../../records/r1-layout-reset-r12-validation.json)、[原生 DRC](../../records/r1-layout-reset-r12-native-drc.json)、[独立铜箔连通](../../records/r1-layout-reset-r12-copper-check.json)、[间距审计](../../records/r1-layout-reset-r12-clearance-audit.json)、[NFC](../../records/r1-layout-reset-r12-nfc-check.json)、[板框与槽](../../records/r1-layout-reset-r12-profile-check.json)、[布局审查](../../records/r1-layout-reset-r12-layout-review.json)。

## 下单前处理

1. 继续逐点检查剩余 8 个同网近焊盘过孔；优先可局部移孔、短线的位置，不移动 USB 保护、去耦或侵入天线净空。网站的阻焊、孔环和丝印告警须按真实 Gerber 复核，不能用本地 DRC 代替。
2. 对照 J1 原厂图纸和实际封装核实 0.60 mm 镀铜槽、焊脚／焊盘模型、贴片坐标；核实 U1 模块边界距板边 0.07 mm 及拼板工艺边。请嘉立创工程师书面确认能否制板、贴片和所需工艺。
3. 取得缺料清单、可接受替代及 PCB＋SMT 完整报价后，由用户确认表面工艺、费用和是否下单。
