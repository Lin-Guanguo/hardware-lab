# 电子名片硬件

## 当前确定方案

更新于 **2026-09-22**。成品沿 **84 × 52 mm（含壳边缘）定制 PCB/PCBA** 继续，优先薄度与装配余量；nRF52840 内置 NFCT、USB-C、GDEH0154E01 六色屏和至少两键。当前 E14 主布局把 301230 类电池按 30 × 12 × 3 mm 标称包体放在左下，屏幕在左上、NFC 在右上、USB/充电/主控在右下；电池规格和 ≤5 mm 仍待实物验证。

新的开工入口是[E15 清理版 PCB 开工记录](pcb-e15-clean-layout.md)。E15 位于 E14 工程内，已清除历史 PCB 图元并保存为 56 个元件、242 个焊盘、0 铜线、0 过孔的独立 PCB 图页；下一步先处理原理图关联、板框/USB 基准和真实电池最大包络。

现有 EDA 保留三颗按键；基本交互只依赖两颗，分别轮换一级栏目和二级选项，二级选到即自动应用。第三颗在不影响薄度、走线和装配时保留，功能待定；本轮未删除元件或修改网络。

- 最新原始工程：[NFC-Business-Card-84x52-E14-Battery-Layout.eprj2](../../../eda/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2)。
- 当前推进方法：[E14 新电池尺寸主布局评审](pcb-e14-battery-layout.md)。E14 是从 E9 复制的无铜块级布局副本，先验收电池、NFC、USB/充电/主控的空间关系；E13 自动布线和 E9/E7 作为历史与走线对照。
- USB [工艺版本复核](usb4500-clearance-review.md)：国内更新说明允许内槽/锣边到铜 ≥0.20 mm，J1 满足名义最小值，保留原封装并继续整体重排；规则写入未成功，原生 58 条告警未变，未裁焊盘或缩槽。
- 当前布局：[E14 新电池尺寸主布局评审](pcb-e14-battery-layout.md)；E7/E9 无铜基线、E13 走线对照、原电路选型和网表继续保留。
- 生产化门槛：[E14 生产化门槛记录](pcb-e14-manufacturing-gates.json)；脚本 [check-e14-gates.py](../scripts/check-e14-gates.py) 只验证当前快照完整性，不会提前生成供应商制造包。
- 在改 CAD 或新建 EDA 副本前，先做[布线空间先行研究](routing-space-study.md)：比较长条电池放左下、右下保留 16.5 mm 高连续布线区的可行性；该研究尚未替换 E9，也未冻结电池型号。
- 最新机械研究：[pcba-e14-battery-layout.FCStd](../enclosure/pcba-e14-battery-layout.FCStd) 与 [按 EDA 实际坐标重绘的 E14 平面图](../enclosure/pcba-e14-battery-layout.svg)；后者由 [e14-eda-snapshot.json](e14-eda-snapshot.json) 和 [生成脚本](../scripts/generate-e14-eda-layout-svg.py)复现，明确显示当前历史板框、机械区和未入 PCB 的电池目标。空间包络已保存重开并通过几何检查。基于意图包络生成的 [外壳 V1 验证样件](../enclosure/nfc-card-e14-enclosure-v1.FCStd)仍保留右侧 USB 假设；新增 [V2 EDA 坐标协调样件](../enclosure/nfc-card-e14-enclosure-v2-eda-coordinate.FCStd)把 USB 开口移到当前 J1 所在的 y=0 边。V1/V2 均为验证样件，仍需先冻结实际板框、J1 朝向、电池包体和 DFM，不能直接下生产单。

E14 保存重开后为 56 个元件、0 铜线、0 过孔；器件间 SMD 重叠已清除。原生 DRC 仍有 222 个叶级结果，其中 188 个为零铜线连接错误，另有板边/测试点间距结果；USB 数据、VBUS、地回流和 EPD_BUSY 仍未完成。NFC 禁布区已移至右上作为空间约束，天线、实物供电/装配和电池完整包体仍待解决，不能直接生产。

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
