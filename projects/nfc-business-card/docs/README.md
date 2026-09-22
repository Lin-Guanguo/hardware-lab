# 电子名片设计资料

## 当前确定方案

更新于 **2026-09-22**。沿含壳 **84 × 52 mm** 的定制 PCB/PCBA 继续，优先薄度和装配余量；E14 采用屏幕左上、301230 类电池左下、NFC 右上、USB/充电/主控右下的主布局方向。使用 nRF52840 内置 NFCT，不推进断电可读；厚度 ≤5 mm 和电池包体仍待实物验证。

交互已确定以两键为基本能力：一级栏目轮换、二级选项轮换，二级选到即自动应用；第三键在空间允许时保留，功能待定。完整规则见[架构](architecture.md)。

当前设计入口为[E14 新电池尺寸主布局评审](../hardware/pcb-e14-battery-layout.md)及[最新 EDA](../../../eda/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2)。E14 已完成块级空间重排并保存重开；56 个元件、0 铜线，原生 DRC 仍有未布线连接错误、板边和测试点间距结果，尚未完成全部连接、RF、供电验证与实物装配。

当前 CAD 空间研究为 [pcba-e14-battery-layout.FCStd](../enclosure/pcba-e14-battery-layout.FCStd) 和 [E14 平面图](../enclosure/pcba-e14-battery-layout.svg)；它不是可打印外壳，窗口、按键孔、USB 开口和装配公差仍待 PCB 走线稳定后设计。旧版 FreeCAD 模型保留作历史对照。屏幕规格差异、BUSY、刷新时间和峰值电流的依据与待测项见[接口评估](gdeh0154e01-evaluation.md#接口与参考电路复核2026-09-21)。

## 当前优先阅读

| 资料 | 用途 |
| --- | --- |
| [软件说明](software.md) | 本机 FreeCAD/EDA 工作流及 `e6-84x52-detail` 生成、检查、预览命令 |
| [GDEH0154E01 评估](gdeh0154e01-evaluation.md) | 六色屏、DESPI-E01 与待实测的驱动/供电问题 |
| [架构](architecture.md) | NFC 身份切换、USB 和固件边界 |
| [NFC 桌面实验](nfc-bench-test.md) | PN532 与现成板的独立功能探索，不代替成品板验证 |
| [来源](sources.md)与[下载清单](download_manifest.json) | 原厂资料、核对时间和文件校验值 |
| [烧录与装配交接](usb-and-prototyping.md) | 工厂首烧目标、USB 恢复、客服确认事项与最终装配分工 |
| [PCBA 调研](pcba-ai-workflow.md) | 嘉立创制造边界、AI 工作流和报价前提 |

## 早期与备选资料

[首版设计启动](design-start.md)、[早期开发计划](development-plan.md)保留讨论依据。[NFC 后续版本选项](nfc-next-version-options.md)中的断电可读已不推进，屏幕后置线圈与隔磁片仅作后续备选。
