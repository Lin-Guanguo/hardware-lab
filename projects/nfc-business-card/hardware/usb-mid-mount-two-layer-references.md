# 双层中置 USB-C 公开参考

## 当前确定方案

2026-09-28 补充：[共同基准复核](usb4500-datum-review-2026-09-28.md)已确认 R17 焊盘纵向位置接近 GCT 推荐，但铜到缺口近零；旧 9.20 mm 指标是后缘直线段，实际侧壁间距为 9.60 mm。原厂尺寸一致性与工厂接受条件仍需分别闭合，下面的外部布线例子不构成该板边结构的加工放行。

同日追加找到 CoolerMasterUsbC 的 JLC 下单、治具与实物反馈记录，见下节。核实后它属于双面焊脚夹板式，推荐下单 1.0 mm；它支持继续研究相关薄型工艺，但不是 USB4500 的同条件制造案例。用户最新方向仍为优先保留中沉，普通顶部贴装只作备选。

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

## 2026-09-28：参考文件的工艺边界复核

本轮只在内存中读取公开源文件，未导入本项目或复制上游代码。后续正式采用参考工程时仍按仓库 submodule 约定固定版本。

| 参考与核对版本 | 本轮核实 | 对本板的用法 |
| --- | --- | --- |
| [Goldfish v2 板文件](https://github.com/staticintlucas/goldfish/blob/03b6db501b80048ce1675b586826d4a5abf1e7e1/cad/goldfish.kicad_pcb) | 1.2 mm、两铜层；连接器侧 `/D-` 一孔、`/D+` 和两个 CC 网无孔；该数据孔外径 0.50 mm、钻孔 **0.20 mm**；保护器件为 USBLC6-2P6 | 参考双插向触点汇合、保护器件朝向和连续通道。它未证明本项目 0.30 mm 钻孔可布通，保护器件也不同，不能直接复制铜线 |
| [Adafruit Sunken 板文件](https://github.com/adafruit/Adafruit-Sunken-USB-Type-C-Breakout-PCB/blob/4cb1207ddd6eae864f4410d110bac38072e9b895/Adafruit%20Sunken%20USB%20Type%20C%20Breakout.brd) | `layerSetup=(1*16)`；全板四孔，钻孔均 **0.3937 mm**：D− 两孔、VBUS/GND 各一孔，D+/CC1/CC2 无孔；是接口与两颗 5.1 kΩ 电阻的简单 breakout | 有[成品页](https://www.adafruit.com/product/6050)，标注整板约 20.4 × 14.7 × 3.3 mm。较大孔的双层扇出有实际参考，但不覆盖本板 ESD／充电，也未证明相同型号和 0.8 mm 板厚 |
| [Goldfish-clone-JLCPCB](https://github.com/JeremyJStarcher/Goldfish-clone-JLCPCB) | README 明确警告 Rev A 的 USB 安装有设计问题、不要使用；其修改说明还有四层及改手焊接口 | **不作为嘉立创成功量产案例**。仓库名包含 JLCPCB 不能替代作者的装配与测试证据 |

读取文件 SHA-256：Goldfish `7e30e5f9a63e4205adb32d22cf740993667d9478ad56157dfdabfc98f4dc62e7`；Adafruit `69c93336fbd822bb387f3f753466ece7d1254a1f5a956ddee6fc482309b2dc7b`。本轮没有运行参考工程的原生 DRC，以上为文件解析及产品页证据，不是本板制造或性能验证。

## 2026-09-28 追加：JLC 夹板式实物案例

来源为作者 [davek184/CoolerMasterUsbC](https://github.com/davek184/CoolerMasterUsbC/tree/d09e3ea05ac0b194804ebe01a342152fa276ca35)，本轮只在内存中读取提交 **`d09e3ea05ac0b194804ebe01a342152fa276ca35`** 的文件，未导入工程或运行上游脚本：

- `pcb/CoolerMaster-USB-C.kicad_pcb`：仅 F.Cu/B.Cu；板厚字段和叠层仍为 1.6 mm。
- `manufacturing/jlcpcbv1.4_bom.csv`：J1 为 C67381；国内[物料详情](https://www.jlc-smt.com/lcsc/detail/C67381.html)对应精拓金 **918-418K2021E40000、24 接点、夹板焊接**。不能把论坛泛称的 mid-mount 当作 USB4500 相同结构。
- `manufacturing/jlcpcbv1.4_gerber.zip`：只有前后两铜层，包含前后锡膏层；J1 在两面各有 12 个电气焊盘及两个外壳焊盘。Gerber 与源文件的下述局部尺寸一致。
- 作者 README 明确下单 **1.0 mm、JLCPCB 标准型装配**，不能沿用源文件的 1.6 mm 默认值；文档称 v1.2 已成功工作，v1.3/v1.4 修改了生产工艺边。当前固定提交的文件不是已收到实物的逐项实测报告。

局部尺寸核对：J1 局部坐标中，电气焊盘中心 `y=0.25 mm`，长度 `1.70 mm`，缺口中间直边 `y=1.40 mm`，故到该直边距离为 `1.40−(0.25+1.70/2)=0.30 mm`。Gerber 的焊盘中心 Y 为 −35.08760 mm、长 1.70 mm，缺口直边 Y 为 −33.93760 mm，独立计算同为 0.30 mm。这里只衡量电气焊盘与中间直边，未评价全板最小间距、外壳焊盘、装配公差或电气设计。板文件 SHA-256 为 `713f1d2bc24b5afbea801262c6bf8e490687b6b7ee679d22bc7c77f33484ec6d`。

[原作者及使用者讨论](https://www.keebtalk.com/t/novatouch-usb-c-daughterboard/19388)记录：2023-07-08 使用者向 JLC 下单；07-10 转述工厂因 J1 要求治具，报价 46 美元，并要求把工艺边放到其它侧；作者随后调整制造文件。讨论同时有装机照片、工作反馈及后续兼容性反馈。这是可追溯的历史交付经验，费用不代表今天国内报价，工艺边方向也不是所有中沉器件的通用规定。

**对本板的价值：**相关接口确实存在标准型装配加治具的交付路径，工艺边必须服从接口装配。**不能照搬之处：**1.0 mm 夹板、双面焊脚和 0.30 mm 间距均与 USB4500 的 0.8 mm、单面信号焊脚、近零板边不同；不复制该封装，也不把该板数据布线或通过条件视为本板已验证。

## 用于下一版的检查顺序

1. 按原厂完整推荐图确定焊盘、四槽、缺口、板厚和连接器实体包络；在原生工程中保存重开后验证封装几何。
2. 先从 USB 引脚按网络分组扇出，安排 VBUS、GND、CC1/CC2、D+/D− 和保护器件，尽量减少 USB 局部不必要的换层；保留 ESD 在分支之前及去耦的服务关系。
3. 再核对双层地回流、过孔／焊盘／板边间距、阻焊桥和丝印；生成 Gerber、BOM、CPL 后跑本地及供应商 DFM。
