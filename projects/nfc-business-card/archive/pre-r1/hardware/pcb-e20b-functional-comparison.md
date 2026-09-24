# E20B functional placement comparison

Status: **placement candidate only; no routing or manufacturing release**. Recorded 2026-09-23.

## Review artifacts

- [Side-by-side layout](../enclosure/renders/e20b-functional-comparison.png): original E20 on the left, native E20B on the right.
- [Transparent assembly preview](../enclosure/e20b-functional-5.8/e20-clear-assembled-iso.png) and [editable FreeCAD assembly](../enclosure/e20b-functional-5.8/e20-clear-assembly.FCStd).
- Native project: `eda/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2` at the repository root.
- Original board: `E20 Production Layout`, PCB `81780e0793288f82`.
- Candidate board: **E20B Functional Layout**, PCB **E20B Functional Groups - Unrouted**, UUID `b56c80ec89c9e8b6`.
- [Exact placement plan](e20b-functional-placement.json), [comparison measurements](records/e20b-placement-comparison.json), [native board metadata](records/e20b-board.json).

## Functional arrangement

| Group | Candidate changes | Reason and tradeoff |
| --- | --- | --- |
| MCU local supply | C1/C6/C7 immediately below the module, supply pads facing its supply pins | All three measured pin distances decrease. Supply routing must reach the capacitor before the load; placement alone does not establish this. |
| USB data | R3/R4 beside the module's USB pins | MCU-side pin distances decrease to about 2 mm. Connector-to-resistor routing still has to pass U5 protection in the correct order. Resistor values remain unresolved. |
| Charger and regulator | C8 above U2 IN; C2/C3 beside SYS/BAT; C4/C5 beside U3 IN/OUT; control resistors beside their circuit | Supply pads face the served pins. All five measured capacitor distances decrease. Ground returns still require routing. |
| Button input pull-ups | R10/R11/R12 form a vertical group beside the MCU input pins | Pull-up branches become local. Switch-to-MCU wiring is still required; the distance reduction is not an estimate of total board wire length. |
| Display power | U4/C9/C10/L1/Q1/R13-R16/D1-D3/C11-C13 translated +2.5 mm in X as a 15-part group | Internal relative placement and rotations preserved; group is nearer J2. The external switching circuit includes J2, so preserved internal geometry is not proof of a small routed current loop. |
| Display capacitors | C14-C22 ordered in one column beside J2, with power pads toward J2 | All nine served-pin distances decrease. Sum 32.45 → 25.19 mm; worst 6.30 → 5.44 mm. Existing 1.8 mm centre pitch for C16-C22 is retained, giving about 0.45 mm pad-edge and 0.50 mm model-body gaps. |
| Battery solder pads | BP/BN/NTC aligned at 3 mm pitch | BP-to-BN nominal copper-edge gap 0.303 → 1.499 mm. Pad sizes and nets are retained; suitability for actual wire gauge and soldering remains unverified. |

A total of **42 components and 3 standalone pads** moved. U1, the connectors, keys, board profile and antenna exclusions retain their baseline locations. The original E20 geometry was re-exported and compared field by field: no changes.

The first 3 × 3 display capacitor trial was rejected: it lengthened several served-pin distances, including C16 to about 6.53 mm. The final ordered column improves every measured display capacitor distance. A first C8 trial overlapped a switch pad; C8 was corrected before the saved/reopened final DRC.

## Named electrical evidence

**DC-001 — local decoupling:** distances below come from exported native pad centres and matching net names. They are geometric measurements, not routed lengths or electrical tests. TI recommends keeping BQ25186 IN/SYS/BAT capacitors close to the corresponding pins in [BQ25186, section 9.1](https://www.ti.com/lit/ds/symlink/bq25186.pdf); U3 placement follows the close input/output capacitor guidance in [TPS7A02 layout guidelines](https://www.ti.com/lit/ds/symlink/tps7a02.pdf). The generic 5/8 mm review thresholds are screening heuristics, not vendor acceptance limits.

| Connection | E20 (mm) | E20B (mm) |
| --- | ---: | ---: |
| C1.1 → U1.32 | 14.32 | 1.24 |
| C8.1 → U2.10 | 3.92 | 1.30 |
| C2.1 → U2.1 | 2.91 | 1.49 |
| C3.1 → U2.2 | 4.60 | 1.83 |
| C4.1 → U3.1 | 4.66 | 1.78 |
| C5.1 → U3.5 | 4.26 | 1.77 |
| C6.1 → U1.28 | 1.87 | 1.53 |
| C7.1 → U1.30 | 3.04 | 1.27 |
| R3.2 → U1.35 | 13.30 | 2.00 |
| R4.2 → U1.34 | 14.17 | 2.10 |
| R10.2 → U1.3 | 46.74 | 2.11 |
| R11.2 → U1.4 | 46.67 | 2.10 |
| R12.2 → U1.5 | 46.48 | 3.28 |
| C14.1 → J2.4 | 3.61 | 1.99 |
| C15.1 → J2.5 | 2.53 | 1.83 |
| C16.1 → J2.16 | 2.53 | 2.40 |
| C17.1 → J2.18 | 2.35 | 1.94 |
| C18.1 → J2.19 | 2.61 | 1.80 |
| C19.1 → J2.20 | 3.39 | 2.47 |
| C20.1 → J2.22 | 4.01 | 3.09 |
| C21.1 → J2.23 | 5.12 | 4.23 |
| C22.1 → J2.24 | 6.30 | 5.44 |

**SW-002/SW-003 — switching geometry:** the 15-part translation preserves relative component positions within export precision (<0.003 mm). There is no switching-node track copper to measure yet. The actual loop, return and connection through the display FPC must be checked after routing; no EMC pass is claimed.

**DC-003 / USB protection returns:** zero vias exist in this placement candidate. Ground-via proximity, actual decoupling loops, protection-return paths and plane continuity remain open. U5/U6 stay near the USB connector. A placement-only result cannot close these gates.

## Height, assembly and appearance

The 5.8 mm clear enclosure is reused with a candidate-specific native PCB STEP. Upper/lower panels remain 0.8 mm, perimeter walls 1.2 mm, with a display aperture and no full-height crossbeams.

- Screen drawing: 0.85 ± 0.15 mm; maximum back at Z = 3.94 mm, PCB top at Z = 1.92 mm, leaving **2.02 mm** for the component and clearance.
- L1 remains the highest library model under the screen: 1.51 mm above PCB; nominal solid clearance to maximum screen envelope **0.510 mm**. No placed model pushes into the screen.
- Minimum component-to-lid gap remains **0.710 mm** at J1; J1-to-tray minimum **0.320 mm**.
- No native model body intersections; minimum body-to-body gap is an unchanged USB-area pair R1/U6 at **0.389 mm**. New adjacent display-cap body gaps are 0.500 mm.
- No components intersect the reserved open-lid FPC access volume. This volume is not the actual folded flex envelope.
- The battery wire service envelope has no component intersections, minimum nominal distance about 0.347 mm; wire exit/diameter remain unmeasured assumptions.
- The display is opaque: parts beneath it will be hidden from a front view even with a transparent shell. The comparison diagram makes the screen transparent only to show their placement. Functional colors in the diagram are annotations, not a solder-mask specification. CAD transparency is illustrative.

The native L1/diode/capacitor heights differ from supplier maximum envelopes. The prior [height review](pcb-e20-placement-review.md) remains applicable; complete mounted tolerances, solder thickness, actual battery and flex samples are still needed. This comparison does not justify reducing case thickness.

## Verification

| Check | Original E20 | Final E20B |
| --- | ---: | ---: |
| Components / pads | 58 / 248 | 58 / 248 |
| Tracks / vias | 0 / 0 | 0 / 0 |
| Native DRC clearance errors | 0 | 0 |
| Native DRC unconnected items | 155 | 154 |
| Independent split non-ground nets | 47 | 47 |
| Schematic vs PCB pin/net mismatches | 0 | 0 (58 refs / 238 pins) |
| Copied schematic pages | 4 | 4 |
| Component body intersections | baseline evidence | 0 |
| Component/screen, component/shell intersections | 0 | 0 |
| Open-lid FPC service/component intersections | baseline envelope | 0 |

The connection count depends on ground-pour contacts; a one-item decrease is not routing progress. The independent connectivity command deliberately returns exit 1 for the 47 unfinished nets. Its `ground_reach` result is advisory and is not used as acceptance evidence.

Evidence: [DRC](records/e20b-placement-drc.json), [snapshot](records/e20b-placement-snapshot.json), [pin map](records/e20b-layout-pins.json), [copied schematic netlist](records/e20b-schematic.enet), [connectivity](records/e20b-connectivity.json), [body checks](records/e20b-body-fit.json), [shell checks](../enclosure/e20b-functional-5.8/e20-clear-report.json), [source preservation](records/e20b-source-preservation.json).

Commands run from the repository root:

```sh
python3 projects/nfc-business-card/scripts/check-netlist-consistency.py --sch projects/nfc-business-card/hardware/records/e20b-schematic.enet --pcb projects/nfc-business-card/hardware/records/e20b-layout-pins.json
python3 projects/nfc-business-card/scripts/check-e16-copper-connectivity.py --snapshot projects/nfc-business-card/hardware/records/e20b-placement-snapshot.json
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd projects/nfc-business-card/scripts/check-e20b-body-fit.py
python3 projects/nfc-business-card/scripts/compare-e20b-placement.py
```

The assembly was generated with `enclosure/e20-clear-shell.py`, frozen `enclosure/e20-clear-window-5.8/design-inputs.json`, `NFC_CASE_HEIGHT=5.8`, candidate native STEP `artifacts/e20-functional-layout/e20b-final-placement.step`, and a new output directory `enclosure/e20b-functional-5.8`. The assembled preview and comparison PNG were visually reviewed. The matching `e20-clear-preview.FCMacro` saves the assembly's transparent appearance.

## Remaining decisions before routing / release

1. Resolve the exact module reference circuit's USB series resistors and local VBUS capacitance, including effective capacitance and USB inrush. Current values are preserved for comparison, not approved. The local Raytac Rev L normal-voltage reference shows 27 Ω and 10 µF; [Nordic's reference guidance](https://devzone.nordicsemi.com/f/nordic-q-a/82014/nrf52840-usb-d-d--impedance-matching/340456) differs on external series resistance. Match the actual module revision before changing BOM.
2. Verify L1 recommended land pattern and maximum mounted envelopes against exact supplier parts. No footprint was changed in this candidate.
3. Review the candidate's routing channels, ground/ESD returns and screen switching loop before committing detailed traces. Silk and visible-board artwork need a later pass with the actual copper.
4. Restore and tune the NFC coil only after the layout is selected; the reserved rectangle is not a fabricated coil. RF matching/read range require hardware.
5. Confirm complete battery pack, lead exit, actual screen flex and assembled clearance with samples. Printed-panel deflection, bond assembly and material transparency are unqualified.

This artifact completes the requested functional placement comparison. It is not an orderable PCB/CAD package.
