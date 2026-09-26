# R21 U1 板边：先验证拼板装配路线

## 当前确定方案

**保留现有 U1 坐标，先设计可拆工艺边的独立拼板候选，再做 SMT 装配确认。**这是选择下一项实验，不是工厂放行。Raytac [MDBT50Q-P1MV2 Ver.L §2.3](https://www.raytac.com/tw/download/index.php?index_id=24)建议将模块放在 PCB 边缘，天线对应位置的每层均不铺地铜。[嘉立创中文拼板指导第 14 项](https://www.jlc.com/portal/server_guide_4069.html)明确：板边元件距成品板边小于 3 mm 时应加工艺边，以便机器装配；同页建议常规宽度 5 mm、板两侧加边、定位孔和 Mark 点。其[国际站 PCBA 条款 §2.3](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service)还写了元件本体距板边至少 2.5 mm。**这些资料支持工艺边路线，但没有给出这块 L 形板与 Raytac 天线的具体拼板/分板放行图。**需以具体拼板预览和装配审核决定。

嘉立创[拼板服务说明](https://www.jlc.com/portal/server_guide_4069.html)将免费代拼限于常规矩形、同面同向的 V 割小批量板；本板有弧线与 L 形板框，优先自行设计独立拼板以控制天线旁连接桥。若改用其不规则付费拼板，公开说明为常规约 **¥30/款**、复杂情形另计，实际费用以当次页面为准。保留工艺边/分板后的成品外形必须与外壳匹配。

[Raytac 官方 Footprint/Design Guide（230606）](https://www.raytac.com/document/act.php?act=1&index_id=30)中的 nRF52840 Eagle 库、P1MV2 STEP 已与 R21 [61 焊盘引脚表](records/r1-layout-reset-r21-pcb-pins.json)、铜箔快照及外壳逐项对照：[可复跑脚本](../scripts/check-r21-u1-official.py)和[结果](records/r1-layout-reset-r21-u1-official-overlay.json)。61 个焊盘编号一致，最大中心偏差 **0.0021 mm**，宽/高偏差最大 **0.0006/0.0012 mm**，矩形焊盘方向一致。按官方 Eagle 天线禁铜外框检查实际铜对象，**顶、底层侵入 0**；原厂名义 STEP 与 6.3 mm 外壳最短距离 **0.566 mm**，无实体重叠。该对照没有核对锡膏/阻焊、实物公差和嘉立创元件模型，因此网站 U1 PIN 边界危险尚未放行。

## 同版几何比较

[可复跑脚本](../enclosure/check-r21-u1-edge.py)从[R21 引脚坐标](records/r1-layout-reset-r21-pcb-pins.json)、Raytac Ver.L 的模块尺寸与 1 号焊盘基准，以及[6.3 mm 外壳几何候选](../enclosure/r1-usb4110-6p3/README.md)生成[计算记录](records/r1-layout-reset-r21-u1-edge-options.json)。R21 顶边在 `y=1.100 mm`；U1 原厂名义本体上缘 `y=1.166 mm`、下缘 `y=16.666 mm`，故本体到成品板边只有 **0.066 mm**。旧外壳 CAD 中 C1/C6/C7 本体上缘 `y=17.200 mm`，与 R21 器件中心坐标一致；U1 对这些电容的名义间隔为 **0.534 mm**。此处电容实体仍是旧 CAD 参考，尚非全部 R21 元件三维同步。

| 尝试 | U1 到成品板顶边 | 新约束 |
| --- | ---: | --- |
| 保持 R21，暂加 5 mm 可拆上工艺边 | 成品仍为 0.066 mm；载板外边名义约 5.066 mm | 符合中文“距边 <3 mm 应加工艺边”的方向；具体连接桥、Mark 点、两侧导轨、分板及天线性能仍待拼板/厂方审核。 |
| U1 单独向板内平移 0.5 mm | 0.566 mm | 到 C1/C6/C7 名义仅剩 **0.034 mm**；还未达到通用 2.5 mm 条款，且天线随之远离成品边缘。不能单独实施。 |
| 成品 PCB 在 U1 顶侧局部外扩 0.5 mm | 0.566 mm | 矩形探针与现有上壳体积相交为 0，但**最短距离为 0**，没有公差余量；不算可装配方案。 |
| 局部外扩 1.0 / 2.434 mm | 1.066 / 2.500 mm | 与当前上壳实体交叠 **4.20 / 10.08 mm³**；必须重做外壳及天线净空/板框，后者还会改变成品尺寸。 |

以上外扩只用矩形实体探针测**碰撞趋势**，没有生成可制造板框；0.5 mm 外扩的接触也不是安全间隙。Raytac 模块尺寸存在公差，名义 0.066 mm 间隔不能保证每片模组都不越过板边。此前 JLC SMT DFM 报 `U1 0.07 mm 危险`，与名义几何吻合。[线上同版记录](production/r1-layout-reset-r21/vendor-dfm-2026-09-26.md)中的 U1 引脚模型危险仍需逐脚与原厂焊盘叠图，不能由工艺边解释。

## 下一项独立实验和放行门槛

1. 以 **R21 成品轮廓不变**建自行拼板候选：按嘉立创异形板指导考虑两侧约 5 mm 工艺边和实际连接桥，标明拼板外轮廓、定位孔、光学点、U1 本体/天线无铜区、可分板路径及外壳会接触的残留毛刺区域。工艺边不能遮挡 USB-C、屏幕或其它元件装配。
2. 官方 **61 焊盘与天线禁铜区已对照**；继续核对锡膏/阻焊及 U1 八条 PIN 边界危险对应的网页贴片模型，把 BOM/CPL 的 P1MV2 与 EDA `1MV2` 名称差异映射到正确的生产坐标。若模型不一致，先修模型。
3. 用具体拼板及 SMT 预览确认嘉立创是否接受这颗靠成品边的模块、采用何种连接桥/分板方式和是否增加费用。**在接受前，不以在线危险计数自动消失为目标改 U1 坐标。**若该工艺路线不被接受，再联合重设 U1、电容、天线净空、板框和外壳；移动 0.5 mm 或永久扩板 0.5 mm 的单点改动都不够。

本轮只读分析，**没有改 EDA/生产包，没有新的 PCB/SMT DFM，也没有下单**。

## 官方资料复跑

官方 RAR 下载后未纳入 Git；结果记录保存了原包、Eagle 库及 STEP 的 SHA-256。下面将文件解到临时目录，再执行复核：

```sh
curl -L --fail 'https://www.raytac.com/document/act.php?act=1&index_id=30' -o /tmp/raytac-mdbt50q-guide.bin
bsdtar -xOf /tmp/raytac-mdbt50q-guide.bin 'MDBT50Q Footprint_Design Guide-230606/Footprint (nRF52840)_MDBT50Q-1MV2 & P1MV2 & U1MV2/MDBT50Q Eagle Library/MDBT50Q_52840_230606.lbr' > /tmp/mdbt50q-52840.lbr
bsdtar -xOf /tmp/raytac-mdbt50q-guide.bin 'MDBT50Q Footprint_Design Guide-230606/2D & 3D Drawing/MDBT50Q-P/3D/MDBT50Q-P 3D Drawing_20180620.stp' > /tmp/mdbt50q-p-20180620.stp
RAYTAC_U1_LIBRARY=/tmp/mdbt50q-52840.lbr RAYTAC_U1_STEP=/tmp/mdbt50q-p-20180620.stp RAYTAC_U1_ARCHIVE=/tmp/raytac-mdbt50q-guide.bin PYTHONHOME=/Applications/FreeCAD.app/Contents/Resources PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd projects/nfc-business-card/scripts/check-r21-u1-official.py
```
