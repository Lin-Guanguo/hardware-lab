# NFC Card R1 — routed engineering prototype

## Current files

- Native source: [NFC-Card-R1.eprj2](../../../eda/NFC-Card-R1.eprj2). One board, one PCB, one four-page schematic. The original E14-named project is unchanged.
- Complete local handoff: [NFC-Card-R1-prototype.zip](../artifacts/NFC-Card-R1-prototype.zip).
- Actual copper review: [front/rear PNG](../enclosure/renders/r1-routed-front-rear.png).
- Coordinated clear case: [R1 CAD](../enclosure/r1-clear-5.8/e20-clear-assembly.FCStd), [STEP](../enclosure/r1-clear-5.8/e20-clear-assembly.step), [tray STL](../enclosure/r1-clear-5.8/e20-clear-tray.stl), [lid STL](../enclosure/r1-clear-5.8/e20-clear-lid.stl), [three keys STL](../enclosure/r1-clear-5.8/e20-clear-keys.stl).
- Frozen design inputs: [r1-design.json](r1-design.json). Verification: [r1-validation.json](records/r1-validation.json).

This is a routed, editable prototype handoff. NFC performance and physical assembly have not been tested; it is not a production-qualified product. No manufacturing order has been submitted.

## Review status

This is the **reviewed prototype checkpoint**, after checkpoint `ccf9f92`. Perimeter ground copper, coil corners/equal edge spacing and the CC2 protection branch are corrected. **C1 remains 14.28 mm from the charger input pin and needs correction before ordering.** [Full review, remaining improvements and applicability](pcb-r1-review.md). Passing export/DRC checks does not close this finding.

## Implemented changes

All 58 component positions, rotations and footprints, and the board outline, retain the accepted E20D placement. The old project is preserved by SHA-256 comparison. Detailed routing now contains 824 line segments, 153 vias, 248 pads and two ground pours.

The complete screen projection through all three exposed board edges is free of pours on both copper layers: X 0–39.62, Y 17–52 mm. The user selected a specific top-layer exception for B+/B− lands at (32.5,18.7)/(35.5,18.7) mm and their narrow routes; all other non-NFC copper remains excluded. See [battery plan](records/r1-battery-b-plan.json) and [RF/assembly limits](../enclosure/r1-height-handoff.md#battery-b-and-ferrite-integration). Five rear debug pads move to X 65/68/71/74/77, Y 48.5 mm (GND/3V3/CLK/DIO/RST). The R1 bottom cover has matching 2.0 mm access holes; the nearby PCB support moves clear of the holes. The screen, key and USB openings retain their accepted positions.

The rear antenna is a five-turn spiral, outer centreline 29.9 × 27.6 mm, nominal trace/space 0.25/0.25 mm, 45° chamfers and 3 mm centreline offsets from the three exposed straight edges, covered by solder mask. The two NFCT terminals share a native net through a schematic short flag. A separate cut-and-reconnect proof verifies that the winding is not bypassed; ordinary net connectivity alone cannot prove this. C23/C24 remain **220 pF C0G provisional tuning values**. U1.52 connects through the C23 branch to NFC2; U1.54 through C24 to NFC1. These pad names are terminal identifiers, not proof of RF tuning.

USB protection/fanout, display power loops and local decoupling were routed before remaining controls and signals. Their construction records are [critical routes](records/r1-critical-plan.json), [local decoupling](records/r1-decoupling-plan.json), [coil](records/r1-nfc-coil-plan.json) and [RF ground return](records/r1-rf-ground-short-plan.json). Final exported geometry, rather than these construction plans, is the verification input. Short local power paths use 0.25–0.4 mm widths; control routing uses finer tracks where needed. USB is full speed; this two-layer layout has no controlled-impedance certification. Charger/display transient behaviour and USB operation still require powered board tests.

Major reference labels remain on the front silkscreen. Fine passive designators are on the assembly layer/PDF, with rear debug labels printed at 1.0 mm height and 0.15 mm stroke. The copper PNG adds reference labels for review; it is not a photorealistic rendering of final silkscreen.

## Verified evidence

| Check | Result |
| --- | --- |
| Saved, closed and reopened native project | SQLite `quick_check=ok`; native DRC **0** |
| Schematic vs PCB | 58 references, 238 component pins, **0 mismatches** |
| Independent physical copper, including ground pours/thermal spokes | **0 split nets, 0 dead ends** |
| Screen exclusion | **0 unexpected copper / 0 poured copper**; only the selected top battery lands/routes are excepted |
| Redundant via audit | **0 isolated or single-layer vias**; three removed along with one dead stub |
| NFC winding | Connected before cut; two correct branches after cutting an outer turn; deliberate bypass rejected |
| Gerber outline | One closed contour, native corner radii, no competing mechanical contour |
| Drills | 153 vias and four 0.6 mm plated mounting slots match the PCB |
| BOM / CPL | 58 references each; positions and rotations match native reference coordinates |
| Stack | Two copper layers, native total 0.800024 mm (nominal 0.8 mm) |
| CAD | See [R1 mechanical check](records/r1-mechanical-check.json); nominal shell/component geometry only; [new wire/ferrite service bodies remain pending](../enclosure/r1-height-handoff.md) |

The native J1 CPL automatic midpoint is 0.15 mm left of its reference origin because the custom signal lands shift the footprint bounds. The native values are retained, and both midpoint and reference coordinates are supplied. Confirm J1 orientation/registration in the assembler's placement preview, as with other connectors.

The independent pour parser was calibrated using asymmetric arc endpoints and a deliberately wrong tenfold fill-unit scale. The historical copper checker omitted pour contact from its dead-end logic; the R1 checker includes actual filled copper and thermal spokes. Native DRC connection results were stale during routing, so the final result was obtained after a full save/quit/reopen cycle.

## Fabrication and assembly parameters

Use the **R1 Gerber ZIP** for an engineering prototype: nominal PCB **81.8 × 49.8 mm**, routed L-shaped outline, two layers, **0.8 mm FR-4**, **1 oz outer copper**, solder mask over the antenna. Standard plated through vias and routed profile; no buried/blind vias, flex process or four-layer conversion. A flat ENIG finish is a reasonable assembly option; mask colour remains a cosmetic choice. Confirm vendor DFM for the custom USB footprint and small plated slots before fabrication.

The export retains only copper, silk, mask, paste and board-outline layers plus native drill/test data. BOM and CPL are normalized to UTF-8 CSV; original native UTF-16 tab-delimited versions remain in the local routing artifacts. The PCB STEP and seven-page native assembly PDF accompany the source project. The PDF includes both assembly faces, BOM, copper faces and drilling.

Public manufacturing references checked for this revision: [JLCPCB capabilities](https://jlcpcb.com/capabilities/Capab) and [assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities). The covered coil's 0.25/0.25 mm nominal geometry exceeds the published 0.15/0.15 mm covered-coil requirement. The USB uses the [GCT USB4500](https://gct.co/connector/usb4500) mechanical family; E20D's documented land/cutout adaptation remains part of this prototype.

The case is **85.2 × 53.2 × 5.8 mm**, two transparent printed halves with 0.8 mm panels, 1.2 mm perimeter walls and three separate keys. No full-height crossbeams. PET/PSA support pieces and patterned adhesive are still assembly consumables; there is no separate PC cover sheet. STL dimensions are in millimetres. The user's vendor specifies 0.8 mm nominal walls and ±0.2 mm accuracy; resin identity and feature-specific tolerances have not been approved. Print one fit sample before treating this enclosure as qualified.

## Physical work still required

1. Measure the complete protected battery, sealed edges and leads. Nominal 31 × 12 × 3 mm is selected; the assumed maximum envelope is 32.5 × 14 × 3.4 mm.
2. Fit the fully inserted display flex and align the screen active area to the bezel. The connector must not pull the screen into alignment. Check USB access, lid bonding, keys and debug access on the printed sample.
3. Bring up the PCB with current-limited power, verify rails/charging/display/USB/SWD, then test NFC using the final screen and case. Measure/tune C23/C24 and evaluate ferrite if required. A PN532 desk test does not qualify the nRF52840 PCB antenna. [Nordic NFCT reference](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/nfc.html).

## Reproduce checks

Run from the repository root, after installing `projects/nfc-business-card/scripts/requirements.txt`:

```sh
python3 projects/nfc-business-card/scripts/check-r1-copper.py --snapshot projects/nfc-business-card/hardware/records/r1-routed-snapshot.json --output projects/nfc-business-card/hardware/records/r1-copper-check.json
python3 projects/nfc-business-card/scripts/check-r1-nfc.py --snapshot projects/nfc-business-card/hardware/records/r1-routed-snapshot.json --output projects/nfc-business-card/hardware/records/r1-nfc-check.json
python3 projects/nfc-business-card/scripts/check-netlist-consistency.py --sch projects/nfc-business-card/hardware/records/r1-schematic.enet --pcb projects/nfc-business-card/hardware/records/r1-pcb-pins.json
python3 projects/nfc-business-card/scripts/check-e20-outline.py --snapshot projects/nfc-business-card/hardware/records/r1-routed-snapshot.json --gerber projects/nfc-business-card/hardware/production/r1/NFC-Card-R1-gerber.zip --output projects/nfc-business-card/hardware/records/r1-profile-check.json
python3 projects/nfc-business-card/scripts/check-r1-delivery.py
python3 projects/nfc-business-card/scripts/render-r1-copper.py --snapshot projects/nfc-business-card/hardware/records/r1-routed-snapshot.json --output projects/nfc-business-card/enclosure/renders/r1-routed-front-rear.png
```

Live snapshot export: `eda-export-r1-snapshot.js`, guarded by both project and PCB UUID. Native final DRC, rule configuration, topology, profile, parser calibration and release-file hashes are recorded under `hardware/records/r1-*`.
