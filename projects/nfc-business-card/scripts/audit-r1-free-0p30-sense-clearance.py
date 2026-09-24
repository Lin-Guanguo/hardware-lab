#!/usr/bin/env python3
"""Locate sub-0.15 mm different-net copper gaps in the Sense snapshot."""

import json
from collections import defaultdict
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point, box
from shapely.ops import nearest_points
from shapely.strtree import STRtree


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "hardware/records"
MM_PER_MIL = 0.0254
TARGET_MM = 0.15


def mm(value):
    return value * MM_PER_MIL


def pad_shape(pad):
    kind, width, height, *_ = pad["pad"]
    width, height = mm(width), mm(height)
    if kind == "RECT":
        shape = box(-width / 2, -height / 2, width / 2, height / 2)
    elif kind == "ELLIPSE":
        shape = affinity.scale(Point(0, 0).buffer(1, resolution=32), width / 2, height / 2)
    elif width < height:
        shape = LineString([(0, -(height - width) / 2), (0, (height - width) / 2)]).buffer(width / 2)
    else:
        shape = LineString([(-(width - height) / 2, 0), ((width - height) / 2, 0)]).buffer(height / 2)
    shape = affinity.rotate(shape, pad["rotation"])
    return affinity.translate(shape, mm(pad["x"]), mm(pad["y"]))


def main():
    snapshot = json.loads((RECORDS / "r1-free-0p30-sense-snapshot.json").read_text())
    objects = []
    for index, line in enumerate(snapshot["lines"]):
        if not line["net"]:
            continue
        shape = LineString(
            [(mm(line["x1"]), mm(line["y1"])), (mm(line["x2"]), mm(line["y2"]))]
        ).buffer(mm(line["widthMil"]) / 2)
        objects.append((shape, line["net"], {line["layer"]}, f"track:{index}"))
    for index, pad in enumerate(snapshot["pads"]):
        if pad["net"]:
            layers = {1, 2} if pad["layer"] == 12 else {pad["layer"]}
            objects.append((pad_shape(pad), pad["net"], layers, f"pad:{pad['number']}:{index}"))
    for index, via in enumerate(snapshot["vias"]):
        shape = Point(mm(via["x"]), mm(via["y"])).buffer(mm(via["diameterMil"]) / 2, resolution=32)
        objects.append((shape, via["net"], {1, 2}, f"via:{index}"))

    tree = STRtree([obj[0] for obj in objects])
    findings = []
    for index, (shape, net, layers, label) in enumerate(objects):
        for match in tree.query(shape.buffer(TARGET_MM)):
            match = int(match)
            if match <= index:
                continue
            other_shape, other_net, other_layers, other_label = objects[match]
            common_layers = layers & other_layers
            if net == other_net or not common_layers:
                continue
            gap = shape.distance(other_shape)
            if gap >= TARGET_MM - 0.0005:
                continue
            a, b = nearest_points(shape, other_shape)
            findings.append({
                "gap_mm": round(gap, 4),
                "net1": net,
                "net2": other_net,
                "object1": label,
                "object2": other_label,
                "closest_midpoint_mm": [round((a.x + b.x) / 2, 2), round((a.y + b.y) / 2, 2)],
                "layers": sorted(common_layers),
            })
    findings.sort(key=lambda item: item["gap_mm"])
    groups = defaultdict(list)
    for finding in findings:
        key = (finding["net1"], finding["net2"], tuple(finding["layers"]))
        groups[key].append(finding)
    report = {
        "target_mm": TARGET_MM,
        "scope": "Lines, pads and vias in the exported snapshot; excludes poured copper and solder-mask openings. Rounded pad geometry is approximate.",
        "pair_count_below_target": len(findings),
        "net_pair_groups_below_target": len(groups),
        "minimum_gap_mm": findings[0]["gap_mm"] if findings else None,
        "groups": [
            {
                "nets": [net1, net2],
                "layers": list(layers),
                "minimum_gap_mm": min(item["gap_mm"] for item in values),
                "closest_midpoint_mm": min(values, key=lambda item: item["gap_mm"])["closest_midpoint_mm"],
                "pair_count": len(values),
            }
            for (net1, net2, layers), values in groups.items()
        ],
        "pairs": findings,
    }
    path = RECORDS / "r1-free-0p30-sense-clearance-audit.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(findings)} pairs across {len(groups)} net/layer groups; minimum {report['minimum_gap_mm']} mm")


if __name__ == "__main__":
    main()
