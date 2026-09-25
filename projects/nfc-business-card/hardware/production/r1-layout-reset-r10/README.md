# R10：顶层封装丝印清理候选

## 当前确定方案

[R10 独立工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R10.eprj2)从 [R9](../r1-layout-reset-r9/README.md)导入，只清理非功能性的顶层封装丝印：D1–D3 的内部装饰线改为外侧阴极标记及上下外框，R0603 电阻去掉拥挤的外框，Q2 删除两段贴近焊盘的外框。D1–D3 阴极标记保留；器件、焊盘、走线、过孔、铺铜、板框和天线均未改动。

修正 [Gerber 丝印审计器](../../../scripts/audit-r1-free-0p30-sense-clearance.py)误把填充区边界当作线条的问题后，顶层封装丝印触及焊盘铜边的线段由 R9 的 **3 段降至 0**；距铜边 <0.13 mm 的线段由 **78 降至 68**。文字丝印的相同近距计数仍为 0。此审计按焊盘铜边近似计算，不能代替阻焊开窗及板厂丝印裁切判断。

R10 原生 DRC **0 条**，独立铜箔连通、NFC 回路、板框与 USB 四槽检查通过。[Gerber 层对比](../../records/r1-layout-reset-r10-gerber-compare.json)证实除顶层丝印外，其余制造层和钻孔与 R9 在导出精度内等价；BOM/CPL 与 R9 逐字节相同。167 个过孔的最小实际钻孔约 **0.30 mm**，最小径向孔环 **0.1016 mm**；本地对象审计没有 <0.15 mm 异网铜间距。仍有 **10 个**同网过孔的孔壁距焊盘铜边 <0.10 mm，其中 R2 和 Q2 附近的 2 个与焊盘铜边重叠。

R10 Gerber、BOM、CPL 已上传 `www.jlc-dfm.com` 的 **DFMP2609250151** 任务，29/29 组 BOM 自动匹配，没有替换或删件。PCB DFM 的 VIA 孔到焊盘危险为 **24 条**（R7 为 30 条）；孔环 100、阻焊桥 43、开窗露线 3、焊盘距焊盘 3、USB 镀铜槽 4 条危险仍在。网页的丝印距焊盘及距孔各显示 50 条危险，详情和真实独立位置还需核对。**SMT DFM 分析待完成；不能下单，未付款。** 记录见[供应商检查](vendor-dfm-2026-09-25.md)。

## 同版文件与本地证据

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R10-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R10-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R10-cpl.csv)从同一原生 PCB 导出。
- [完整本地制造包校验](../../records/r1-layout-reset-r10-validation.json)、[孔距及丝印审计](../../records/r1-layout-reset-r10-clearance-audit.json)、[原生 DRC](../../records/r1-layout-reset-r10-native-drc.json)、[独立铜箔连通](../../records/r1-layout-reset-r10-copper-check.json)、[NFC 回路](../../records/r1-layout-reset-r10-nfc-check.json)、[板框与槽](../../records/r1-layout-reset-r10-profile-check.json)。
- [PCB 快照](../../records/r1-layout-reset-r10-routed-snapshot.json)与 R9 逐字节相同；[PCB 引脚表](../../records/r1-layout-reset-r10-pins.json)同样不变。

## 下单前处理

1. 核对 R10 线上 PCB/SMT DFM 详情，特别是 R2/Q2 的过孔压盘、剩余过孔到焊盘距离、阻焊桥及丝印。可局部移孔改短线，但不得为减少计数破坏 USB 保护、去耦、NFC 或板框配合。
2. 请供应商按真实 Gerber 和连接器图纸确认 **0.1016 mm 径向孔环**、**0.60 mm USB-C 镀铜槽**、J1 实物焊脚／焊盘模型、U1 板边与拼板工艺边。自动规则显示危险不等于工厂已接受。
3. 让用户确认工艺、缺料替代、最终 PCB＋SMT 报价和是否下单。现在的文件只是工程候选，未制造或实测。
