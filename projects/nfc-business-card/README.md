# Programmable NFC Business Card

## 当前确定方案

**PN532 桌面实测（2026-09-25）：**[PN532 与 ESP32-S3-CAM 六线接线图](wiring-diagrams/pn532-esp32-spi.html)已归档。SET0=L、SET1=H 时，SPI 探测返回 `PROBE_OK chip=0x32 firmware=1.6`；[NDEF 测试固件](firmware/pn532_ndef_test/README.md)现支持串口临时切换 URI。手机已正确打开 `https://example.com`；小红书主页短链可经浏览器到达正确主页。微信个人二维码的 HTTPS 地址只到下载页，`weixin://addfriend/...` 可唤起微信选择但未进入加好友页。实验结束后当前运行状态切回小红书链接，ESP32 重启会恢复 `example.com`。下一步验证墨水屏显示微信原始二维码并让另一部手机用微信扫码；实体按键切换待测。详细记录见 [NFC 桌面实验](docs/nfc-bench-test.md)。

**3.0 mm 内腔研究：**按用户反馈电池最厚处可卡入 3 mm，已完成 [4.6 mm 总厚诊断](enclosure/r1-cavity-3mm-study/README.md)。现有 USB、主控、FPC 座和按键运动存在干涉；局部深腔与平整外表两条路线已有尺寸预算，尚无可打印的 3 mm 内腔方案。电池 3.0 mm 仅用于本次研究，打包版不变。

**最新减薄候选：**[3.6 mm 内腔／5.2 mm 总厚度](enclosure/r1-usb-height-5.2/README.md)已生成。保持电池 3.4 mm 包络及 PCB 安装高度，调整键帽中央压柱后，静止无预压干涉、完整行程几何通过；USB-C 顶部名义余量约 0.11 mm，打印公差和实物回弹仍未验证。5.8 mm 打包版保持不变。

**减薄方向更新：**以 USB-C 安装高度为约束的 [5.4 mm 圆角候选](enclosure/r1-usb-height-5.4/README.md)已生成。键帽底面局部挖空后完整行程几何检查通过，仍保留 3.4 mm 电池包络；键帽局部薄壁、回弹公差与可拆底盖待解决，尚未替换 5.8 mm 打包版。

**CAD 最新接口同步：**[2.54 mm SWD 圆角候选](enclosure/r1-rounded-rear-soft-swd254/README.md)沿用 5.8 mm 厚度，仅更新底盖五孔：Ø1.60 mm、孔口 R0.05，表面最窄连桥 0.84 mm。用户接受通用夹具假设，实物试夹待完成。可拆底盖与按钮减薄仍在设计中。

**外壳工艺评审：**[SLA 打印与 SWD 烧录说明](enclosure/r1-rounded-rear-soft/manufacturing-review.md)已完成，保留五个调试孔。圆角候选仍需解决薄底盖、胶接定位、涂层配合和按键轴向公差；首选向嘉立创 3D 询价，备选 PCBWay。成品板固件尚未开发；首次 bootloader 由用户通过 SWD 写入，不安排工厂代烧。

**最新圆角候选：**[加大圆角的上壳与底盖](enclosure/r1-rounded-rear-soft/README.md)已生成，正面／背面／俯视四角为 R1.2／R0.7／R3.2 mm；外尺寸与 PCB 不变，装入几何检查通过。仍待底盖固定与实物工艺验证。

**外壳方向更新，2026-09-24：**用户选择正面＋侧壁一体、独立底盖、背面内移接缝和外露圆角。[独立 CAD 候选与剖面](enclosure/r1-rounded-rear-study/README.md)保持原外尺寸，PCB 对上壳的装入路径检查通过；底盖固定、胶接工艺和实际装配仍待验证，尚未替换现有 CAD 或制造文件。

**R1 is the current editable engineering prototype.** Three front keys and a front e-paper display; rear NFC coil; right-centred recessed USB-C; two-layer 0.8 mm PCB; transparent printed enclosure, 85.2 × 53.2 × 5.8 mm. The selected battery is nominally 31 × 12 × 3 mm.

**Reviewed prototype checkpoint, 2026-09-24:** the perimeter GND rim is removed, the rear coil has 45° corners and equal offsets to the three exposed edges, and USB CC2 now branches at its protection pad. DRC/connectivity checks pass. **The C1 finding was retracted after identifying C8 as the existing charger input capacitor.** [Review and discussion items](hardware/pcb-r1-review.md). RF tuning, battery measurements and physical assembly remain unverified. The earlier archive checkpoint is `ccf9f92`; the PCB and enclosure study checkpoint is `bee8846`. Subsequent drill/return-path changes are described in the [pre-order review](hardware/r1-preorder.md).

**Latest electrical review:** CE/SCL routing now uses two fewer vias and 4.88 mm less combined trace; saved/reopened DRC and independent copper checks pass. R3/R4 changed to 0 ohm / C21189. [USB update/logging and SWD recovery plan](hardware/r1-usb-swd-recovery.md) records the implemented 2.54 mm SWD row, its synchronized cover access and the user-selected SWD programmer recovery path. The selected generic 5P clip is accepted on nominal dimensions; actual contact is a prototype check. Current manufacturing files are refreshed; the user confirmed on 2026-09-24 that R1 needs no hidden RESET switch or side opening. Next: [production verification handoff](hardware/r1-preorder.md#next-task-handoff).

![Actual front and rear copper](enclosure/renders/r1-routed-front-rear.png)

**Battery follow-up:** battery pads are routed at the user-selected **B position beneath the screen**, with the pack lead exit toward the upper right; both pads were subsequently shifted **1.5 mm right**, to (32.5,18.7)/(35.5,18.7) mm. Three redundant signal vias and one unused stub were removed; reopened DRC and independent copper checks pass. [Regional height/button handoff](enclosure/r1-height-handoff.md) records the accepted 3.4 mm battery and 0.25 mm ferrite assumptions. Thickness/button work is deferred; the active case remains **5.8 mm**. Its old wire/ferrite service bodies need revision for the new pads.

## R1 file index

| Entry | Purpose |
| --- | --- |
| [Native EDA project](../../eda/NFC-Card-R1.eprj2) | Primary editable source: one PCB and one four-page schematic |
| [Manufacturing files](hardware/production/r1/README.md) | Gerber for bare PCB; BOM and CPL for assembly; PDF, STEP and portable EDA backup |
| [Design and verification](hardware/pcb-r1-delivery.md) | Design decisions, checks, limits and reproduction commands |
| [USB/SWD recovery](hardware/r1-usb-swd-recovery.md) | Electrical checks, UF2/CDC plan, clip dimensions and selected SWD recovery |
| [Design inputs](hardware/r1-design.json) | PCB, screen, flex, battery and enclosure dimensions |
| [Clear enclosure](enclosure/README.md) | Editable CAD, assembled STEP and printable tray/lid/three-key meshes |
| [Evidence](hardware/records/r1-validation.json) | Saved DRC, netlist, physical copper, winding and export checks |
| [Scripts](scripts/README.md) | Current export, verification and package commands |
| [Progress](docs/progress.md) | Remaining engineering and physical work |
| [Complete local ZIP](artifacts/NFC-Card-R1-prototype.zip) | Rebuildable handoff containing PCB, CAD and checks; do not upload it as a Gerber ZIP |
| [Historical archive](archive/README.md) | E-series designs, experiments, old indexes and migration map |

## PN532 桌面测试程序

当前 ESP32-S3-CAM 上运行 [pn532_ndef_test](firmware/pn532_ndef_test/README.md)，SET0=L、SET1=H；串口可临时切换 NDEF URI。接线按[六线交互图](wiring-diagrams/pn532-esp32-spi.html)；手机实测及限制见 [NFC 桌面实验](docs/nfc-bench-test.md#个人主页与微信入口实测2026-09-25)。

| 程序 | 作用 | 本次实测 |
| --- | --- | --- |
| [pn532_probe](firmware/pn532_probe/README.md) | 串口收到 `PROBE` 后读取 PN532 芯片和固件版本 | `PROBE_OK chip=0x32 firmware=1.6` |
| [pn532_ndef_test](firmware/pn532_ndef_test/README.md) | 模拟只读 NFC Type 4 标签，上电默认 `example.com`，串口可临时切换 URI | `NDEF_READY`、`NDEF_SESSION`；小红书短链可达，个人微信直达未成功 |

两个工程都独立构建，具体工具链、依赖、构建与烧录命令在各自 README。NDEF 工程直接使用锁定在 `upstreams/` 的 Seeed PN532 与 don/NDEF 子模块。当前结果只覆盖桌面模块与这一部手机；实体按键、墨水屏和最终 nRF52840 板仍未测试。

## Physical validation still required

- Measure the complete protected battery, sealed edges and wires against the assumed 32.5 × 14 × 3.4 mm envelope.
- Fit the fully inserted display flex, printed enclosure, keys and USB plug; check screen-to-aperture alignment and adhesive retention.
- Bring up the assembled PCB and tune NFC with the final screen and enclosure. C23/C24 = 220 pF is provisional.

[Bench experiments](docs/nfc-bench-test.md) and their firmware are separate from production-board qualification. No order has been placed.
