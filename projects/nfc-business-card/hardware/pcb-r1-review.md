# R1 antenna and layout review — 2026-09-24

## Status

**Reviewed prototype checkpoint; discuss remaining placement changes before ordering.** The organized checkpoint is Git commit `ccf9f92`. [Current files](../README.md), [machine-readable review](records/r1-review.json), [actual copper preview](../enclosure/renders/r1-routed-front-rear.png).

All 58 component placements, footprints and rotations are unchanged. The board outline and enclosure geometry are unchanged. Routing now has **824 segments and 153 vias**, compared with 792 and 151 in the checkpoint.

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

## Findings to discuss

### 1. C1 input decoupling — fix before ordering

**C1.1 to U2.10 is 14.28 mm** between pad centres. C1 is the external bypass capacitor on `USB_VBUS`; U2 is the BQ25186 charger. This exceeds the upstream DC-001 8 mm review threshold. More directly, TI specifies local IN/SYS/BAT capacitors at the IC. Move C1 close to U2 IN/GND, or retain it and add an appropriately specified local input capacitor after checking the BOM and bias derating. Component placement is deliberately left for the next discussion. [BQ25186 datasheet, sections 7.2.2 and 9.1](https://www.ti.com/lit/ds/symlink/bq25186.pdf).

This is a layout finding that DRC and netlist agreement cannot detect. The other checked service pairs C2–C7/C9/C10 are 1.27–2.20 mm from their named supply pins; their nearest GND vias are all within 1.65 mm. C1's own GND via is near it, which does not compensate for the long connection to U2.

### 2. USB return stitching — optimization

Five USB signal vias are beyond the contextual 1.6 mm nearest-GND-via guideline: gaps are about 1.68, 1.99, 2.12, 2.46 and 3.66 mm. The two largest are near X54.1 at the MCU-side fanout. Evaluate legal nearby GND stitching without obstructing power/USB routing. This is a geometry-based return-path concern, not a demonstrated USB failure or an impedance certification.

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
| Mechanical reuse | 58 unchanged placements and outline; 238 exported STEP solids match in volume, area and bounds; existing case retained |

The TVS routing change follows TI's recommendation to eliminate the branch between the protected line and the TVS. It does not claim ESD qualification; the retained connector fanout still uses layer changes. [TI SLVA680A, sections 2.1 and 2.3](https://www.ti.com/lit/an/slva680/slva680.pdf).

## Verification

Saved, closed and reopened native DRC: **0**. Independent copper: **0 split nets, 0 dead ends, 0 orphan copper, 0 single-layer or isolated vias**. Schematic/PCB: **58 references, 238 pins, 0 mismatches**. NFC winding cut and deliberate bypass negative control pass. Coil corners/spacing/edge offsets and the expanded screen/BLE exclusions are measured from the saved native snapshot. Manufacturing exports are refreshed for this review checkpoint.

```sh
python3 projects/nfc-business-card/scripts/review-r1-layout.py --snapshot projects/nfc-business-card/hardware/records/r1-routed-snapshot.json --pins projects/nfc-business-card/hardware/records/r1-pcb-pins.json --output projects/nfc-business-card/hardware/records/r1-review.json
```

See [delivery checks](pcb-r1-delivery.md#reproduce-checks) for copper, topology, netlist, profile and bundle verification. Passing those checks does not close the C1 finding.

## Method and provenance

Applied the repository [pcb-methodology skill](../../../.agents/skills/pcb-methodology/SKILL.md), with read-only references to:

- `upstreams/kicad-happy/skills/emc/references/pcb-emc-rules.md`, revision `a6bba1add1e18b89e3aa0824b9769ed1d9d79174`: DC-001/DC-003, GP-003, SW-002/SW-003, ES-001/ES-002, RP-001 and BE-002.
- `upstreams/pcb-skill/skills/pcb/SKILL.md`, revision `6e939b64907e3c63236c7522c511af5d7d1afaad`: independently verify physical geometry and manufacturing outputs.
- `upstreams/pcba-design-skills/.agents/skills/pcb-layout-review/references/layout-review-checklist.md`, revision `d41e9996f052016727403236cf0f7476f8f23a1b`: prove each copper fragment reaches its net; invalidate downstream evidence after copper changes.

Thresholds are used only with stated board-specific applicability. This was one agent's systematic review with independent exported-geometry checks, not a separate human review or physical certification.
