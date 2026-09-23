#!/usr/bin/env python3
"""Check proposed copper against the live E16 snapshot before drawing it.

Native DRC only sees the board once the copper exists; this tool answers the
same questions offline for a *plan*: does every trace and via keep the design
clearances to the existing traces, pads and vias, stay inside the board, stay
out of the keep-out regions and keep 0.30 mm hole-to-hole.

Route files use the shape that plan-nfc-coil.py emits:

    {
      "tracks": [{"net": "...", "layer": 1|2, "width_mm": 0.15, "points": [[x,y], ...]}],
      "vias":   [{"net": "...", "x": .., "y": .., "diameter_mm": 0.30, "hole_mm": 0.20}],
      "keepouts": [{"x0": .., "y0": .., "x1": .., "y1": ..}],   # optional, overrides the defaults
      "ignore_nets": ["NFC1_TBD", "NFC2_TBD"],                  # copper this route is allowed to touch
      "pads": [{"net": "GND", "x": .., "y": ..,                 # optional: proposed component
                "half_w_mm": 0.4, "half_h_mm": 0.45}]           # placement, checked like copper
    }

Moving a component moves its pads, and pads were previously checked only against
route tracks, never the other way round: a pad moved on top of an existing trace
had no offline check at all. The "pads" list closes that. Pads are rectangles in
millimetres, axis aligned, and are checked against existing traces, pads, vias and
the board edge, plus against the route's own tracks and vias.

    python3 scripts/check-proposed-route.py --route hardware/e16-nfc-coil-plan.json
    python3 scripts/check-proposed-route.py --route plan.json --snapshot hardware/e16-right-mid-snapshot.json

Exit status is 0 when nothing violates a rule. The JSON report gives the worst
gap in each category, so a comfortable pass is visible rather than assumed.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PROJECT = REPO / "projects/nfc-business-card"
DEFAULT_SNAPSHOT = PROJECT / "hardware/e16-right-mid-snapshot.json"
MIL = 39.37007874015748

# Clearances from the project's rule set (JLCPCB Capability, multiple layers).
CL_TRACK_TRACK = 0.102
CL_PAD_TRACK = 0.152
CL_PAD_PAD = 0.152
CL_VIA_TRACK = 0.152
CL_EDGE = 0.300
CL_HOLE_HOLE = 0.300
# Both E16 keep-out regions forbid pours and fills only (ruleType [2,6,7]); the
# solder-side reserve additionally forbids wires *today* ([2,6,5,7]), which the
# plan's note records as a prerequisite to relax. Entries with "no_wires": true
# are therefore reported as planning notes, not as per-sample violations.
DEFAULT_KEEPOUTS = [
    {"name": "NFC reserve", "x0": 60.0, "y0": 24.0, "x1": 82.0, "y1": 50.0, "no_wires": False},
    {"name": "U1 antenna", "x0": 59.7, "y0": 0.2, "x1": 70.3, "y1": 2.5, "no_wires": False},
]
SEGMENT_SAMPLES = 0.02  # mm between sample points along a centre line


def point_to_segment(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_to_box(px, py, box):
    cx, cy, half_w, half_h = box
    return math.hypot(max(0.0, abs(px - cx) - half_w), max(0.0, abs(py - cy) - half_h))


def pad_boxes(snapshot):
    boxes = []
    for pad in snapshot["pads"]:
        raw = pad.get("pad") or []
        width = float(raw[1]) if len(raw) > 1 and isinstance(raw[1], (int, float)) else 6.0
        height = float(raw[2]) if len(raw) > 2 and isinstance(raw[2], (int, float)) else width
        if abs(pad.get("rotation", 0)) % 180 == 90:
            width, height = height, width
        boxes.append((
            pad["x"] / MIL, pad["y"] / MIL, width / MIL / 2, height / MIL / 2,
            pad.get("net") or "", pad.get("number") or "", pad.get("layer"),
        ))
    return boxes


def track_samples(points, step=SEGMENT_SAMPLES):
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        length = math.hypot(x2 - x1, y2 - y1)
        count = max(2, int(length / step) + 1)
        for index in range(count + 1):
            t = index / count
            yield x1 + (x2 - x1) * t, y1 + (y2 - y1) * t


def check(route, snapshot):
    ignore = set(route.get("ignore_nets") or [])
    raw_keepouts = route.get("keepouts") or DEFAULT_KEEPOUTS
    keepouts = []
    for entry in raw_keepouts:
        if isinstance(entry, dict):
            keepouts.append((entry["x0"], entry["y0"], entry["x1"], entry["y1"],
                             entry.get("name", "keepout"), bool(entry.get("no_wires"))))
        else:
            keepouts.append((*entry, "keepout", True))
    boxes = [b for b in pad_boxes(snapshot) if b[4] not in ignore]
    lines = [(
        line["x1"] / MIL, line["y1"] / MIL, line["x2"] / MIL, line["y2"] / MIL,
        line["widthMil"] / MIL / 2, line.get("net") or "", line["layer"],
    ) for line in snapshot["lines"] if (line.get("net") or "") not in ignore]
    vias = [(
        via["x"] / MIL, via["y"] / MIL, via["diameterMil"] / MIL / 2,
        via["holeMil"] / MIL / 2, via.get("net") or "",
    ) for via in snapshot["vias"] if (via.get("net") or "") not in ignore]

    proposed_pads = []
    for pad in route.get("pads", []) or []:
        proposed_pads.append((
            pad["x"], pad["y"], pad["half_w_mm"], pad["half_h_mm"],
            pad.get("net") or "", pad.get("layer"),
        ))

    notes = []
    seen_keepout_notes = set()
    worst = {"track_to_track": (9e9, None), "track_to_pad": (9e9, None), "track_to_via": (9e9, None),
             "via_to_track": (9e9, None), "within_route": (9e9, None),
             "board_edge": (9e9, None), "hole_to_hole": (9e9, None),
             "pad_to_track": (9e9, None), "pad_to_pad": (9e9, None), "pad_to_via": (9e9, None)}
    violations = []

    def note(kind, gap, where, rule):
        if gap < worst[kind][0]:
            worst[kind] = (gap, where)
        if gap < rule - 1e-9:
            violations.append({"kind": kind, "gap_mm": round(gap, 4), "rule_mm": rule, "at": where})

    route_tracks = []
    for track in route.get("tracks", []):
        layer = track["layer"]
        half = track["width_mm"] / 2
        points = [(float(x), float(y)) for x, y in track["points"]]
        route_tracks.append((layer, half, points, track.get("net") or ""))
        for x, y in track_samples(points):
            note("board_edge", min(x, 84 - x, y, 52 - y) - half, (round(x, 3), round(y, 3)), CL_EDGE)
            for (x0, y0, x1, y1, name, no_wires) in keepouts:
                if x0 - half < x < x1 + half and y0 - half < y < y1 + half:
                    if no_wires:
                        violations.append({"kind": "keepout-no-wires", "gap_mm": 0.0,
                                           "rule_mm": 0.0, "at": (name, round(x, 3), round(y, 3))})
                    elif name not in seen_keepout_notes:
                        seen_keepout_notes.add(name)
                        notes.append({"kind": "keepout-pours-only", "keepout": name,
                                      "at": (round(x, 2), round(y, 2)),
                                      "detail": "wires are allowed; only fills and pours are forbidden"})
            for (ax, ay, bx, by, half_other, net, other_layer) in lines:
                if other_layer != layer:
                    continue
                # Same-net copper is meant to touch; the clearance rules only
                # constrain different nets. Without this a ground via cannot
                # legally meet a ground trace.
                if net and net == track.get("net"):
                    continue
                note("track_to_track", point_to_segment(x, y, ax, ay, bx, by) - half - half_other,
                     (round(x, 3), round(y, 3), net), CL_TRACK_TRACK)
            for (cx, cy, half_w, half_h, net, number, pad_layer) in boxes:
                if pad_layer != layer:
                    continue
                if net and net == track.get("net"):
                    continue
                note("track_to_pad", point_to_box(x, y, (cx, cy, half_w, half_h)) - half,
                     (round(x, 3), round(y, 3), f"pad {number} {net}"), CL_PAD_TRACK)
            for (vx, vy, radius, _hole, net) in vias:
                if net and net == track.get("net"):
                    continue
                note("track_to_via", max(0.0, math.hypot(x - vx, y - vy) - radius) - half,
                     (round(x, 3), round(y, 3), net), CL_VIA_TRACK)

    # spacing inside the route itself (same or different nets on one layer)
    def shares_endpoint(a, b, tol=1e-6):
        return any(abs(pa[0] - pb[0]) <= tol and abs(pa[1] - pb[1]) <= tol
                   for pa in (a[0], a[1]) for pb in (b[0], b[1]))

    for i, (layer_a, half_a, points_a, net_a) in enumerate(route_tracks):
        for layer_b, half_b, points_b, net_b in route_tracks[i:]:
            if layer_a != layer_b:
                continue
            for segment_a in zip(points_a, points_a[1:]):
                for segment_b in zip(points_b, points_b[1:]):
                    if segment_a == segment_b or shares_endpoint(segment_a, segment_b):
                        continue        # the same copper piece, or a real junction
                    for (x, y) in track_samples(list(segment_a), 0.05):
                        note("within_route",
                             point_to_segment(x, y, segment_b[0][0], segment_b[0][1], segment_b[1][0], segment_b[1][1])
                             - half_a - half_b,
                             (round(x, 3), round(y, 3), f"{net_a}/{net_b}"), CL_TRACK_TRACK)

    route_vias = [(float(v["x"]), float(v["y"]), v["diameter_mm"] / 2, v["hole_mm"] / 2,
                   v.get("net") or "") for v in route.get("vias", [])]
    for (x, y, radius, hole, net) in route_vias:
        for (vx, vy, other_radius, other_hole, other_net) in vias + route_vias:
            if (vx, vy) == (x, y):
                continue
            # Hole-to-hole is mechanical, so it applies between any two drills
            # regardless of net.
            note("hole_to_hole", math.hypot(x - vx, y - vy) - hole - other_hole,
                 (round(x, 3), round(y, 3), other_net), CL_HOLE_HOLE)
            if net and net == other_net:
                continue
            note("track_to_via", max(0.0, math.hypot(x - vx, y - vy) - other_radius) - radius,
                 (round(x, 3), round(y, 3), other_net), CL_VIA_TRACK)
        for (cx, cy, half_w, half_h, pad_net, number, pad_layer) in boxes:
            if net and net == pad_net:
                continue
            note("track_to_pad", point_to_box(x, y, (cx, cy, half_w, half_h)) - radius,
                 (round(x, 3), round(y, 3), f"pad {number} {pad_net}"), CL_PAD_TRACK)
        # A through via has to clear copper on every layer, not just its own.
        for (ax, ay, bx, by, half_other, other_net, _layer) in lines:
            if net and net == other_net:
                continue
            note("via_to_track", point_to_segment(x, y, ax, ay, bx, by) - half_other - radius,
                 (round(x, 3), round(y, 3), other_net), CL_VIA_TRACK)

    # Proposed component placements: the pads move, so every pad is checked the
    # way a route would be. Unlike route copper this is distance *to* the pad
    # rectangle, not from a centreline.
    for (px, py, phw, phh, pnet, player) in proposed_pads:
        pad_box = (px, py, phw, phh)
        for (ax, ay, bx, by, half_other, other_net, other_layer) in lines:
            if pnet and pnet == other_net:
                continue
            if player is not None and other_layer != player:
                continue
            length = math.hypot(bx - ax, by - ay)
            count = max(2, int(length / 0.05) + 1)
            for i in range(count + 1):
                s = i / count
                sx, sy = ax + (bx - ax) * s, ay + (by - ay) * s
                note("pad_to_track", point_to_box(sx, sy, pad_box) - half_other,
                     (round(px, 3), round(py, 3), other_net), CL_PAD_TRACK)
        for (cx, cy, half_w, half_h, pad_net, number, pad_layer) in boxes:
            if pnet and pnet == pad_net:
                continue
            if player is not None and pad_layer != player:
                continue
            gap = 9e9
            for i in range(41):
                s = i / 40
                ox = cx - half_w + 2 * half_w * s
                oy = cy - half_h + 2 * half_h * s
                gap = min(gap, point_to_box(ox, oy, pad_box), point_to_box(ox, cy + half_h - 2 * half_h * s, pad_box))
            note("pad_to_pad", gap, (round(px, 3), round(py, 3), f"pad {number} {pad_net}"), CL_PAD_PAD)
        for (vx, vy, radius, _hole, other_net) in vias:
            if pnet and pnet == other_net:
                continue
            note("pad_to_via", point_to_box(vx, vy, pad_box) - radius,
                 (round(px, 3), round(py, 3), other_net), CL_PAD_TRACK)
        note("board_edge", min(px - phw, 84 - px - phw, py - phh, 52 - py - phh),
             (round(px, 3), round(py, 3), "pad"), CL_EDGE)

    return {
        "route": route.get("name", "unnamed"),
        "tracks": len(route.get("tracks", [])),
        "pads": len(proposed_pads),
        "vias": len(route_vias),
        "worst_gap_mm": {kind: {"gap": round(value[0], 4), "at": value[1]} for kind, value in worst.items()},
        "notes": notes,
        "violations": violations,
        "ok": not violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()
    report = check(json.loads(args.route.read_text()), json.loads(args.snapshot.read_text()))
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
