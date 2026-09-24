# R1 pre-order review — 2026-09-24

## Saved state and current result

Checkpoint **`bee8846`** preserves the PCB, delivery files and separate enclosure studies. The changes below follow that checkpoint and are included in the current repository checkpoint at the user's request. No order or supplier message has been sent.

| Work item | Result |
| --- | --- |
| Six nominal 0.20 mm vias | Five USB vias enlarged to 0.25 mm drill / 0.45 mm land; battery via enlarged to 0.30 / 0.55 mm |
| Battery connection | Via moves from X40.20 to X40.05 mm, with three local trace adjustments; B+/B− positions stay (32.5,18.7)/(35.5,18.7) mm |
| Thin annular rings | Former CC2 0.30/0.20 mm vias now have nominal 0.10 mm radial copper, previously 0.05 mm |
| USB ground return | Two connected GND stitching vias added; worst nearest-ground-via distance 3.66 → 2.62 mm |
| Charger input capacitor | Earlier C1 finding corrected: C1 serves U1.32, while C8 already serves U2.10 |
| Charger-control routing | CE/SCL rerouted together: two fewer vias, 4.88 mm shorter combined path; other signal routes unchanged |
| USB series resistors | R3/R4 changed from 27 ohm to 0 ohm / C21189; native schematic, PCB and BOM synchronized |
| SWD clip adaptation | Five rear pads and labels moved to 2.54 mm pitch; square GND/pin 1, no added vias; cover access synchronized under accepted nominal fixture assumptions |
| Native and independent checks | Saved/reopened DRC 0; no split nets, dead ends, orphan copper or single-layer vias; NFC cut proof passes |
| Manufacturing consistency | 58 BOM/CPL references, 238 matching schematic pins, 153 vias, four plated slots; unchanged outline/components |
| Mechanical reuse | All 238 component STEP solids retain identical volume, area and bounds; this does not validate the pending wire/ferrite service volumes |

Evidence: [change plan and before/after metrics](records/r1-preorder-plan.json), [layout review](pcb-r1-review.md), [delivery checks](records/r1-validation.json), [C8 evidence](records/r1-input-capacitor-check.json).

## Why small holes existed, and why keep 0.25 mm now

The September 22 USB fanout experiments used a **“Multiple Layers Board” DRC preset** to permit smaller lands/holes around the connector's 0.5 mm pitch pads. The electrical board remained two-layer. A preset name is not a requirement to manufacture four layers. See the [archived USB experiment](../archive/pre-r1/hardware/pcb-e16-usb-right-mid.md), especially the “Multilayer-rule fanout experiment” and subsequent fanout records.

The current geometry supports removing every 0.20 mm drill without moving components or changing the USB protection topology. A nominal 0.25 mm hole with 0.45 mm copper land provides 0.10 mm radial copper. There are now **97 nominal 0.25 mm and 56 nominal 0.30 mm vias**. Larger holes are possible in open areas; enlarging all lands in place is not possible in the existing dense fanout. Eliminating the 0.25 mm tier would require broader routing changes and a new verification cycle. That is justified if the actual supplier quote or DFM reveals a material constraint or cost, rather than by the old preset alone.

The current Gerber drill tools are **0.248920, 0.250000, 0.299999 and 0.305001 mm**, plus **0.599999 mm** for the four mounting slots. The near-nominal differences come from legacy imperial dimensions and native export precision. The quote must use the actual Gerber, not a hand-rounded drill file.

## Current JLC domestic capability

Checked the [official JLC capability table](https://www.jlc.com/portal/vtechnology.html) on 2026-09-24:

- Two-layer boards support 0.15 mm drills, explicitly described as unconventional and expensive; the recommended minimum hole is 0.20 mm or larger.
- Via land diameter must exceed hole diameter by at least 0.10 mm; the recommendation is 0.15 mm or more. Current new 0.45/0.25 and 0.55/0.30 sizes exceed that recommendation.
- Unconventional two-layer holes require ink/resin filling. The page does not settle which quote tier our actual near-0.25 mm tools will use or what it costs.
- Minimum plated slot width/length for two layers is 0.5/1.0 mm; length should be at least twice width. R1 has two 0.6 × 1.8 mm and two 0.6 × 1.4 mm plated slots, including rounded ends.
- Published 1 oz two-layer track/space capability is 0.10/0.10 mm. Retain 1 oz; thicker copper has different limits.

Therefore **0.20 mm was not intrinsically unmanufacturable and did not require four layers**. Removing it improves the two smallest annular rings and simplifies the minimum-hole requirement. Neither the public capability page nor DRC is a quote or a supplier acceptance of this custom USB footprint.

## Fabrication selection and DFM brief

Use the [current Gerber](production/r1/NFC-Card-R1-gerber.zip), **89,074 bytes**, SHA-256 `bc26ce13373705df8b42c041d1c44eba96881d41cc013b50b29b341e18924c5b`.

| Field | R1 selection / constraint |
| --- | --- |
| Board | Two-layer FR-4, nominal 81.8 × 49.8 mm, routed L-shaped profile |
| Thickness / copper | 0.8 mm / 1 oz outer copper |
| Finish | ENIG is the proposed flat finish for this prototype; confirm the actual quote |
| Mask | Both faces, including the NFC winding; no exposed antenna, gold fingers or edge plating |
| Vias | Plated through; no blind/buried vias or HDI; confirm required filling/tenting and surcharge from actual drills |
| Connector cutout | Retain the exported contour and four plated slots; do not replace the board outline with an assembly/mechanical drawing |
| Clearance | Smallest pad-to-board-edge geometry is approximately 0.299 mm; signal-pad-to-USB-cutout clearance is approximately 0.301 mm, not the obsolete 0.2007 mm figure |
| Panel / rails | Ask the assembler to prepare/approve tooling rails for the L-shaped 0.8 mm board and protruding mid-mount USB body; keep rails removable and outside the final contour |

Before payment, obtain confirmation for the actual minimum drill tier, hole treatment, four plated slots and USB cutout. These are manufacturing acceptance questions, not a request to invent a special PCB process. The remaining 0.25 mm tier may still affect price.

## 嘉立创 PCB 网页试算（2026-09-24）

按 5 片、双层 FR-4、81.8 × 49.8 mm、0.8 mm 板厚、1 oz、绿色阻焊、沉金和 0.25 mm 最小孔径在[嘉立创 PCB 下单页](https://www.jlc.com/newOrder/#/pcb/pcbPlaceOrder)试算。选择 0.25 mm 后，页面提示该孔径属于高难度工艺，并自动选择过孔塞油及四线低阻全测。价格明细如下；这是未上传 Gerber 的裸板参数试算，不是已审核报价，也不含 SMT、器件和钢网。

| 网页价格项 | 5 片试算 | 说明 |
| --- | ---: | --- |
| 最小孔径/外径 | ¥102.04 | 对应 0.25 mm 档；Gerber DFM 识别最小孔径 0.25 mm |
| 喷镀费 | ¥102.85 | 所选沉金；DFM 估算沉金面积 6.53%，未达到页面提示的 30% 大面积加价线 |
| 阻焊覆盖费 | ¥100.20 | 页面因 0.25 mm 孔径自动选择过孔塞油；Gerber 的实际过孔属性仍须审核 |
| 四线低阻全测费 | ¥101.63 | 0.25 mm 档自动选中，页面禁用“无要求”；正式订单仍须确认 |
| 特价 | ¥30.00 | 裸板基础试算项 |
| 品质赔付费 | ¥10.00 | 页面默认选择的可选保障服务，不属于 PCB 工艺 |

网页合计 **¥446.72**，显示所选快递包邮。固定上述其他参数，仅将孔径改为免费 0.30 mm 档、将塞油与全测复位为普通选项，合计 **¥142.85**；重新选择 0.25 mm 档，页面再次自动选中塞油和全测，合计回到 ¥446.72。两档差 **¥303.87**，恰好是孔径 ¥102.04、塞油 ¥100.20、全测 ¥101.63 三项之和。若另外改用免费表面处理并取消默认品质赔付服务，普通档可低至这次的 ¥30 基础项；这不表示现有 R1 Gerber 可按普通档生产。实际运费和价格以订单审核为准。0.8 mm 板厚、1 oz、绿色阻焊没有在这次价格明细中单列加价。四个镀铜槽、L 形外形、SMT 工艺边和元器件仍待供应商确认，不能据此试算认定免费或可生产。DFM 页面使用了默认有铅喷锡显示，而本试算选择沉金；最终表面处理要以正式制造参数为准。

## Assembly preparation

Bare-board fabrication needs the Gerber ZIP. SMT assembly additionally needs the [BOM](production/r1/NFC-Card-R1-bom.csv), [CPL](production/r1/NFC-Card-R1-cpl.csv) and [assembly PDF](production/r1/NFC-Card-R1-assembly.pdf). A supplier number in the BOM is not proof of current stock or automatic assembly support.

| Part | Assembly / purchasing confirmation |
| --- | --- |
| U1 MDBT50Q-P1MV2, C5119772 | Confirm exact module suffix and antenna variant; check the module orientation and availability |
| U2 BQ25186DLHR, C44639442 | Confirm WSON-10 exposed-pad stencil and placement; do not substitute a charger by similar name |
| J1 USB4500-03-0-A, C5354966 | Custom adapted mid-mount footprint: review signal lands, tabs, slots and placement overlay; native CPL midpoint is 0.15 mm left of its reference origin |
| J2 FPC-05FB-24PH20, C2856831 | Verify contact side, latch direction and insertion orientation against the screen flex |
| C8 CL10A475KO8NNNC, C19666 | Samsung marks it NRND; check stock. Suggested successor is CL10A475KO8NQN#, but a substitution requires value, bias, package and height confirmation |
| SW1–SW3 SKQGABE010, C115351 | Three electrical switches are in the BOM; printed keycaps are separate enclosure parts |
| Battery, display, ferrite | Fit and connect after PCBA reflow; they are not populated by the 58-component CPL |

No live assembler BOM matching, stock reservation, stencil approval, panel approval or binding quotation has been completed. The bare-board parameter estimate above is provisional. Those remaining checks depend on the actual selected service and its review screen. The intentional R3/R4 substitution is documented in the [USB/SWD review](r1-usb-swd-recovery.md); no supplier-driven substitutions are approved.

## Remaining work and ownership

1. **Recovery design settled, 2026-09-24:** the user accepts recovery through an SWD programmer. Retain the five existing SWD/NRESET pads; do not add a hidden RESET switch or side opening. The current export implements 2.54 mm SWD pitch for the selected generic 5P clip, with synchronized cover access; nominal assumptions were accepted and trial fitting is a prototype check. [USB/SWD contract](r1-usb-swd-recovery.md).
2. **Supplier / order preview:** drill tier and filling, USB slot/cutout acceptance, component matches/stock, rotations and tooling rails. The package and questions are ready; no supplier acceptance is claimed.
3. **Prototype electronics:** current-limited power-up, rails, charging, display, SWD and USB full-speed operation. Four USB transitions still exceed the contextual 1.6 mm ground-via guideline; this is a review cue, not a proven USB fault. Firmware must be built and validated for this nRF52840 board.
4. **Assembled NFC:** tune the provisional C23/C24 values with the actual screen, 0.25 mm ferrite, battery and shell. Geometry checks do not establish resonance or read range.
5. **Separate enclosure work:** the active 5.8 mm case and rounded rear-cover candidate have separate status. Battery dimensions/lead dress, B-pad solder access, ferrite notches, display flex, cover fixing and key travel need the mechanical iteration and fit sample. See the [height handoff](../enclosure/r1-height-handoff.md) and [rounded candidate](../enclosure/r1-rounded-rear-study/README.md).

The current files can be uploaded for a fabrication/assembly quote and DFM review now. Before payment, accept the supplier's actual parts, connector placement and hole/profile review. Firmware development and RF/USB/physical validation can follow on the first small prototype batch. Print a fit sample before ordering finished transparent housings; the preferred rounded cover still needs a closure decision. This is an engineering prototype, not a production-qualified release.

## Next-task handoff

The PCB/manufacturing checkpoint is `ccdc51d`; the subsequent recovery decision above does not change the PCB or Gerber. The user plans a separate task for production verification. Start with the current Gerber, BOM/CPL and assembly PDF: verify export consistency, inspect the supplier's board preview, select fabrication parameters, review drill/slot/profile acceptance, and match actual assembly parts, orientation, availability and tooling rails. Record the quote and unresolved supplier findings before ordering. Do not reopen the hidden RESET decision or request further clip dimensions. Enclosure iteration proceeds separately; firmware and assembled RF/USB/fit tests remain prototype work.
