# 新 PCB 开工清单与参考入口

## 当前确定方案

2026-09-28：围绕 **0.8 mm 中沉 USB-C＋标准型 SMT**重新设计，保持成品外形及电池、屏幕、NFC 总体布局。USB4110 仅作备选；中沉的确切料号、板边接受条件、治具与拼板尚未定型。沿用 2 层、1 oz、绿色阻焊作为试布基线，表面处理另按封装和实际报价选择。

**本轮交付为清单、参考和工具适用性评审；下一步先做设计输入包，再摆件和试布。**重布局已经授权，无需再次询问。客服由用户联系，代理先准备可审核的具体方案。本轮未创建或改写 EDA/CAD、运行新板 DRC、上传制造文件或测试硬件。

## 本次 review 已关闭的准备项

- [x] 将 USB4110／直板边的旧任务从当前[七区参考](../hardware/r1-seven-zone-reference-plan.md)中移出，保留为历史对照。
- [x] 合并重复待办，给每步指定输入、产物和进入下一阶段的条件；实际设计输入产物仍待完成。
- [x] 定位原厂图纸、布局章节、国内工艺说明和外部 PCB 的适用边界；8 份已有 PDF 的 SHA-256 与下载清单一致，新增参考见下表。
- [x] 审计现有检查器的 UUID、固定坐标、默认输入和写文件行为；已列出复用条件，尚未改成新板工具。
- [x] 重跑 USB4500 历史尺寸审查，独立 Gerber 对照通过；“9.20 mm 缺口宽”更正为后缘直线段，不再作为侧壁间距。

## 下一轮执行清单

下面是同一条执行链。P1–P3 可并行收集资料；P5 先准备工厂问题，随 P2/P4 形成的局部图补齐，不必等整板完成才询问。未打勾表示产物未完成，不能把已有参考当作验收结果。

| 步骤 | 输入与工作 | 必须交付的产物／完成条件 | 依赖与负责方 |
| --- | --- | --- | --- |
| ☐ P0 同版电气基线与工具身份 | 以 [R21 原生工程](../../../eda/NFC-Card-R1-Layout-Reset-R21-USB-CC2.eprj2)的已核功能为起点，检查磁盘与打开工程身份、未保存修改；按最终 J1 同步符号／焊盘／网络／BOM | 同一候选的原理图网表、BOM、引脚及封装表、输入指纹；列出相对 R21 的有意变更。J1 未选定时保留明确占位差异，不能宣称输入已冻结。导出工具先绑定候选 UUID，旧工程保持可对照 | 代理；先导出基线，P2 选料后闭合 J1 差异 |
| ☐ P1 机械限制图 | 现有板框、屏体／FPC 图、4.8 mm 薄壳、背面 NFC、电池、三键和五点调试接口 | 同一坐标系正反面图及关键剖面：本体、装配／插拔空间、FPC 插入弯折、磁片与电池引线、键帽运动、两类天线净空；标明硬约束和可移动簇。U1、去耦和可拆工艺边共同推导 | 代理重建；涉及实物差异时向用户列出具体待量尺寸。功能区定型前完成 |
| ☐ P2 工艺与封装表 | [国内工艺复核](../hardware/jlc-mid-mount-process-review-2026-09-28.md)、[USB 共同基准](../hardware/usb4500-datum-review-2026-09-28.md)、R21 DFM 根因和原厂推荐焊盘 | 每条写清对象、制造下限、设计目标、来源、例外、EDA 字段／补充检查。逐一核 J1/J2/U1/U2 焊盘、阻焊、锡膏、模型和方向；比较确切中沉料号，给出拟选料号和含公差的板框关系。普通区先试 0.30 mm 孔／0.60 mm 外径、0.20 mm 铜距；这些是留余量目标，细间距扇出另审 | 代理；设置规则并用可丢弃小样验证命中后才试布。供应商边界交 P5 |
| ☐ P3 电源与保护预算 | BQ25186、TPS7A02、TPS22919、屏幕外围、实际电池规格及 R21 电源网络 | 分列 USB 输入、充电、系统峰值与热耗散；检查屏幕刷新＋无线并发、低电压 LDO 余量、VBUS 到 U1/U2 的保护覆盖。结论是现有器件够用或明确需变更，并给依据；没有峰值数据时先给有依据的上界或测量计划，不能据此冻结电源区 | 代理算预算；用户补实际电池允许充放电规格。屏幕转接板测试按实际设备和授权安排 |
| ☐ P4 整体布局与关键区试布 | P0–P3 的已闭合输入、[七区参考](../hardware/r1-seven-zone-reference-plan.md)和[外部双层板](../hardware/usb-mid-mount-two-layer-references.md) | 独立候选、带尺寸的布局图、供回电／信号通道图；先试 USB／保护和屏幕电源。记录实际过孔、路径、地回流、同网近距、阻焊和装配间隙；保存重开后检查。未布网络单列，局部通过不能写成整板通过 | 代理；未定接口只作明确标注的候选试验，不能当已获认可的生产尺寸。整板详细布线前完成 |
| ☐ P5 工厂确认包 | P2 的确切料号、原厂叠图与局部制造层，P1/P4 的工艺边和生产拼板候选 | 用户可直接发送的材料及问题：是否保留近边焊盘、成品边／槽／板厚公差、沉板定位焊接治具、U1 边缘装配与分板、细间距阻焊／锡膏处理、分项费用。记录回复对应文件版本和接受条件，回写 P1/P2 | 代理备料，用户问客服；USB 区和拼板定型前闭合相关条件 |

下一项具体交付是 **P0–P3 设计输入包**：同版电气基线、机械限制图、工艺／封装表、电源预算。小证据存 `hardware/records/`，解释存项目文档；新原生候选放仓库 `eda/`，使用独立文件名。复用现有工具，针对实际新输入适配，不先开发通用重设计框架。

## 已确认且不应重复推翻的输入

- **电池由用户适配，继续追求 4.8 mm 薄壳目标。**[旧薄壳候选](../enclosure/r1-usb-fit-4.8/README.md)主体内腔 3.2 mm，电池预留 32.5 × 14 × 3.2 mm 是空腔量规，不含胶、引线与膨胀分配；不再用旧 3.4 mm 电池假设强制增厚。新板与薄壳仍需配合验证，4.8 mm 不是已保证的成品厚度。
- 保留屏幕电源控制、C14/C15/C19 三颗现有 4.7 µF、TS 固定 10 kΩ、可控电池采样、五点 SWD／NRESET；不因重布局重复增件或扩大功能。
- R21 UTF-16、Tab 分隔 BOM 有 29 组／66 器件，引脚表有 66 位号／256 引脚。R19 接 TS/MR 到 GND；R20–R23、Q2/Q3/C25 已组成采样支路。`USB_VBUS` 接 J1、C1、C8、U1.32、U2.10，U5/U6 分别保护数据与 CC；VBUS 保护覆盖需在 P3 判断。读取旧表不等于新同版网表已验证。
- U1 的 P1MV2 物料与现有 `1MV2` 命名封装已按官方库核完 61 焊盘；无需重做“是否兼容”的泛查。新坐标下仍要重验天线、去耦、板边与装配。J2 是 `FPC-05FB-24PH20`，不能套旧 FH12A 图。

## 前置参考已定位到哪里

截至 2026-09-28。器件阈值以对应原厂版本为依据，网页工艺条款以后按实际下单复核。PDF 缓存位于被忽略的 `downloads/`；[下载清单](download_manifest.json)保存来源、版本说明及 SHA-256，不把缓存当已入库附件。旧记录的失败尺寸和外部板的坐标不是新板默认值。

| 用途／步骤 | 一手参考与具体入口 | 本板适用范围与剩余工作 |
| --- | --- | --- |
| USB 机械，P1/P2 | [GCT USB4500 A1，2023-05-31](https://gct.co/connector/usb4500)第 1 页推荐 PCB 图；[HRO M-13 原厂图 A，2018-01-12](https://atta.szlcsc.com/upload/public/pdf/source/20190321/C223906_97EBC11092760FCA5FB297BEECA53A8E.pdf) | 两份图及 [R14/R17 叠图](../hardware/usb4500-datum-review-2026-09-28.md)已有；HRO 缺少完整缺口定位尺寸，不能直接替换。USB4500 近零板边、公差须 P5 确认 |
| PCB／SMT，P2/P5 | [PCB 能力表](https://www.jlc.com/portal/vtechnology.html)、[可贴工艺](https://www.jlc-smt.com/help_document/id/4025.html)、[治具说明](https://www.jlc-smt.com/help_document/id/36095.html)、[新阻焊说明](https://www.jlc.com/portal/server_guide_34402.html) | 支持标准型沉板路线的依据已在[国内复核](../hardware/jlc-mid-mount-process-review-2026-09-28.md)整理；还须把条款映射到新封装／规则／拼板，不能用可贴库资格代替本板审核 |
| 充电 U2，P2/P3/P4 | [BQ25186 SLUSF69A，2025-01](https://www.ti.com/lit/ds/symlink/bq25186.pdf) §5、§7–9、DLH 封装图，§9 布局见第 48 页 | 本地 PDF 指纹已复核；C8→IN、C2→SYS、C3→BAT、EP 接地和散热关系先定，再计算充电／系统电流；IC 额定值不是整板能力 |
| LDO U3，P3/P4 | [TPS7A02 SBVS277C，2022-09](https://www.ti.com/lit/ds/symlink/tps7a02.pdf) §6、§8.4；DBV 布局图 8-7 | 本地指纹已复核；使用本板 SOT-23-5 DBV 图，不套 DQN/YCH；200 mA、压差、瞬态和热预算需结合负载 |
| 屏幕开关 U4，P3/P4 | [TPS22919 SLVSEN5B，2019-05](https://www.ti.com/lit/ds/symlink/tps22919.pdf) §6、§9–11；布局第 18 页 | 本轮补缓存／指纹；核 C9/C10 服务关系、上电浪涌、放电与控制，不把开关额定电流当屏幕峰值 |
| USB 保护 U5/U6，P3/P4 | [TPD2EUSB30 SLVSAC2G，2021-06](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf) §10，第 11–13 页；[TI SLVAF82B，2024-01](https://www.ti.com/lit/pdf/SLVAF82) §2/3、§7 | 本轮补缓存／指纹；复用 DRT 三引脚保护路径及低阻接地方法，核数据、CC、VBUS 各自覆盖。应用笔记用于选型评估，不把其中 USB-PD 方案或 USB 3.0 坐标照搬到本板 |
| U1 模块，P1/P2/P4 | [Raytac MDBT50Q-P1MV2 Rev L](https://www.raytac.com/product/ins.php?index_id=47) §2.2–2.4；[官方 Eagle/STEP 已核记录](../hardware/r1-r21-u1-edge-decision.md) | PDF 指纹及 61 焊盘证据可复用；新模块／去耦簇、BLE 无铜区、工艺边重新推导 |
| 屏幕／FPC，P1/P2/P3 | [GDEH0154E01](https://www.good-display.com/companyfile/2038.html)、[DESPI-E01 原理图](https://www.good-display.cn/companyfile/1817.html)、[指南](https://www.good-display.cn/companyfile/1816.html)、[XUNPU FPC-05FB-24PH20 图 Rev A](https://www.lcsc.com/datasheet/C2856831.pdf) | 4 份本地指纹已复核；面板尺寸／接线和转接板电路可用，实际排线朝向、升压外围选择及峰值仍要按[专项评估](gdeh0154e01-evaluation.md)核对。三颗 4.7 µF 保留为现方案，不声称已实测 |
| NFC／按键，P1/P4 | [nRF52840 NFCT](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/nfc.html)、[Nordic NWP026](https://docs.nordicsemi.com/r/bundle/nwp_026/page/wp/nwp_026/nwp_026_intro.html)、[ALPS SKQG](https://tech.alpsalpine.com/c/products/category/tact-switch/sub/02/series/skqg/) | NFCT 按实际 nRF52840 核；NWP026 针对 nRF52832，仅借鉴调谐方法，不能照搬电容值。按键对位／行程见[封装研究](../hardware/r1-packaging-study.md)，成品调谐和手感留样板 |
| 双层扇出，P4 | [Adafruit、Goldfish、CoolerMaster 固定版本核查](../hardware/usb-mid-mount-two-layer-references.md) | 已记录板厚、孔径、保护器件和装配差异；可借鉴路径，尚无“USB4500＋本板保护＋0.30 mm 孔”的整套可直接复制设计 |

规则冲突按[PCB 规则索引](../../../docs/pcb-design-rules.md)与 [pcb-methodology](../../../.agents/skills/pcb-methodology/SKILL.md)处理，敏感件以命名引脚、实际路径和一手来源审核。没有来源的数值明确写为设计目标或待验证假设。

## 工具复用前必须检查

实际操作从[环境自检](../../../docs/environment.md)开始；本轮只读脚本并运行历史尺寸审查，没有把新板流程跑通。

| 入口 | 当前适用性／下一轮动作 |
| --- | --- |
| [快照导出](../scripts/eda-export-r1-snapshot.js)、[PCB 引脚导出](../scripts/eda-export-pcb-pins.js) | 固定旧 R1 项目 UUID 和 PCB UUID `8033127c48771f3b`，会打开该文档；不能直接对新候选执行。P0 先绑定候选并核项目／页身份、输出路径 |
| [逐脚网表核对](../scripts/check-netlist-consistency.py) | 可复用；必须显式传同候选的 `--sch`、`--pcb`，不能拿旧 58 器件导出与新板比较 |
| [独立铜连通](../scripts/check-r1-copper.py) | 支持 `--snapshot`／`--output`，但内含固定屏幕区与 `r1-battery-b-plan.json`；P1 后核对净空及允许穿越路径，再作为新板检查。连通通过不证明敏感件电气合理 |
| [路线预检](../scripts/check-proposed-route.py) | 可复用计算；始终显式给新候选 `--snapshot` 和 `--route`，禁止依赖旧默认快照 |
| [旧 R1 交付检查](../scripts/check-r1-delivery.py) | 固定 58 位号、旧工程与 E20D 几何；还会改写旧 BOM/CPL 编码及旧报告。不能作为新板检查运行；后续按新输入适配必要部分，输出到新记录 |
| [旧板框检查](../scripts/check-e20-outline.py)、[USB4500 尺寸复核](../scripts/review-usb4500-datum.py) | 都是历史版本专用。后者校验 R14/R17 快照与 Gerber、生成叠图；前者旧 `usb_notch_width_mm` 不是侧壁间距。两者不替代新封装、公差或原生 DRC |

## 样板阶段与固件交接

最终装配后的 NFC 调谐／读距、USB 稳定性、温升、待机电流、屏幕全范围表现及键帽／打印公差需样板。现在预留可测点和首板上电顺序，不要求布局前全部实测。可能改变电源器件的负载边界则在 P3 处理。

CE／充电看门狗、USB 状态限流、LFRC、屏幕上掉电及 BUSY 超时列入固件交接，不据此自动加芯片、晶振或按键。PN532 桌面试验仅验证交互思路，不能证明本板 NFCT、线圈或六色屏电源可用。接线、通电与烧录按实际设备和授权执行。

## 本轮检查记录

- `python3 projects/nfc-business-card/scripts/review-usb4500-datum.py`：通过 R14/R17 的 16 个 J1 铜焊盘和板框端点独立 Gerber 对照，重建 JSON／PNG；尺寸图已目视检查。
- Python 本地链接检查、13 份相关 PDF 的大小及 SHA-256 核对通过；新增缓存只登记来源与指纹，PDF 本体不入 Git。
- `git diff --check`：通过。新板的 EDA 规则命中、保存重开、原生 DRC 和制造审核均留待实际候选阶段，不计入本轮通过项。

## 历史回查的发现

范围为本机 Codex 的 `NFC card`、`NFC 调研薄型 NFC 卡片方案`、`NFC 3D打印外壳`、`EDA 继续硬件NFC卡片PCB与CAD设计`。先用应用任务工具读取，再对前两项的本地 JSONL 提取相关用户消息；归档外壳和早期 EDA 任务只读相关分页。这不是跨机器、Claude/DeepSeek 或全部历史的穷尽检索。

- `NFC card`：9 月 24 日用户已经要求低成本工艺、0.30 mm 钻孔、约 0.10 mm 径向孔环、尽量 0.15 mm 异网间距；当天也明确要求保留旧版、独立重做功能分区。后续又指出布线后改过孔导致顺序混乱。新一轮必须验证约束进入工具和布局，不能仅再写一次重做提示词。
- 同一任务：用户要求直接电池采样，随后允许在确实挤不下时省略。它是可评估的简化选项，不表示现在应删除；R21 已有采样电路，先保留并计算占地。
- `EDA 继续硬件NFC卡片PCB与CAD设计`：用户已选择五点 SWD／NRESET 恢复，不增加隐藏 RESET，不因重新规划扩大功能范围。
- `NFC 3D打印外壳`：用户选简单独立打印蘑菇键帽，曾研究 4.8 mm 壳体；该几何基于旧接口。6.3 mm USB4110 候选是后续名义解，尚不能表述为用户已经接受的最终厚度。

本地原文追溯：Codex `sessions/2026/09/24/rollout-2026-09-24T14-18-42-01a0d210-f8e2-7c81-81ab-2c6198d16d74.jsonl` 第 6167（工艺）、10443（独立重做）、10762（采样可省）、13819（执行顺序）行。历史消息解释决策来源，工程事实仍以对应版本文件为准。

## 已有核查证据（不是新板验收）

| 项目 | 结果与边界 |
| --- | --- |
| Git | 本轮清单评审起点为 `9f988b1`，位于 `master`；此前重规划记录为 `41e76b0` |
| R21 文件身份 | 原生工程、快照、Gerber、BOM、CPL 的 SHA-256 均与[制造记录](../hardware/records/r1-layout-reset-r21-manufacturing.json)匹配；只读 SQLite `PRAGMA quick_check` 为 `ok`。证明文件一致与完整，不证明电气正确 |
| TS 固定电阻 | [R21 BOM](../hardware/production/r1-layout-reset-r21/NFC-Card-R1-Layout-Reset-R21-USB-CC2-bom.csv)中 R19 为 10 kΩ；[PCB 引脚表](../hardware/records/r1-layout-reset-r21-pcb-pins.json)显示 R19 接 `BAT_NTC_TBD`—GND，U2.6 同网。旧文档“尚未加入”已过期 |
| 电池电压采样 | R20–R23、Q2/Q3、C25 已存在；U1.10=`BAT_MEAS_EN`、U1.11=`BAT_ADC_SENSE`。不能再按旧 R1 的“没有采样”重复增件；准确度/采样时间未实测 |
| 历史 R21 连接器 | R21 BOM 的 J1=`USB4110-GF-A`，J2=`FPC-05FB-24PH20`；新板已确定中沉方向，需要明确更换 J1 并同步原理图／PCB，不能混用旧 USB4500 封装或 FH12A 屏幕座 |
| 工具环境 | 子模块已初始化；前次检查桥接为按需停止状态，不是故障；实际使用前按环境文档自检。尚未启动 EDA 做本轮读写/保存重开验证 |
| 空间 | 已有[约 43.28 × 49.8 mm 右侧包络估算](pcb-replan-2026-09-28.md#当前空间余量的初步判断)；没有完成器件/机构/通道扣除，尚不能称“余量充足” |
