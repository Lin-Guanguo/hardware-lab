#!/usr/bin/env python3
"""Check every real component model against the board material of E16.

The shell check (check-e16-board-fit.py) compares parts with the printed
enclosure. This one compares them with the board itself: the PCB outline is
prismed at its real 0.8 mm thickness and every placed component solid from the
exported STEP is intersected with it. Surface-mount parts sit on the board, so
the only solids that may legitimately dip into it are mid-mount or board-edge
parts such as J1; anything else means the outline does not match the parts.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        projects/nfc-business-card/scripts/check-e16-board-clearance.py

Exit code 1 means a real overlap. The exported board STEP carries unplaced
library models on the origin corner; they are filtered out.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Import
import Part

REPO = Path(__file__).resolve().parents[3]
DEFAULT_STEP = Path("/tmp/e16-board.step")

# Board profile from the saved E16 outline (layer 11), in mm: the L-shape with
# the lower-left battery bite and the right-edge USB notch.
OUTLINE = [(33.5, 0.0), (33.5, 15.0), (0.0, 15.0), (0.0, 52.0), (84.0, 52.0),
           (84.0, 20.62), (77.5, 20.62), (77.5, 11.38), (84.0, 11.38), (84.0, 0.0)]
BOARD = (0.0, 0.0, 84.0, 52.0)
PCB_T = 0.8


def parse_args():
    step = DEFAULT_STEP
    for token in sys.argv[1:]:
        if token.startswith("--step="):
            step = Path(token.split("=", 1)[1])
    return step


def board_solid() -> Part.Shape:
    wire = Part.makePolygon([App.Vector(x, y, 0.0) for x, y in OUTLINE]
                            + [App.Vector(*OUTLINE[0], 0.0)])
    return Part.Face(wire).extrude(App.Vector(0, 0, PCB_T))


def main() -> int:
    step = parse_args()
    if not step.is_file():
        raise SystemExit(f"board STEP not found: {step}")

    imported = App.newDocument("BoardClearanceCheck")
    Import.insert(str(step), imported.Name)

    solids = []
    for obj in imported.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull():
            continue
        solids.extend(shape.Solids)

    board = board_solid()

    def placed(solid: Part.Shape) -> bool:
        box = solid.BoundBox
        x0, y0, x1, y1 = BOARD
        if box.XMin < x0 - 0.5 or box.YMin < y0 - 0.5 or box.XMax > x1 + 0.5 or box.YMax > y1 + 0.5:
            return False
        # unplaced library models sit on the origin corner
        return not (box.XMax <= 1.5 and box.YMax <= 1.5)

    def is_board_slab(solid: Part.Shape) -> bool:
        box = solid.BoundBox
        return (abs(box.XMin) < 0.5 and abs(box.YMin) < 0.5 and abs(box.XMax - BOARD[2]) < 0.5
                and abs(box.YMax - BOARD[3]) < 0.5 and 0.5 < (box.ZMax - box.ZMin) < 1.2)

    overlaps = []
    for solid in solids:
        if not placed(solid) or is_board_slab(solid):
            continue
        if not board.BoundBox.intersect(solid.BoundBox):
            continue
        volume = board.common(solid).Volume
        if volume <= 0.001:
            continue
        box = solid.BoundBox
        overlaps.append({
            "volume_mm3": round(volume, 4),
            "bbox": [round(v, 2) for v in (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)],
        })

    overlaps.sort(key=lambda entry: -entry["volume_mm3"])
    report = {
        "step": str(step),
        "solids_total": len(solids),
        "board_outline_mm": OUTLINE,
        "board_thickness_mm": PCB_T,
        "board_volume_mm3": round(board.Volume, 3),
        "overlaps": overlaps,
        "ok": not overlaps,
    }
    print(json.dumps(report, ensure_ascii=False, indent=1), flush=True)
    return 0 if report["ok"] else 1


raise SystemExit(main())
