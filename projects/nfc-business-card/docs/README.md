# 电子名片设计资料

## 当前确定方案

更新于 **2026-09-23**。沿含壳 **84 × 52 mm** 的定制 PCB/PCBA 继续，优先薄度和装配余量；屏幕左上、301230 类电池左下、NFC 右上、USB/充电/主控右侧（USB 取右边缘中部）。使用 nRF52840 内置 NFCT，不推进断电可读；厚度 ≤5 mm 和电池包体仍待实物验证。

交互以两键为基本能力：一级栏目轮换、二级选项轮换，二级选到即自动应用。硬件为**三颗按键**（SW1 (38.1, 3.30)、SW3 (38.1, 15.10) 一列 + 三角第三点 SW2 (46.3, 8.80)，外壳 V7 开三个键孔），第三颗接在原本空置的带上拉输入 `KEY_NEXT_N` 上，功能待定。完整规则见[架构](architecture.md)。

当前设计入口为 [E16 右侧中部 USB 布局](../hardware/pcb-e16-usb-right-mid.md) 及 [最新 EDA](../../../eda/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2) 内的 `Board1_2`：56 个元件、244 个焊盘、800 段铜线、168 个过孔、两层 GND 覆铜，原生 DRC 连接 0（只剩 24 项 `Board Outline to SMD Pad`，即 J1 焊盘离板边 0.2007 mm 的固有几何），逐引脚网表 234 项 0 差异。RF 性能、供电余量与实物装配仍未验证。

当前外壳为 [E16 V7](../enclosure/nfc-card-e16-enclosure-v7.FCStd)（L 形板框、电池袋封闭、三个齐平键帽、三条加强筋、4.5 mm 叠层），对导出的真实元件 STEP 0 干涉；0.4/0.5 mm 薄壁与键帽行程仍需实物样件验证。历史 CAD 研究（[pcba-e14-battery-layout.FCStd](../enclosure/pcba-e14-battery-layout.FCStd) 等）保留作对照。屏幕规格差异、BUSY、刷新时间和峰值电流的依据与待测项见[接口评估](gdeh0154e01-evaluation.md#接口与参考电路复核2026-09-21)。

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
