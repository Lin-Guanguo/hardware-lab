---
description: USB 编程需求、现成板原型与定制薄板的分工
last_updated: 2026-09-18
---

# USB 编程与装配路线

用户明确希望卡上有可编程 USB 口。本项目将其作为 V1 必需功能，当前按 **USB-C 连接电脑烧录固件，同时供电/充电**规划。USB 键盘模拟、U 盘配置文件等不是已确认需求。

## 主控调整

主方案由 nRF52832 薄模块转为 **nRF52840 原生 USB + NFC**。之前 nRF52832 + 日常 SWD 的推荐已被此需求取代。nRF52832 可另加 USB 转串口配串口 bootloader，但会多一套接口硬件和固件，本项目不优先采用。

芯片具备 USB 外设不等于装上插座即可刷机。需要完整的 D+/D−、供电/检测、Type-C 受电端 CC 配置、ESD 和 bootloader 设计。选支持 USB 2.0 数据的插座，不能误买仅充电的六脚 Type-C 座。原厂参考：[nRF52840](https://www.nordicsemi.com/Products/nRF52840/Modules)、[GCT 数据型 Type-C 系列](https://gct.co/news/16pin-usb-type-c)。

## 不必从每颗芯片开始拼

| 路线 | 已有成品提供什么 | 我们还要做什么 | 适合阶段 |
| --- | --- | --- | --- |
| **EN04 集成板** | XIAO nRF52840 Plus、USB-C、墨水屏接口、充电、三个用户按键 | 接兼容屏，核对/配置 NFC 天线与引脚，编写切换固件；电池确认规格后再接 | 接线较少的桌面功能样机 |
| XIAO nRF52840 / Plus 小板 | 主控、USB-C 与现成 USB 下载流程 | 增加屏幕驱动/转接板、按钮、NFC 天线和接线 | 希望部件可以重新排布的原型 |
| nRF52840 DK | 原厂开发环境、调试器与 NFC 天线 | 外接屏幕和交互；区别板载调试口和目标 MCU 的 USB 口 | 更重视 SDK/USB/NFC 联合调试时 |
| 定制 PCB + 工厂 PCBA | 工厂按图加工电路板并焊接元件 | 选型、原理图/布局、固件；最后接屏、电池、装壳与验证 | 成品小板无法满足布局/可靠性时的备选，厚度仍须验证 |

EN04 官方列有 1.54 英寸单色屏兼容项，也有通过 USB 进入下载流程的文档，但这不证明它已经运行“按键切换名片”的固件，或整套厚度符合 5 mm。24 pin 接口相同也不能代替具体屏幕型号核对。[EN04 官方资料](https://wiki.seeedstudio.com/epaper_EN04/)、[USB 下载说明](https://wiki.seeedstudio.com/EN04_opendisplay/)

XIAO 的 NFC 文档给出了 URL 标签例程，标明验证过 Seeed nRF52 Boards 1.1.13，并提醒 Plus 型号检查 NFC 引脚配置和 bootloader。现成板仍需验证 NFC 与 USB 下载能共存。当前只读资料，不修改任何设备的 UICR/bootloader。[Seeed NFC 指南](https://wiki.seeedstudio.com/XIAO-BLE-Sense-NFC-Usage/)

原型先用 USB 供电。小电池充电能力与开发板默认充电电流未必匹配；XIAO 文档列出的电流档位不能直接当作 EN04 各版本或 40–60 mAh 电池的适配证明。[XIAO 电源说明](https://wiki.seeedstudio.com/XIAO_BLE/)

## 当前优先：成品小板 + 飞线 + 打印定位壳

2026-09-18 用户希望降低定制 PCB 带来的复杂度，当前先筛选能平铺装壳的现成小板。功能上可用这种方式实现，不把定制 PCB 作为必经步骤；整机 ≤5 mm 是否可达还需完整高度图和实物验证。手焊与机械固定的工作仍然存在，只是省去主板设计、制板和贴片流程。

候选组合为带 USB 的 nRF52840 小板、与屏幕匹配的成品驱动/转接板、裸屏、独立按键、匹配的 NFC 天线和充电参数兼容的薄电池。主控上的 USB 插座直接对准壳体开口，不先拆座飞线引出 USB。屏幕经 FPC 接驱动板，驱动板的 SPI 与电源信号再接主控；不能把裸屏驱动外围省掉。

目前核实的采购线索：

- [Seeed XIAO nRF52840 系列](https://wiki.seeedstudio.com/XIAO_BLE/) 标称平面尺寸 21 × 17.8 mm，带 USB 和充电电路；具体版本 NFC 引脚、下载配置、完整最大高度与小电池充电匹配仍需核实。
- [Good Display DESPI-C02](https://www.good-display.com/product/516.html) 页面标称 41 × 22 mm、3.3 V、24-pin 0.5 mm FPC，并引出 SPI 信号；作为现成屏幕外围板的例子。具体屏幕兼容性、出厂排针形态、版本和含开关/连接器的高度未确认，不是已冻结采购项。

装壳时优先不带排针的小板，以细绝缘导线连接可焊焊盘；导线与焊点放入预留空间，不叠在最高元件上。打印壳的定位台阶承担电路板、按钮和 USB 插拔受力，不能只靠飞线固定。天线位置、匹配和与电池的距离另验，不把两根随意拉长的线当成完整 NFC 天线方案。此处是结构原则，未提供或验证任何具体接线引脚表。

两面 0.8 mm 壳壁在标称 5 mm 外高内只留 3.4 mm；每块板均须计算 PCB、两面器件、焊点、线材、绝缘和固定间隙的完整包络。后文 3.2 mm 是 MDBT50Q 模块焊到定制 PCB 的旧预算，不能代替 XIAO 成品板厚度。先筛选高度并排布，再决定是否值得购买，避免先拼出过厚样机后才发现无法装壳。

## 两种 USB 固件路线

| 路线 | 使用体验 | 要处理的事情 |
| --- | --- | --- |
| **现成板 bootloader / UF2 或串口 DFU** | 保留板厂下载方式；部分配置可拖入 UF2，或由开发工具经 USB 上传 | 对应精确板型、bootloader 版本、Flash 起始地址和镜像格式；不能任意重命名二进制为 UF2 |
| **nRF Connect SDK + MCUboot 的 USB CDC 恢复/升级** | 通过 USB 虚拟串口与配套工具上传镜像 | 配置 USB、Flash 分区、镜像检查、进入恢复模式的按键和掉电恢复；不是默认自带拖拽 U 盘 |

优先在选定开发板上保留原下载器做功能验证。若使用 Nordic SDK，则先决定复用原 bootloader 还是改 MCUboot，验证兼容后再统一工具链。不要同时假定 Arduino/UF2 与 NCS/MCUboot 镜像可互换。

参考：[Adafruit nRF52 USB bootloader](https://github.com/adafruit/Adafruit_nRF52_Bootloader)、[NCS v3.4.0 MCUboot USB CDC 恢复说明](https://github.com/nrfconnect/sdk-nrf/blob/v3.4.0/doc/nrf/app_dev/bootloaders_dfu/mcuboot_serial_recovery.rst)。这些是可复用实现，未导入本项目；采用时记录 revision 和许可证。

成品日常通过 USB 刷固件；裸片/未预烧模块的首烧，以及 bootloader 损坏后的救援，保留 **SWD 测试焊盘**。这可由工厂或开发阶段完成，不要求用户每次拿外置烧录器。恢复按键必须能在应用程序损坏时进入 bootloader，不能只依赖应用菜单。

## 对厚度与卡套的影响

目前核对过的 MDBT50Q-P1MV2 模块高 2.00 mm、预算上限 2.20 mm。加 0.8 mm PCB（上限 0.90）与 0.10 mm 焊接预留，主控区成为 **3.20 mm**，比早期 nRF52832 方案高 0.50 mm。

因此卡套“净高 3.2 mm”已没有这一局部的额外固定间隙。可研究 3.5–3.7 mm 净高、薄前后片、更薄 PCB 或其他更薄的 USB 主控封装；完整外形仍以 ≤5 mm 为目标，不擅自放宽。

例如两片各 0.50 mm、胶各 0.10 mm、净高 3.70 mm，合计 **4.90 mm**。这是无公差示例，余量很小；USB 插座还须单独核算壳体总高、板上下突出、定位脚和插头插入空间，不能由模块区域预算推断一定放得下。

沉板式 USB-C 是待评估选项，已有厂商提供 USB 2.0 数据型产品；实际订货后缀、板厚适配和最大包络未冻结。[GCT 沉板系列](https://gct.co/usb-connector/list?mountposition=Mid+mount&style=%2CType+C&version=%2C2.0)

## 下一步与验收

先筛选 XIAO 类小板与成品屏幕驱动板的完整高度，验证：USB 上传 → 显示身份 → 按键切换 → 手机读到对应链接。用打印定位壳验证飞线装配；EN04/DK 仍可用作桌面调试备选。只有现成板布局或可靠性无法达到目标时，再评估定制 PCB；届时可委托工厂 PCBA 焊接小元件。

新增验收：USB-C 正反插均能传输数据；多次升级后 NFC 仍正常；应用损坏时可按键进入恢复；升级中断后的恢复行为明确；USB 供电/充电时刷屏与 NFC 不复位。使用数据线，区分仅充电线造成的故障。尚未进行这些测试，也没有安装软件或采购硬件。
