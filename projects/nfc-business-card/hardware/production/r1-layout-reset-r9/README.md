# R9：局部过孔避焊盘候选

## 当前确定方案

[R9 独立工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R9.eprj2)从 [R8 丝印候选](../r1-layout-reset-r8/README.md)导入。继续保留 8 个过近顶层位号的隐藏状态，只移动 R15、Q3、R1 附近的 3 个 GND 过孔及其相连短线，重新铺铜；器件、保护拓扑、板框、天线、其余过孔和走线未移动。尝试移动 Q2 附近的电池过孔时与 GND 铺铜冲突，已撤回该试位。

保存重开后的原生 DRC 为 **0 条**。[独立铜箔连通](../../records/r1-layout-reset-r9-copper-check.json)、[NFC 回路断线验证](../../records/r1-layout-reset-r9-nfc-check.json)、[板框与四槽](../../records/r1-layout-reset-r9-profile-check.json)及[同版制造包检查](../../records/r1-layout-reset-r9-validation.json)通过。167 个过孔的最小实际钻孔约 **0.30 mm**，最小径向孔环 **0.1016 mm**；本地对象审计未发现小于 **0.15 mm** 的异网铜间距。同网过孔孔壁到焊盘铜边小于 0.10 mm 的不同过孔由 R7/R8 的 **13 个降至 10 个**，孔壁压入焊盘的由 **4 个降至 2 个**。该近似计算不包含阻焊开窗或供应商加工公差，不能替代线上 DFM。

R9 Gerber 于 **2026-09-25 17:31** 上传到嘉立创 DFM“我的文件”，网页显示“解析完成”。本次浏览器操作未打开 R9 分析结果，**尚无 R9 线上 PCB/SMT 结论**；BOM/CPL 尚未上传到该任务。R7 线上报告中的孔环、阻焊、USB 镀铜槽和 J1/U1 贴装危险仍按[原记录](../r1-layout-reset-r7/vendor-dfm-2026-09-25.md)待复核。**R9 不能下单，未付款。**

## 同版文件与检查

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R9-gerber.zip)，SHA-256 `4372106192cd50d1bd0117c15449aba5b81be32f288e98e088018bbbdbad8d9e`；[BOM](NFC-Card-R1-Layout-Reset-R9-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R9-cpl.csv)。BOM/CPL 与 R8 逐字节相同。
- [R9 孔距审计](../../records/r1-layout-reset-r9-clearance-audit.json)及[完整本地验证](../../records/r1-layout-reset-r9-validation.json)记录剩余位置、钻孔、孔环和装配资料一致性。[R8/R9 Gerber 对比](../../records/r1-layout-reset-r9-gerber-compare.json)确认丝印、阻焊、钢网和板框在导出精度内未变，铜层及钻孔按三处移孔改变。
- [PCB 快照](../../records/r1-layout-reset-r9-routed-snapshot.json)与 R7 对比，除上述 3 个过孔及相连 3 条短线外，器件、焊盘、铺铜边界、板框及天线相同。

## 下单前处理

1. 继续逐点审查剩余 10 个同网薄孔到焊盘位置，优先处理 R2、Q2 两个实际压入焊盘的孔；只有在原生 DRC、独立连通、保护与去耦约束都通过时才保留新孔位。靠近 USB-C、U1、NFC 的孔不可单纯为减少计数破坏功能。
2. 清理顶层封装外框与焊盘开窗可能重叠的非功能性丝印；保留极性、接口和装配方向标识。本地审计尚有 96 段外框距焊盘铜边 <0.13 mm，其中 21 段触及铜边；按最近焊盘归类为 D1/D2/D3 各 6 段、R22 两段、U6 一段。D1–D3 是有方向的二极管，删外框时必须保留或另设清晰的阴极标记。这是按焊盘铜边做的近似定位，最终以阻焊开窗及供应商丝印裁切为准。
3. 取得 R9 嘉立创 PCB 分析结果，上传同版 BOM/CPL 做 SMT 检查，和 R7 危险项逐项对照。请供应商工程师确认约 0.10 mm 径向孔环、0.60 mm USB 镀铜槽、阻焊、J1/U1 实物模型与工艺边，再由用户决定工艺、缺料替代、费用和是否下单。
