# R1 antenna and layout review — 2026-09-24

## Status

**Reviewed engineering prototype; vendor DFM and powered/physical tests remain open.** Earlier checkpoints are `bee8846` (PCB/CAD studies) and `ccf9f92` (organization). The current repository checkpoint includes the subsequent drill, return-path, control routing, USB resistor and 2.54 mm SWD/CAD changes. [Current files](../README.md), [machine-readable review](records/r1-review.json), [actual copper preview](../enclosure/renders/r1-routed-front-rear.png).

All 58 component placements, footprints and rotations are unchanged. The board outline is unchanged. SWD cover access is synchronized to the new 2.54 mm pitch. Routing now has **819 segments and 153 vias**. The immediately preceding drill/return-path revision had 825 segments and 155 vias; checkpoint `bee8846` had 824 and 153. Component values R3/R4 are now 0 ohm; their geometry is unchanged.

## Implemented

| Item | Before | After / evidence |
| --- | --- | --- |
| Screen projection | The old rectangle stopped short of the exposed board edges, leaving GND strips | Both layers free of pours in X 0–39.62, Y 17–52 mm, including all three exposed edges; later user-selected top battery B lands/routes are the only non-NFC exception |
| Coil | Five rectangular turns, outer centreline 30 × 24 mm; unequal edge offsets | Five turns, 20 corners at 45°; outer centreline 29.9 × 27.6 mm |
| Edge spacing | Left 2.9, lower 2.7, upper 6.9 mm to centreline | All three 3.000 mm to centreline / 2.875 mm to copper edge |
| Winding spacing | 0.25 mm nominal | 0.25 mm straight and diagonal minimum; 0.50 mm normal pitch maintained through nested chamfers |
| USB CC2 protection | Load branch before U6, leaving about 3.30 mm of TVS stub | Load leaves U6's protection pad; two added vias are on the protected load branch. Incoming connector routing is retained |
| Independent copper audit | Only copper groups containing pads/vias were examined | Detached fill fragments are also checked; injected orphan-fill negative control is rejected |

The coil is made from native PCB trace primitives, with a top crossover and two preserved vias. It is not an image or silkscreen drawing. The native single-net representation is intentional; a separate cut proof checks that the winding is not bypassed.

Nearby conductive material can introduce eddy-current losses and detuning. This supports removing the unnecessary rim, but does not quantify the improvement on this board. The screen remains a nearby load, and the changed winding requires assembled RF tuning. The matching capacitors remain provisional. [NXP AN11564, sections 2.2 and 3.2](https://www.nxp.com/docs/en/application-note/AN11564.pdf).

## Battery B and redundant-via follow-up

Following the user-requested 1.5 mm right shift, B+/B− are at **(32.5,18.7)/(35.5,18.7) mm**, with the battery lead exit at the upper right. Rounded 1.8 × 1.5 mm top lands have approximately **0.65 mm** board-edge clearance, polarity silk and 0.35 mm power routing. A 0.20 mm GND link reconnects a pour island isolated by the new route. No screen-area pours were restored. [Plan](records/r1-battery-b-plan.json), [checks](records/r1-battery-b-check.json).

Removed three vias that no longer join copper on both faces:

| Net | XY, mm | Removed geometry |
| --- | --- | --- |
| BAT_PACK_TBD | (45.840,24.646) | Via at former battery landing route; bottom traces remain joined |
| USB_CC2 | (72.100,28.800) | Via with only top traces after CC2 rerouting |
| VDD_3V3 | (61.665,17.936) | Via and the unused top branch ending there |

Nearby GND stitching vias still contact both face pours and are retained. The audit now checks each via for copper contact on both faces; an injected single-layer CC2 via is rejected. It also rejects unapproved screen-area tracks and any new pour, even inside an allowed battery pad.

The top battery routes cross rear NFC feedlines in XY and approach the winding to approximately **0.87 mm in XY**, on opposite PCB faces. The pads alone remain about 0.73 mm from NFC copper. The right shift increases the route-to-winding XY gap from 0.15 to 0.87 mm; feedline crossings are unchanged. These are geometric facts, not RF qualification. The ferrite lies between the PCB and screen; it does not isolate front battery copper from the rear coil. Assembled tuning remains required.

The user deferred thickness/button work. The [height handoff](../enclosure/r1-height-handoff.md) retains the current 5.8 mm case and records the 3.4 mm pack / 0.25 mm sheet assumptions. The frozen CAD wire/ferrite service volumes need updating for B-pad access in the next mechanical iteration.

## Charger-control routing cleanup

The foldback near (49,23.2) and the overlapping SCL segment were reviewed together with adjacent routing. The saved result reroutes CHG_CE_N and CHG_SCL as a group:

| Net | Segments before → after | Vias before → after | Length before → after |
| --- | ---: | ---: | ---: |
| CHG_CE_N | 29 → 21 | 6 → 4 | 39.56 → 32.98 mm |
| CHG_SCL | 18 → 19 | 4 → 4 | 33.76 → 35.46 mm |

Together: **7 fewer segments, 2 fewer vias and 4.88 mm less trace**. SCL grows by 1.70 mm to free the shorter CE path. This is a verified local improvement, not a claim of globally optimal routing. The numbers come from the saved/reopened native snapshot; EDA merged some proposed segments during creation. All unrelated net traces/vias, pads, placements, board outline and antenna exclusions match the preceding snapshot exactly. USB D− and CC2 retain their functional crossings and protection routing.

[Before/after front and rear comparison](../enclosure/renders/r1-control-routing-comparison.png), [actual metrics and preservation checks](records/r1-route-cleanup-check.json), [construction plan](records/r1-route-cleanup-plan.json).

## USB firmware and recovery hardware

R3/R4 changed from 27 ohm to **0 ohm / C21189**, with schematic/PCB procurement fields and native BOM synchronized. The nRF52840 PHY already includes series resistors. D+/D−, CC pull-downs, VBUS, charger defaults, existing key and all five SWD signals were checked against the netlist. [Hardware review, primary references and firmware/bench follow-up](r1-usb-swd-recovery.md), [machine checks](records/r1-usb-swd-check.json).

UF2 and USB CDC remain firmware candidates requiring board-specific implementation and tests. The user will perform initial SWD programming; no factory programming is requested. The user selected the generic Lushen single-row 5P clip and accepted nominal 2.54 mm fit assumptions. Five rear lands/silk and their access routes are updated; TP1/GND is square for orientation. A physical trial fit remains. [SWD change check](records/r1-swd-254-check.json). A hidden side-operated RESET has a [CAD space study](../enclosure/r1-recovery-study.md), but its tool guide/stop and final footprint are not released; no RESET component has been added.

## Findings to discuss

### 1. C1/C8 service assignment — previous finding retracted

The previous review mapped C1 to U2.10 and omitted C8. That was incorrect. **C1.1 is 1.24 mm from U1.32 (module VBUS); C8.1 is 1.75 mm from U2.10 (charger IN).** Both capacitors share `USB_VBUS`, but serve different local loads. No component was moved. The checker now names both service pairs, with ground-via distances computed from the saved geometry.

C8 is Samsung CL10A475KO8NNNC, 4.7 µF / 16 V / X5R. Its manufacturer typical 25 °C DC-bias curve gives about 2.35 µF at 5 V (about 2.12 µF when also allowing −10% nominal tolerance). TI requires at least 1 µF effective IN capacitance. This supports the existing 5 V input choice; it does not guarantee full-temperature behaviour or replace transient testing. The manufacturer now marks this part NRND and suggests CL10A475KO8NQN#; no BOM substitution was made. [Samsung product data](https://product.samsungsem.com/mlcc/CL10A475KO8NNN.do), [TI sections 7.2.2/9.1](https://www.ti.com/lit/ds/symlink/bq25186.pdf), [recorded evidence](records/r1-input-capacitor-check.json).

### 2. USB return stitching — partial geometric improvement

Added GND vias at **(52.25,12.35)** and **(75.00,24.15) mm**, outside SMT lands. Both touch copper on both faces and belong to the single connected GND network. The worst nearest-GND-via distance falls from **3.66 to 2.62 mm**. Four USB transitions remain above the contextual 1.6 mm guideline (about 1.68, 2.11, 2.46 and 2.62 mm).

A closer candidate at (53.35,14.95) would sit in a region isolated from local GND on both layers; local 0.25 mm GND-route screening could not connect it without crossing existing copper. It was not installed. Eliminating every detour would require additional signal rerouting; the proximity guideline alone does not establish that tradeoff is necessary for USB full speed. Reference continuity and USB operation remain prototype validation items, not claimed fixes or certifications.

### 2a. Small holes — enlarged

All six nominal 0.2 mm holes are gone: five USB holes are now 0.25 mm with 0.45 mm lands; the battery via is now 0.30/0.55 mm, shifted 0.15 mm left. Battery solder lands remain at the user's selected positions. The two former 0.30/0.20 mm CC2 vias now have a nominal 0.10 mm annular ring instead of 0.05 mm. The board remains two-layer, with 97 nominal 0.25 mm and 56 nominal 0.30 mm vias. [Decision, current capabilities and remaining vendor checks](r1-preorder.md).

### 3. NFC screen/ferrite/tuning — physical validation

The enlarged coil is still behind the screen. The existing optional ferrite service envelope covers it, but neither a ferrite material nor a final tuning capacitance has been qualified. Test the assembled screen, case and battery environment. Keep the ground rim removed during those tests.

## Other reviewed areas

| Rule / area | Computed result / applicability |
| --- | --- |
| GP-003 / ground connectivity | One connected GND network across layers; no orphan copper fragments |
| BLE module keepouts | No copper intrusion in either all-layer keepout or top-only extension |
| ES-002 / TVS ground | U5 nearest GND via 0.899 mm, 7 within 3 mm; U6 0.800 mm, 6 within 3 mm |
| ES-001 / CC2 topology | Removing the incoming U6 trace separates J1 from the U6 + R2 branch; prior pre-protection tee removed |
| SW-002 / switching node | `EPD_SW` copper area 9.757 mm²; below the upstream 25 mm² review threshold |
| SW-003 / placement proxy | C10–L1–Q1 pad triangle 5.643 mm²; e-paper charge-pump topology needs waveform validation, not a generic buck-loop claim |
| Ground ring BE-002 | Not applied inside the NFC keepout; its plane-pair edge-emission premise does not override antenna clearance |
| GP-002 / inner-layer rules | Not applicable to this two-layer board |
| Full-board copper-fill percentage | Not a gate because NFC/BLE clearances intentionally remove copper |
| Mechanical reuse | 58 unchanged placements and outline; 238 exported component STEP solids match in volume, area and bounds; the 5.8 mm case has synchronized 2.54 mm SWD holes |

The TVS routing change follows TI's recommendation to eliminate the branch between the protected line and the TVS. It does not claim ESD qualification; the retained connector fanout still uses layer changes. [TI SLVA680A, sections 2.1 and 2.3](https://www.ti.com/lit/an/slva680/slva680.pdf).

## Verification

Saved, closed and reopened native DRC: **0**. Independent copper: **0 split nets, 0 dead ends, 0 orphan copper, 0 single-layer or isolated vias**. Schematic/PCB: **58 references, 238 pins, 0 mismatches**. NFC winding cut and deliberate bypass negative control pass. Coil corners/spacing/edge offsets and the expanded screen/BLE exclusions are measured from the saved native snapshot. Manufacturing exports are refreshed for this review checkpoint.

```sh
python3 projects/nfc-business-card/scripts/review-r1-layout.py --snapshot projects/nfc-business-card/hardware/records/r1-routed-snapshot.json --pins projects/nfc-business-card/hardware/records/r1-pcb-pins.json --output projects/nfc-business-card/hardware/records/r1-review.json
```

See [delivery checks](pcb-r1-delivery.md#reproduce-checks) for copper, topology, netlist, profile and bundle verification. Passing these checks does not qualify RF, USB operation or physical assembly.

## Method and provenance

Applied the repository [pcb-methodology skill](../../../.agents/skills/pcb-methodology/SKILL.md), with read-only references to:

- `upstreams/kicad-happy/skills/emc/references/pcb-emc-rules.md`, revision `a6bba1add1e18b89e3aa0824b9769ed1d9d79174`: DC-001/DC-003, GP-003, SW-002/SW-003, ES-001/ES-002, RP-001 and BE-002.
- `upstreams/pcb-skill/skills/pcb/SKILL.md`, revision `6e939b64907e3c63236c7522c511af5d7d1afaad`: independently verify physical geometry and manufacturing outputs.
- `upstreams/pcba-design-skills/.agents/skills/pcb-layout-review/references/layout-review-checklist.md`, revision `d41e9996f052016727403236cf0f7476f8f23a1b`: prove each copper fragment reaches its net; invalidate downstream evidence after copper changes.

Thresholds are used only with stated board-specific applicability. This was one agent's systematic review with independent exported-geometry checks, not a separate human review or physical certification.
