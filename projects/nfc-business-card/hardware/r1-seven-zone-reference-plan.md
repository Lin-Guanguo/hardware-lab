# R1 七个功能区的原厂参考与重排门槛

## 当前确定方案

先按器件原厂的**封装、机械边界和电气布局建议**固定不能随意移动的关系，再在各区之间分配空间，最后局部布线。参考板只能提供拓扑和摆位思路，不能替代本板的板厚、屏幕、天线、板框和制造验证。[R19](r1-usb4110-sync-r19.md)已用完整 USB4110 官方器件与直板边取得原生 DRC 0，[R18B 线上 DFM](production/r1-layout-reset-r18b/vendor-dfm-2026-09-26.md)验证接口路线的部分工艺收益；[R20](production/r1-layout-reset-r20/README.md)清理三处过孔到焊盘间距，[R21](production/r1-layout-reset-r21/README.md)手工简化 CC2 绕行。[R21 线上 PCB／SMT DFM](production/r1-layout-reset-r21/vendor-dfm-2026-09-26.md)确认 VIA 孔到焊盘危险 0，但焊盘近距、阻焊、U1 装配仍有危险，不是制造放行版。

下表把用户提出的七区作为功能索引；当前位号和坐标以 [R21 重开工程快照](records/r1-layout-reset-r21-routed-snapshot.json)为准，早期距离代理另有版本标注。所谓“标准”分为原厂强约束、原厂示例与可借鉴的公开板三层，不把示例的间距或坐标照抄进本板。

| 区 | 原厂／公开参考 | 本板应先固定的关系 | 可调整的部分与下一项检查 |
| --- | --- | --- | --- |
| ① 屏幕安放 | [Good Display GDEH0154E01 规格书](https://www.good-display.com/companyfile/2038.html)给屏体与 FPC 尺寸；本项目的[六色屏专项评估](../docs/gdeh0154e01-evaluation.md)记录版本差异 | 屏体、FPC 尾巴、上壳和电池的实际包络；显示区不是可自由占用的布线余量 | 只在几何余量经剖面验证后缩减留白，重新查装配高度和 FPC 弯折；不能因俯视图空白就移入器件 |
| ② 屏幕供电与接口 | [Good Display DESPI-E01](https://www.good-display.com/product/1087.html)可作电路功能参考；[TI TPS22919 §11](https://www.ti.com/lit/ds/symlink/tps22919.pdf)要求输入／输出电容靠近开关、VIN/VOUT/GND 短而宽 | J2 的实际 FPC 方向及原厂焊盘；U4、C9/C10 与 L1/Q1/D1–D3 的升压电流回路；开关输入输出去耦 | 可排列外围元件，但先画电流回路再排线；重点消除 L1-2/Q1-3 约 0.072 mm 的同网窄阻焊桥。DESPI-E01 是电路参考，未证实有可直接复用的同条件 PCB 布局 |
| ③ USB 接口 | [GCT USB4110 官方图纸](https://gct.co/files/drawings/usb4110.pdf)规定顶部贴装焊盘与两颗 Ø0.65 mm 非镀定位孔；[TI TPD2EUSB30 §10](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf)要求 ESD 靠近接口、受保护路径尽量直且接地低阻；[旧中置方案比较](usb-mid-mount-two-layer-references.md)只供分析失败原因 | J1 官方焊盘、直板边及定位孔，U5/U6 保护顺序和低阻接地路径 | R18B 已消除旧四槽与 J1 焊脚重叠危险；R21 将 CC2 过孔 4→2、线长 12.454→8.196 mm。下一轮逐组检查 D+/D−、CC1、VBUS 的过孔、长度和成品铜／阻焊间距；减少孔数不能以破坏保护为代价 |
| ④ 充电与稳压 | [TI BQ25186 §9](https://www.ti.com/lit/ds/symlink/bq25186.pdf)要求 IN/SYS/BAT 电容靠近芯片、热焊盘接地、供电铜线按电流定宽；[TI TPS7A02 §8.4](https://www.ti.com/lit/ds/symlink/tps7a02.pdf)要求输入／输出电容靠近稳压器，且给出了与本板 SOT-23-5 对应的 DBV 布局示例 | U2 对 C8(IN)、C2(SYS)、C3(BAT) 的服务关系；U3 对 C4/C5 的服务关系 | 可移动两个功能簇之间的非敏感器件和信号线，不能把电容当“同一电源区元件”随意移远；R16 相关焊盘距约 1.5–1.8 mm，为现有几何证据，不是电气实测 |
| ⑤ 主控 | [Raytac MDBT50Q-P1MV2 Rev L §2.2–2.4](https://www.raytac.com/product/ins.php?index_id=47)给推荐焊盘、模块天线各层无地铜区及板边摆位；[Nordic nRF52840 NFCT](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/nfc.html)给 NFC1/NFC2 差分线圈和调谐要求 | U1 的**P1MV2** 模块天线、板边位置、无铜区；C1/C6/C7 对具体 U1 电源脚的去耦；核对 EDA 封装名 `MDBT50Q-1MV2` 与 BOM `MDBT50Q-P1MV2` 是否共用焊盘 | 主控周围可整理控制线和过孔；U1 板边 0.07 mm 网页危险应按 Raytac 真实本体和贴片模型复核，不能为了清零把天线推入板内。NFC 调谐值须在成板后测量 |
| ⑥ 按键 | [ALPS SKQGABE010 原厂系列页](https://tech.alpsalpine.com/c/products/category/tact-switch/sub/02/series/skqg/)给 5.2 × 5.2 × 1.5 mm 本体和 0.25 mm 名义行程；[项目按键／外壳研究](r1-packaging-study.md)已有压柱、行程余量 | SW1–SW3 与上壳按键、实际封装和指腹操作位置匹配 | 按键网络是低速，可在不破坏手感与开孔对位前提下整理扇出；“三颗排成一条直线”本身不是电气要求 |
| ⑦ 背面 NFC 与调试 | [Nordic nRF52840 NFCT 建议](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/nfc.html)要求 NFC1/NFC2 差分接线及匹配调谐电容；[Raytac RF 净空建议](https://www.raytac.com/product/ins.php?index_id=47)另针对模块自带 2.4 GHz 天线；[本板天线与板框记录](pcb-r1-review.md) | 背面线圈外缘、匝距、引线、上层不侵入的净空；五个 SWD 触点与外壳通孔位置 | 线圈和触点先冻结，再整理附近低速走线；两类天线不同，不能把模块 2.4 GHz 的无地铜区规则直接套成 NFC 线圈的全部规则。线圈谐振与调试夹具需实物验证 |

## 当前工程的逐区判定

下表沿用 [R16 几何评审快照](records/r1-layout-reset-r16-layout-review.json)中的服务距离代理，[R14 线上 DFM 根因](production/r1-layout-reset-r14/dfm-root-cause-review-2026-09-25.md)与 [R18B 线上 DFM](production/r1-layout-reset-r18b/vendor-dfm-2026-09-26.md)中的供应商结果；③区接口状态更新至 R21。以下均是**图纸／几何状态**，不是成板实测：

| 区 | 当前状态 | 下一步是否要移动器件 |
| --- | --- | --- |
| ① 屏幕 | 外露边附近的错误覆铜已移除；装入、FPC 弯折和实物高度未验证 | 暂不动屏幕包络 |
| ② 屏幕供电 | U4 输入、开关及电感的摆位代理面积约 5.64 mm²；L1/Q1 同网阻焊桥约 0.072 mm 仍需处理 | 可局部微调 L1/Q1 或开窗，保留短回路 |
| ③ USB | R21 的 J1 焊脚重叠危险 0，旧镀铜槽 0、VIA 孔到焊盘危险 0；[扇出复核](r1-usb-routing-review-r21.md)确认 CC2 的 4 孔降为 2 孔，`USB_DM_CONN` 仍有 5 孔。D+/D− 焊盘交错，局部换层确有几何原因；U5 GND 已有约 2.30 mm 顶层明线到地过孔，向北更短直连会与 D+ 相交。网页最小线距 0.15 mm，余下危险主要是焊盘近距、阻焊及 U1 装配 | 保留已核实的 U5 接地通道；先定位实际危险，只在有净收益时联合重布 D+/D−，不先搬远 U5/U6 |
| ④ 充电／稳压 | C8→U2.IN 约 1.75 mm，C2→U2.SYS 约 1.49 mm，C3→U2.BAT 约 1.83 mm，C4/C5→U3 约 1.78 mm；均为焊盘间几何距离 | 保留命名电容服务关系，外围低速件可重排 |
| ⑤ 主控 | [官方 Eagle/STEP 叠图](r1-r21-u1-edge-decision.md)确认 P1MV2 的 61 焊盘与天线禁铜区，STEP 对壳无碰撞；U1 板边／装配模型仍有网站危险，封装名称与 BOM 后缀不同 | 不为网站计数移动模块；先建可拆工艺边独立拼板并核对具体 SMT 审核及网页贴片模型 |
| ⑥ 按键 | 三颗位号和电路已存在；外壳按压、夹具与实物行程尚无验证 | 可整理低速线路；位置改变须同步外壳 |
| ⑦ NFC／调试 | 五匝 45° 线圈、匝间约 0.25 mm、外露三边铜边约 2.875 mm；独立几何／连通检查通过 | 保留线圈和五触点，后续实物调谐与试夹 |

## 先后顺序与验收

1. **封装先行。** 对 J1/J2/U1/U2 逐项核对原厂推荐焊盘、机械边界、阻焊、锡膏和装配方向。当前 J1 采用 USB4110 官方顶部贴装封装、直板边和两颗非镀定位孔；[R18B](production/r1-layout-reset-r18b/README.md)已验证旧四槽与 J1 焊脚重叠危险消失。仍须按新接口真实外形修改外壳与装配模型，不能只优化单个网页计数。
2. **敏感簇先行。** 保留或改善上述命名电容的服务距离、USB ESD 接地／保护顺序、屏幕供电开关与升压回路、两类天线净空。给其余元件留间隔，再布线；过孔尺寸在布线前设为 0.30 mm 普通钻孔，目标径向孔环不小于约 0.10 mm，异网铜对象目标间距至少 0.15 mm，同时检查阻焊和成品 Gerber。
3. **先做 USB 小区。** R21 已完成 CC2 一组；下一独立工程继续按 D+/D−、VBUS、CC1 分组画最短可行扇出，减少绕圈和不必要换层；逐孔比较 R21 的全网过孔数和走线长度，并确认 ESD 不被绕过。若无法在保留保护、0.30 mm 孔和低成本间距下实现，再评估整体区位或接口机械方案及费用代价。
4. **逐区验收。** 每次只改一个功能簇；保存并关闭 EDA 后重开，执行原生 DRC、逐引脚网表、独立铜连通、板框／NFC、Gerber 钻孔／孔环／铜距／阻焊、BOM/CPL 及供应商 PCB/SMT DFM。只根据重复计数不做整板移动；R14 [根因复盘](production/r1-layout-reset-r14/dfm-root-cause-review-2026-09-25.md)中固定节距、规则口径差异和真实过孔薄距需分开处理。

以上是布局审核与实施门槛；R21 是经重开验证的 USB CC2 局部候选，**尚未产生获制造放行的新版**，板子仍不可下单。
