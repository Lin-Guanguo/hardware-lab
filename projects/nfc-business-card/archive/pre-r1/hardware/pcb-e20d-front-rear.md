# E20D: front controls and rear NFC

Recorded 2026-09-23. **Unrouted placement and nominal assembly candidate; not a manufacturing release.**

## Layout acceptance — 2026-09-24

Lin Guanguo accepted the arrangement shown in `e20d-front-rear.png` as the layout baseline for completion. Preserve the front display and three keys, rear NFC reservation, centred right-edge USB, battery pocket and clear enclosure appearance during routing. A necessary change to these constraints must be recorded with its electrical or mechanical reason and a matching CAD review.

The [acceptance record](records/e20d-layout-acceptance.json) identifies the reviewed diagram and design evidence by SHA-256. The 15 artifacts in the preceding validation record were checked against their recorded hashes and all matched. Acceptance covers placement and appearance; routing, RF tuning and physical assembly remain open.

| Current file | Use |
| --- | --- |
| [Native EDA project](../../../../../eda/archive/nfc-business-card/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2) | Select PCB `8033127c48771f3b`, **E20D Front Controls Rear NFC - Unrouted**; the E14 filename is the project container, not the selected PCB revision. |
| [Front/rear view](../enclosure/renders/e20d-front-rear.png) | Accepted visual layout; the drawn coil is illustrative. |
| [Screen/FPC view](../enclosure/renders/e20d-screen-fpc-registration.png) | Screen, aperture and connector datums. |
| [FreeCAD source](../enclosure/e20d-front-rear-refined-5.8/e20-clear-assembly.FCStd) / [assembly STEP](../enclosure/e20d-front-rear-refined-5.8/e20-clear-assembly.step) | Current nominal assembly. |
| [Tray STL](../enclosure/e20d-front-rear-refined-5.8/e20-clear-tray.stl) / [lid STL](../enclosure/e20d-front-rear-refined-5.8/e20-clear-lid.stl) / [keys STL](../enclosure/e20d-front-rear-refined-5.8/e20-clear-keys.stl) | Existing fit-study meshes; print and assembly tolerance qualification remains open. |

Completion work and required physical inputs are tracked in the [current progress board](../../../docs/progress.md). The `e20d-profile-review.zip` archive only verifies the outline and must not be sent as a routed manufacturing package.

## Review files

- [Front/rear layout](../enclosure/renders/e20d-front-rear.png), with an explicitly illustrative coil reservation.
- [Clear enclosure preview](../enclosure/e20d-front-rear-refined-5.8/e20-clear-assembled-iso.png), [FreeCAD assembly](../enclosure/e20d-front-rear-refined-5.8/e20-clear-assembly.FCStd), [assembly STEP](../enclosure/e20d-front-rear-refined-5.8/e20-clear-assembly.step).
- Native project: `eda/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2` at the repository root.
- Board: **E20D Front Controls Rear NFC**. PCB: **E20D Front Controls Rear NFC - Unrouted**, UUID `8033127c48771f3b`.
- [Frozen design inputs](e20d-design.json), [placement changes](e20d-placement.json), [absolute native snapshot](records/e20d-placement-snapshot.json), [validation record](records/e20d-validation.json).

## Adopted arrangement

The user selected front display and keys, rear-side NFC phone reading, a nominal 31 × 12 × 3 mm purchased battery, and all three keys shifted right 1 mm. The enclosure remains entirely printed, with adhesive and below-board support pads used for assembly.

| Area | E20D change | Evidence and tradeoff |
| --- | --- | --- |
| Three keys | SW1 (41.1, 4.5), SW3 (41.1, 14.4), SW2 (49.6, 8.8) mm | All move +1 mm X from E20B; coordinated cap holes and travel models. C8 moves to (46.1, 16.8) to clear SW3 copper. |
| Battery cutout | Right boundary X = 36.5 mm; corner radii retained | Straight cavity span 35.9 × 16.7 mm. At X = 1.5, the 31 mm pack has 0.9 mm left and 4.0 mm right nominal gaps. Total length remainder is 4.9 mm before tolerances. |
| USB | J1 centre Y = 26.0 mm, mid-point of the right edge | Footprint and X position retained; connector, outline notch, protection parts, case opening and supports coordinated. R1/R2 adjusted locally for pad clearance. |
| Display power | U4/C9/C10/L1/Q1/R13–R16/D1–D3/C11–C13 translated +36 mm X | All 15 parts leave the screen projection for the former right-side antenna area. The initial group translation was followed by the documented capacitor/diode refinement below. External J2 branches still require a routing review. |
| Rear NFC | Planned outer centreline rectangle 30 × 24 mm on B.Cu, X4–34 / Y20–44 | Both-layer exclusion X3–35 / Y19–45 removes components and pours. Actual coil and feed lines are not drawn. SWD pads remain outside the reservation. |
| Matching parts | C23/C24 beside the MCU NFC pins; NFC1/NFC2 rear pads at X36.3, Y27/30 | Existing capacitor values remain provisional. Do not treat these parts as a tuned network. |
| Upper-right space | Approximately 9 × 13 mm geometric spare area | No new feature selected. Routing, mechanical access and BLE performance must be reviewed before adding parts. |

E20B was re-exported after the changes: [no geometry differences](records/e20d-source-preservation.json). E20C is an intermediate battery/key candidate. Its initial STEP predates the final C8 correction and is not the current assembly source; use E20D files above.

## Electrical and RF review

**RF-001 — screen environment:** Opposite PCB sides do not establish RF isolation. Nearby conductive material can introduce eddy-current loss and detune an NFC antenna; measurements must include the final surroundings and any ferrite. This is the physical guidance in [NXP AN11564, sections 2.2 and 3.2](https://www.nxp.com/docs/en/application-note/AN11564.pdf). That guide concerns PN7120; its matching values are not transferred to this nRF52840 design. The actual screen's conductive stack has not been characterised.

The planned 30 × 24 mm outer rectangle has 720 mm² area, versus 383.4 mm² for the former 18 × 21.3 mm study. The approximately 88% increase is geometric, **not a read-range prediction**. Turn count, trace width, feed geometry and matching values require measurement. The five-turn drawing is a reservation illustration, not connected PCB copper.

The native RF exclusion prohibits components, fills and pours on both layers. Tracks are allowed for the future antenna; routing must separately prevent unrelated signals from entering the area. The independent audit found no pads in the region and no filled copper at 13,312 sampled positions per layer on a 0.25 mm grid. This is a geometric check, not an RF simulation. An optional 0.2 mm ferrite service volume is reserved between PCB and screen; no ferrite material or part has been selected, and it is excluded from the physical assembly STEP.

**EPD-001 — moved display power:** The initial 15-part group translation retained relative geometry. A subsequent refinement aligned D2/D3/C13 on X72, placed D2/D3 on the same rows as C12/R16, and shortened local supply connections. J2 and its nine rail capacitors moved together by +3.17 mm X / +0.26 mm Y following the screen/FPC datum check. R17/R18 now align with the connector centre. Nets, values, footprints and the L1/Q1/D1/C11 switching-node pad positions are unchanged.

| Local connection | Initial E20D (mm) | Refined E20D (mm) |
| --- | ---: | ---: |
| C9 input capacitor → U4 IN | 3.33 | 1.55 |
| C10 output capacitor → U4 OUT | 3.51 | 2.85 |
| C10 → L1 supply pad | 5.52 | 3.04 |
| D2 → D3 pump branch | 5.25 | 4.53 |
| R13 pull-down → U4 ON | 2.17 | 2.38 |

These are pad-centre measurements, not routed loop lengths. C9/C10 locality follows [TI TPS22919 section 11](https://www.ti.com/lit/ds/symlink/tps22919.pdf). The small R13 branch increase is the explicit alignment tradeoff. J2-related distances mostly improve; R15 to J2 remains 16.99 mm versus 15.89 mm in E20B and must be reviewed during routing. [All measurements](records/e20d-layout-audit.json).

The nine C14–C22 parts serve separate screen rails; their ordered column is retained beside J2. Their 0.8 mm designators are aligned in a separate column; C14 has a 0.7 mm label offset to avoid the adjacent C10 pad area. Other refined group labels use horizontal text. This is a focused placement/silkscreen refinement, not a BOM reduction.

**DC-001 — retained charger decoupling:** The C8 adjustment clears the shifted SW3 pad. C8.1 to U2 IN is now 1.75 mm, versus 1.30 mm in E20B and 3.92 mm in original E20. The capacitor remains beside its served pin; the actual supply and ground path must still follow [TI BQ25186 layout guidance](https://www.ti.com/lit/ds/symlink/bq25186.pdf).

## Screen and FPC registration

The user's two photographs read **51.5 mm unplugged** and approximately **54.8 mm plugged to the connector rear**. The official drawing gives 37.32 + 14.3 = **51.62 mm** unplugged. Adding the connector after nominal 2.1 mm insertion gives **54.42 mm to the body rear**, or **54.92 mm including the leads**. These different endpoints explain the readings. [Detailed derivation, pin orientation and remaining assembly checks](pcb-e20d-screen-fit.md).

The screen and aperture remain fixed; J2 is now at **(54.70, 34.26) mm**. The FPC centre comes from the 9.59 mm edge offset and 12.5 mm tail width. The generated model measures **54.575 mm from the screen far edge to the connector rear lead**, leaving about 0.345 mm of nominal tail length beyond its plan projection for vertical accommodation. This allowance is not a validated bend-radius or tolerance result. The 6 mm stiffener stays straight.

## Enclosure and height

- Outer size: **85.2 × 53.2 × 5.8 mm**. Floor/lid: 0.8 mm. Perimeter walls: 1.2 mm. No internal crossbeams.
- PCB bottom/top: Z1.12 / Z1.92 mm. Maximum screen back: Z3.94 mm, giving **2.02 mm empty height above the PCB** under the screen. No component model overlaps the screen projection.
- Nominal screen: 37.32 × 31.8 × 0.85 mm; thickness maximum used: 1.0 mm. The active area remains exposed through the lid window.
- Regional nominal height requirements: USB 5.39, battery 5.40, MCU 5.22, display 4.08, depressed key 5.62 mm. The three-key construction still controls height; moving screen components does not automatically make the whole card thinner.
- Conservative battery envelope retained: 32.5 × 14 × 3.4 mm. The purchased 31 × 12 × 3 mm nominal pack is not yet measured. The wider 32 × 20 × 3 mm pack is not supported by this cutout.
- A reserved lead corridor uses the widened pocket and passes under the screen, outside the RF exclusion. Actual wire diameter, protection board, exit direction and final flex bend remain unmeasured; screen and tail nominal dimensions are now checked against user photographs.

The generated [solid-intersection report](../enclosure/e20d-front-rear-refined-5.8/e20-clear-report.json) found no tested collisions among native component models, case, screen maximum, lead reservation and pressed keys. All six support footprints lie fully beneath PCB material. J1 nominal distance to tray/lid is 0.320 / 0.710 mm. The separate [body check](records/e20d-body-fit.json) found no component-to-component intersections or component intrusion into the open-lid FPC service volume.

These are nominal library-model checks. The 0.6 mm key radial running gap and 0.05 mm flange-to-lid rest gap describe the current key concept; the small axial gap is **not a qualified print tolerance**. Key feel, panel deflection, adhesive closure, USB insertion loads and actual maximum part dimensions still require samples. The FPC service box is assembly access, not the folded cable shape. CAD transparency does not establish printed optical quality or copper visibility through solder mask.

## Verification performed

| Check | Result |
| --- | --- |
| Saved/reopened native DRC | 154 connection errors only; zero clearance errors |
| Native content | 58 components, 248 pads, 0 tracks, 0 vias |
| Schematic versus PCB | 58 references / 238 component pins, zero net mismatches |
| Independent connectivity | Unrouted failure expected; 47 split nets |
| Exported profile | One closed contour, expected corner arcs and four USB slots, no conflicting mechanical layer |
| RF reservation | No pad overlaps; both copper pours excluded at sampled positions |
| CAD | Valid single-solid tray and lid; tested nominal intersections zero |
| Visual review | Front/rear diagram and assembled clear-case preview inspected |

Commands run from the repository root (the native DRC and export steps used the local EDA bridge):

```sh
python3 projects/nfc-business-card/scripts/check-e20d-layout.py
python3 projects/nfc-business-card/scripts/check-e20-outline.py --gerber projects/nfc-business-card/artifacts/e20d-front-rear/e20d-profile-review.zip --snapshot projects/nfc-business-card/hardware/records/e20d-placement-snapshot.json --output projects/nfc-business-card/hardware/records/e20d-profile-review.json
python3 projects/nfc-business-card/scripts/check-e16-copper-connectivity.py --snapshot projects/nfc-business-card/hardware/records/e20d-placement-snapshot.json
NFC_E20_CONFIG="$PWD/projects/nfc-business-card/hardware/e20d-design.json" NFC_E20_OUT="$PWD/projects/nfc-business-card/enclosure/e20d-front-rear-refined-5.8" NFC_E20_PCB="$PWD/projects/nfc-business-card/artifacts/e20d-front-rear/e20d-refined-native.step" NFC_CASE_HEIGHT=5.8 /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd projects/nfc-business-card/enclosure/e20-clear-shell.py
NFC_BODY_REVIEW_REV=e20d NFC_E20_OUT="$PWD/projects/nfc-business-card/enclosure/e20d-front-rear-refined-5.8" /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd projects/nfc-business-card/scripts/check-e20b-body-fit.py
python3 projects/nfc-business-card/scripts/render-e20d-front-rear.py
python3 projects/nfc-business-card/scripts/review-e20d-fpc.py
```

The CAD generator refuses to overwrite an existing assembly; select a new output directory to reproduce it. The profile archive is review evidence only, not a fabrication package.

## Remaining work

1. Review J2 switching/return paths and USB routing order, then route the chosen placement and rear antenna. Recheck native DRC, netlist, copper connectivity and manufacturing exports after routing.
2. Test the NFC antenna with the actual screen and complete enclosure; compare loading with/without the screen, select ferrite if required, then tune matching components and verify rear reads on target phones. A PN532 desk test alone does not qualify the final nRF52840 antenna.
3. Measure the protected battery, verify the final screen/FPC bend with a sample, and test printed keycaps, USB access and the bonded case.
4. Confirm unresolved component values, material/tolerance acceptance, assembly process and complete release gates before ordering.
