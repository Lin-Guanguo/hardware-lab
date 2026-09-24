# R1 height and button handoff

## 最新研究方向

用户进一步要求研究 **3.0 mm 内腔**，并报告电池最厚处可以卡入 3 mm。[4.6 mm 总厚研究](r1-cavity-3mm-study/README.md)已按该电池输入检查：USB 超出约 0.49 mm、主控最大高度超出 0.32 mm、FPC 座超出 0.13 mm，当前键帽完整按压的竖向间隙为 −0.52 mm。均匀内腔方案失败；局部深腔或结构/器件联动仍可研究。以下 3.4 mm 电池是旧方案输入，不再作为此次 3 mm 研究的输入。

后续推进到 [3.6 mm 内腔／5.2 mm 外厚](r1-usb-height-5.2/README.md)：保持 3.4 mm 电池包络，修正中央压柱高度后静止与完整行程无干涉；USB／电池名义间隙约 0.11／0.10 mm。5.4 mm 为较宽松的对照，打包版仍保持 5.8 mm。

2026-09-24 用户恢复减薄设计：以 USB-C 高度为约束，已生成 [5.4 mm／内腔 3.8 mm 候选](r1-usb-height-5.4/README.md)。采用局部凹底键帽，保留 3.4 mm 电池包络；3.2 mm 仅为待实测对比，不通过挤压电池减薄。完整按压行程几何检查通过，但 0.6 mm 局部键帽和 0.05 mm 轴向间隙仍未通过工艺验证。下面“暂缓厚度”的决定已由本研究方向更新，交付模型仍保留 5.8 mm。

## Current decision

2026-09-24: the user deferred enclosure thickness and button manufacturing to a separate discussion. **Keep the current 5.8 mm enclosure; no thinner case has been selected.** The user accepted a **3.4 mm maximum battery pack** and **0.25 mm ferrite including adhesive** as design assumptions. Neither value is a verified assembly measurement.

Battery solder pads have separately moved to **option B, beneath the screen's lower edge**. The battery stays horizontal with its lead exit toward the upper-right corner. See the [PCB route plan](../hardware/records/r1-battery-b-plan.json) and [current copper](renders/r1-routed-front-rear.png).

## Coordinate system and regional heights

All heights below start at the **inside surface of the bottom cover**. The outside floor is 0.80 mm lower. Current cavity height is **4.20 mm**; upper and lower panels are **0.80 mm** each. PCB supports are **0.20 mm PET + two 0.06 mm adhesive layers = 0.32 mm**, followed by **0.80 mm PCB**. They are physical materials, not spare air.

| Region | Stack / location above inner floor | Current clearance |
| --- | --- | --- |
| Battery, PCB cutout | 0.10 adhesive + 3.40 pack maximum = **3.50 mm** | **0.70 mm** below lid |
| Recessed USB | 0.32 support + 3.170 model = **3.490 mm** | **0.710 mm** below lid; connector shares the PCB height |
| MCU | 0.32 + 0.80 + 2.20 maximum = **3.32 mm** | **0.88 mm**; nominal 2.03 mm model gives 3.15 mm occupied height |
| Display FPC socket | 0.32 + 0.80 + 2.010 model = **3.130 mm** | **1.070 mm**; folded flex still needs separate fitting |
| Screen | Front at **4.14 mm** under 0.06 mm bezel adhesive; back at **3.14 mm** for a 1.00 mm maximum screen | **2.02 mm** from PCB top (1.12) to screen back |
| Ferrite under screen | PCB top 1.12 + 0.10 spacing + 0.25 sheet = **1.47 mm** | **1.67 mm** to maximum screen back; sheet needs relief around battery solder joints |
| Switch | 0.32 + 0.80 + 1.55 actuator height = **2.67 mm** | Current cap tip starts at 2.72 mm: about **0.05 mm** contact gap |
| Keycap | Flange bottom/top **3.15 / 4.15 mm**, thickness 1.00 mm; plunger length **0.43 mm** | **0.05 mm** flange-to-lid gap; conservative motion clearance **0.28 mm** to fixed switch body |

The switch's fixed body reaches approximately **2.37 mm** above the inner floor. Its moving actuator must be excluded from fixed-body collision checks. The screen aperture is open; do not add another cover thickness over the display active area.

These dimensions are based on the saved CAD, component models and accepted maximum dimensions. Evidence: [computed thickness study](../hardware/records/r1-packaging-study.json), [study discussion and sources](../hardware/r1-packaging-study.md), and [frozen CAD build inputs](r1-clear-5.8/design-inputs.json).

## Thickness comparisons retained for the next discussion

Clearances are nominal, before accumulating print tolerances, adhesive variation or battery expansion. Take the tallest regional stack; do not average the regions.

| Overall / cavity | Battery gap | USB gap | MCU maximum gap | FPC socket gap | Ferrite-to-screen gap |
| --- | --- | --- | --- | --- | --- |
| **5.8 / 4.2 mm, current** | 0.70 | 0.71 | 0.88 | 1.07 | 1.67 |
| 5.6 / 4.0 mm | 0.50 | 0.51 | 0.68 | 0.87 | 1.47 |
| 5.5 / 3.9 mm | 0.40 | 0.41 | 0.58 | 0.77 | 1.37 |
| 5.4 / 3.8 mm | 0.30 | 0.31 | 0.48 | 0.67 | 1.27 |
| 5.2 / 3.6 mm | 0.10 | 0.11 | 0.28 | 0.47 | 1.07 |

**Buttons currently set the practical reduction limit.** At 5.4 mm, retaining the 1.0 mm flange produces a 0.12 mm collision under the expanded motion test. A 0.8 mm flange gives clearances of 0.28 / 0.18 / 0.08 mm at overall heights 5.6 / 5.5 / 5.4 mm; at 5.2 mm it still collides by 0.12 mm. These are CAD results, not print qualification.

Purchased **ALPS SKQGABE010 switches** are already in the BOM. The visible caps are three separate printed moving parts. Their manufacturing process can be changed in the next discussion without assuming the electrical switches must also change. The motion check uses the ALPS upper travel value 0.45 mm plus approximately 0.05 mm initial gap; the older case report tested only a 0.30 mm cap translation. Supplier acceptance for tiny caps, resting preload, reliable return and strength remain open.

## Battery B and ferrite integration

- B+ center **(32.5, 18.7)** and B− center **(35.5, 18.7) mm**, after shifting both right by 1.5 mm; each top land is **1.8 × 1.5 mm**, with rounded corners and polarity silk. Minimum pad copper-to-board-edge clearance is **0.65 mm**.
- The pack's assumed maximum XY envelope is (1.5, 1.5) to (34.0, 15.5) mm. Its upper-right corner is about **3.54 mm** from the pad centers in XY. The actual nominal pack and lead exit can differ; allow bends and soldering slack before trimming wires.
- Reserve access for soldering before installing the screen. A **1.0 mm solder/wire height above the PCB** would leave **1.02 mm** to the maximum screen back at the current 5.8 mm case. This is an assumption pending wire diameter and actual solder height.
- The old rectangular ferrite service box covers the new lands. A **candidate local notch X 31.3–36.7, Y 18.0–19.75 mm** clears the pads by at least 0.30 mm at their upper edges. Confirm the wire approach and cutting tolerance before making the sheet. Keep the coil covered; the notch is not a qualified RF detail.
- The top battery routes **cross the rear NFC feedlines in XY projection**; minimum separation from the winding itself is approximately **0.87 mm in XY** (previously 0.15 mm), while the pads alone are about 0.73 mm away. These conductors are on opposite PCB faces. This is a changed RF environment; the ferrite between PCB and display does not isolate two copper layers on the PCB. Tune/test with the assembled battery, display and ferrite.
- Both layers remain free of ground pours throughout the screen projection. Only the explicitly recorded top battery lands and narrow routes are allowed there.

**Frozen CAD limitation:** the existing FCStd/STEP still show the former long battery-wire corridor and 0.20 mm ferrite service body. They remain useful for the unchanged shell and component placement, but do not validate the new local solder/wire/ferrite arrangement. Refresh those service volumes in the next mechanical iteration; do not treat the old zero-intersection report as proof of their fit.

## Suggested next-session scope

Read this handoff, the packaging study and current PCB review. Compare button processes and minimum reliable cavity height using the accepted 3.4 mm battery and 0.25 mm ferrite. Keep the selected B pads, upper-right battery lead exit and screen aperture registration. Resolve cap motion/tolerances, local solder/wire relief, ferrite notch and folded FPC before regenerating a thinner case. The current 5.8 mm case is the reference, not an approval of a new thickness. PCB and enclosure studies are checkpointed in `bee8846`. The subsequent drill, USB, routing and 2.54 mm SWD changes are included in the current repository checkpoint. The earlier C1 finding was retracted after confirming the existing charger input capacitor C8; see the [pre-order review](../hardware/r1-preorder.md).
