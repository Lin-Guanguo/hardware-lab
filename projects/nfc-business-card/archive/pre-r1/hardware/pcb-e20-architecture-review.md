---
description: E20 architecture comparison before PCB placement and enclosure redesign
last_updated: 2026-09-23
status: historical_comparison_followed_by_selected_e20_clear_shell
---

# E20 architecture review

**Decision update:** The user initially selected the ≤5 mm mid-mount USB plus sheet-cover option, then requested an all-printed transparent enclosure and authorized a new thickness comparison. E20 now exists as an unrouted independent layout. See [current E20 record](pcb-e20-production-layout.md). The sections below preserve the earlier trade study.

## Recommendation

Start an independent E20 placement study, retaining the reviewed schematic connections, component research, and E19 as a comparison. Reconsider the PCB outline, functional groups, connector mounting, and enclosure together before detailed routing. Existing tracks do not constrain the new placement.

At the time of this study the user had requested a comparison of the existing **≤5 mm** target and thicker alternatives. The subsequent selection and implementation are recorded above.

## 1. Is a mid-mount USB connector necessary?

Not inherently. It saves height in this particular stack, and both mounting styles are standard products:

| Reference | Manufacturer geometry | Consequence on a 0.8 mm PCB |
| --- | --- | --- |
| [GCT USB4500](https://gct.co/connector/usb4500), current J1 | Mid mount, 3.16 mm profile, 0.80 mm offset | Connector and PCB share height within a routed board cutout. Approximately 3.16 mm from PCB underside to connector top. |
| [GCT USB4110](https://gct.co/connector/usb4110), comparison only | Top mount, 3.26 mm above PCB, SMT shell stakes | PCB plus connector occupies 4.06 mm. No body-sized board cutout, but its own land pattern and locating holes are required. |

The top-mount example adds **0.90 mm** to the nominal local stack. This is specific to these two products, not a universal value for every USB-C connector. USB4110 is a dimensional comparator, not a frozen substitute; shell retention, solder process, stock, maximum dimensions, and the mating plug still need checking.

The current V7 PCB top is at `0.4 + 0.3 + 0.8 = 1.50 mm`. Installing the top-mount comparator at that height puts its nominal top at **4.76 mm**, leaving **0.24 mm total** below a 5 mm exterior for both upper cover and clearance. It is therefore not a drop-in replacement within the present envelope.

The current mid-mount J1 STEP reaches z=3.870021 mm; the [actual solid clearance check](records/e19-j1-shell-clearance-2026-09-23.json) found 0.339979 mm to the V7 top shell. The previous 0.13 mm reference-plane difference must not be used as the shell clearance.

### Comparable local thickness budgets

All values are in mm. These are **USB-zone nominal arithmetic**, not whole-card dimensions or tolerance-qualified fits. The sheet and gap dimensions below are study assumptions, not supplier guarantees. Adhesive, solder height, maximum component dimensions, cover variation, and mounting details remain to be allocated; the battery and display can set a larger whole-card thickness.

| Cover assumption | Lower / upper gap | Mid mount: covers + gaps + 3.16 | Top mount: covers + gaps + 0.8 + 3.26 |
| --- | --- | ---: | ---: |
| Two 0.25 mm nonmetallic sheets on a supporting frame | 0.30 / 0.30 | 4.26 | 5.16 |
| Same sheets, reduced clearance sensitivity case | 0.15 / 0.15 | 3.96 | 4.86 |
| Two 0.90 mm printed covers | 0.30 / 0.30 | 5.56 | 6.46 |

For example, the last top-mount row is `0.90 + 0.30 + 0.80 + 3.26 + 0.30 + 0.90 = 6.46`. The printed-cover assumption exceeds the [JLC3DP 8001 recommendation of >0.8 mm walls](https://jlc3dp.com/help/article/photosensitive-8001-resin), but does not by itself establish strength or assembly fit. That process lists ±0.2 mm or 0.3% dimensional tolerance; this is not a substitute for a feature-specific tolerance stack.

The 4.86 mm top-mount case leaves only 0.14 mm to the target before unresolved dimensions. It demonstrates nominal geometric possibility, **not a comfortable ≤5 mm design**. The 0.15 mm gaps also require reconciliation with the selected manufacturing tolerances. A 5.5–6 mm top-mount candidate should therefore use a sheet/frame or other qualified cover construction; a fully printed version needs a separate budget, around 6.5 mm nominal in this example.

**Working candidates:** A: ≤5 mm, mid mount plus supported thin covers. B: 5.5–6 mm, top mount plus supported thin covers. C: approximately 6.5 mm or more, top mount plus printed covers. Final maxima may increase after tolerance allocation. A and B deserve placement comparison first; C is a useful manufacturing reference.

## 2. Are four copper layers necessary?

The saved design is **two copper layers, 0.8 mm**. `JLCPCB Capability(Multiple Layers Board)` is the name of the EDA rule preset previously selected to allow small vias. It does not change the physical stack to four layers. The subsequent two-layer USB fanout and network routing superseded the earlier claim that USB could not be routed on two layers.

[JLCPCB's current capability table](https://jlcpcb.com/capabilities/Capab) permits 0.15/0.25 mm minimum via hole/diameter on both two-layer and multilayer FR-4. The current approximately 0.20/0.30 mm vias are therefore not a reason to order four layers; that combination is an extra-cost via option. Layer count and via fabrication options are separate choices.

Start E20 with two layers and an explicitly documented two-layer rule set. As **layout preferences**, try 0.20 mm general signal width/clearance and 0.30/0.60 mm hole/diameter vias where practical; use documented local exceptions at fine-pitch parts. These are not blanket requirements for power traces, USB geometry, or antenna tuning, and do not justify distorting the manufacturer's land pattern.

Reconsider four layers if the new placement still forces fragmented return paths, poor power/ESD routing, or excessive detours and small vias. E19 connectivity checks alone do not prove adequate ground return paths. Four layers at the same finished thickness can help electrical routing, but do not reduce the USB body or enclosure height.

## 3. What the new placement must solve together

| Area | Placement decision and review evidence |
| --- | --- |
| Exterior and PCB | Retain 84 × 52 mm as a working whole-product envelope and 85.60 × 53.98 mm as the recorded maximum. Define frame walls before the board outline; do not add walls outside a PCB already using the complete exterior envelope. Review board support and USB insertion force together. |
| Battery | Compare the 301230-class target and the previously selected 302030 sample using complete-pack envelopes. The present 33.5 × 15 mm pocket is not fixed. A nominal 32 × 20 × 3 mm pack cannot simply replace the current pack in that pocket; global relocation remains open. Protection board, leads, insulation, adhesive, retention, and thickness allowance need explicit space. |
| Display and FPC | Keep the actual GDEH0154E01 outline and active-area window. Reconsider the tall parts beneath the screen, which currently cause about 1.5 mm standoff; moving them may help the display zone, but does not reduce a top-mount USB stack elsewhere. Preserve short switching loops and space to open/insert the FPC latch. |
| MCU | Compare a left shift and alternative orientation while moving its support parts as functional groups. Apply the module manufacturer's antenna keepout to both copper layers and nearby metal. Counts of tracks underneath its body are not collision or rerouting counts. |
| USB and protection | Compare the connector maker's recommended footprint, public same-part reference, and actual board. Establish shell anchors, mating face, plug-overmold access, insertion depth, and load transfer before placing ESD/CC/power parts. For mid mount, model router-radius relief and one unambiguous manufacturing outline. |
| NFC | Reserve the antenna area and its feed corridor before general routing. Compare E19 with a moderately smaller, wider-spaced coil, preserving matching access. Do not assume shrinking the coil leaves performance unchanged; metal proximity, inductance, tuning, and read range need assembled tests. |
| Power and ground | Group the charger, its BAT capacitor, and the display switching circuit by their reference layouts. Reserve continuous return paths early and inspect actual filled copper after routing. Old routing completion is not a ground-quality certificate. |
| Keys and servicing | Place all three keys by finger access, cap retention and travel, and support stiffness. Keep SWD/reset/power test points accessible for initial programming and recovery with the display installed. |
| Enclosure and assembly | Budget battery, display, USB, keys, adhesive, frame, and PCB independently; whole-card height is the maximum local stack. Model assembly order, screen support without concentrated load, battery retention, and plug access alongside CAD solids. |

### Sequence

1. Produce comparable component-envelope placements for A and B, including maximum-dimension assumptions and functional groups. Keep old routing visible only as a reference.
2. Select the stack and connector style from their actual clearance, assembly, and manufacturing tradeoffs; then instantiate the E20 PCB and matching CAD from one coordinate/height basis.
3. Place critical local circuits and route critical paths, maintaining ground return space; finish general routing last.
4. Recheck schematic-to-PCB pin mapping, native DRC, copper and NFC branch continuity, actual component/shell distances, board outline export, and assembly access for the selected version.

## 4. What can proceed and what needs physical input

- **Can proceed now:** manufacturer/reference footprint comparison; A/B envelope studies; regrouping components; conventional process selection; outline cleanup; SWD access; cover and plug-clearance concepts; tolerance budget with explicitly provisional values.
- **Needs the user or actual samples before final dimensions:** complete battery and screen/FPC measurements, chosen cover finish/construction, and acceptable final thickness after comparison.
- **Needs prototype testing:** a development board can validate basic NFCT behavior and phone compatibility. It cannot validate the final custom PCB coil beside its real battery, screen, and enclosure. Final tuning/read range, display power transients, and assembly fit still require representative hardware.

## Evidence checked

- Existing EDA SHA256: `16cd65a2089653ea6b0b5723ef6ad56e50db22991cd7fb656e3a4ffb35cc9505`; unchanged by this study.
- V7 stack constants: [enclosure generator](../enclosure/e16-enclosure-right-mid-usb-v7.py); actual J1 clearances: the solid-check record linked above.
- Connector mounting and dimensions: GCT product pages linked above, checked 2026-09-23. USB4500 same-part reference: [KiCad 9.0.7 TinyTapeout PCB](https://github.com/KiCad/kicad-source-mirror/blob/9.0.7/demos/tiny_tapeout/tinytapeout-demo.kicad_pcb).
- Nominal stack sums recalculated with Python. No new placement, routing, DRC, CAD interference, or RF result is claimed for E20.
