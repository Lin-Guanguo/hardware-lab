# 电子名片硬件

## 当前确定方案

更新于 **2026-09-23**。成品沿 **84 × 52 mm（含壳边缘）定制 PCB/PCBA** 继续，优先薄度与装配余量；nRF52840 内置 NFCT、USB-C（右边缘中部）、GDEH0154E01 六色屏和**三颗按键**。301230 类电池按 30 × 12 × 3 mm 标称包体放在左下电池挖空里，屏幕在左上、NFC 净空在右上、USB/充电/主控在右侧；电芯最大包络与目标厚度仍待实物验证。

当前开工入口是 E14 工程内的 **`Board1_2` / E16 Right-Mid USB Study**（2026-09-23 与 `Schematic1` 关联）：L 形板框（84 × 52，左下 33.5 × 15 mm 电池挖空 + 右边缘 9.24 × 6.5 mm USB 缺口），**56 个元件、242 个焊盘、781 段铜线、162 个过孔、两层 GND 覆铜**；原生 DRC 保存/关闭/重开后普通间距 **0**、连接 **0**，只剩 12 项 J1 沉板槽边告警（0.20 mm，板厂下限允许）；原理图与 PCB **逐引脚 234 项、0 处网名差异**。外壳 V7 对导出的真实元件 STEP 0 干涉。[E15 底边 USB 版](pcb-e15-clean-layout.md) 与 `Board1/E6` 保留作回退。

按键为**三颗**：SW1 (38.1, 3.30)、SW3 (38.1, 15.10) 一列 + 三角第三点 SW2 (46.3, 8.80)，外壳 V7 开三个键孔。基本交互只用键 1 / 键 2（一级栏目 / 二级选项，选到即自动应用），第三颗接在原本空置的 `KEY_NEXT_N` 上，功能待定。

- 最新原始工程：[NFC-Business-Card-84x52-E14-Battery-Layout.eprj2](../../../eda/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2)。
- 当前布局记录：[E16 右侧中部 USB 布局](pcb-e16-usb-right-mid.md)（落盘、三键三角形、外壳干涉复检、制造包核对、电池接口与 NFC 馈线预研）；E15/E14/E13/E9/E7/E6 保留作历史与走线对照。
- USB [工艺版本复核](usb4500-clearance-review.md)：国内更新说明允许内槽/锣边到铜 ≥0.20 mm，J1 满足名义最小值，保留原封装；那 12 项槽边告警就是这条 0.20 mm 规则的体现。
- 生产化门槛：[E14 生产化门槛记录](pcb-e14-manufacturing-gates.json)；脚本 [check-e14-gates.py](../scripts/check-e14-gates.py) 只验证当前快照完整性，不会提前生成供应商制造包。当前仍未放行，阻塞项是电芯包络、NFC 天线、外壳实物验证与最终放行。
- 待输入三件：① 电芯实物最大包络与出线方向（硬边界见 [E16 记录](pcb-e16-usb-right-mid.md)）；② PN532 桌面实验定 NFC 天线形式，再补两条馈线与匹配网络；③ 打印 V7 四件验键帽行程、屏幕贴合与 0.4–0.5 mm 薄壁公差。
- 当前机械研究：[E16 外壳 V7](../enclosure/nfc-card-e16-enclosure-v7.FCStd)；历史：[pcba-e14-battery-layout.FCStd](../enclosure/pcba-e14-battery-layout.FCStd)、[E14 平面图](../enclosure/pcba-e14-battery-layout.svg)、[V1](../enclosure/nfc-card-e14-enclosure-v1.FCStd)/[V2](../enclosure/nfc-card-e14-enclosure-v2-eda-coordinate.FCStd) 验证样件。

J2 采用参考板同款 FPC-05FB-24PH20 / C2856831；已有 [79 项名义尺寸比较](fpc-connector-review.json)不代替样品插合。电路取舍及规格差异见[本版记录](pcb-e6-84x52.md)与[屏幕资料](../docs/gdeh0154e01-evaluation.md)。

## 选型与历史记录

- [候选 BOM](candidate-bom.md)与[器件选项](component-options.md)：追溯候选、供货快照和待确认规格，不是冻结采购清单。
- [原理图草案](schematic-draft.md)与[网表快照](schematic-draft.enet)：原 27 元件电路基线，未包含新增候选的完整连接。
- [Bottom-USB 排布](pcb-bottom-usb.md)、[旧试布线](pcb-routing.md)和[首次预布局](pcb-prelayout.md)：保留历史对照；旧版 DRC 数量不能代替新版结果。
- [E7 布局评审](pcb-e7-placement.md)：主控、USB/充电区的无铜布局副本和下一轮关键通道验收标准。
- [E9 USB 局部排布评审](pcb-e9-usb-local.md)：在不改变板框和厚度假设的前提下收紧 USB/CC 小组；包含 CC 试线结果和数据扇出缺口。
- [E10 按键右移对照](pcb-e10-button-right.md)：验证按键移动是否能给 USB 区让出通道；当前不采用。
- [E11 USB 数据扇出对照](pcb-e11-data-fanout.md)：两轮错开通孔试验和清理结果；当前不采用。
- [系统设计](system-design.md)：早期电路设计输入；与当前方案不同的屏幕、电池及接口选择，按首章和最新排布记录继续修订。
