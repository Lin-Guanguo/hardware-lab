# E15 清理版 PCB 开工记录

## 当前确定方案

更新于 **2026-09-22**。下一轮从 E14 工程内的 **E15 Clean Layout - New Battery** 图页开工。E15 是新电池方向的干净 PCB 起点：屏幕左上、长条电池左下、NFC 保留区右上、USB/充电/主控和主要走线区放在下方与右侧；USB 暂以底边中部为优先位置。目标外形仍是 **84 × 52 mm**，整机厚度目标 **≤5 mm**。

- 工程：[NFC-Business-Card-84x52-E14-Battery-Layout.eprj2](../../../eda/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2)
- 图页快照：[e15-clean-layout.json](e15-clean-layout.json)
- 审查图：[pcba-e15-clean-layout.svg](../enclosure/pcba-e15-clean-layout.svg)
- 生成脚本：[generate-e15-clean-layout-svg.py](../scripts/generate-e15-clean-layout-svg.py)
- 旧布局证据：[E14 新电池尺寸主布局评审](pcb-e14-battery-layout.md)

E15 已从 E14 的历史 PCB 图元中清理出 56 个电路元件和 242 个焊盘，当前为 0 铜线、0 过孔。工程数据库 `PRAGMA quick_check` 通过，图页坐标快照和 SVG 格式检查通过。E15 仍是布局起点，不是制造稿。

## 开工顺序

1. **先统一基准。** 在 EasyEDA 中确认 E15 是否关联现有 Board/原理图；明确 84 × 52 mm 是 PCB 板框还是含外壳边缘的目标尺寸。未确认前不继续画板框和外壳。
2. **锁机械入口。** 根据实际 J1 封装、插拔方向和外壳边界重画底边中部 USB 开口；同时确认 Layer 11 板框、锚脚、槽边到铜和工艺边。
3. **放真实电池边界。** 先使用交付最大包络，而不是只使用 30 × 12 × 3 mm 标称值；包络要包含保护板、胶带、焊点、引线和鼓胀余量。未取得供应商数据前，电池只能作为可替换的保守占位。
4. **验证连接关系。** 从原理图重新导出网表，在 E15 中核对元件关联、封装和关键电源网络；记录未布线数量作为新基线。
5. **按风险布线。** 依次处理 USB DP/DM、CC1/CC2、VBUS、GND 回流、充电/SYS/BAT、3V3、主控 USB 和屏幕关键时序；每个区块保存、关闭、重开并重新跑 DRC。
6. **再同步 CAD。** 只有板框、J1、屏幕/FPC、电池包络和按键位置冻结后，才从 E15 坐标生成外壳开口、支撑和装配公差。现有 E14 V1/V2 只作验证样件。

## 本轮放行条件

- E15 图页与原理图 Board 关联明确，保存重开后元件和网络一致。
- PCB 板框、USB 缺口、屏幕/FPC 区、电池包络和 NFC 净空使用同一坐标基准。
- 关键 USB/电源网络有可审查的走线，DRC 结果按类别记录；未解决的连接或板边错误不能被标记为完成。
- 实际电池和屏幕到货前，不冻结厚度、壳体卡扣或供应商制造文件。

本阶段不生成 Gerber、Excellon、最终 BOM/CPL、生产 STEP 或可直接打印的外壳。E14、E13、E9 及其他历史工程保留用于回退和比较。
