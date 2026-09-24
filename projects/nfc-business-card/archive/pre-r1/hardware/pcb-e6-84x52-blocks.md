# 84 × 52 mm 功能块布局与出线检查

## 当前确定方案

2026-09-21：继续使用独立 [NFC-Business-Card-84x52-E6-Blocks.eprj2](../../../../../eda/archive/nfc-business-card/NFC-Business-Card-84x52-E6-Blocks.eprj2)，保留 [E6 原版](../../../../../eda/archive/nfc-business-card/NFC-Business-Card-84x52-E6.eprj2)作比较。含壳 84 × 52 mm、优先薄度、至少两键、屏幕与电池平铺的约束不变。当前仍是**试布线草案，不能下单**。

后续经[整板评审](board-design-review.md)调整推进顺序：先解决 USB 封装与工艺边界，再整体规划 USB/充电区，暂停下文所述的逐网局部修补。以下保存该版的实际改动和验证记录。

本轮调整 USB/充电区与屏幕电容排布，共移动 11 个小器件；主控、USB 插座、屏幕插座、按键、板框及保留区不变。56 个元件、242 个焊盘，保存重开后 DRC **67 → 58 条**，其中 34 条连接问题、24 条原有 USB 槽边距问题。没有新增间距或原生网表告警。

入口：[检查快照](pcb-e6-84x52-blocks.json)、[整板画布](pcb-e6-84x52-blocks.png)、[原理图网表](e6-blocks-circuit.enet)、[PCB 网表](e6-blocks-pcb.enet)。器件选择和电路依据继续见[原 E6 电路说明](pcb-e6-84x52.md)。[FreeCAD](../enclosure/pcba-e6-84x52-detail.FCStd)尚未同步实际外围与本轮位置，不能作为装配验收结果。

## 本轮布局调整

坐标单位为 mm，沿用 EDA 原点与方向。

| 位号 | 原中心 → 新中心 | 调整目的 |
| --- | --- | --- |
| C2 | (30.6, 10.9) → (30.7, 11.1) | 给 SYS、BAT 两个相邻引脚共同留出出口，避免只缩短 SYS 却堵住 BAT |
| U5 | (33.8, 9.4) → (32.0, 9.5)，旋转 270° | 将数据线保护移到接口数据脚附近，已接通 A6/A7 到保护器件的两段短连接 |
| U6 | (30.5, 12.7) → (36.1, 10.0) | CC 防静电移出充电输出附近，减少功能块交叉 |
| R2 | (31.6, 9.55) → (38.5, 10.0) | 配合 U6 安排 CC2 下拉，给接口中心留空间 |
| C16–C22 | x=56.5；y=31.6…45.4 → y=34.8、36.6、38.4、40.2、42.0、43.8、45.6 | 按屏幕引脚对应关系重新安排七颗电容，把电源脚附近的绕线缩短，留出控制信号出线位置 |

- SYS→C2 约 1.45 mm、BAT→C3 约 2.63 mm，均为本轮局部连接长度；SYS 和 BAT 网络在最终 DRC 中没有连接告警。
- J2→C16–C22 七条短连接分别约 2.74、2.41、2.82、3.81、4.60、6.64、6.82 mm。其中六条走顶层；VCOM 使用两个普通通孔。VGL 到电路其他部分另行接回；七个相关网络在最终 DRC 中没有连接告警。
- J2 的 VDD、GND、DC 已安排出线及过孔，但 **VDD 和 DC 的全网连接尚未完成**。已局部出线不等于整条网络布通。
- A6/A7→U5 各约 0.99/0.98 mm，仅表示两个局部分支；另一组 USB 接触脚、CC 分支和通往主控的 D+/D− 主干仍需处理。没有宣称差分阻抗、完整回流或双面插入已通过验证。
- 新线使用 8/10 mil；新增普通通孔约 0.305 mm 孔径 / 0.610 mm 外径。未放宽设计规则，也未改变两层方案。

## 验证结果与边界

| 检查 | 结果 |
| --- | --- |
| 原理图及 PCB 引脚赋网 | 234 + 234 项通过 |
| SCH/PCB 元件 ID、封装关联 | 112 项通过；未修改电路网络 |
| 平面几何 | 56 元件、242 焊盘；焊盘/主体相交、越界、NFC 侵入、FPC 弯折区主体侵入均为 0 |
| 几何数据核对 | 使用本项目未修改的封装缓存；234 个焊盘中心与当前 API 返回坐标在 0.002 mm 内一致 |
| 规则与机械边界 | RULE、RULE_TEMPLATE、RULE_SELECTOR、LAYER_PHYS、POLY、REGION 与副本基线一致 |
| 保存与重开 | 638 段铜线、102 个过孔、两块地铜；DRC 58 条，无 Netlist Error |
| 视觉检查 | 检查当前整板画布；剩余飞线仍可见，不代替电气/装配评审 |
| 数据库与原版 | 副本 SQLite `quick_check=ok`；原 E6 文件 SHA-256 与本轮开始一致 |

原版为 648 段线、107 个过孔；当前净少 10 段线、5 个过孔。两版均未完成连接，不能据此断言完整布线效率或电气性能已经更好。几何检查也不包括焊锡、器件高度、FPC 曲面、电池公差、键帽和完整外壳。

复验命令（仓库根目录）：

```sh
python3 projects/nfc-business-card/scripts/check-e6-netlist.py projects/nfc-business-card/hardware/e6-blocks-circuit.enet --pcb projects/nfc-business-card/hardware/pcb-e6-84x52-blocks.json --pcb-netlist projects/nfc-business-card/hardware/e6-blocks-pcb.enet
git diff --check
```

## 下一步与可复用方法

1. **先完成 USB 密脚出口，再决定保护器件的最终距离。** 目前接口的 CC、VBUS 和两组数据脚仍有分支未接；保留成对主干的通道，避免普通信号先占满。
2. **处理整网供电与地回路。** GND、VBUS、3.3 V、EPD_VDD 仍有分离的铜段或节点；必须区分焊盘已接线、铜区接地和完整网络连通。
3. **小组同时检查相邻引脚。** 本轮 C2 的近距离摆放曾挡住 BAT，最后位置同时验证了 SYS/BAT；屏幕区按整组七个电源脚安排，避免逐条长绕线挤占其他出口。
4. **修改前保存副本，局部拆线，关键线路先行。** 元件移动后清理旧连接和发生冲突的铜线，先验证出线和局部连接，再补普通控制网络；每轮重建地铜、检查 DRC、保存重开，不仅看自动布线的成功计数。
5. **先确认两层能否形成合理走线和回流。** 若密脚出口与主干仍反复拥堵，再比较四层与工艺能力；不以盲目缩线宽或修改全局间距掩盖问题。

剩余 34 条连接问题按对象计数：GND 7、USB_VBUS 4、VDD_3V3 5、EPD_VDD 2、USB_CC1/2 各 2、USB_DP_CONN/USB_DM_CONN 各 3、BAT_NTC_TBD 2、USB_DM_MCU 2、EPD_DC_TBD 2。24 条槽边距仍需结合 GCT USB4500 图纸和制造能力解决。NFC 线圈、VBUS 保护、充电限流/NTC、完整供电与刷新实测、CAD 同步仍未完成。

方法参考：[Altium 布局与布线教程](https://www.altium.com/documentation/altium-designer/tutorial/component-placement-routing-board)、[功能分组与固定器件布局](https://resources.altium.com/p/where-do-they-all-go-pcb-layout-component-placement-guidelines)、[关键网络优先、出线与自动布线准备](https://resources.altium.com/p/automated-pcb-routing-with-situs-topological-autorouter)。这些方法用于指导取舍，不替代本板验证。API 调用、几何脚本、各阶段快照和在线备份保存在被忽略的 `artifacts/archive/eda-block-layout/`。
