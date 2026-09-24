# R1 scripts

## 当前确定方案

Use these scripts with the [R1 files](../README.md). Historical E-series scripts are [archived](../archive/pre-r1/scripts/) and must not be run against the live R1 project.

| Script | Purpose |
| --- | --- |
| `eda-exec-wait.mjs`, `eda-export-r1-snapshot.js` | Bridge execution and live geometry export, guarded by both project and PCB UUID |
| `check-r1-copper.py`, `pour_geometry.py` | Independent physical copper connectivity including pours and thermal spokes |
| `check-r1-nfc.py` | Cut-winding topology proof and deliberate bypass negative control |
| `check-netlist-consistency.py` | Schematic/PCB pin-by-pin agreement |
| `check-e20-outline.py` | Generic closed Gerber outline and USB plated-slot verification |
| `check-r1-delivery.py` | Manufacturing files, positions, drill hits, saved evidence and native-source checks |
| `check-r1-case.py` | FreeCAD solid, print mesh and debug-hole checks |
| `render-r1-copper.py` | Render actual saved copper |
| `compare-gerber-exports.py` | Compare manufacturing geometry across different native export presets |
| `package-r1.py` | Rebuild the complete local handoff ZIP from tracked source, exports, CAD and evidence |
| `check-proposed-route.py`, `pcb-maze-router.py` | Candidate-route geometry and routing helpers; plans require independent verification |

[Verification commands](../hardware/pcb-r1-delivery.md#reproduce-checks). Install Python dependencies from [requirements.txt](requirements.txt). FreeCAD checks use the [documented runtime](../docs/software.md).

Rebuild the local handoff from the repository root:

```sh
python3 projects/nfc-business-card/scripts/package-r1.py
```
