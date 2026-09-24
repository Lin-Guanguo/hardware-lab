# E20 placement review before routing

Reviewed 2026-09-23. The user asked to pause routing and review placement, pads, performance, height and appearance through the transparent enclosure. **No EDA placement, routing, schematic or CAD geometry was changed in this review.**

Evidence: [measured pin locations](records/e20-layout-review-pins.json), [native body bounds](records/e20-layout-review-body-bounds.json), [review metrics](records/e20-layout-review.json), [annotated plan](../enclosure/renders/e20-placement-review.png). Measurements use the current E20 source, not an earlier routed revision. Pad distances below are straight-line centre distances, not predicted routed lengths.

## 1. Screen and component height

The GDEH0154E01 drawing, [page 5](../../../downloads/gdeh0154e01.pdf), specifies a 37.32 × 31.8 mm screen body and **0.85 ±0.15 mm thickness**. The current 5.8 mm case uses the 1.0 mm maximum for its screen-back check:

| Reference plane | Z from enclosure underside |
| --- | ---: |
| PCB top | 1.92 mm |
| Maximum-thickness screen back | 3.94 mm |
| Screen front | 4.94 mm |
| Printed bezel underside | 5.00 mm |
| Enclosure outer face | 5.80 mm |

Therefore **2.02 mm is available above the PCB under the screen**, before subtracting component assembly height. The screen is retained by its border and must not rest on the electronic components.

| Parts below screen | Native CAD height above PCB | Manufacturer package maximum | Gap using current CAD |
| --- | ---: | ---: | ---: |
| L1 NRH3010T470MN | 1.510 mm | 1.00 mm | 0.510 mm |
| D1–D3 MBR0530T1G | 1.450 mm | 1.35 mm | 0.570 mm |
| C9–C13 CL21B105KBFNNNE | 1.300 mm | 1.35 mm | 0.720 mm |
| Q1 SI1308EDL | 1.176 mm | 1.10 mm | 0.844 mm |
| U4 TPS22919DCKT | 1.000 mm | 1.10 mm | 1.020 mm |
| R10–R16, where overlapping screen | 0.450 mm | Not requalified in this review | 1.570 mm |

Manufacturer sources: [Taiyo Yuden](https://ds.yuden.co.jp/TYCOMPAS/cs/detail?pn=LSXNE3030KKT470MN&u=M) identifies NRH3010T470MN as the former part number; [onsemi package drawing](https://www.onsemi.com/download/data-sheet/pdf/mbr0530t1-d.pdf); [Samsung CL21B105KBFNNN](https://product.samsungsem.com/mlcc/CL21B105KBFNNN.do); [Vishay SI1308EDL](https://www.vishay.com/docs/63399/si1308edl.pdf); [TI TPS22919 DCK outline](https://www.ti.com/lit/ds/symlink/tps22919.pdf).

**Finding:** the current nominal assembly does not push the screen upward, but the CAD library is not a consistent maximum-envelope model. L1 is substantially taller in CAD than the specified component, while C9–C13 and U4 are shorter than their package maxima. The 0.720 mm capacitor gap must not be presented as a guaranteed maximum-part clearance.

As a sensitivity calculation, allocating an additional 0.10 mm above the 1.35 mm package maximum for mounting gives `2.02 − 1.35 − 0.10 = 0.57 mm`. This mounting allocation is a design assumption, not a measured solder joint or factory tolerance agreement. PCB variation, cover/ledge variation, screen position and panel deflection remain separate contributors.

Moving only L1 out from under the display has limited benefit: the diodes and 0805 capacitors still occupy approximately 1.35 mm before mounting allowance. The keycap stack also limits overall thickness. Relocate the complete switching group only if the resulting electrical loops and mechanical clearance improve together; do not scatter the inductor and diodes to make the drawing look emptier.

## 2. Placement changes worth studying

| Priority | Current measured condition | Proposed direction | Benefit and tradeoff |
| --- | --- | --- | --- |
| High | C1.1 → U1 VBUS pin 32: **14.324 mm** | Establish a local VBUS capacitor beside the module pin, coordinated with charger input capacitance. | Reduces the local supply loop. Capacitance and USB attachment/inrush budget need explicit review, not just a move. |
| High | USB R3/R4 MCU-side pads → module: **13.30 / 14.17 mm** | Review the resistor requirement and group any retained series links near the relevant module pins; keep ESD protection at the connector. | Clearer connector → protection → module path. Exact module guidance conflicts with generic Nordic guidance; see below. |
| Medium | C3 → charger BAT: **4.603 mm**; C8 → charger IN: **3.917 mm** | Rotate/reposition the charger capacitors around their served pins before aligning the surrounding resistors. | Better local loops and less routing congestion. Preserve wire soldering access. |
| Medium | R10/R11/R12 → their MCU pins: **46.74 / 46.67 / 46.48 mm** | Move the three button pull-ups into one compact group near the relevant inputs or button corridor. | Removes unnecessary long branches and simplifies the visible layout. These slow signals are not a demonstrated functional failure at the present distance. |
| Medium | C14–C22 are in a long column; C22 → J2.24: **6.30 mm**, C21 → J2.23: **5.12 mm** | Group capacitors by the connector pin bank they serve, then align each group. | Shorter connections while retaining an orderly appearance. Preserve the FPC insertion/latch corridor and NFC exclusion. |

The current C6/C7 supply-pad distances to their module pins are approximately **1.87 / 3.04 mm**. These are already substantially more local than C1. They should not be moved away merely to form an evenly spaced row.

### MCU position and orientation

The module's USB data pins currently face toward decreasing X, while J1 is on the right edge. A further left shift of U1 lengthens the direct USB separation unless another part of the interface is reorganized. The region to the module's left does contain geometric room, but that alone is not a reason to move it.

A 90° orientation could be studied as a separate layout candidate, but preserving the antenna at an exterior edge would then require coordinated connector, module and antenna-clearance changes. First compare a compact peripheral layout around the current module; do not casually trade the established antenna exclusion for visual symmetry.

### Reference discrepancies to resolve before routing USB

The local Raytac Rev L [normal-voltage reference, page 40](../../../downloads/raytac_mdbt50q_rev_l.pdf), shows a **10 µF VBUS capacitor and 27 Ω USB series resistors**. The current PCB has 2.2 µF at C1 and 4.7 µF at C8, physically separated. This does not by itself establish a suitable local bypass network.

[Nordic's technical response](https://devzone.nordicsemi.com/f/nordic-q-a/82014/nrf52840-usb-d-d--impedance-matching/340456) says the nRF52840 PHY contains its series resistors and is intended to work without external ones. That is a real discrepancy with the module reference. Verify the exact module/build guidance before fixing R3/R4 population and value. This review has **not** changed them or declared the present module circuit invalid.

## 3. Pads and assembly access

- **Component land patterns:** use the manufacturer pattern and verified package. Rotate an entire two-terminal footprint where that puts power/ground toward the correct connection. Do not move individual pads independently to obtain visual alignment.
- **L1:** native pads are approximately 1.501 × 3.320 mm with 2.654 mm centre spacing; the native model footprint is wider than the stated 3 × 3 mm body. This is a reason to compare the exact recommended land pattern, not proof of an invalid footprint. The manufacturer's linked DXF/dimension download returned an error during this review; the footprint comparison remains open.
- **USB J1:** preserve the reviewed shell stakes, plated slots, signal lands and matching routed notch while evaluating other placement options. Decorative pad resizing would invalidate that coordinated geometry.
- **Battery BP/BN:** current pads are approximately 1.50 mm diameter, at (49.5, 23.55) and (47.7, 23.7) mm. Their nominal copper-to-copper gap is approximately **0.30 mm**. The geometric DRC result does not establish comfortable manual soldering access or wire retention. Study grouping them nearer the battery lead exit, with soldering clearance and strain relief, once the actual lead exit is confirmed.
- **SWD TP1–TP5:** five bottom pads in an approximately 2.50 mm pitch row, matched by existing bottom access holes. Keep this group aligned with its programming fixture and case openings. It is already a coherent group.
- **NFC feed/matching pads:** keep the two feed branches identifiable even though the netlist uses a common NFC net. Place tuning parts close to the intended feed and preserve probe/rework access. Final routing must pass the cut-coil/no-bypass audit.

## 4. Appearance through a clear shell

The display and battery are opaque. The visibly exposed top area is therefore mainly the module, controls, USB/power parts, FPC connector and NFC region; the transparent bottom also exposes the board underside. The realistic visual goal is a readable arrangement of functional groups, not making every component visible from above.

Suggested order of decisions:

1. Establish the critical component-to-pin relationships, switching loops and antenna keepouts.
2. Align the edges and orientations of parts within each functional group, using consistent spacing where it does not lengthen a critical connection.
3. Keep the NFC loop area visually clear, with a uniform trace pattern. Do not add decorative copper inside its reserved area.
4. Use a restrained silkscreen hierarchy (USB, PWR, NFC and key labels). Keep labels readable through the chosen finish and clear of pads; choose solder-mask color after the layout is settled.
5. Place necessary ground vias for return paths first. Their visual regularity is secondary to electrical placement.

Recommended next comparison: **current module/connector positions with compact functional groups** versus **a coordinated alternate module orientation**. Show the proposed component positions, key connection lengths, height limits and RF/assembly exclusions before applying either candidate. Routing remains paused for this layout discussion.

## Verification performed

- Read live E20 counts: 58 components, 248 pads, 0 copper tracks, 0 vias.
- Exported actual per-component pin coordinates; measured only matching-net pad pairs.
- Loaded the saved native CAD without saving changes and extracted component bounds.
- Checked the screen drawing and the listed manufacturer height specifications.
- Ran `python3 projects/nfc-business-card/scripts/review-e20-layout.py` and visually inspected the generated plan.

No mechanical load simulation, assembled height measurement, routing quality assessment or RF qualification is claimed.
