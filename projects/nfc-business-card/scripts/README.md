# R1 scripts

## 当前确定方案

Use these scripts with the [R1 files](../README.md). Historical E-series scripts are [archived](../archive/pre-r1/scripts/) and must not be run against the live R1 project.

| Script | Purpose |
| --- | --- |
| `eda-exec-wait.mjs`, `eda-export-r1-snapshot.js` | Bridge execution and live geometry export, guarded by both project and PCB UUID |
| `check-r1-copper.py`, `pour_geometry.py` | Physical connectivity, detached pours, single-layer vias and the precise battery B exception within the screen exclusion |
| `check-r1-nfc.py` | Cut-winding topology proof and deliberate bypass negative control |
| `check-netlist-consistency.py` | Schematic/PCB pin-by-pin agreement |
| `check-e20-outline.py` | Generic closed Gerber outline and USB plated-slot verification |
| `check-r1-delivery.py` | Manufacturing files, positions, drill hits, saved evidence and native-source checks |
| `check-r1-case.py` | FreeCAD solid, print mesh and debug-hole checks |
| `render-r1-copper.py` | Render actual saved copper |
| `study-r1-packaging.py` | Read-only CAD/PCB study of thickness, full key motion and battery landing options |
| `compare-gerber-exports.py` | Compare manufacturing geometry across different native export presets |
| `review-r1-layout.py` | Named service-pin decoupling, antenna spacing, copper fragments, TVS topology and discussion findings |
| `plan-r1-chamfered-coil.py` | Generate constant-normal-pitch 45° coil geometry |
| `export-r1-manufacturing.py` | Export the guarded native PCB into a fresh output directory |
| `package-r1.py` | Rebuild the complete local handoff ZIP from tracked source, exports, CAD and evidence |
| `check-proposed-route.py`, `pcb-maze-router.py` | Candidate-route geometry and routing helpers; plans require independent verification |

[Verification commands](../hardware/pcb-r1-delivery.md#reproduce-checks). Install Python dependencies from [requirements.txt](requirements.txt). FreeCAD checks use the [documented runtime](../docs/software.md).

Rebuild the local handoff from the repository root:

```sh
python3 projects/nfc-business-card/scripts/package-r1.py
```
