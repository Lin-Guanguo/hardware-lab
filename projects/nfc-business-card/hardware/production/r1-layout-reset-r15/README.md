# R15：USB4500 信号焊盘位移诊断

## 当前确定方案

[R15 独立原生工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R15.eprj2)继承 [R14](../r1-layout-reset-r14/README.md)。实验时按 GCT `USB4500-03-0-A` 原厂推荐 PCB 图，在 EDA 实时会话中把 J1 的 12 个信号焊盘相对四槽移动 **0.29972 mm**。该改动出现在当次 Gerber 和线上 DFM 中，**却未写入保存后重新打开的原生工程**：重新读取时 12 个焊盘恢复到 R14 坐标。顶层禁止铺铜区保存了，焊盘位移没有保存。因此此目录的制造文件与原生工程在 J1 焊盘几何上不一致，不能作为可复现工程或交付文件。

当次 [线上 PCB／SMT DFM](vendor-dfm-2026-09-25.md)显示接触比改善但仍报 12 条 SMT 危险，并新增 12 条信号焊盘到锣边 **0 mm** 危险。四个 **0.60 mm** 镀铜槽未改。这些数字仅用于判断几何敏感性；R15 **不可下单**，尚未下单或付款。

## 同版文件与检查

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R15-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R15-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R15-cpl.csv)取自当次实时会话；BOM 29 组、CPL 66 个位号。Gerber 的 J1 焊盘与重新打开的原生工程不一致。
- [原生 DRC](../../records/r1-layout-reset-r15-native-drc.json)当次为 **0 条**；[独立铜箔连通](../../records/r1-layout-reset-r15-copper-check.json)、[NFC](../../records/r1-layout-reset-r15-nfc-check.json)、[板框和镀铜槽](../../records/r1-layout-reset-r15-profile-check.json)、[异网间距审计](../../records/r1-layout-reset-r15-clearance-audit.json)和[完整校验](../../records/r1-layout-reset-r15-validation.json)仅验证了当次导出状态，不能证明原生工程重开后仍保持相同焊盘几何。
- GCT 原厂依据：[USB4500 产品页及下载图纸](https://gct.co/connector/usb4500)。本仓库保存的原厂图纸为 `projects/nfc-business-card/downloads/usb4500-drawing.pdf`；R15 对照外侧镀铜槽中心和信号焊盘两端的名义尺寸。

## 下一步

先在封装主数据或受支持的实例覆盖机制中持久修正 J1 焊盘，保存重开后重测坐标，再按 GCT 图纸核对缺口与器件包络。R15 缺口最窄约 **8.64 mm**，原厂推荐 **9.24 mm**、本体宽 **8.94 mm**；机械干涉尚待验证。R15 **不可下单**。
