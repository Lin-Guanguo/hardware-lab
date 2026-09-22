#!/usr/bin/env python3
"""Audit the E16 snapshot's copper for split nets and dead ends.

The native DRC panel reports "connection 0" for the E16 board even when a net
is split, so this checker walks the copper geometry itself:

* every net's pads and vias must end up in one connected copper group
  (GND is excluded: it also connects through the two ground pours);
* every copper end must land on a pad, a via or another trace of the same net,
  so a stub left behind by a reroute shows up instead of hiding in the pour.

Pad extents are stored in the footprint's local frame, so the snapshot's pad
rotation is applied before the overlap test. Distances use the real trace
widths: two pieces of copper connect when their copper bodies overlap.

    python3 scripts/check-e16-copper-connectivity.py
    python3 scripts/check-e16-copper-connectivity.py --snapshot hardware/old.json

Exit status is 0 when no net is split and no dead copper end exists.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

MIL = 39.37007874015748
REPO = Path(__file__).resolve().parents[3]
DEFAULT_SNAPSHOT = REPO / "projects/nfc-business-card/hardware/e16-right-mid-snapshot.json"


def pad_box(pad):
    """Board-frame half extents of a pad, honouring its own rotation."""
    raw = pad.get("pad") or []
    width = float(raw[1]) if len(raw) > 1 and isinstance(raw[1], (int, float)) else 6.0
    height = float(raw[2]) if len(raw) > 2 and isinstance(raw[2], (int, float)) else width
    if abs(pad.get("rotation", 0)) % 180 == 90:
        width, height = height, width
    return pad["x"], pad["y"], width / 2, height / 2


def point_to_segment(px, py, line):
    ax, ay, bx, by = line["x1"], line["y1"], line["x2"], line["y2"]
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _closest_on_segment(px, py, line):
    ax, ay, bx, by = line["x1"], line["y1"], line["x2"], line["y2"]
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return ax + t * dx, ay + t * dy


def segment_to_segment(first, second):
    ax, ay, bx, by = first["x1"], first["y1"], first["x2"], first["y2"]
    cx, cy, dx, dy = second["x1"], second["y1"], second["x2"], second["y2"]

    def cross(ox, oy, px, py, qx, qy):
        return (px - ox) * (qy - oy) - (py - oy) * (qx - ox)

    d1 = cross(ax, ay, bx, by, cx, cy)
    d2 = cross(ax, ay, bx, by, dx, dy)
    d3 = cross(cx, cy, dx, dy, ax, ay)
    d4 = cross(cx, cy, dx, dy, bx, by)
    if (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0):
        return 0.0
    return min(
        point_to_segment(ax, ay, second), point_to_segment(bx, by, second),
        point_to_segment(cx, cy, first), point_to_segment(dx, dy, first),
    )


def distance_to_box(x, y, box):
    cx, cy, half_w, half_h = box
    return math.hypot(max(0.0, abs(x - cx) - half_w), max(0.0, abs(y - cy) - half_h))


class Groups:
    def __init__(self):
        self.parent = {}

    def add(self, key):
        self.parent.setdefault(key, key)

    def find(self, key):
        while self.parent[key] != key:
            self.parent[key] = self.parent[self.parent[key]]
            key = self.parent[key]
        return key

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def audit(snapshot):
    lines = snapshot["lines"]
    vias = snapshot["vias"]
    if any("rotation" not in pad for pad in snapshot["pads"]):
        raise SystemExit(
            "snapshot has no pad rotation; re-export it with eda-export-e16-snapshot.js "
            "(pad extents are stored in the footprint's local frame)"
        )

    groups = Groups()
    for index in range(len(lines)):
        groups.add(("line", index))

    terminals = []  # (kind, label, net, geometry)
    for pad in snapshot["pads"]:
        label = f"{pad['number']}@({pad['x'] / MIL:.2f},{pad['y'] / MIL:.2f})"
        terminals.append(("pad", label, pad.get("net"), pad_box(pad)))
    for index, via in enumerate(vias):
        radius = via["diameterMil"] / 2
        label = f"via@{index}({via['x'] / MIL:.2f},{via['y'] / MIL:.2f})"
        terminals.append(("via", label, via.get("net"), (via["x"], via["y"], radius, radius)))
    for kind, label, net, _ in terminals:
        if net:
            groups.add((kind, label, net))

    by_layer = defaultdict(list)
    for index, line in enumerate(lines):
        by_layer[line["layer"]].append(index)
    for _, indices in by_layer.items():
        for position, i in enumerate(indices):
            for j in indices[position + 1:]:
                first, second = lines[i], lines[j]
                if first["net"] != second["net"]:
                    continue
                if segment_to_segment(first, second) <= (first["widthMil"] + second["widthMil"]) / 2:
                    groups.union(("line", i), ("line", j))

    for kind, label, net, box in terminals:
        if not net:
            continue
        key = (kind, label, net)
        for index, line in enumerate(lines):
            if line["net"] != net:
                continue
            if kind == "pad":
                # Closest point of the trace centreline to the pad centre, then
                # the distance from that point to the pad rectangle.
                ax, ay = _closest_on_segment(box[0], box[1], line)
                distance = distance_to_box(ax, ay, box)
            else:
                distance = max(0.0, point_to_segment(box[0], box[1], line) - box[2])
            if distance <= line["widthMil"] / 2:
                groups.union(("line", index), key)

    for position, (kind_a, label_a, net_a, box_a) in enumerate(terminals):
        for kind_b, label_b, net_b, box_b in terminals[position + 1:]:
            if not net_a or net_a != net_b:
                continue
            if kind_a == "pad" and kind_b == "pad":
                overlaps = (abs(box_a[0] - box_b[0]) <= box_a[2] + box_b[2]
                            and abs(box_a[1] - box_b[1]) <= box_a[3] + box_b[3])
            elif kind_a == "via" and kind_b == "via":
                overlaps = math.hypot(box_a[0] - box_b[0], box_a[1] - box_b[1]) <= box_a[2] + box_b[2]
            else:
                pad, via = (box_a, box_b) if kind_a == "pad" else (box_b, box_a)
                overlaps = distance_to_box(via[0], via[1], pad) <= via[2]
            if overlaps:
                groups.union((kind_a, label_a, net_a), (kind_b, label_b, net_b))

    by_net = defaultdict(list)
    for kind, label, net, _ in terminals:
        if net:
            by_net[net].append((kind, label, net))
    split_nets = []
    for net, members in sorted(by_net.items()):
        if net == "GND":
            continue  # also connects through the two ground pours
        buckets = defaultdict(list)
        for kind, label, member_net in members:
            buckets[groups.find((kind, label, member_net))].append(label)
        if len(buckets) > 1:
            split_nets.append({"net": net, "groups": [sorted(group) for group in buckets.values()]})

    dead_ends = []
    for index, line in enumerate(lines):
        half_width = line["widthMil"] / 2
        for x, y in ((line["x1"], line["y1"]), (line["x2"], line["y2"])):
            attached = []
            for kind, label, net, box in terminals:
                if not net or net != line["net"]:
                    continue
                distance = distance_to_box(x, y, box) if kind == "pad" else max(0.0, math.hypot(x - box[0], y - box[1]) - box[2])
                if distance <= half_width:
                    attached.append(label)
            for other_index, other in enumerate(lines):
                if other_index == index or other["layer"] != line["layer"] or other["net"] != line["net"]:
                    continue
                if point_to_segment(x, y, other) <= half_width + other["widthMil"] / 2:
                    attached.append(f"line{other_index}")
            if not attached:
                dead_ends.append({
                    "net": line["net"],
                    "layer": line["layer"],
                    "x_mm": round(x / MIL, 3),
                    "y_mm": round(y / MIL, 3),
                    "segment_length_mm": round(math.hypot(line["x2"] - line["x1"], line["y2"] - line["y1"]) / MIL, 3),
                })

    return {
        "snapshot": str(snapshot.get("_path", "")),
        "components": len(snapshot["components"]),
        "pads": len(snapshot["pads"]),
        "copper_lines": len(lines),
        "vias": len(vias),
        "nets_checked": len(by_net) - 1,
        "split_nets": split_nets,
        "dead_ends": dead_ends,
        "ok": not split_nets and not dead_ends,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    snapshot["_path"] = str(args.snapshot)
    report = audit(snapshot)
    report["snapshot"] = str(args.snapshot)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
