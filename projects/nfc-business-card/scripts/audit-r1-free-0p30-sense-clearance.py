#!/usr/bin/env python3
"""Audit copper, via-to-pad, and optional Gerber silk-to-pad clearances."""

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

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


def silk_pad_audit(gerber, pads):
    results = {}
    with ZipFile(gerber) as archive:
        for filename, layer in (("Gerber_TopSilkscreenLayer.GTO", 1),
                                ("Gerber_BottomSilkscreenLayer.GBO", 2)):
            lines = archive.read(filename).decode().splitlines()
            apertures = {
                int(match[1]): float(match[2])
                for line in lines
                if (match := re.fullmatch(r"%ADD(\d+)C,([\d.]+)\*%", line))
            }
            pad_shapes = [pad_shape(pad) for pad in pads if pad["layer"] in (layer, 12)]
            tree = STRtree(pad_shapes)
            section = "other"
            aperture = None
            previous = None
            in_region = False
            counts = defaultdict(lambda: {"strokes": 0, "within_0p13_mm": 0, "touching_pad": 0})
            for line in lines:
                if line.startswith("G04 Text Start"):
                    section = "text"
                elif line.startswith("G04 PolygonModel Start"):
                    section = "footprint"
                elif line.startswith("G04 Circle Start"):
                    section = "circle"
                if line == "G36*":
                    in_region = True
                    previous = None
                    continue
                if line == "G37*":
                    in_region = False
                    previous = None
                    continue
                if match := re.fullmatch(r"G54D(\d+)\*", line):
                    aperture = int(match[1])
                    continue
                if in_region:
                    continue
                match = re.fullmatch(r"G0[123]X(\d+)Y(\d+)D(0[123])\*", line)
                if not match:
                    continue
                x, y, operation = match.groups()
                position = (int(x) / 1_000_000, int(y) / 1_000_000)
                if operation == "01" and previous is not None and aperture in apertures:
                    stroke = LineString((previous, position)).buffer(apertures[aperture] / 2)
                    counts[section]["strokes"] += 1
                    gaps = [stroke.distance(pad_shapes[int(index)])
                            for index in tree.query(stroke.buffer(.13))]
                    if gaps and min(gaps) < .13:
                        counts[section]["within_0p13_mm"] += 1
                    if gaps and min(gaps) < .01:
                        counts[section]["touching_pad"] += 1
                previous = position
            results[filename] = dict(counts)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=RECORDS / "r1-free-0p30-sense-snapshot.json")
    parser.add_argument("--pins", type=Path, help="Exported PCB pin map for component references")
    parser.add_argument("--gerber", type=Path, help="Gerber ZIP for approximate silk-to-pad stroke audit")
    parser.add_argument("--output", type=Path, default=RECORDS / "r1-free-0p30-sense-clearance-audit.json")
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    pin_map = json.loads(args.pins.read_text()) if args.pins else []
    pin_locations = [
        (component["ref"], pin)
        for component in pin_map
        for pin in component["pins"]
    ]
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
                pair = {
                    "gap_mm": round(gap, 4),
                    "net": via["net"],
                    "via_index": via_index,
                    "pad_index": pad_index,
                    "via_center_mm": [round(center.x, 4), round(center.y, 4)],
                    "pad_number": pad["number"],
                }
                if args.pins:
                    matches = [ref for ref, pin in pin_locations
                               if pin["number"] == pad["number"]
                               and pin["net"] == pad["net"]
                               and pin["layer"] == pad["layer"]
                               and math.dist((pin["x"], pin["y"]), (pad["x"], pad["y"])) * MM_PER_MIL < .03]
                    if len(matches) > 1:
                        raise ValueError(f"Ambiguous PCB pin match for pad {pad_index}: {matches}")
                    pair["pad_ref"] = matches[0] if matches else None
                via_hole_pad_pairs.append(pair)
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
        "same_net_via_hole_to_pad_danger_pairs_below_0p10_mm": sum(pair["gap_mm"] < .10 for pair in via_hole_pad_pairs),
        "same_net_via_hole_to_pad_danger_distinct_vias": len({pair["via_index"] for pair in via_hole_pad_pairs if pair["gap_mm"] < .10}),
        "same_net_via_hole_overlapping_pad_pairs": sum(pair["gap_mm"] == 0 for pair in via_hole_pad_pairs),
        "snapshot_sha256": hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
    }
    if args.pins:
        report["pins_sha256"] = hashlib.sha256(args.pins.read_bytes()).hexdigest()
    if args.gerber:
        report["silkscreen_to_pad"] = silk_pad_audit(args.gerber, snapshot["pads"])
        report["gerber_sha256"] = hashlib.sha256(args.gerber.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(findings)} pairs across {len(groups)} net/layer groups; minimum {report['minimum_gap_mm']} mm")


if __name__ == "__main__":
    main()
