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
| `check-r1-free-0p30-sense.py` | 独立电池采样候选的工程、BOM/CPL、Gerber 孔径/孔环与已有本地证据校验；目前报告不可投产 |
| `check-r1-relayout-r3.py` | R3 独立布局试验的原生工程、BOM/CPL、钻孔/孔环与本地检查对账；明确报告小孔阻塞 |
| `check-r1-layout-r4.py` | R4 已布线候选的保存工程、同版 Gerber/BOM/CPL、孔环与本地检查记录对账；供应商 DFM 另行审核 |
| `audit-r1-free-0p30-sense-clearance.py` | 定位该候选中走线/焊盘/过孔的 <0.15 mm 异网间距，生成坐标记录；不包括铺铜 |
| `check-r1-usb-swd.py` | USB/charger/key/SWD pin assignments and R3/R4 procurement consistency; records unverified firmware and fixture status |
| `check-r1-case.py` | FreeCAD solid, print mesh and debug-hole checks |
| `render-r1-copper.py` | Render actual saved copper |
| `study-r1-packaging.py` | Read-only CAD/PCB study of thickness, full key motion and battery landing options |
| `compare-gerber-exports.py` | Compare manufacturing geometry across different native export presets |
| `review-r1-layout.py` | Named service-pin decoupling, antenna spacing, copper fragments, TVS topology and discussion findings |
| `plan-r1-chamfered-coil.py` | Generate constant-normal-pitch 45° coil geometry |
| `export-r1-manufacturing.py` | Export the guarded native PCB into a fresh output directory; an independent candidate can specify its project UUID, prefix and diagnostic core files |
| `package-r1.py` | Rebuild the complete local handoff ZIP from tracked source, exports, CAD and evidence |
| `check-proposed-route.py`, `pcb-maze-router.py` | 候选走线几何与离线布线辅助；后者默认 0.30 mm 钻孔、0.55 mm 外径、0.15 mm 线间距目标，结果仍需独立验证 |

[Verification commands](../hardware/pcb-r1-delivery.md#reproduce-checks). Install Python dependencies from [requirements.txt](requirements.txt). FreeCAD checks use the [documented runtime](../docs/software.md).

Rebuild the local handoff from the repository root:

```sh
python3 projects/nfc-business-card/scripts/package-r1.py
```
