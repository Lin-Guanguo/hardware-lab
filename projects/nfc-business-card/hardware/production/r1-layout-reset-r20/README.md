# R20：过孔到焊盘间距候选

## 当前确定方案

[独立原生工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R20-Via-Clearance.eprj2)从 [R19 USB4110 同步版](../../r1-usb4110-sync-r19.md)复制。只移动 C23、R7/R9、NFC2 附近三个过孔及其相连短线，分别约 0.11、0.025、0.10 mm；器件、焊盘、USB 接口、板框和天线没有移动。R18B 线上 DFM 的“VIA 孔到焊盘”6 条危险对应本地三处同网孔壁近焊盘，本次以消除这三处为目标。**线上 R20 DFM 结果尚未读到，不能把本地改善写成供应商危险已清零。**

## 同版文件与本地检查

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R20-Via-Clearance-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R20-Via-Clearance-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R20-Via-Clearance-cpl.csv)从保存并重开的 R20 原生工程导出。
- EDA 关闭重开后原生 DRC **0 条**，原理图与 PCB 为 66 个位号、256 个引脚、0 个网络差异；独立[铜连通](../../records/r1-layout-reset-r20-copper-check.json)与[NFC 线圈](../../records/r1-layout-reset-r20-nfc-check.json)检查通过。
- [制造对账记录](../../records/r1-layout-reset-r20-manufacturing.json)与[复核脚本](../../../scripts/check-r20-manufacturing.py)确认 BOM/CPL 均含 66 个位号，Gerber 有 167 个过孔，最小实际钻孔约 0.30 mm，最小径向孔环 0.1016 mm；[板框／USB 孔检查](../../records/r1-layout-reset-r20-profile-check.json)确认旧四个镀铜槽为 0，两颗 Ø0.65 mm 非镀定位孔保留。
- [独立铜间距审计](../../records/r1-layout-reset-r20-clearance-audit.json)未发现 <0.15 mm 的异网离散铜对象配对；三处同网孔壁到焊盘铜边 <0.10 mm 的配对降为 0。该审计不覆盖铺铜和阻焊；R18B 网站曾报最小线距 0.12 mm，仍需用 R20 成品层定位。
- [重开工程快照](../../records/r1-layout-reset-r20-routed-snapshot.json)与[引脚清单](../../records/r1-layout-reset-r20-pcb-pins.json)供复查，不代替原生工程。

## 线上与后续

[嘉立创上传记录](vendor-dfm-2026-09-26.md)：R20 Gerber 已上传至“我的文件”并解析；分析结果页没有成功打开，PCB／SMT DFM 结果和费用均未获取，BOM/CPL 也尚未提交到该分析任务。下一步先读取同版线上 DFM，确认过孔危险与孔环、阻焊、0.12 mm 线距、U1 装配等剩余问题；然后在独立候选中按[七区原厂参考](../../r1-seven-zone-reference-plan.md)手工整理 USB 数据、CC、VBUS 扇出，不移动 ESD 或关键去耦来换取整齐。

现有 5.8 mm 外壳与 USB4110 名义干涉约 0.18 mm，尚无可装配的新外壳验证。**R20 不可下单，未下单或付款。**
