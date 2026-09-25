# R18B：USB4110 顶部贴装接口诊断

## 当前确定方案

[独立原生工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R18B-USB4110-Diagnostic.eprj2)保留 R16 的 66 个器件与功能分区，将 J1 整颗替换为 GCT USB4110-GF-A（嘉立创 C5143397）的库器件，并把 USB4500 的板边缺口改为直边。**这是一份接口与工艺诊断，不是可下单版。** R14 仍是原生 DRC 0 的对照基线。

整颗库器件在板上有 16 个 SMT 铜焊盘、两个 Ø0.65 mm 非镀定位孔；导出 Gerber 中没有原来的四个 Ø0.60 mm 镀铜槽。此前只替换封装主数据时，板上实例仍保留 USB4500 图元；该失败尝试未作为交付。随后整颗替换，并删除试验中重复添加的手工定位孔，才得到本版。

## 同版文件与验证

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R18B-USB4110-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R18B-USB4110-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R18B-USB4110-cpl.csv)来自 R18B 原生工程；BOM 29 组、CPL 66 个位号。J1 的 CPL 是 USB4110-GF-A、16 焊盘、顶层 90°、参考点 (78.402, 26.000) mm。
- 保存重开后[原生 DRC](../../records/r1-layout-reset-r18b-native-drc.json)没有几何错误，仍有 **1 条 Netlist Error / Import Changes**。独立导出的原理图与 PCB 为 66/66 位号、256/256 引脚、0 个引脚网络不一致；这不能替代关闭原生同步提示。原理图 J1 仍显示旧 USB4500 符号与旧分件名，外壳脚号已改为 8–11，符号图形和库绑定还需完整同步。
- [独立铜箔连通](../../records/r1-layout-reset-r18b-copper-check.json)、[NFC 线圈](../../records/r1-layout-reset-r18b-nfc-check.json)检查通过。[离散铜对象间距](../../records/r1-layout-reset-r18b-clearance-audit.json)未发现 <0.15 mm 的异网走线／焊盘／过孔配对；该审计不含铺铜和阻焊。嘉立创网页报告最小线距 **0.12 mm**，需要定位并按成品 Gerber 解决。
- [板框与定位孔检查](../../records/r1-layout-reset-r18b-profile-check.json)通过：一条闭合板框、六处原板角圆弧、无 USB 镀铜槽、两颗 Ø0.65 mm 非镀孔。167 个过孔的最小钻孔 0.30 mm，最小径向孔环 0.1016 mm；详见[制造对账](../../records/r1-layout-reset-r18b-validation.json)。
- [嘉立创 PCB／SMT DFM](vendor-dfm-2026-09-26.md)已完成，J1 槽宽和焊脚相交危险消除；孔环、阻焊、局部间距、U1 贴装及原生同步问题仍在。
- [正反面布线图](../../records/r1-layout-reset-r18b-copper.png)表明 USB 区仍沿用 R16 的多次换层和长距离连线，换接口后尚未按功能簇重新布线。

## 机械边界

[外壳包络代理](../../records/r1-layout-reset-r18b-case-proxy.json)把 USB4110 按原厂 3.26 mm 顶部高度置于现有 PCB 高度：5.8 mm 外壳内侧名义干涉约 0.18 mm；6.3 mm 总厚时顶部名义余量约 0.32 mm。该代理仍以旧 USB4500 的外壳 CAD 定位，不含新接口 STEP、定位柱、开口、焊料或打印公差，**不能当作装配合格**。现有外壳制造版未改。

## 下一步

1. 在新的独立候选中将原理图 J1 符号、外壳脚号、器件／封装绑定与 PCB 同步，重开后清除原生 `Import Changes`；保留 USB 数据、CC、VBUS、GND 实际网络不变。
2. 以 USB4110 焊盘和固定孔为基准，局部重布 J1→ESD／CC／VBUS，不移动保护器件、关键去耦或侵入天线净空；去除不必要的绕线和换层，再重跑连通、0.15 mm 间距、钻孔及线上 PCB／SMT DFM。
3. 以真实 USB4110 机械模型创建独立约 6.3 mm 外壳候选，核对插头入口、按键、屏幕、电池和打印公差。剩余网页危险逐点按 Gerber／器件图纸判定；无需为了计数擅改标准封装。

当前无下单、付款或供应商投产确认。
