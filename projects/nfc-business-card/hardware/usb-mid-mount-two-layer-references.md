# 双层中置 USB-C 公开参考

## 当前确定方案

可找到已制成产品、公开原生板文件的**双层中置 USB-C**案例，但尚未找到“GCT USB4500-03-0-A、0.8 mm 板厚、双层且有可核验装配结果”的完整同条件参考。设计继续以 [GCT USB4500 原厂产品页与图纸](https://gct.co/connector/usb4500)作为器件封装与缺口的尺寸基准，再借鉴同类双层板的扇出拓扑；这些参考不能直接替代本板 DRC、机械与 SMT DFM。

| 公开设计 | 可核对的事实 | 本板适用范围 |
| --- | --- | --- |
| [Adafruit Sunken USB Type C Breakout](https://github.com/adafruit/Adafruit-Sunken-USB-Type-C-Breakout-PCB) | [Eagle 原生板文件](https://github.com/adafruit/Adafruit-Sunken-USB-Type-C-Breakout-PCB/blob/main/Adafruit%20Sunken%20USB%20Type%20C%20Breakout.brd)使用顶／底铜两层，有 4 个过孔；[产品页](https://www.adafruit.com/product/6050)提供成品。连接器不是 USB4500。 | 证明同类中置 USB-C 可做双层；可参考从焊盘分组向外扇出、CC 电阻靠近端口的布局，不复制封装尺寸。 |
| [Goldfish v2](https://github.com/staticintlucas/goldfish) | [KiCad 原生板文件](https://github.com/staticintlucas/goldfish/blob/main/cad/goldfish.kicad_pcb)只有 F.Cu/B.Cu，板厚 **1.2 mm**，封装有 16 个信号接点、四个 0.60 mm 镀铜槽和板边缺口；作者把 USB4500 列在可选兼容接口表中。 | 比 breakout 更接近完整小板，可研究 ESD、保险丝、CC 与数据线布局；兼容列表并不证明这块板实际贴过 USB4500，也不能照搬 1.2 mm 板厚。 |
| [nRFMicro](https://github.com/joric/nrfmicro) | [KiCad 原生板文件](https://github.com/joric/nrfmicro/blob/main/hardware/nrfmicro.kicad_pcb)只有 F.Cu/B.Cu，板厚设为 **1.6 mm**，使用另一款中置接口。 | 可参考完整无线小板的 USB 周边布局；板厚与接口均不同。 |

曾检查 [Tiny Tapeout Demo Board](https://github.com/TinyTapeout/tt-demo-pcb)：当前板文件是四层、约 1.56 mm，未在当前板文件中找到 USB4500，故不作为本次双层 USB4500 走线证据。

[嘉立创同型号物料页](https://jlcpcb.com/partdetail/6154270-USB4500_03_0A/C5354966)列出支持 SMT、仅标准型 PCBA、装配难度高。器件可贴装与本板制造包获批是两回事，现有 J1 焊脚模型危险仍需消除或取得针对实际图纸的确认。

## J1 原厂图纸与现有封装的可核对部分

2026-09-25 从本项目导出的 `.epro2` 中读取 `USB4500 E20` 封装主数据，并与 [GCT USB4500-03-0-A 原厂图纸](https://gct.co/connector/usb4500)的 *Recommended PCB Layout* 对照：8 个中间信号焊盘名义宽 **0.30 mm**、中心距 **0.50 mm**；两侧四个电源／地焊盘名义宽 **0.60 mm**。封装中的 12 个 SMT 焊盘同列，信号宽 `11.8 mil≈0.2997 mm`、宽焊盘 `23.6 mil≈0.5994 mm`，中心距约 0.50 mm；四个固定槽名义宽约 **0.60 mm**。这证明宽度与横向节距的基本方案有原厂依据。原厂图还明确 0.80 mm 板厚和 9.24 mm 缺口尺寸；具体公差、纵向焊盘位置和 SMT 模型仍需按共同基准叠图，不能仅凭网页接触比修改焊盘。

R15 把 12 个焊盘整体移动约 0.30 mm 后，网站接触比提高，但同时出现 12 条焊盘贴近缺口边缘危险，且位移没有保存到原生工程。这是网页模型的敏感性试验，**不是原厂图纸要求把焊盘移动 0.30 mm**。在封装主数据与贴片模型按共同基准核对前，保留 R14/R16 原焊盘位置。

[R17 诊断](production/r1-layout-reset-r17/README.md)随后把同样的 12 个焊盘位移写入封装主数据，并通过关闭重开及同版 Gerber 验证。原生 DRC 和线上 PCB DFM 都报 12 条焊盘贴近缺口边缘；这把“未保存”问题与“机械／工艺基准”问题分开了。GCT 图中焊盘与缺口的接近关系是图纸观察，尚不能证明本板的零间隙加工被嘉立创接受。应在共同基准叠图及成品层核对后，再决定维持中置连接器并取得工艺认可，还是换更容易制造的接口方案。

## 本板 USB 走线实测

从 [R16 重开工程快照](records/r1-layout-reset-r16-routed-snapshot.json)提取连接器及保护器件附近的[顶／底层走线图](records/r1-layout-reset-r16-usb-routing.png)。`USB_CC2` 全网有 **4 个过孔**；连接器侧 `USB_DM_CONN` 有 **5 个**（其中 4 个在图示 70–82.5 × 21–31 mm 区域），`USB_DP_CONN` 有 **2 个**（图示区域 1 个）；`USB_CC1` 没有过孔。图上 CC2 在底层从连接器两组焊盘绕到中部，VBUS 在顶层绕开中心区，说明当前扇出需要专门重审。不能仅凭过孔数宣称电气错误，仍要逐段检查路径、保护器件顺序和地回流。

对照 Goldfish v2 原生板文件，其 D− 全网 **1 个过孔**、D+ 与两个 CC 网络 **0 个过孔**；但它的 ESD／电源拓扑和器件位置与本板不同，只能说明两层不必天然堆出大量信号换层，不能照抄过孔数。优先重排 USB 小区的网络出口与保护器件周围布线，再判断能否减少这些换层。

## 用于下一版的检查顺序

1. 按原厂完整推荐图确定焊盘、四槽、缺口、板厚和连接器实体包络；在原生工程中保存重开后验证封装几何。
2. 先从 USB 引脚按网络分组扇出，安排 VBUS、GND、CC1/CC2、D+/D− 和保护器件，尽量减少 USB 局部不必要的换层；保留 ESD 在分支之前及去耦的服务关系。
3. 再核对双层地回流、过孔／焊盘／板边间距、阻焊桥和丝印；生成 Gerber、BOM、CPL 后跑本地及供应商 DFM。
