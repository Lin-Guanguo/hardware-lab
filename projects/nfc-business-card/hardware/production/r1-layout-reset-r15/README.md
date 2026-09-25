# R15：USB4500 信号焊盘基准修正

## 当前确定方案

[R15 独立原生工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R15.eprj2)继承 [R14](../r1-layout-reset-r14/README.md)。按 GCT `USB4500-03-0-A` 原厂推荐 PCB 图，将 J1 的 12 个信号焊盘整体向板内移动 **0.29972 mm**，以四个固定镀铜槽为基准；没有移动连接器、器件、过孔、走线、板框或天线。信号焊盘的外侧边到外侧槽中心由约 6.00 mm 改为约 **5.70 mm**，内侧边到外侧槽中心由约 4.90 mm 改为约 **4.60 mm**，对应原厂推荐图。顶层局部增加禁止铺铜区，避免改变焊盘铜形时铺铜靠近信号焊盘；缩小该区后确认 GND 铜箔仍连通。

这项调整修正的是连接器封装的焊盘与安装槽相对位置。四个 **0.60 mm** 镀铜槽保持原厂尺寸，不为清除网页提示改大槽。[线上 PCB／SMT DFM](vendor-dfm-2026-09-25.md)显示接触比改善但仍报 12 条 SMT 危险，并新增 12 条信号焊盘到锣边 **0 mm** 危险。因此 R15 是**诊断候选，不升级为制造版**；尚未下单或付款。

## 同版文件与检查

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R15-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R15-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R15-cpl.csv)来自同一 R15 工程；BOM 29 组、CPL 66 个位号。
- [原生 DRC](../../records/r1-layout-reset-r15-native-drc.json)为 **0 条**；[独立铜箔连通](../../records/r1-layout-reset-r15-copper-check.json)、[NFC](../../records/r1-layout-reset-r15-nfc-check.json)、[板框和镀铜槽](../../records/r1-layout-reset-r15-profile-check.json)、[异网间距审计](../../records/r1-layout-reset-r15-clearance-audit.json)和[完整校验](../../records/r1-layout-reset-r15-validation.json)通过。167 个过孔最小钻孔约 **0.30 mm**，最小径向孔环 **0.1016 mm**，离散铜对象未发现 <0.15 mm 的异网配对。
- GCT 原厂依据：[USB4500 产品页及下载图纸](https://gct.co/connector/usb4500)。本仓库保存的原厂图纸为 `projects/nfc-business-card/downloads/usb4500-drawing.pdf`；R15 对照外侧镀铜槽中心和信号焊盘两端的名义尺寸。

## 下一步

以 GCT 完整推荐板边形状重新推导 USB 缺口与器件包络。当前缺口最窄宽约 **8.64 mm**，而原厂推荐缺口宽 **9.24 mm**、连接器本体宽 **8.94 mm**；这提示可能存在机械干涉，仍需复核实际装配截面。再决定能否在常规工艺内保留中置 USB-C，或需要换连接器并同步外壳。R15 **不可下单**。
