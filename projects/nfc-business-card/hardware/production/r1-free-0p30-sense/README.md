# R1 0.30 mm 普通钻孔与电池采样候选

## 当前确定方案

本目录是独立的**工程候选和检查文件**。新增 BQ25186 TS/MR 到地的 10 kΩ 电阻及可关断的电池电压采样；Gerber、BOM、CPL 均从同一新工程导出。原 R1 制造包和上一版 0.30 mm 试验包未被替换。**本版尚不可投产或下单。** [新版嘉立创 DFM](vendor-dfm-2026-09-24.md)仍提示孔环、槽宽、铜间距、阻焊和 SMT 几何危险；工厂尚未人工接受。

| 文件 | 用途 |
| --- | --- |
| [原生 EDA 工程](../../../../../eda/NFC-Card-R1-Free-0p30-Sense.eprj2) | 本版唯一可编辑源文件 |
| [Gerber ZIP](NFC-Card-R1-Free-0p30-Sense-gerber.zip) | 已上传线上 DFM；非批准制造包 |
| [BOM](NFC-Card-R1-Free-0p30-Sense-bom.csv) / [CPL](NFC-Card-R1-Free-0p30-Sense-cpl.csv) | 已上传 SMT 预览；未授权替代料 |
| [本地验证](../../records/r1-free-0p30-sense-validation.json) | 文件哈希、孔径、孔环及本地检查摘要 |
| [线上 DFM](vendor-dfm-2026-09-24.md) | 任务号、全部主要危险和处理顺序 |
| [下一步计划](next-steps.md) | 局部重布顺序、逐阶段验收与供应商确认边界 |

## 电路变更与验证范围

- R19（10 kΩ）将 U2 BQ25186 的 TS/MR 接地，执行不装温度探头的选型。
- Q2 AO3401A、Q3 SI1308EDL、R20–R23（各 1 MΩ）和 C25（100 nF）组成受 GPIO 控制的电池采样通路。U1 的 P0.29 用作 `BAT_MEAS_EN`，P0.02/AIN0 用作 `BAT_ADC_SENSE`。固件需启用后等待采样节点稳定再读 ADC，并在关断/睡眠时关闭通路；电压阈值和电池曲线尚未实测。
- PCB 焊盘网络复核：Q2 的 1/2/3 脚分别为门极/电池源极/分压供电漏极，Q3 的 1/2/3 脚分别为 GPIO 门极/GND 源极/Q2 门极漏极；R22 将 Q2 门极上拉至电池，R23 将 GPIO 下拉。依据 [AOS AO3401A 数据手册](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf)、[Vishay Si1308EDL 数据手册](https://www.vishay.com/docs/63399/si1308edl.pdf)和 [Nordic nRF52840 引脚表](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/pin.html)核对器件极性与 ADC 引脚；上述连接尚未经实物测量。
- 新器件主要放在正面右上空白区，未移动 USB 防护器件、本地去耦、板框或 NFC 天线。元件编号在嘉立创匹配 29/29 组；这不验证封装焊脚、实物方向、库存或贴片费用。特别要复核 Q2/Q3 的 PCB 封装与匹配器件封装尺寸。
- 保存后重开原生工程：DRC 0、原理图和 PCB 66/66 器件一致、独立铜连通、NFC 净空、板框及四个镀铜槽检查通过。[复查脚本](../../../scripts/check-r1-free-0p30-sense.py)还检查 Gerber 钻孔与 BOM/CPL 位号，但本地检查不能代替供应商接受及样机电测。

## 仍阻碍投产的工艺项

- 170 个过孔中 97 个径向孔环不足 0.10 mm，最小 **0.075946 mm**；18 个导出钻孔略小于精确 0.300 mm（最小 **0.29972 mm**），网页仅四舍五入显示 0.30 mm。需要修正导出/孔径并扩大焊盘，不能以网页显示代替精确 Gerber。
- 直接把薄孔环过孔全部扩大到 0.508 mm 外径、0.3048 mm 名义钻孔后，原生 DRC 出现 64 条冲突。局部移动 37 孔、重接 65 个端点和一段 GND 走线的诊断尝试降至 **24 条 DRC**，仍不合格；[诊断工程](../../../../../eda/archive/NFC-Card-R1-Free-0p30-Sense-Ring-Study-DRC24.eprj2)保留在 EDA 归档，仅供后续继续局部重布，未导出制造包。[试验 DRC](../../records/r1-free-0p30-sense-ring-study-drc.json)记录冲突，勿把试验当成本版通过结果。
- 尚需局部重布 USB D+/D− 扇出、显示供电与控制、GND 过孔，达到孔环 ≥约 0.10 mm 且尽量让异网铜间距 ≥0.15 mm；然后重新跑本地全部检查和供应商 PCB/SMT DFM。不要为腾空间移远保护器件、去耦，或侵入天线净空。
- 当前候选的[异网走线/焊盘/过孔间距审计](../../records/r1-free-0p30-sense-clearance-audit.json)在 11 组网络/层组合中发现 <0.15 mm，最窄约 0.1093 mm；精确坐标与局限见[线上 DFM 记录](vendor-dfm-2026-09-24.md#015-mm-异网间距的具体缺口)。

未下单、未付款，OSP 和实际 PCB+SMT 分项价也未按本版文件审核。
