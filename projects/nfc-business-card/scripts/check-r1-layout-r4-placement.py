#!/usr/bin/env python3
"""Check the independent R4 component placement against the R2 baseline."""

import json
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, box


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "hardware/records"
R2 = json.loads((RECORDS / "r1-free-0p30-sense-ring-r2-snapshot.json").read_text())
R4 = json.loads((RECORDS / "r1-layout-reset-r4-placement-snapshot.json").read_text())
BASE_PADS = {
    c["ref"]: c
    for c in json.loads((RECORDS / "r1-layout-reset-r4-baseline-padmap.json").read_text())
}
NEW_PADS = {
    c["ref"]: c
    for c in json.loads((RECORDS / "r1-layout-reset-r4-placement-padmap.json").read_text())
}

EXPECTED_MOVES = {
    "U4", "C9", "C10", "L1", "Q1", "D1", "C11", "C12", "R13",
    "R14", "R15", "R16", "D2", "D3", "C13",
}
PAIRS = [
    ("C9", "1", "U4", "1"),
    ("C9", "2", "U4", "2"),
    ("C10", "1", "U4", "5"),
    ("C10", "2", "U4", "2"),
    ("L1", "1", "C10", "1"),
    ("L1", "2", "Q1", "3"),
    ("C11", "1", "L1", "2"),
]


def pad_distance(data, a, an, b, bn):
    first = next(p for p in data[a]["pads"] if p["n"] == an)
    second = next(p for p in data[b]["pads"] if p["n"] == bn)
    return math.hypot(first["x"] - second["x"], first["y"] - second["y"]) * .0254


def pad_shape(p):
    raw = p["shape"]
    width = raw[1] * .0254
    height = raw[2] * .0254 if len(raw) > 2 else width
    if raw[0].upper() in ("ELLIPSE", "CIRCLE"):
        shape = affinity.scale(Point(0, 0).buffer(1, quad_segs=24), width / 2, height / 2)
    else:
        shape = box(-width / 2, -height / 2, width / 2, height / 2)
    return affinity.translate(
        affinity.rotate(shape, p.get("rot", 0)), p["x"] * .0254, p["y"] * .0254
    )


def main():
    old_components = {c["ref"]: c for c in R2["components"]}
    new_components = {c["ref"]: c for c in R4["components"]}
    assert len(old_components) == len(new_components) == 66
    assert set(old_components) == set(new_components) == set(BASE_PADS) == set(NEW_PADS)
    changed = {
        ref for ref in old_components
        if any(old_components[ref][key] != new_components[ref][key] for key in ("x", "y", "rotation"))
    }
    assert changed == EXPECTED_MOVES, (changed - EXPECTED_MOVES, EXPECTED_MOVES - changed)

    # Routing is deliberately still the R2 copper. R4 is a placement checkpoint.
    for key in ("lines", "vias", "pours", "poured", "polylines", "regions"):
        assert R2[key] == R4[key], key
    assert len(R4["pads"]) == len(R2["pads"]) == 266

    distances = []
    for a, an, b, bn in PAIRS:
        before = pad_distance(BASE_PADS, a, an, b, bn)
        after = pad_distance(NEW_PADS, a, an, b, bn)
        assert abs(after - before) < .02, (a, an, b, bn, before, after)
        distances.append({"pair": f"{a}-{an} / {b}-{bn}", "r2_mm": round(before, 3), "r4_mm": round(after, 3)})

    closest = None
    for ref in EXPECTED_MOVES:
        for other, c in NEW_PADS.items():
            if other == ref or (other in EXPECTED_MOVES and other < ref):
                continue
            for a in NEW_PADS[ref]["pads"]:
                for b in c["pads"]:
                    if not a["net"] or not b["net"] or a["net"] == b["net"]:
                        continue
                    candidate = (pad_shape(a).distance(pad_shape(b)), ref, a["n"], other, b["n"])
                    if closest is None or candidate < closest:
                        closest = candidate
    assert closest and closest[0] >= .15, closest

    result = {
        "status": "placement_only_not_for_manufacture",
        "source": "R2 native PCB imported as an independent R4 project",
        "components": len(new_components),
        "pads": len(R4["pads"]),
        "moved_components": sorted(changed),
        "routes_unchanged_and_stale": True,
        "named_pad_center_distances": distances,
        "nearest_different_net_pad_gap_involving_moved_component_mm": round(closest[0], 3),
        "nearest_different_net_pad_pair": list(closest[1:]),
        "scope": "Pad copper only; excludes old tracks, vias, pours, solder mask and component bodies.",
    }
    path = RECORDS / "r1-layout-reset-r4-placement-check.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
