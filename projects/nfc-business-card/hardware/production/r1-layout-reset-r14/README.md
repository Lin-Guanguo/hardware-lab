# R14：四处过孔局部移位候选

## 当前确定方案

[R14 独立原生工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R14.eprj2)继承 [R12](../r1-layout-reset-r12/README.md) 的电路、器件位置、板框、天线净空和丝印，仅移动 R1、C1、C8 附近的同网过孔及 SWDIO 过孔，重接相连短线并重新铺铜。USB 保护和去耦器件没有移位。中间 R13 试验还移动了 R7 过孔，但线上出现新的焊盘间距高危；R14 已撤销该处改动，R13 不作为制造候选。

工程保存、关闭、重开后原生 DRC **0 条**。独立铜箔连通、NFC、板框和四个 USB 镀铜槽检查通过；167 个过孔最小实际钻孔约 **0.30 mm**，最小径向孔环 **0.1016 mm**，没有发现 <0.15 mm 的异网铜对象间距。同网过孔孔壁距焊盘铜边 <0.10 mm 的不同过孔 **8→4**，没有孔壁压入焊盘铜边。顶层丝印文字和封装线均未触及焊盘铜边。

[嘉立创 R14 PCB/SMT DFM](vendor-dfm-2026-09-25.md)已从本版 Gerber、BOM、CPL 完成：VIA 孔到焊盘危险 **20→12**，焊盘间距高危仍为 3；孔环、阻焊、USB 槽及 J1/U1 贴装告警未关闭。**这是一份可供供应商审核的候选，不是已获投产批准的文件；未下单或付款。**

## 同版文件与检查

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R14-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R14-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R14-cpl.csv)均来自 R14 原生工程；66 个 CPL 位号、29 组 BOM。
- [完整校验](../../records/r1-layout-reset-r14-validation.json)、[原生 DRC](../../records/r1-layout-reset-r14-native-drc.json)、[独立铜箔连通](../../records/r1-layout-reset-r14-copper-check.json)、[间距审计](../../records/r1-layout-reset-r14-clearance-audit.json)、[NFC](../../records/r1-layout-reset-r14-nfc-check.json)、[板框与槽](../../records/r1-layout-reset-r14-profile-check.json)、[布局审查](../../records/r1-layout-reset-r14-layout-review.json)。

## 下一步

先按 [DFM 根因与设计流程复盘](dfm-root-cause-review-2026-09-25.md)做原厂封装、成品 Gerber、CPL 和实物包络叠图。其余四个同网薄间距过孔中，J1、NFC 天线及 R7 区域不可只为消除计数而破坏连接器基准、天线或敏感电路。自检后只向供应商询问无法按公开规则确定的具体贴片可行性与费用；再由用户决定表面工艺、缺料替代、费用及是否下单。
