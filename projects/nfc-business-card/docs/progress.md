# R1 progress

## 当前确定方案

2026-09-28 开工清单 review：确定 **0.8 mm 中沉 USB-C＋标准型 SMT**，保持外形和电池、屏幕、NFC 总体布局。[P0–P5 清单](pcb-start-readiness-2026-09-28.md)已合并重复待办、纠正七区表的 USB4110 旧约束，并集中列出原厂章节与工具适配点；补存 TPS22919、TPD2EUSB30、TI USB 保护参考及下载指纹。下一步先完成同版电气、机械限制、工艺／封装和电源预算输入包，再开展独立候选与试布。工厂问题由代理备图、用户询问。本轮未改 PCB/CAD。

2026-09-28：[开工准备核查](pcb-start-readiness-2026-09-28.md)回查了四个本机 Codex 任务，核对 R21 工程/快照/制造文件五项指纹和 SQLite 完整性，并确认 TS 电阻及电池采样已存在。已校正过期文档入口；机械版本、工艺/封装约束、电源负载预算与新同版原理图导出仍需整理。可以开始准备与布局实验，暂不展开整板详细布线；未改 EDA 或执行新的 DRC/DFM。

2026-09-28：用户决定在 `master` 上重新规划 PCB，停止沿 R21 局部修补；[新一轮范围与完成条件](pcb-replan-2026-09-28.md)替代下列历史记录中的“下一步”。首轮交付新整体布局、关键网络与回流通道、独立工程的局部试布证据，随后评审是否进入整板布线。R21 仅作对照，已核实的原理图、封装和机械要求继续复用；本次只记录决定，尚未修改 EDA 或启动新设计验证。

2026-09-26：[R21 U1 板边三路线比较](../hardware/r1-r21-u1-edge-decision.md)以 Raytac 原厂本体、R21 引脚和外壳 CAD 为基准：U1 距成品板边名义 0.066 mm，与 C1/C6/C7 本体约 0.534 mm；单独内移 0.5 mm 会将后者压至 0.034 mm，成品局部扩板 0.5 mm 则与外壳零间隙。[Raytac 官方 Eagle/STEP 叠图](../hardware/records/r1-layout-reset-r21-u1-official-overlay.json)核完 61 个焊盘，最大中心偏差 0.0021 mm，天线禁铜区无铜侵入，STEP 至外壳 0.566 mm。嘉立创中文拼板指导明确板边元件距边 <3 mm 时应加工艺边，常规宽度约 5 mm；本 L 形板需自行拼板或付费不规则拼板。下一步保留 R21 坐标，建可拆工艺边独立拼板、核对锡膏/阻焊及网页 U1 模型。本轮只读、无 EDA 或生产包修改。

2026-09-26：[R21 USB4110 6.3 mm 独立外壳几何候选](../enclosure/r1-usb4110-6p3/README.md)已从同版 Gerber 重建板框和两颗定位孔，将旧 J1 参考体换为 GCT 名义尺寸包络。上壳抬高 0.5 mm、屏幕和三键同步；保存重开后接口与壳体最短名义距离 0.32 mm，外壳脚宽度包络距壳 0.449 mm，端口不相交，三键约 0.50 mm 全行程无碰撞。STEP 五实体有效、上壳 STL 封闭并已目视检查。缺真实连接器/插头、公差及其余 R21 器件 CAD 同步；U1 板边 0.066 mm 与 PCB/SMT DFM 危险仍在，未改 EDA 或下单。

2026-09-26：[R21 布线前复核](../hardware/r1-r21-pre-routing-review.md)冻结同版工程、引脚表与线上 DFM，确认旧 USB 槽、J1 焊脚重叠和 VIA 孔到焊盘危险已清零。U1 `P1MV2` 物料与 `1MV2` 命名封装按 Raytac 图纸抽查五个焊盘，坐标吻合；原厂本体上缘对 Gerber 顶边仅约 0.066 mm，与网站 0.07 mm 危险相符，需比较拼板工艺边、内移和扩板。USB4110 与 5.8 mm 外壳名义约 0.18 mm 干涉仍在。VBUS 两支明线已拆算，下支 11.882 mm 为 0.15 mm 宽，载流是否可接受仍取决于实际输入电流/铜厚。网页计数或走线外观不再单独触发整板重排。此次只更新复核与门槛，未改 EDA 或制造文件，仍不可下单。

2026-09-26：[R21 USB CC2 局部候选](../hardware/production/r1-layout-reset-r21/README.md)从 R20 仅重布 `USB_CC2`，去除并行底层绕行。过孔 4→2，线长 12.454→8.196 mm；器件、焊盘、原理图网络、天线、板框不变。首次布线产生微小孤立 GND 铜，已在独立试验中修正；最终工程保存重开后原生 DRC 0，独立连通无孤立铜，离散异网 0.15 mm 间距、Gerber 钻孔／孔环、BOM/CPL 检查通过。[线上 R21 PCB／SMT DFM](../hardware/production/r1-layout-reset-r21/vendor-dfm-2026-09-26.md)已完成：网页最小线距 0.15 mm，VIA 孔到焊盘危险 6→0，USB 槽与 J1 焊脚重叠危险 0，BOM 29/29 组匹配；仍有焊盘距焊盘 3、开窗露线 3、阻焊桥 43、U1 板边 0.07 mm 等危险。[逐孔复核](../hardware/r1-usb-routing-review-r21.md)确认 D− 五孔各有几何任务，U5 GND 已有约 2.30 mm 顶层明线到地过孔，向北直连会与 D+ 相交，试布已撤销。下一步先按同版 Gerber／网络定位局部危险、核对 U1 模型与 USB4110 外壳，再决定是否联合重布 D+/D− 和 VBUS；**不可下单**。

2026-09-26：[R20 过孔间距候选](../hardware/production/r1-layout-reset-r20/README.md)在 R19 上局部移动 C23、R7/R9 和 NFC2 附近三个过孔，未移动器件、USB 接口、板框或天线。保存重开后原生 DRC 0，66 个位号／256 个引脚网络一致；独立连通、NFC、Gerber 钻孔／孔环、0.15 mm 异网离散铜间距及 BOM/CPL 检查通过。本地三处同网孔到焊盘 <0.10 mm 配对已消；[Gerber 已上传](../hardware/production/r1-layout-reset-r20/vendor-dfm-2026-09-26.md)，但 R20 线上 PCB／SMT 结果未读到。下一步读取网站结果，再手工简化 USB 扇出并处理剩余阻焊、孔环、装配和外壳问题；**不可下单**。

2026-09-26：[R19 USB4110 同步候选](../hardware/r1-usb4110-sync-r19.md)修正了 R18B 原理图 J1 沿用旧符号导致的“器件／封装属性有误”。官方符号的 14 个有网络引脚保持原连接，SBU1/SBU2 不接；保存重开后原生 DRC **0**，原理图／PCB 66 个位号、256 个引脚逐脚一致。PCB 器件、焊盘、线、孔、板框和铺铜与 R18B 逐项相同。下一轮局部重布 USB 扇出、定位线上剩余工艺危险，并做真实 USB4110 机械候选；**不可下单**。

2026-09-26：[R18B USB4110 独立诊断](../hardware/production/r1-layout-reset-r18b/README.md)完成整颗 J1 库器件替换、直板边、两颗 Ø0.65 mm 非镀定位孔、同版 Gerber／BOM／CPL 与[嘉立创 PCB／SMT DFM](../hardware/production/r1-layout-reset-r18b/vendor-dfm-2026-09-26.md)。旧接口四槽危险 4→0、J1 焊脚相交危险 12→0，BOM 29/29 组自动匹配；保存重开的原生 DRC 几何错误 0，但有 1 条 `Import Changes`，原理图 J1 仍带旧 USB4500 符号。孔环、阻焊、局部间距和 U1 贴装危险未关闭；现有 5.8 mm 外壳名义干涉约 0.18 mm。下一轮先同步原理图、重布 USB 局部并建独立外壳候选，**不可下单**。

2026-09-25：按[GCT 原厂图与嘉立创物料页比较 USB4500／USB4110](../hardware/usb-connector-options.md)。USB4110 是 16 针顶部贴装，四个外壳 SMT 焊盘和两个 Ø0.65 mm 定位孔，可避开中置缺口与四个 0.60 mm 镀铜槽；料号 C5143397 的网页列为 Economic/Standard PCBA、装配难度 High。现有 5.8 mm 外壳按名义高度会与其干涉约 0.18 mm；若保留约 0.30 mm 顶部间隙，需研究约 6.3 mm 的独立外壳候选。连接器和外壳路线待用户选择，不改现有 BOM／外壳交付版。

2026-09-25：[R17 USB4500 封装诊断](../hardware/production/r1-layout-reset-r17/README.md)从 R16 独立导出项目，在封装主数据里把 J1 的 12 个 SMT 焊盘中心从 113.2 改为 101.4 mil；导入、保存、关闭重开后位置保持。原生 DRC 新增 **12 条 J1 焊盘到缺口边缘错误**；独立连通、0.30 mm 钻孔、≥0.1016 mm 径向孔环、离散异网 0.15 mm 间距及板框／槽几何检查通过。[嘉立创 PCB／SMT DFM](../hardware/production/r1-layout-reset-r17/vendor-dfm-2026-09-25.md)的 VIA 孔到焊盘危险 12→6、焊盘距外型线危险 0→12；BOM 29/29 组匹配。J1 焊脚接触比约 0.35→0.50，但 **12 条 SMT 危险仍在**。下一步先按 GCT 图纸统一焊盘／槽／缺口／CPL 基准，明确这处板边铜是否符合普通制造与装配，再重布 USB；**R17 不可下单，R14 仍是 DRC 0 审核基线**。

2026-09-25：按七个功能区整理了[器件原厂参考与重排门槛](../hardware/r1-seven-zone-reference-plan.md)。USB、充电／稳压、屏幕供电、主控天线各有不能为整齐而打散的局部关系；按键和普通控制线有更多排布自由度。此前单焊盘 API 试验只改变实时坐标，未持久写入；R17 改为修改封装主数据并经重开验证。

2026-09-25：[R16 USB 缺口诊断](../hardware/production/r1-layout-reset-r16/README.md)把缺口最窄宽加至约 9.20 mm、内角 R0.20 mm，重开工程后原生 DRC 0、独立连通／NFC／间距／板框／钻孔检查通过。[线上 PCB／SMT DFM](../hardware/production/r1-layout-reset-r16/vendor-dfm-2026-09-25.md)显示焊盘距外型线危险 0，但 J1 接触比仍约 0.35、12 条装配危险未消；孔环、阻焊和槽宽问题仍在。R0.20 加工及装配公差尚未确认，**不可下单**。[双层中置接口参考](../hardware/usb-mid-mount-two-layer-references.md)已整理。

2026-09-25：[R15 USB4500 焊盘诊断](../hardware/production/r1-layout-reset-r15/README.md)当次 Gerber 将 12 个信号焊盘位移 0.29972 mm，[线上 DFM](../hardware/production/r1-layout-reset-r15/vendor-dfm-2026-09-25.md)显示 J1 接触比约 0.35→0.50，同时出现 12 条焊盘到缺口边 0 mm 危险。**事后重开原生工程发现焊盘位移未保存**，当次 Gerber 无法由保存工程复现；先修封装持久化，R15 仅作敏感性诊断，不下单。

2026-09-25：[R14 独立候选](../hardware/production/r1-layout-reset-r14/README.md)在 R12 上只移动 R1、C1、C8 和 SWDIO 附近四个过孔及短线；R13 的 R7 移孔因产生新焊盘间距危险已撤销。原生工程保存重开后 DRC 0；独立连通、NFC／板框、约 0.30 mm 钻孔、≥0.10 mm 径向孔环与异网 0.15 mm 间距检查通过。本地同网孔到焊盘薄间距的不同过孔 **8→4**；[嘉立创 PCB/SMT DFM](../hardware/production/r1-layout-reset-r14/vendor-dfm-2026-09-25.md)的 VIA 孔到焊盘危险 **20→12**，BOM **29/29** 组匹配。孔环 100、阻焊桥 43、USB 四槽、J1 焊脚相交 12 和 U1 板边 0.07 mm 危险仍在；[根因复盘](../hardware/production/r1-layout-reset-r14/dfm-root-cause-review-2026-09-25.md)将其归并为固定封装、局部过孔及线上图元／贴片模型问题，下一步先做原厂封装和成品层复核，**不下单**。

2026-09-25：[R12 独立候选](../hardware/production/r1-layout-reset-r12/README.md)从 R10 原生工程重新建立，只移动 R2、Q2 附近两孔和相连短线，保留 R10 顶层丝印。保存重开后原生 DRC 0；独立连通、NFC／板框、0.30 mm 钻孔、≥0.10 mm 径向孔环与异网 0.15 mm 间距检查通过。同网过孔压入焊盘 **2→0**；[嘉立创 PCB/SMT DFM](../hardware/production/r1-layout-reset-r12/vendor-dfm-2026-09-25.md)确认孔落焊盘警告 **4→0**、VIA 孔到焊盘危险 **24→20**，BOM 29/29 组匹配；孔环 100、阻焊桥 43、USB 四槽、J1 焊脚相交 12 和 U1 板边 0.07 mm 危险仍在，供应商未确认，**不下单**。

2026-09-25：[R10 独立候选](../hardware/production/r1-layout-reset-r10/README.md)从 R9 导入，只清理顶层封装外框，保留 D1–D3 阴极标记；铜、孔、装配、板框和天线不变。修正 Gerber 填充边界误计后，顶层外框触及焊盘线段 **3→0**，距焊盘 <0.13 mm 的线段 **78→68**。原生 DRC 0、独立连通、NFC／板框、0.30 mm 钻孔、≥0.10 mm 径向孔环检查通过。R10 Gerber/BOM/CPL 已上传嘉立创，29/29 组器件自动匹配；PCB DFM 的 VIA 孔到焊盘危险为 24，孔环 100、阻焊桥 43、USB 四槽等危险仍在。SMT DFM 后续返回 J1 焊脚相交 12 和 U1 板边 0.07 mm 危险，**不下单**。

2026-09-25：[R9 独立候选](../hardware/production/r1-layout-reset-r9/README.md)继承 R8 丝印清理，只移动 R15、Q3、R1 附近的 3 个 GND 过孔及短线。本地同网孔壁到焊盘铜边 <0.10 mm 的不同过孔 13→10，压入焊盘 4→2；保存重开的原生 DRC 0，独立连通、NFC/板框、0.30 mm 钻孔、≥0.10 mm 径向孔环和 0.15 mm 异网间距检查通过。Gerber 已上传嘉立创“我的文件”，线上结果页未打开，BOM/CPL 尚未上传到该任务；剩余孔距、封装外框丝印、孔环、阻焊、USB 槽及 J1/U1 装配危险待复核，**不下单**。

2026-09-25：[R8 独立丝印候选](../hardware/production/r1-layout-reset-r8/README.md)从 R7 导入，在顶层实物丝印隐藏 U4、U5、U6、L1、R21、R23、Q2、Q3 八个位号；保留装配资料中的位号及板上接口、极性标记。保存后的原生 DRC 0；Gerber 导出对比确认除顶层丝印外的制造层在导出精度内与 R7 等价。本地顶层文字距焊盘 <0.13 mm 的笔画 89→0，封装外框仍有 96 段过近。R8 Gerber 已上传嘉立创“我的文件”，线上结果页尚未打开，孔环、孔到焊盘、阻焊、USB 槽和 J1/U1 装配风险仍待处理；**不下单**。

2026-09-25：[R7 独立候选](../hardware/production/r1-layout-reset-r7/README.md)继承 R4 的显示供电分区及 R5/R6 的 C9、USB CC2 修正，最终只移动 U1 附近一颗 GND 过孔及其短线。保存重开后原生 DRC 0；独立铜箔连通、CC2 保护断线、NFC/板框、Gerber 钻孔与孔环、同版 BOM/CPL 检查通过。167 个过孔最小实际钻孔约 0.30 mm、最小径向孔环 0.1016 mm，异网铜对象无 <0.15 mm 配对。[R7 线上 PCB/SMT DFM](../hardware/production/r1-layout-reset-r7/vendor-dfm-2026-09-25.md)确认 U1 焊脚到孔 2→0 条危险，VIA 孔到焊盘 32→30 条；孔环 100、阻焊桥 43、USB 四槽、J1 焊脚重叠 12、U1 板边 1 等危险未消除。下一步按实物图纸和供应商工艺规则逐点处理及确认，**不下单**。

2026-09-25：[R4 初版](../hardware/production/r1-layout-reset-r4/README.md)完成显示供电区 15 个器件成组重排及布线，但线上 DFM 发现 C9 孔位、盘到线、PTH 孔到线危险；[R5](../hardware/production/r1-layout-reset-r5/README.md)消除这些新增危险但 CC2 焊盘间距回退，[R6](../hardware/production/r1-layout-reset-r6/README.md)修正 CC2 并确认保护拓扑，R7 继续修正 U1 孔位。各版独立工程和制造包保留用于回溯。

2026-09-24：[R2 独立候选](../hardware/production/r1-free-0p30-sense-ring-r2/README.md)在原电池采样候选上完成局部移孔和重布线，保留敏感器件、板框与天线不动。重开原生 DRC 0；最小钻孔 0.30226 mm、最小径向孔环 0.1016 mm；走线/焊盘/过孔异网间距审计未发现 <0.15 mm。Gerber/BOM/CPL 已从同一工程导出，本地独立连通、NFC、板框、四槽及 66/66 位号检查通过。[新版线上 PCB/SMT DFM](../hardware/production/r1-free-0p30-sense-ring-r2/vendor-dfm-2026-09-24.md)走线间距警告由 12 降至 1，盘到线及 PTH 孔到线危险清零；但孔环危险仍显示 100，VIA 孔到焊盘危险增至 32，SMT 新增 U1 焊脚到孔 2 条危险，J1/U1 原有问题未变。需继续局部处理和人工审核；原 R1 制造基准未变，未下单。

2026-09-24：[R3 独立重排试验](../hardware/production/r1-power-relayout-r3/README.md)将显示供电区与 USB/充电区分开，保留电池采样。66/66 引脚、重开原生 DRC、独立铜箔连通、屏幕/NFC 净空及 0.15 mm 异网间距在旧规则下本地检查通过。**自动布线产生 54 个约 0.25 mm 孔**；仅扩大至 0.30 mm／0.51 mm 外径的离线试验又有 29 对 <0.15 mm 的间距。当前工程已把过孔内径最小/默认设为 0.30 mm、外径最小/默认设为 0.50/0.55 mm；原生 DRC 据此报 54 条过孔尺寸错误。另已在嘉立创 EDA 保存同尺寸的双面板规则为新建 PCB 默认配置。命名焊盘复核发现 L1-1 到 C10-1 从 3.04 增至 7.37 mm，C11-1 到 L1-2 从 4.40 增至 10.29 mm，显示供电相对摆位需重做。本版标为布局起点与失败工艺试验，未送供应商 DFM，不可投产；R2 仍是低成本候选。下一步先优化敏感器件相对摆位，再以 0.30 mm 孔和 0.15 mm 目标约束布线。

[R2 线上 DFM 记录](../hardware/production/r1-free-0p30-sense-ring-r2/vendor-dfm-2026-09-24.md#接下来的处理顺序)列明下一步：先处理 U1 焊脚到孔与过孔贴近焊盘，再请工厂按实际 Gerber/器件图纸核实孔环、J1 槽和贴片模型、U1 工艺边。危险和费用未明确前不合入主分支作为制造版。

2026-09-24: checkpoint `ccf9f92` is committed. The [subsequent antenna/layout review](../hardware/pcb-r1-review.md) and battery-pad changes are saved in checkpoint `bee8846` at the user's request, alongside the separate enclosure studies. The subsequent drill/USB/routing review and 2.54 mm SWD/CAD synchronization are included in the current repository checkpoint at the user's request.

| Work | Status / next step |
| --- | --- |
| Source and file organization | R1 active files indexed; E-series history archived; manufacturing outputs tracked |
| Existing electrical checks | Saved/reopened native DRC 0; 58 components, 238 schematic pins matched; copper connectivity and winding cut proof pass |
| Screen protrusion perimeter | Corrected: no pours through the three exposed board edges; selected top B pads/routes are a narrow recorded exception |
| Coil appearance and edge offsets | Complete: five turns, 45° chamfers, equal 3 mm centreline offsets |
| Broader layout review | Review complete; CC2 branch corrected, exports refreshed. C1/C8 assignment corrected; no relocation required. Six nominal 0.2 mm drills eliminated; two GND stitches added, reducing worst USB via proximity from 3.66 to 2.62 mm. [DFM, assembly and remaining tests](../hardware/r1-preorder.md). |
| Control routing cleanup | CE 6 → 4 vias, 39.56 → 32.98 mm; SCL remains four vias and grows 1.70 mm. This step had 818 segments / 153 vias; the subsequent SWD adaptation has 819 / 153. Saved/reopened DRC and independent checks pass. |
| USB/SWD recovery | R3/R4 corrected to 0 ohm / C21189. [Hardware and recovery review](../hardware/r1-usb-swd-recovery.md): firmware and real USB tests pending; 2.54 mm 5P lands and cover access implemented under user-accepted generic clip assumptions; physical trial fit pending. User selected SWD programmer recovery on 2026-09-24; no hidden RESET switch or opening will be added for R1. |
| Enclosure | Nominal fit and meshes pass; physical assembly unverified |
| Packaging optimization | 用户确认按 USB 定厚；[4.8 mm 候选](../enclosure/r1-usb-fit-4.8/README.md)的局部避空、薄键帽、装入与导出检查通过，视觉预览已检查。0.12 mm 安装层、薄壁/键帽与底盖固定待制造验证；电池由用户适配。打包版仍为 5.8 mm。 |
| Battery B pads | Applied at (32.5,18.7)/(35.5,18.7) mm for upper-right lead exit; native DRC and copper checks pass. Frozen CAD wire/ferrite service volumes need later revision. |
| Redundant vias | Removed BAT/CC2/3V3 single-layer vias and one dead stub; all remaining vias contact copper on both faces. Audit rejects an injected redundant via. |
| RF and bring-up | User/agent must test the assembled board; provisional 220 pF tuning capacitors |
| 0.30 mm 低成本候选 | 改 TS 前的 Gerber 已完成[线上 DFM 任务 DFMP2609240514](../hardware/production/r1-free-0p30/vendor-dfm-2026-09-24.md)。孔环、镀铜槽、阻焊桥和 J1 SMT 告警尚未关闭；¥30 仅为裸板参数试算。制造前需在新版本补 TS/MR 10 kΩ 到地。供应商未正式接受，未下单。 |
| 0.30 mm＋电池采样前版 | [独立工程与文件](../hardware/production/r1-free-0p30-sense/README.md)已补 TS/MR 及采样；[线上 PCB/SMT DFM](../hardware/production/r1-free-0p30-sense/vendor-dfm-2026-09-24.md)完成，29 组器件匹配。薄孔环、槽、铜/阻焊、J1/U1 危险未关闭；其扩大孔环诊断 DRC 24，已由 R2 局部重布承接。 |
| R2 孔环与间距候选 | [独立工程与文件](../hardware/production/r1-free-0p30-sense-ring-r2/README.md)的本地检查通过，最小钻孔 0.30226 mm、最小径向孔环 0.1016 mm；独立对象间距审计无 <0.15 mm。[线上 PCB/SMT DFM](../hardware/production/r1-free-0p30-sense-ring-r2/vendor-dfm-2026-09-24.md)仍报孔环 100、VIA 到焊盘 32、U1 焊脚到孔 2、J1 焊脚重叠 12 条危险；需继续局部修改与工厂人工审核，不能作为下单包。 |
| R3 功能区重排 | [独立工程与预览](../hardware/production/r1-power-relayout-r3/README.md)已保存。电池采样保留，USB 保护/主控去耦/屏幕/NFC 未挪；本地几何连通检查通过。54 个小钻孔及显示供电回路扩大阻止其成为制板版；先做按工艺约束的下一轮布线。 |
| R4 已布线重排 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r4/README.md)已保存、重开；本地 DRC、连通、孔环与 0.15 mm 异网对象间距检查通过。[线上 PCB/SMT DFM](../hardware/production/r1-layout-reset-r4/vendor-dfm-2026-09-24.md)显示新增 C9 孔位、盘到线和 PTH 孔到线危险，另有孔环、J1/U1 和阻焊风险；下一版先局部修复，不可下单。 |
| R5／R6 局部修正 | [R5](../hardware/production/r1-layout-reset-r5/README.md)消除 C9 和部分 CC2 新危险；[R6](../hardware/production/r1-layout-reset-r6/README.md)修正 CC2 回退并完成线上 PCB/SMT 对照，U1 焊脚到孔仍有 2 条危险；保留对照，不可下单。 |
| R7 DFM 基线 | [同版工程与文件](../hardware/production/r1-layout-reset-r7/README.md)本地检查通过，[线上 DFM](../hardware/production/r1-layout-reset-r7/vendor-dfm-2026-09-25.md)确认 U1 焊脚到孔危险 0；孔环、过孔到焊盘、阻焊、四槽、J1/U1 模型危险仍待处理和工厂审核，不可下单。 |
| R8 丝印候选 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r8/README.md)已保存，原生 DRC 0，8 个过近顶层位号已隐藏；文字到焊盘近距笔画 89→0，封装外框与其他 DFM 危险仍待处理。Gerber 已上传，线上结果尚未读取，不可下单。 |
| R9 过孔局部修正 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r9/README.md)已保存并重开，原生 DRC 0；同网薄孔到焊盘 13→10，压入焊盘 4→2。Gerber 已上传，线上 PCB/SMT 结果尚未读取；继续局部处理并请供应商审核，不可下单。 |
| R10 顶层封装丝印 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r10/README.md)已保存，原生 DRC 0；修正审计器后触及焊盘铜边的丝印线段 3→0。线上 PCB/SMT DFM 仍有孔环、过孔到焊盘、阻焊、四槽及 J1/U1 装配危险，不可下单。 |
| R12 两孔局部修正 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r12/README.md)已保存重开，原生 DRC 0；孔落焊盘警告清零、过孔到焊盘危险 24→20。线上 PCB/SMT 仍报孔环、阻焊、四槽及 J1/U1 危险，待进一步局部修改与供应商审核，不可下单。 |
| R14 四孔局部修正 | [独立工程与制造文件](../hardware/production/r1-layout-reset-r14/README.md)已保存重开，原生 DRC 0；过孔到焊盘危险 20→12，焊盘间距危险未增加。线上 PCB/SMT 其余危险列入供应商审核清单，不可下单。 |
| R15 USB 封装诊断 | [实时文件与线上 DFM](../hardware/production/r1-layout-reset-r15/README.md)显示焊盘位移会提高网站 SMT 接触比，但改动未持久保存到原生工程；不作为下单包。 |
| Battery | User measures protected pack and wires; nominal 31 × 12 × 3 mm |

No order placed. [Historical progress and experiments](../archive/pre-r1/readmes/projects/nfc-business-card/docs/progress.md) retain earlier findings and resolutions.
