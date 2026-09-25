# Native EDA projects

## 当前确定方案

Open [NFC-Card-R1.eprj2](NFC-Card-R1.eprj2) for the NFC card. It contains one PCB and one four-page schematic. [Current files, status and checks](../projects/nfc-business-card/README.md).

[NFC-Card-R1-Free-0p30-Sense.eprj2](NFC-Card-R1-Free-0p30-Sense.eprj2) 是新增 TS/MR 电阻、可关断电池采样的独立试验源文件；[对应制造文件与风险](../projects/nfc-business-card/hardware/production/r1-free-0p30-sense/README.md)尚不可投产。先前的 0.30 mm 试验源仍单独保留。

[NFC-Card-R1-Power-Relayout-R3.eprj2](NFC-Card-R1-Power-Relayout-R3.eprj2) 是在独立工程中重新划分显示供电与 USB/充电功能区的**布局试验**。[R3 检查与下一轮约束](../projects/nfc-business-card/hardware/production/r1-power-relayout-r3/README.md)说明了自动布线产生的 0.25 mm 小孔及放大孔后的间距问题；此文件不可用于下单。R2 的 0.30 mm 低成本候选仍保留。

[NFC-Card-R1-Layout-Reset-R14.eprj2](NFC-Card-R1-Layout-Reset-R14.eprj2) 是当前最新的**独立已布线候选**。[R14 检查与线上 DFM](../projects/nfc-business-card/hardware/production/r1-layout-reset-r14/README.md)记录了四处过孔局部移位和仍待供应商审核的工艺危险；不可用于下单。[R12](NFC-Card-R1-Layout-Reset-R12.eprj2)、[R10](NFC-Card-R1-Layout-Reset-R10.eprj2)、[R7](NFC-Card-R1-Layout-Reset-R7.eprj2)、[R8](NFC-Card-R1-Layout-Reset-R8.eprj2)、[R9](NFC-Card-R1-Layout-Reset-R9.eprj2)及更早的 [R4](NFC-Card-R1-Layout-Reset-R4.eprj2)、[R5](NFC-Card-R1-Layout-Reset-R5.eprj2)、[R6](NFC-Card-R1-Layout-Reset-R6.eprj2)工程保留为各步对照。

[NFC-Card-R1-Layout-Reset-R17.eprj2](NFC-Card-R1-Layout-Reset-R17.eprj2) 是 USB4500 的独立**封装／机械诊断工程**。12 个 SMT 焊盘的调整已保存重开，但产生 12 条 J1 焊盘到 USB 缺口边缘的原生 DRC 错误；[同版制造文件与线上检查](../projects/nfc-business-card/hardware/production/r1-layout-reset-r17/README.md)仅供分析，不可下单。[R16](NFC-Card-R1-Layout-Reset-R16.eprj2)是单独的缺口诊断，[R15](NFC-Card-R1-Layout-Reset-R15.eprj2)的焊盘实时位移未持久保存。

Historical projects and database checkpoints are preserved in [archive/nfc-business-card](archive/nfc-business-card/). The E14-named project contains later E-series experiments; its filename does not identify the final R1 source.

[孔环扩张诊断工程](archive/NFC-Card-R1-Free-0p30-Sense-Ring-Study-DRC24.eprj2)保留 24 条 DRC 冲突，只供继续局部改线；不能作为制造工程。

Save and close the EDA application before moving or committing `.eprj2` databases. SQLite journals and local automatic backups are ignored. Active projects live directly in this directory; superseded sources live in `archive/`.
