#!/usr/bin/env python3
"""Check the printed shells against the real component models of the E16 board.

Run with FreeCAD's command line tool:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        projects/nfc-business-card/scripts/check-e16-board-fit.py

Inputs:
  * enclosure model: enclosure/nfc-card-e16-enclosure-v7.FCStd (override with
    --enclosure=...)
  * board + component STEP exported from EasyEDA
    (pcb_ManufactureData.get3DFile('name', 'step', ['Component Model'], 'Outfit', true)
     then sys_FileSystem.saveFile(); the file lands in ~/Downloads under a
     hidden name and needs a few seconds to finish flushing)

The enclosure puts the PCB bottom face at z = 0.7 mm (0.4 plate + 0.3 gap), so
the exported board, whose datum is its own bottom face, is lifted by that
offset before the comparison. The export also carries unplaced library models
at the origin; they are filtered out. Exit code 1 means a real interference.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Import
import Part

REPO = Path(__file__).resolve().parents[3]
DEFAULT_ENCLOSURE = REPO / "projects/nfc-business-card/enclosure/nfc-card-e16-enclosure-v7.FCStd"
DEFAULT_STEP = Path("/tmp/e16-board.step")
PCB_Z0 = 0.7
CEILING_Z = 4.0
RIBS = [(34.5, 16.4, 47.0, 17.2), (42.6, 0.5, 43.4, 15.5), (1.0, 7.1, 33.0, 7.9)]
BOARD = (0.0, 0.0, 84.0, 52.0)
# The GDEH0154E01 tail leaves the module edge (x 39.32, z 3.05) and has to reach
# J2's mouth at x 48.0 while dropping to the board side; everything under that
# corridor must stay below the tail.
FPC_CORRIDOR = (39.5, 25.0, 48.0, 40.0)


def parse_args():
    args = {"enclosure": DEFAULT_ENCLOSURE, "step": DEFAULT_STEP}
    for token in sys.argv[1:]:
        if token.startswith("--enclosure="):
            args["enclosure"] = Path(token.split("=", 1)[1])
        elif token.startswith("--step="):
            args["step"] = Path(token.split("=", 1)[1])
    return args


def main() -> int:
    args = parse_args()
    if not args["enclosure"].is_file():
        raise SystemExit(f"enclosure model not found: {args['enclosure']}")
    if not args["step"].is_file():
        raise SystemExit(f"board STEP not found: {args['step']}")

    doc = App.openDocument(str(args["enclosure"]))
    shells = {name: doc.getObject(name).Shape for name in ("BottomShell", "TopShell")}
    caps = {name: doc.getObject(name).Shape for name in ("KeyCap1", "KeyCap2") if doc.getObject(name)}

    imported = App.newDocument("BoardFitCheck")
    Import.insert(str(args["step"]), imported.Name)

    raw = []
    for obj in imported.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull():
            continue
        raw.extend(shape.Solids)

    def inside_board(solid: Part.Shape) -> bool:
        box = solid.BoundBox
        x0, y0, x1, y1 = BOARD
        if box.XMin < x0 - 0.5 or box.YMin < y0 - 0.5 or box.XMax > x1 + 0.5 or box.YMax > y1 + 0.5:
            return False
        # unplaced library models sit on the origin corner
        return not (box.XMax <= 1.5 and box.YMax <= 1.5)

    placed = [s.translate(App.Vector(0, 0, PCB_Z0)) for s in raw if inside_board(s)]

    def intersect(shape: Part.Shape, solid: Part.Shape) -> float:
        if not shape.BoundBox.intersect(solid.BoundBox):
            return 0.0
        return shape.common(solid).Volume

    def board_slab(solid: Part.Shape) -> bool:
        box = solid.BoundBox
        return (abs(box.XMin) < 0.5 and abs(box.YMin) < 0.5 and abs(box.XMax - BOARD[2]) < 0.5
                and abs(box.YMax - BOARD[3]) < 0.5 and 0.5 < (box.ZMax - box.ZMin) < 1.2)

    report = {
        "enclosure": str(args["enclosure"].relative_to(REPO)),
        "step": str(args["step"]),
        "solids_total": len(raw),
        "solids_on_board": len(placed),
        "pcb_z0_mm": PCB_Z0,
        "ceiling_z_mm": CEILING_Z,
        "ceiling_note": "Reference plane only; cutouts and local relief change the real shell clearance.",
        "shell_collisions": [],
        "rib_collisions": [],
        "cap_collisions": [],
        "highest_parts": [],
    }

    for name, shell in shells.items():
        for solid in placed:
            volume = intersect(shell, solid)
            if volume <= 0.001:
                continue
            box = solid.BoundBox
            entry = {
                "shell": name,
                "slab": board_slab(solid),
                "volume_mm3": round(volume, 4),
                "bbox": [round(v, 2) for v in (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)],
            }
            report["shell_collisions"].append(entry)

    for rib in RIBS:
        x0, y0, x1, y1 = rib
        box = Part.makeBox(x1 - x0, y1 - y0, CEILING_Z - 3.6, App.Vector(x0, y0, 3.6))
        for solid in placed:
            volume = intersect(box, solid)
            if volume > 0.001:
                bb = solid.BoundBox
                report["rib_collisions"].append({
                    "rib": list(rib),
                    "volume_mm3": round(volume, 4),
                    "bbox": [round(v, 2) for v in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)],
                })

    for cap_name, cap in caps.items():
        for solid in placed:
            volume = intersect(cap, solid)
            if volume <= 0.001:
                continue
            box = solid.BoundBox
            report["cap_collisions"].append({
                "cap": cap_name,
                "volume_mm3": round(volume, 4),
                "bbox": [round(v, 2) for v in (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)],
            })

    seen = set()
    for solid in sorted(placed, key=lambda s: -s.BoundBox.ZMax):
        box = solid.BoundBox
        key = (round(box.XMin, 1), round(box.YMin, 1), round(box.ZMax, 2))
        if key in seen:
            continue
        seen.add(key)
        report["highest_parts"].append({
            "top_z_mm": round(box.ZMax, 3),
            "height_below_reference_ceiling_mm": round(CEILING_Z - box.ZMax, 3),
            "bbox": [round(v, 2) for v in (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)],
        })
        if len(seen) >= 8:
            break

    # Select the placed connector assembly, excluding unplaced library solids.
    j1_objects = [obj for obj in imported.Objects if obj.Label.startswith("J1~")]
    if len(j1_objects) != 1:
        raise RuntimeError(f"Expected one placed J1 assembly, found {len(j1_objects)}")
    j1 = j1_objects[0].Shape.copy()
    j1.translate(App.Vector(0, 0, PCB_Z0))
    report["j1_shell_clearance"] = {}
    for name, shell in shells.items():
        distance, points, _ = j1.distToShape(shell)
        report["j1_shell_clearance"][name] = {
            "minimum_distance_mm": round(distance, 6),
            "intersection_mm3": round(j1.common(shell).Volume, 6),
            "nearest_points_mm": [
                [[round(v, 6) for v in point] for point in pair]
                for pair in points[:3]
            ],
        }

    fx0, fy0, fx1, fy1 = FPC_CORRIDOR
    corridor = []
    for solid in placed:
        box = solid.BoundBox
        if box.XMax < fx0 or box.XMin > fx1 or box.YMax < fy0 or box.YMin > fy1:
            continue
        corridor.append((round(box.ZMax, 3), [round(v, 2) for v in (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)]))
    corridor.sort(reverse=True)
    report["fpc_corridor"] = {
        "box": list(FPC_CORRIDOR),
        "highest_z_mm": corridor[0][0] if corridor else None,
        "highest_bbox": corridor[0][1] if corridor else None,
        "free_above_mm": round(CEILING_Z - corridor[0][0], 3) if corridor else None,
        "solids": len(corridor),
    }

    real = [c for c in report["shell_collisions"] if not c["slab"]]
    report["real_shell_collisions"] = len(real)
    report["ok"] = not real and not report["rib_collisions"] and not report["cap_collisions"]
    # freecadcmd drops unflushed stdout when the script exits.
    print(json.dumps(report, ensure_ascii=False, indent=1), flush=True)
    return 0 if report["ok"] else 1


# freecadcmd sets __name__ to the file stem, so the entry point runs directly.
raise SystemExit(main())
