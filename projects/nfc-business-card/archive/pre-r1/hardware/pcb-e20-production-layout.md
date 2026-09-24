# E20 clear enclosure and unrouted layout

**Superseded placement:** Continue with [E20D front controls / rear NFC](pcb-e20d-front-rear.md). The measurements and artifact links below describe the original E20 clear-shell study, including its former under-screen components.

## Original E20 design — 2026-09-23

**Placement review in progress:** The user paused routing to examine pad access, local circuits, screen clearance and transparent-case appearance. See the [read-only placement review](pcb-e20-placement-review.md). The current positions and CAD below are unchanged candidates; they are not a frozen electrical layout.

The user selected an entirely transparent printed enclosure, accepted a thickness above 5 mm, then confirmed **0.8 mm walls** using a vendor screenshot. The screenshot also states ±0.2 mm accuracy and 49 °C heat resistance; it does not identify the resin. These are supplier claims, not measurements of this enclosure. Do not assume that this vendor material is identical to [JLC3DP 8001](https://jlc3dp.com/help/article/photosensitive-8001-resin), whose separate page recommends walls greater than 0.8 mm.

The current candidate is **85.2 × 53.2 × 5.8 mm**:

- Two clear printed shell halves and three printed keycaps; no separate PC sheet covers.
- Bottom and upper panel thickness: **0.8 mm**. Perimeter walls: **1.2 mm**, which do not increase total height.
- A **27.8 × 27.8 mm open display window** around the screen's 27 × 27 mm active area. The front border is bonded under the printed bezel; the active pixels have no resin cover. Screen front is recessed 0.86 mm below the outer face.
- No internal crossbeams or battery divider. Six 0.32 mm support stacks sit below the PCB. The existing support concept uses PET and adhesive pads; assembly still needs ordinary adhesive materials.
- Battery sits in the PCB cutout, rather than on top of the board. The assumed complete-pack envelope is 32.5 × 14 × 3.4 mm, pending measurement.
- PCB: **81.8 × 49.8 × 0.8 mm**, two copper layers, nominal 0.5 mm clearance to the enclosure's straight inner walls.

Sources of truth: [design inputs](e20-design.json), [FreeCAD assembly](../enclosure/e20-clear-window-5.8/e20-clear-assembly.FCStd), [assembly STEP](../enclosure/e20-clear-window-5.8/e20-clear-assembly.step), [geometry report](../enclosure/e20-clear-window-5.8/e20-clear-report.json). Printable candidates: [tray STL](../enclosure/e20-clear-window-5.8/e20-clear-tray.stl), [lid STL](../enclosure/e20-clear-window-5.8/e20-clear-lid.stl), [keycaps STL](../enclosure/e20-clear-window-5.8/e20-clear-keys.stl). These files are **not a manufacturing release**.

[Assembled preview](../enclosure/e20-clear-window-5.8/e20-clear-assembled-iso.png) / [open enclosure preview](../enclosure/e20-clear-window-5.8/e20-clear-open-iso.png). Transparency is illustrative; the unrouted board has no modeled copper coil yet.

## Height calculation

Compute each local stack independently, then take the maximum. Battery, USB and screen are in different regions; their heights must not be added together. The calculations include a **0.30 mm nominal design gap**, not a verified worst-case tolerance stack.

| Region | Interior stack, excluding upper and lower printed panels | Total with 0.8 + 0.8 mm panels |
| --- | --- | ---: |
| Mid-mount USB | 0.32 support + 0.80 PCB + 2.37 above PCB + 0.30 gap | **5.39 mm** |
| Battery | 0.10 adhesive + 3.40 pack envelope + 0.30 gap | **5.40 mm** |
| MCU | 0.32 support + 0.80 PCB + 2.20 module maximum + 0.30 gap | **5.22 mm** |
| Display | 0.32 support + 0.80 PCB + 1.51 component below screen + 0.30 gap + 1.00 screen maximum + 0.06 border adhesive | **5.59 mm** |
| Depressed keycap | 0.32 support + 0.80 PCB + 1.25 stationary switch envelope + 0.30 travel + 1.00 retaining flange + 0.05 flange-to-lid gap + 0.30 gap | **5.62 mm** |

The CAD model therefore supports approximately **5.7 mm as a rounded nominal calculation**, and **5.8 mm as the current candidate**. Keeping 1.0 mm upper/lower panels would add 0.4 mm, giving approximately 6.1 mm after rounding. Neither value is a guaranteed finished dimension.

The screen window removes material above the pixels, but the surrounding printed bezel still supports the screen border. Opening this window does not automatically subtract a complete panel thickness from the whole product. A flush-mounted display would require a different mounting detail.

The 1.51 mm under-screen component height comes from the current native library STEP (L1). It is conservative relative to the selected part's documented 1.0 mm maximum, but the library geometry has not been replaced with a qualified maximum-envelope model. No thickness saving is claimed from that discrepancy here. Other library models are also not guaranteed supplier maxima.

### Correction to the previous 5.8 / 6.2 mm comparison

The older `e20-clear-5.8` and `e20-clear-6.2` directories used 1.0 mm panels and a continuous transparent lid. They are retained as historical candidates, not the current design. A collision with `FPCServiceVolume` was previously used to reject the thinner candidate. That box describes **open-lid assembly access**, not a measured folded flex cable. It cannot establish a hard minimum closed height. Actual flex routing, bending radius and insertion geometry remain unverified.

## Geometry and production boundaries

The native PCB STEP supplies all 58 component solids. The geometry report checks component-to-tray/lid/display clearances, battery and PCB placement, wire space, and keycaps at rest and 0.30 mm depression. The current checks do not constitute structural analysis or an optical-quality guarantee.

The 5.8 mm candidate generated successfully in FreeCAD 1.1.3. Both shell halves are valid single solids. No intersection was found in the tested relations. Nominal remaining clearances are **0.710 mm above J1**, **0.700 mm above the battery envelope**, **0.510 mm between the tallest modeled under-screen component and the maximum-thickness screen**, and **0.480 mm between a depressed keycap flange and the stationary switch body**. The connector underside is approximately 0.320 mm above the tray floor. These are geometric results using the stated models, not tolerance-qualified production margins.

The supplier's ±0.2 mm headline accuracy cannot simply be applied once to the complete stack: enclosure surfaces, support thickness, PCB thickness, solder height, component envelopes and screen positioning all contribute. A representative printed sample must verify panel deflection, key return/retention, bonding and USB insertion load. The battery assumption is not a qualified swelling allowance.

The screen drawing is [GDEH0154E01, page 5](../../../downloads/gdeh0154e01.pdf). It gives 37.32 × 31.8 × 0.85 mm nominal body dimensions, ±0.15 mm thickness, and an asymmetric border beside the FPC. Window placement follows that drawing rather than centering the window on the complete glass outline.

## PCB status

The active document is **E20 Clear Shell - Unrouted**, UUID `81780e0793288f82`, in the [EDA source](../../../../../eda/archive/nfc-business-card/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2). E19 remains available as a historical reference.

All **796 inherited traces and 148 vias were removed** before the new placement. Current counts are **58 components, 248 pads, zero traces and zero vias**. The native DRC after save/close/reopen reports **155 unfinished connection items**, with no clearance or schematic-netlist mismatch category. This is an intentionally incomplete PCB, not a DRC-cleared production board. The independent connectivity checker finds 47 split non-ground nets, as expected before routing.

The 238 schematic component pins match the PCB map across 58 references. The reopened placement snapshot preserves pad identities, geometry, nets and layers. Evidence: [validation record](records/e20-clear-layout-validation-2026-09-23.json), [native DRC](records/e20-clear-placement-drc.json), [snapshot](records/e20-clear-placement-snapshot.json).

The [profile check](records/e20-unrouted-profile-review.json) verifies one closed exported outline, native/export vertex agreement, eight correct-radius corner arcs, no conflicting mechanical outline, and four plated USB shell slots. This qualifies the profile check only. Copper, assembly exports and the complete fabrication package remain unqualified.

The layer-aware connectivity checker was corrected so opposite-layer SMD pads do not join merely because their XY projections overlap. Calibration verifies separation without a via and connection with a via; a duplicate exported outline is also rejected. See [checker calibration](records/e20-checker-calibration.json). The ground checker remains advisory until checked against actual filled copper.

### Placement changes carried into this case

- U1 moved left 2 mm and inward from the case wall; its antenna copper exclusions move with the module. Module body now starts at approximately y=1.151 mm.
- J1 uses the GCT USB4500 mid-mount method on a 0.8 mm PCB. Its signal lands, slots, paste and routed corner radii were reviewed against the [GCT drawing](https://gct.co/connector/usb4500) and a [same-part reference footprint](https://github.com/TinyTapeout/tinytapeout-kicad-libs/blob/0301871/footprints/TinyTapeout.pretty/GCT_USB4500-03-0-A_REVA.kicad_mod).
- Connector face x≈83.504 mm; the case locally ends at x=83.1 mm, leaving approximately 0.404 mm protrusion for plug access.
- The NFC area is reserved, but the coil has not yet been redrawn after the routing reset. Matching capacitor values remain provisional.

## Remaining work

Work that can continue without samples:

1. Finish functional placement review, including the local U1 VBUS decoupling requirement. C1 is currently near USB, about 14 mm from the module's VBUS pin; total capacitance alone does not establish adequate placement.
2. Route the board from the clean placement, then verify return paths, power/switching loops, USB protection and the NFC feed.
3. Run native DRC, independent layer-aware connectivity, the NFC cut-coil/no-bypass check, actual filled-ground review and final Gerber/BOM/CPL consistency.

Measurements and sample checks:

1. Complete battery pack size, protection board, leads, and retention/expansion provision.
2. Actual screen/FPC bend, latch insertion, border bonding and final installed screen height.
3. Printed shell accuracy, panel flex, key feel, assembly bond and plug access.
4. Assembled custom-PCB NFC tuning/read range. A development board tests basic operation but does not qualify this coil beside its real battery and screen.

## Reproduction

Run from the repository root, choosing a new output directory to avoid overwriting any existing assembly:

```sh
NFC_E20_OUT=/tmp/e20-clear-window-rebuild \
NFC_E20_CONFIG=projects/nfc-business-card/enclosure/e20-clear-window-5.8/design-inputs.json \
NFC_E20_PCB=projects/nfc-business-card/artifacts/e20-production-study/clear-shell/e20-clear-placement.step \
NFC_CASE_HEIGHT=5.8 \
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
  projects/nfc-business-card/enclosure/e20-clear-shell.py

python3 projects/nfc-business-card/scripts/check-e20-outline.py \
  --gerber projects/nfc-business-card/artifacts/e20-production-study/clear-shell/e20-clear-unrouted-profile.zip \
  --snapshot projects/nfc-business-card/hardware/records/e20-clear-placement-snapshot.json \
  --output /tmp/e20-profile-review.json

python3 projects/nfc-business-card/scripts/check-netlist-consistency.py \
  --sch projects/nfc-business-card/hardware/records/e20-schematic.enet \
  --pcb projects/nfc-business-card/hardware/records/e20-pcb-pins.json
```

The native STEP and unrouted profile export are local regenerable artifacts. Re-export from the active E20 document if they are absent. The geometry report records the STEP hash; generated design inputs freeze each case candidate. Use `e20-clear-preview.FCMacro` in GUI FreeCAD with `NFC_E20_OUT` to render the saved assembly without changing geometry.

## E20B placement comparison — 2026-09-23

The original E20 remains the baseline. A separate [E20B functional candidate](pcb-e20b-functional-comparison.md) now provides native placement, a side-by-side drawing and a matching 5.8 mm assembly. It is still unrouted and is not a manufacturing release.
