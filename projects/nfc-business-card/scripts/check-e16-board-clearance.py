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

Two kinds of overlap are reported but do not fail the check, because they are
artefacts of the CAD data rather than the mechanical fit:

* a surface contact thinner than 0.05 mm, which is modelling precision on a face
  (the connector body touches the board's top face by 4 um);
* a copper land smaller than 1 mm2 that the footprint draws as a block through
  the board thickness (the four J1 shell pads). Pads belong to the board, so
  their crude 3D boxes always overlap it.

Everything else, i.e. any solid that intrudes more than 0.4 mm through the board
over an area above 1 mm2 and by more than 0.05 mm3 of material, fails with exit
code 1. All overlaps are listed in the
report either way. The exported board STEP also carries unplaced library models
on the origin corner; they are filtered out.
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
           (84.0, 20.62), (76.704165, 20.62), (76.704165, 11.38), (84.0, 11.38), (84.0, 0.0)]
BOARD = (0.0, 0.0, 84.0, 52.0)
PCB_T = 0.8
MIN_INTRUSION_DEPTH = 0.4   # mm through the board before an overlap is real
MIN_INTRUSION_AREA = 1.0    # mm2 footprint before an overlap is real
MIN_INTRUSION_VOLUME = 0.05  # mm3 of material before an overlap is real
SURFACE_CONTACT = 0.05      # mm thickness that counts as a face touch, not a fit


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
        piece = board.common(solid)
        solid_box = solid.BoundBox
        # judge each piece of the intersection, not its overall bounding box
        for index, fragment in enumerate(piece.Solids):
            b = fragment.BoundBox
            size = (b.XMax - b.XMin, b.YMax - b.YMin, b.ZMax - b.ZMin)
            overlaps.append({
                "solid_bbox": [round(v, 2) for v in (solid_box.XMin, solid_box.YMin, solid_box.ZMin,
                                                     solid_box.XMax, solid_box.YMax, solid_box.ZMax)],
                "fragment": index,
                "volume_mm3": round(fragment.Volume, 4),
                "intrusion_bbox": [round(v, 3) for v in (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)],
                "intrusion_size_mm": [round(v, 3) for v in size],
                "surface_contact": min(size) <= SURFACE_CONTACT,
                "real": (size[2] >= MIN_INTRUSION_DEPTH
                         and (size[0] * size[1]) >= MIN_INTRUSION_AREA
                         and fragment.Volume >= MIN_INTRUSION_VOLUME
                         and min(size) > SURFACE_CONTACT),
            })

    overlaps.sort(key=lambda entry: -entry["volume_mm3"])
    real = [entry for entry in overlaps if entry["real"]]
    report = {
        "step": str(step),
        "solids_total": len(solids),
        "board_outline_mm": OUTLINE,
        "board_thickness_mm": PCB_T,
        "board_volume_mm3": round(board.Volume, 3),
        "overlaps": overlaps,
        "real_intrusions": real,
        "ok": not real,
    }
    print(json.dumps(report, ensure_ascii=False, indent=1), flush=True)
    return 0 if report["ok"] else 1


raise SystemExit(main())
