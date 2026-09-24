# E14 新电池尺寸主布局评审

## 当前确定方案

更新于 **2026-09-22**。E14 是当前主布局候选，沿 84 × 52 mm 板框继续，把新电池方向作为主要约束：屏幕位于左上，301230 类电池按 **30 × 12 × 3 mm 标称包体**放在左下，NFC 净空移到右上，USB-C/充电/稳压和主控集中到右下。电池尺寸仍是可调整空间，完整包体、保护板、引线、胶带和鼓胀余量没有实物确认。

- 原始工程：[NFC-Business-Card-84x52-E14-Battery-Layout.eprj2](../../../../../eda/archive/nfc-business-card/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2)
- 过程报告：[E14 布局快照](pcb-e14-battery-layout.json)
- CAD 空间研究：[pcba-e14-battery-layout.FCStd](../enclosure/pcba-e14-battery-layout.FCStd)、[平面图](../enclosure/pcba-e14-battery-layout.svg)、[STEP 包络](../enclosure/pcba-e14-layout-envelope.step)；这些文件仅用于空间评审。按 EDA 实际 J1 坐标生成的 [V2 外壳协调样件](../enclosure/nfc-card-e14-enclosure-v2-eda-coordinate.FCStd)及 [几何报告](../enclosure/nfc-card-e14-enclosure-v2-eda-coordinate-report.json)也已保存，但仍是验证样件。
- EDA 坐标快照：[e14-eda-snapshot.json](e14-eda-snapshot.json)、[器件/焊盘坐标](e14-eda-components-pins.json)和[平面图生成脚本](../scripts/generate-e14-eda-layout-svg.py)。当前平面图按 E14 保存重开后的板框、机械层、禁布区和 56 个器件坐标重绘，并修正了两处会改变形状的错误：EDA 多边形首点后的坐标是二元组，不是连续三元组；原生画布的 Y=0 在图面下边，图面因此对 Y 做了翻转。旧的意图示意保留为 [pcba-e14-battery-layout-intended.svg](../enclosure/pcba-e14-battery-layout-intended.svg)，不再作为实际布局依据。
- 外壳首轮样件：[nfc-card-e14-enclosure-v1.FCStd](../enclosure/nfc-card-e14-enclosure-v1.FCStd)；几何有效但仍是可打印验证样件，不能替代生产壳或已发布板框。
- 走线对照：[E13 路由基线](../../../../../eda/archive/nfc-business-card/NFC-Business-Card-84x52-E13-Routing.eprj2)；E13 仅用于评估自动布线与后续扇出，不是当前主布局。

## 已完成的 EDA 调整

E14 从 E9 的保存版本独立复制，未改 E9 原工程。已完成以下块级调整，并在客户端保存、关闭、重新打开后复核：

- 将 U1 主控移到右下（EDA 坐标约 3000,1500 mil），其去耦电容沿左侧下方展开。
- 将 USB-C、ESD、CC、充电器和稳压器移到中下部，给左下电池包体留下连续的布局意图；三颗按键保持在左侧中段。
- 当前保存快照中，右上方的 **Layer 9 `be5a8ef32ca73c6f`** 机械矩形是约 **22 × 26 mm 的 NFC RESERVE**；它只是空间保留，尚未画线圈、匹配网络或调谐。另有 Layer 14 历史 reserve 和两个名称都为 `PROHIBIT` 的 Layer 12 区域；这些图元的名称没有说明用途，平面图按原始坐标标出，不能把它们统称成 NFC 禁布区。
- 保留 J2 和屏幕升压器件作为现有工程的一部分；FPC 触点、折弯和机械支撑仍需根据样品核对。

实际坐标复核也暴露出一个必须继续修正的差异：当前 Layer 11 板框仍是带缺口的历史候选轮廓，位于全局 84 × 52 mm 参考框内约 x=1.5–82.5、y=1.5–50.5 mm；Layer 9 的 37.42 × 31.90 mm 屏幕机械区位于 EDA 坐标 y=17.0–48.9 mm，按原生画布显示在上方；电池只有 30 × 12 mm 目标标注，尚未成为 PCB 封装。新版平面图把这些事实直接画出，并用虚线标出尚未落入 PCB 的电池目标，不能再把意图布局误读成已完成板框。

保存重开后的快照为 56 个 PCB 元件、0 条铜线、0 个过孔、13 条遗留多段线，脚本统计到 234 个元件引脚。原生 DRC 仍有 222 个叶级结果，其中 188 个是零铜线造成的连接错误；另有 19 个板边到焊盘、1 个板边到通孔和 2 个测试点间距结果。布局中的器件间 SMD-to-SMD 重叠已清除，但这不等于走线、回流、板框和 USB 开口通过。

## 目前不能作为供应商制造稿的原因

1. 原理图/PCB 网络尚未完成生产级同步，USB 数据、VBUS、地回流、屏幕外围和 EPD_BUSY 仍需逐网确认。
2. J1 的板边开口和锚脚位置仍沿历史板框，E14 的 USB/电源块只是新方向的空间候选；板框、槽、工艺边和插拔受力要一起重定义。
3. 301230 只是包体尺寸目标，没有供应商最大外形、保护板、出线、胶带和允许充放电电流资料；不能据此冻结电池位或厚度。
4. NFC 净空已移动到右上，但天线铜、匹配网络、金属件距离和实测读距尚未验证。
5. 当前没有导出的 Gerber/Excellon、最终 BOM/CPL、生产 STEP 或可打印 STL；FreeCAD 仍需先同步 E14 的布局，再进入外壳窗口、按键孔、USB 开口和装配公差设计。

## 下一步门槛

- 先在 E14 上完成电池真实封装占位和板框/USB 开口重定义，再做 USB 数据和主控逃线；每轮保存并重开后复核 DRC。
- 用到货电池和屏幕测量完整包体、FPC 插合、按键最高点和电源峰值，更新 EDA 与 CAD 的边界。
- EDA 通过网络、板框、DRC 和 DFM 复核后，才生成供应商用制造包；在此之前任何导出都只能作为评审快照，不能下单。

## 今晚执行门槛（可复现检查）

生产化门槛已拆成机器可读记录：[pcb-e14-manufacturing-gates.json](pcb-e14-manufacturing-gates.json)。当前快照明确为 `BLOCKED_BEFORE_MANUFACTURING_EXPORT`：

1. **先锁电池交付上界。** 301230 的 30 × 12 × 3 mm 只是一项布局假设；没有保护板、出线、胶带、允许电流和鼓胀余量，不能把电池位置变成生产禁布区或冻结厚度。
2. **再锁 J1 基准和板框。** USB 插拔方向、沉板槽、锚脚、铜到槽边距离和外壳开口必须使用同一个机械基准；不能只移动连接器而保留旧板框。
3. **然后做关键网络。** 按 USB VBUS/CC/DP/DM、充电 SYS/BAT、3V3、地回流、EPD 时序和去耦的顺序推进；每个块完成后保存、关闭、重开并复核 DRC。
4. **最后才做外壳和制造导出。** 当前 FCStd/STEP 仍是空间包络。只有板框、USB 开口、网络、RF 和装配公差通过后，才生成 Gerber/Excellon、最终 BOM/CPL 和供应商 CAD。

当前 E14 已保存重开且 SQLite `quick_check` 为 `ok`；但仍为 0 铜线、0 过孔、188 个未布线连接结果和 20 个板边相关结果。该门槛记录用于指导推进，不代表已达到下单条件。
