#!/usr/bin/env python3
"""Locate sub-0.15 mm different-net copper gaps in the Sense snapshot."""

import argparse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=RECORDS / "r1-free-0p30-sense-snapshot.json")
    parser.add_argument("--output", type=Path, default=RECORDS / "r1-free-0p30-sense-clearance-audit.json")
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
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
            if gap >= TARGET_MM:
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
    via_hole_pad_pairs = []
    for via_index, via in enumerate(snapshot["vias"]):
        center = Point(mm(via["x"]), mm(via["y"]))
        radius = mm(via["holeMil"]) / 2
        for pad_index, pad in enumerate(snapshot["pads"]):
            if pad["net"] != via["net"] or pad["layer"] not in (1, 2, 12):
                continue
            gap = max(0, center.distance(pad_shape(pad)) - radius)
            if gap < TARGET_MM:
                via_hole_pad_pairs.append({
                    "gap_mm": round(gap, 4),
                    "net": via["net"],
                    "via_index": via_index,
                    "pad_index": pad_index,
                    "via_center_mm": [round(center.x, 4), round(center.y, 4)],
                    "pad_number": pad["number"],
                })
    via_hole_pad_pairs.sort(key=lambda item: item["gap_mm"])
    report = {
        "target_mm": TARGET_MM,
        "scope": "Different-net copper: lines, pads and vias. Same-net via-hole-to-pad: drilled hole to pad copper. Excludes poured copper and solder-mask openings; rounded pad geometry is approximate.",
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
        "same_net_via_hole_to_pad_pairs_below_target": via_hole_pad_pairs,
    }
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(findings)} pairs across {len(groups)} net/layer groups; minimum {report['minimum_gap_mm']} mm")


if __name__ == "__main__":
    main()
