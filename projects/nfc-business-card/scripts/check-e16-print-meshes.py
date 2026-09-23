#!/usr/bin/env python3
"""Validate the exported E16 V7 print meshes (the STL files a printer consumes).

The V7 geometry report checks the FreeCAD *solids*; the slicer only ever sees
the exported *meshes*, so this script re-opens the three STL files and reports
what a slicer would complain about:

* is the mesh closed (a solid) and free of non-manifold edges;
* are there self-intersections or degenerate/duplicate triangles;
* does the bounding box match the documented stack (84 x 52 outer, 4.5 mm total).

Run it with FreeCAD's bundled interpreter, which ships the Mesh module:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
      projects/nfc-business-card/scripts/check-e16-print-meshes.py
"""

from __future__ import annotations

import json
from pathlib import Path

import FreeCAD  # noqa: F401  (imported for the module side effects)
import Mesh

REPO = Path(__file__).resolve().parents[3]
ENCLOSURE = REPO / "projects/nfc-business-card/enclosure"
MESHES = {
    "bottom_shell": ENCLOSURE / "nfc-card-e16-bottom-v7.stl",
    "top_shell": ENCLOSURE / "nfc-card-e16-top-v7.stl",
    "keycaps": ENCLOSURE / "nfc-card-e16-keycaps-v7.stl",
}
OUTER_MM = (84.0, 52.0)
TOTAL_HEIGHT_MM = 4.5


def bbox(mesh):
    return [round(v, 3) for v in (*(mesh.BoundBox.XMin, mesh.BoundBox.YMin, mesh.BoundBox.ZMin),
                                  *(mesh.BoundBox.XMax, mesh.BoundBox.YMax, mesh.BoundBox.ZMax))]


def count_degenerate(mesh):
    """Facets with a repeated corner or (near) zero area."""
    count = 0
    for facet in mesh.Facets:
        idx = list(facet.PointIndices)
        if len(set(idx)) < 3:
            count += 1
            continue
        pts = [mesh.Points[i].Vector for i in idx]
        cross = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        if cross.Length < 1e-9:
            count += 1
    return count


def count_duplicate_points(mesh):
    """Vertices that sit on top of each other (slicers usually merge these)."""
    seen = {}
    duplicates = 0
    for point in mesh.Points:
        key = (round(point.Vector.x, 6), round(point.Vector.y, 6), round(point.Vector.z, 6))
        if key in seen:
            duplicates += 1
        else:
            seen[key] = True
    return duplicates


def check(path: Path):
    mesh = Mesh.Mesh(str(path))
    report = {
        "file": path.name,
        "facets": mesh.CountFacets,
        "points": mesh.CountPoints,
        "bbox_mm": bbox(mesh),
        "volume_mm3": round(mesh.Volume, 3),
        "area_mm2": round(mesh.Area, 3),
        "is_solid": mesh.isSolid(),
        "self_intersections": len(mesh.getSelfIntersections()),
        "has_non_manifolds": mesh.hasNonManifolds(),
        "degenerate_facets": count_degenerate(mesh),
        "duplicate_points": count_duplicate_points(mesh),
        "problems": [],
    }
    b = report["bbox_mm"]
    if report["facets"] == 0:
        report["problems"].append("empty mesh")
    if not report["is_solid"]:
        report["problems"].append("mesh is not closed")
    if report["self_intersections"]:
        report["problems"].append("self-intersecting facets")
    if report["has_non_manifolds"]:
        report["problems"].append("non-manifold edges or points")
    if report["degenerate_facets"]:
        report["problems"].append("degenerate facets")
    width, height = b[3] - b[0], b[4] - b[1]
    if path.name.startswith("nfc-card-e16-keycaps"):
        # The keycap file is a cluster of three caps around the key column, not a
        # full-card part: it only has to sit inside the card and reach the top face.
        if b[0] < 0 or b[1] < 0 or b[3] > OUTER_MM[0] or b[4] > OUTER_MM[1]:
            report["problems"].append(f"keycaps outside the {OUTER_MM[0]} x {OUTER_MM[1]} outline")
        if round(b[5], 2) != TOTAL_HEIGHT_MM:
            report["problems"].append(f"keycap top {b[5]} mm does not reach the {TOTAL_HEIGHT_MM} mm top face")
    else:
        if round(width, 2) != OUTER_MM[0] or round(height, 2) != OUTER_MM[1]:
            report["problems"].append(f"outer size {width:.2f} x {height:.2f} mm != {OUTER_MM[0]} x {OUTER_MM[1]}")
        if b[5] > TOTAL_HEIGHT_MM + 0.01:
            report["problems"].append(f"z max {b[5]} exceeds the {TOTAL_HEIGHT_MM} mm stack")
    return report


def run():
    reports = []
    for label, path in MESHES.items():
        if not path.is_file():
            reports.append({"part": label, "file": str(path), "problems": ["missing file"]})
            continue
        report = check(path)
        report["part"] = label
        reports.append(report)
    ok = all(not r["problems"] for r in reports)
    result = {"ok": ok, "parts": reports}
    # FreeCAD's mesh routines print progress to stdout after this script finishes,
    # so keep the machine-readable copy in a file and print a short summary here.
    out = REPO / "projects/nfc-business-card/enclosure/nfc-card-e16-print-meshes-report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(f"ok={ok}  report={out}")
    for r in reports:
        print(f"  {r['part']:12s} facets={r.get('facets')} solid={r.get('is_solid')} "
              f"self={r.get('self_intersections')} nonmanifold={r.get('has_non_manifolds')} "
              f"degenerate={r.get('degenerate_facets')} problems={r['problems']}", flush=True)
    return 0 if ok else 1


# freecadcmd execs the file without setting __name__ to "__main__", so call it
# unconditionally (same pattern as the other FreeCAD checkers in this folder).
raise SystemExit(run())
