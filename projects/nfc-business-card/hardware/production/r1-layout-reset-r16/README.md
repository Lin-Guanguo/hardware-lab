# R16：USB 缺口几何诊断

## 当前确定方案

[R16 独立原生工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R16.eprj2)只用于验证 USB4500 缺口加宽后的板框关系，**不可下单**。以 R15 工程为输入，把缺口最窄宽改为约 **9.20 mm**、内角半径改为 **R0.20 mm**；连接器、走线、过孔、天线和器件未移。R15 的 J1 焊盘位移没有持久写入工程，所以 R16 重开后仍是 R14 的 J1 焊盘坐标，不能把 R16 当作“焊盘修正＋缺口加宽”的组合候选。

[GCT USB4500 图纸](https://gct.co/connector/usb4500)的推荐缺口宽为 **9.24±0.05 mm**，连接器本体宽约 **8.94 mm**。9.20 mm 只是名义宽度落在推荐区间内；板厂外形公差、R0.20 内角可加工性及实体装配余量仍未确认。R16 的[线上 PCB／SMT DFM](vendor-dfm-2026-09-25.md)没有清除 J1 装配危险。

## 同版文件与检查

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R16-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R16-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R16-cpl.csv)与保存重开的工程对应；BOM 29 组、CPL 66 个位号。
- 重开后[原生 DRC](../../records/r1-layout-reset-r16-native-drc.json)为 **0 条**；[铜箔连通](../../records/r1-layout-reset-r16-copper-check.json)、[NFC](../../records/r1-layout-reset-r16-nfc-check.json)、[异网间距](../../records/r1-layout-reset-r16-clearance-audit.json)、[板框与槽](../../records/r1-layout-reset-r16-profile-check.json)及[制造包校验](../../records/r1-layout-reset-r16-validation.json)通过。过孔最小钻孔约 **0.30 mm**、最小径向孔环 **0.1016 mm**；离散铜对象未发现 <0.15 mm 的异网配对。
- 检查通过只说明导出几何与既有电连接未恶化，不能确认连接器真实可装、PCB 锣边公差或 SMT 贴装。

## 下一步

从原厂推荐封装重建可持久保存的 J1 焊盘与板框基准，保存重开后确认每个焊盘的坐标。完成两层 USB 局部走线评审，再重新导出并跑原生 DRC、独立连通、机械检查及线上 PCB／SMT DFM。R14 仍是当前可复现的制造审核基线，尚未获投产放行。
