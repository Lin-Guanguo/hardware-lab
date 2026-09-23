# 第一版 EDA 原理图草案

更新：2026-09-20。源工程为 [`eda/NFC-Business-Card.eprj2`](../../../eda/NFC-Business-Card.eprj2)，直接保存在根目录 `eda/`。这是可编辑的电路设计草案；同工程已进入 [PCB 第一轮试布线](pcb-routing.md)，布线与电路均未完成，不能用于制造。之前的 `AI-API-Smoke-Test` 工程未修改。

## 图页与覆盖范围

| 图页 | 已绘制 | 尚未完成 |
| --- | --- | --- |
| 01 USB and Power - DRAFT | USB-C、CC 下拉、数据串阻、BQ25186、TPS7A0233、电源去耦与控制上拉 | USB ESD、输入限流/浪涌、有效电容、电池与 NTC |
| 02 MCU and Controls - DRAFT | MDBT50Q-P1MV2、三按键及上拉、供电、USB/I2C 连接；SWD/NFC/屏幕信号预留 | SWD 测试焊盘、NFC 天线及匹配、屏幕外围、固件 |
| 03 Display Battery RF - TBD | 待确认事项与 FH12 连接器候选 | J2 未接线，明确排除 BOM 与 PCB；不以空接线代替已经完成的显示电路 |

已连接部分共 **27 个元件、32 个命名网络**；图中另有一个不转 PCB 的 J2 候选。相同网络名代表电气连接，跨页适用。原始 EDA 网表评审快照见 [schematic-draft.enet](schematic-draft.enet)。修改工程后必须重新导出，快照不会自动跟随。

## 本版电路安排

- 正常电压模式：U1 pin 28 VDD 与 pin 30 VDDH 同接 `VDD_3V3`；pin 31 DCCH 标为不连接。模块所有五个 GND 引脚接地；VBUS 单独接 USB 输入。依据 Raytac Rev L 第 14–17、40 页。
- USB：J1 的 A6/B6 接 D+，A7/B7 接 D−；R3/R4 各串 27 Ω。CC1/CC2 各用独立 5.1 kΩ 下拉。外壳锚脚当前接 GND，布局时再评审屏蔽与 ESD 回流。
- 电源：`USB_VBUS → U2 SYS → U3 → VDD_3V3`；电池正极 `BAT_PACK_TBD` 与 SYS 分开。U2 热焊盘接地；U3 EN 接 SYS，NC 不连接。
- R5/R6 按 BQ25186 引脚说明暂选 10 kΩ I2C 上拉，取代早期候选表的 4.7 kΩ；总线速度与上升时间仍需验证。INT、PG 各用 10 kΩ 上拉。
- R7 将充电使能 `/CE` 上拉到 3.3 V，由 MCU 控制。它只能在该电源建立后起作用，**不保证上电瞬间禁止充电**；BQ25186 的复位默认 10 mA / 4.2 V、看门狗恢复默认值仍必须满足最终电池规格。电池未确认前不接电池调试。
- 三个 ALPS 按键的 **1、2 脚内部相连，3、4 脚内部相连**；前一组接带 10 kΩ 上拉的 GPIO，后一组接地，按下为低。与原厂电路图和库符号一致。
- C1/C8 在 USB_VBUS 上名义合计 6.9 µF。C8 的 4.7 µF 是电容预算暂定值，**不同于 Raytac 第 40 页的 10 µF 参考值**，尚需核对模块要求、器件 DC bias、容差及整体 USB 浪涌，不能据此宣称 USB 合规。其他各轨有效电容及屏幕启动峰值同样待核算。

| 位号 | 本版值 | 库中供应商料号 |
| --- | --- | --- |
| R1/R2 | 5.1 kΩ，1%，0603 | C23186 |
| R3/R4 | 27 Ω，1%，0603 | C325726 |
| R5–R12 | 10 kΩ，1%，0603 | C25804 |
| C1/C3/C4/C5 | 2.2 µF，16 V，X5R，0603 | C23630 |
| C2/C6 | 10 µF，10 V，X5R，0603 | C19702 |
| C7 | 100 nF，50 V，X7R，0603 | C14663 |
| C8 | 4.7 µF，16 V，X5R，0603，暂定 | C19666 |

供应商编号表示本轮实际取得的 EDA 库器件，不代表嘉立创贴片库存或已完成选型。主器件料号与供应缺口见 [候选 BOM](candidate-bom.md)。符号关键引脚已对照原厂资料；封装缩略图只作初筛，**尚未完成全部焊盘尺寸、编号、沉板槽、阻焊及禁布区审核**。库中 USB 的“24P”描述与原厂 16 接点图存在差异，继续以原厂图逐焊盘审核。

## GPIO 草案

下表使用模块脚号，不是裸 nRF52840 封装脚号；固件尚未使用这些定义。

| 功能 | GPIO / 模块脚号 |
| --- | --- |
| 前 / 后 / 确认 | P1.10 / 3；P1.11 / 4；P1.12 / 5 |
| 充电 SDA / SCL | P0.26 / 19；P0.27 / 16 |
| 充电 INT / PG / CE | P0.04 / 20；P0.05 / 21；P0.06 / 22 |
| 屏幕 SCK / MOSI / CS / DC | P0.14 / 36；P0.13 / 37；P0.16 / 38；P0.15 / 39 |
| 屏幕 RESET / BUSY / EN | P0.17 / 41；P0.08 / 24；P0.11 / 27 |
| NFC1 / NFC2 | P0.09 / 52；P0.10 / 54 |
| SWDIO / SWDCLK / RESET | 51 / 53 / 40；另需 VTref 与 GND 焊盘 |

P1.10–P1.12 的低频使用限制适合按键；I2C/SPI 分配到其他 GPIO。使用内部低频 RC 的固件安排尚未验证，原厂测试程序不能被当作本项目 USB bootloader。

## 已完成检查与限制

- EDA 保存后关闭图页并重开工程；重新导出的全部元件引脚网络与保存前一致。SQLite `PRAGMA quick_check` 为 `ok`，导出 `.epro2` 的 ZIP 完整性检查通过。
- [检查脚本](../scripts/check-schematic-netlist.py)通过 **108 项关键引脚连接检查**，覆盖电源轨、USB、CC、I2C、按键内部配对及必要 NC。该脚本检查导出网表，不代替电路仿真、ERC、封装审核或实测。
- EDA 原理图 DRC：**0 致命错误、0 错误、15 警告**，整体检查返回 `false`，未宣称通过。13 条为仅接一个引脚的预留网络：NTC、7 条屏幕信号、2 条 NFC、SWDIO/SWDCLK/RESET；另外两类是 J2 引脚未连接，以及修改后的元件显示名称/参数与供应商库标准属性不一致。保留这些可见提醒，未关闭规则或伪造连接消除告警。
- 三页图纸做了视觉检查并修正标签重叠及文字单位问题。PDF、工程导出包、API 执行记录及检查结果在被忽略的 `artifacts/archive/eda-draft/`；可随时从源工程重新导出。
- 未烧录、未仿真、未做 NFC/USB/充电/显示实测；没有生成可下单的 PCB/Gerber 或最终 BOM。

从仓库根目录核对本次快照：

```sh
python3 projects/nfc-business-card/scripts/check-schematic-netlist.py projects/nfc-business-card/hardware/schematic-draft.enet
```

下一步结合 PCB 预布局核对 USB 槽边距与布线通道，收敛六色屏当前规格和电池/NTC，补 USB ESD 与 SWD 焊盘并完成封装审核，再收敛正式布线。主控供货和 5 mm 结构预算仍按 [系统设计](system-design.md) 中的缺口推进。

来源：[Raytac 模块资料](https://www.raytac.com/product/ins.php?index_id=47)、[BQ25186 原厂手册](https://www.ti.com/lit/ds/symlink/bq25186.pdf)、[TPS7A02 原厂手册](https://www.ti.com/lit/ds/symlink/tps7a02.pdf)、[GCT USB4500](https://gct.co/connector/usb4500)、[ALPS SKQG 原厂电路与尺寸图](https://tech.alpsalpine.com/cms.media/product_catalog_ta_02_skqg_en_d003713f01.pdf)。主器件 PDF 的版本与校验值见 [下载清单](../docs/download_manifest.json)。
