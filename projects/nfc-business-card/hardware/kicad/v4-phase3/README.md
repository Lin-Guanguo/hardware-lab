# NFC V4 本轮冻结候选

## 当前确定方案

2026-09-29，按用户要求停止批量试路，先交付[全板复盘与两个布局方案](../../v4-layout-routability-review.md)。**本目录保持已保存的局部候选，不是整板完成版，不可投厂。**打开 [NFC-Card-V4.kicad_pro](NFC-Card-V4.kicad_pro)。

当前 361 段／65 孔，ERC 0、parity 0、DRC 114、61 个未连接。保存前后 PCB SHA 相同；[冻结工程、库与失败记录](../../records/kicad-v4-phase3/layout-review/checkpoint.zip)、[文件指纹](../../records/kicad-v4-phase3/layout-review/checkpoint-manifest.json)、[全部端点和功能组图](../../records/kicad-v4-phase3/layout-review/index.html)可复查。

实际 U3/C4/C5 已回到 MCU 东北侧，U3=(176.2,110.1,90°)；早期西置方案只是对照，不再把 README 的历史描述当作实际位置。C2/C9/R13 的后续实验移动仅存在未采用模型中，未应用到本目录 PCB。原生文件及保存记录才是当前状态。

## 对照与下一步

D、[V4 第一阶段](../v4/README.md)、[第二阶段](../v4-phase2/README.md)保留。双层 0.8 mm、4.8 mm 外壳目标、板框／接口／天线基准和电池采样功能不变。没有换料、降低规则或增加忽略项。

`*-spec.json`、`*-plan.json` 包含失败和被替代方案，**不是顺序执行清单**。最新复盘说明了固定局部前缀、过孔排布、网格与已有铜连接的算法限制，不能把 failures 当作板面积不足的证明。当前不继续执行这些计划。

下一步等待用户选择：A 充电整组东置，或 B 电源西置／完整显示电源北移。先依复盘中的联合通过条件验证，再决定是否推进整板。

## 电气与制造边界

[具体电气与制造问题](../../v4-phase3-decisions.md)仍保留。C3 建议换料尚未应用；C1、VBUS 保护、U3 负载、屏幕峰值、电池电流与工艺接受状态没有被布局复盘关闭。本版最终制造包和 PCB/SMT DFM 未完成，不能沿用前版报告。
