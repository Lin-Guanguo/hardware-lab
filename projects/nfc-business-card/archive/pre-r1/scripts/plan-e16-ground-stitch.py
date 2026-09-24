#!/usr/bin/env python3
"""Plan ground-stitching vias for the E16 ESD devices.

Why here: ES-002 found that U5's ground pad has three thermal spokes into the
top pour while U6's has none, and both are >3.5 mm from the nearest ground via.
The ESD clamp's ground return is a high-dI/dt path, so TI SLVA680 wants at least
two ground vias right at the device. This places them next to the pad and ties
them with a short wide trace, which is what a refill alone would not do: the
pour's thermal setting decides whether a spoke appears, and it did not for U6.

The clearance rules and their values mirror scripts/check-proposed-route.py,
which is the authority; this planner only proposes, and the result is validated
there before anything is written to the board.

    python3 scripts/plan-e16-ground-stitch.py --json /tmp/stitch.json
    python3 scripts/check-proposed-route.py --route /tmp/stitch.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pour_geometry import load_pours  # noqa: E402

MIL_PER_MM = 39.37007874015748
MM_PER_MIL = 0.0254

# Same values as check-proposed-route.py (JLCPCB multi-layer rule set).
CL_VIA_TRACK = 0.152
CL_PAD_TRACK = 0.152
CL_EDGE = 0.300
CL_HOLE_HOLE = 0.300

VIA_DIAMETER = 0.61
VIA_HOLE = 0.305
TRACK_WIDTH = 0.30
SEARCH_RADIUS = 1.20
GRID_STEP = 0.10
TARGETS_PER_PAD = 2
# Two 0.30/0.20 vias need 0.50 mm centre-to-centre for a 0.30 mm hole gap; this
# is only a preference for spreading them, and the hole-to-hole test below is
# what makes a pair legal.
MIN_VIA_SPACING = 0.52
# A placement with less slack than this is designed to the rule limit.
MIN_VIA_MARGIN = 0.05
MIN_TIE_MARGIN = 0.05

# Preference order. The larger via stays out of JLCPCB's premium tier (0.2 mm
# hole with a pad under 0.45 mm), but U6 sits in a pocket of CC and data traces
# where only the small via fits at all; the board already carries 121 of them.
VIA_OPTIONS = [(0.61, 0.305, 0.30), (0.45, 0.25, 0.25), (0.30, 0.20, 0.25)]

# ESD devices whose ground return is being improved. U5 already has spokes; the
# vias there halve its via inductance rather than fix a missing connection.
# U5's ground pad has three spokes and can take a pour tie plus two standard
# vias. U6's own pad is walled in: USB_CC2 crosses the only gap to the pour and
# the best via position beside it had 9.5 um of slack, so nothing legal fits.
# R1's ground pad overlaps U6's and is the same electrical node, and it has room
# for two small vias, which gives U6 the low-inductance path without touching the
# NFC feed. The vias land 0.57 mm from U6's ground pad, inside ES-002's 3 mm.
TARGET_PADS = {
    "U5": (73.10, 16.60),
    "U6 via R1 ground pad": (72.65, 14.75),
}


def point_segment_distance(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def point_box_distance(px, py, cx, cy, half_w, half_h):
    return math.hypot(max(0.0, abs(px - cx) - half_w), max(0.0, abs(py - cy) - half_h))


class Board:
    def __init__(self, snapshot):
        self.lines = [{
            "x1": l["x1"] * MM_PER_MIL, "y1": l["y1"] * MM_PER_MIL,
            "x2": l["x2"] * MM_PER_MIL, "y2": l["y2"] * MM_PER_MIL,
            "half": l["widthMil"] * MM_PER_MIL / 2, "net": l.get("net") or "",
            "layer": l["layer"],
        } for l in snapshot["lines"]]
        self.pads = []
        for p in snapshot["pads"]:
            raw = p.get("pad") or []
            w = float(raw[1]) if len(raw) > 1 else 6.0
            h = float(raw[2]) if len(raw) > 2 else w
            if abs(p.get("rotation", 0)) % 180 == 90:
                w, h = h, w
            self.pads.append({
                "x": p["x"] * MM_PER_MIL, "y": p["y"] * MM_PER_MIL,
                "half_w": w * MM_PER_MIL / 2, "half_h": h * MM_PER_MIL / 2,
                "net": p.get("net") or "", "number": p.get("number"),
            })
        self.vias = [{
            "x": v["x"] * MM_PER_MIL, "y": v["y"] * MM_PER_MIL,
            "radius": v["diameterMil"] * MM_PER_MIL / 2,
            "hole": v["holeMil"] * MM_PER_MIL / 2, "net": v.get("net") or "",
        } for v in snapshot["vias"]]

    def via_violations(self, x, y, diameter=None, hole_dia=None):
        radius = (VIA_DIAMETER if diameter is None else diameter) / 2
        hole = (VIA_HOLE if hole_dia is None else hole_dia) / 2
        out = []
        if min(x, 84.0 - x, y, 52.0 - y) - radius < CL_EDGE:
            out.append(("board_edge", 0.0))
        for l in self.lines:
            if l["net"] == "GND":
                continue
            gap = point_segment_distance(x, y, l["x1"], l["y1"], l["x2"], l["y2"]) - l["half"] - radius
            if gap < CL_VIA_TRACK:
                out.append(("via_to_track", round(gap, 4)))
        for p in self.pads:
            if p["net"] == "GND":
                continue
            gap = point_box_distance(x, y, p["x"], p["y"], p["half_w"], p["half_h"]) - radius
            if gap < CL_PAD_TRACK:
                out.append(("via_to_pad", round(gap, 4)))
        for v in self.vias:
            gap = math.hypot(x - v["x"], y - v["y"]) - hole - v["hole"]
            if gap < CL_HOLE_HOLE:
                out.append(("hole_to_hole", round(gap, 4)))
        return out

    def via_margin(self, x, y, diameter, hole_dia):
        """Smallest clearance margin for a via here; negative means illegal."""
        radius, hole = diameter / 2, hole_dia / 2
        margin = min(x, 84.0 - x, y, 52.0 - y) - radius - CL_EDGE
        for l in self.lines:
            if l["net"] == "GND":
                continue
            margin = min(margin, point_segment_distance(x, y, l["x1"], l["y1"], l["x2"], l["y2"])
                         - l["half"] - radius - CL_VIA_TRACK)
        for p in self.pads:
            if p["net"] == "GND":
                continue
            margin = min(margin, point_box_distance(x, y, p["x"], p["y"], p["half_w"], p["half_h"])
                         - radius - CL_PAD_TRACK)
        for v in self.vias:
            margin = min(margin, math.hypot(x - v["x"], y - v["y"]) - hole - v["hole"] - CL_HOLE_HOLE)
        return margin

    def pour_entry_directions(self, px, py, pour, max_len=1.50, step=0.05, count=72):
        """Directions in which a straight trace from the pad first enters copper.

        Searching every direction matters: the nearest point on the pour can be
        unreachable because a trace crosses the gap (USB_CC2 does exactly that
        above U6), while a slightly longer path is clear.
        """
        entries = []
        for k in range(count):
            angle = 2 * math.pi * k / count
            ux, uy = math.cos(angle), math.sin(angle)
            r = 0.20
            while r <= max_len:
                x, y = px + ux * r, py + uy * r
                inside = False
                for region in pour.regions:
                    bx0, by0, bx1, by1 = region.bbox
                    if not (bx0 - 0.05 <= x <= bx1 + 0.05 and by0 - 0.05 <= y <= by1 + 0.05):
                        continue
                    if region.contains(x, y):
                        inside = True
                        break
                if inside:
                    entries.append((ux, uy, r))
                    break
                r += step
        return entries

    def track_margin(self, points, width, net):
        """Smallest clearance margin along a trace; negative means illegal."""
        half = width / 2
        margin = 9e9
        for i in range(len(points) - 1):
            (x1, y1), (x2, y2) = points[i], points[i + 1]
            length = math.hypot(x2 - x1, y2 - y1)
            count = max(2, int(length / 0.05) + 1)
            for k in range(count + 1):
                t_ = k / count
                x, y = x1 + (x2 - x1) * t_, y1 + (y2 - y1) * t_
                margin = min(margin, min(x, 84.0 - x, y, 52.0 - y) - half - CL_EDGE)
                for l in self.lines:
                    if l["net"] == net:
                        continue
                    margin = min(margin, point_segment_distance(x, y, l["x1"], l["y1"], l["x2"], l["y2"])
                                 - l["half"] - half - CL_VIA_TRACK)
                for p in self.pads:
                    if p["net"] == net:
                        continue
                    margin = min(margin, point_box_distance(x, y, p["x"], p["y"], p["half_w"], p["half_h"])
                                 - half - CL_PAD_TRACK)
                for v in self.vias:
                    if v["net"] == net:
                        continue
                    margin = min(margin, math.hypot(x - v["x"], y - v["y"]) - v["radius"] - half - CL_VIA_TRACK)
        return margin

    def track_violations(self, points, width, net):
        half = width / 2
        out = []
        for i in range(len(points) - 1):
            (x1, y1), (x2, y2) = points[i], points[i + 1]
            length = math.hypot(x2 - x1, y2 - y1)
            count = max(2, int(length / 0.02) + 1)
            for k in range(count + 1):
                t = k / count
                x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                if min(x, 84.0 - x, y, 52.0 - y) - half < CL_EDGE:
                    out.append(("board_edge", 0.0))
                for l in self.lines:
                    if l["net"] == net:
                        continue
                    gap = point_segment_distance(x, y, l["x1"], l["y1"], l["x2"], l["y2"]) - l["half"] - half
                    if gap < CL_VIA_TRACK:
                        out.append(("track_to_track", round(gap, 4)))
                for p in self.pads:
                    if p["net"] == net:
                        continue
                    gap = point_box_distance(x, y, p["x"], p["y"], p["half_w"], p["half_h"]) - half
                    if gap < CL_PAD_TRACK:
                        out.append(("track_to_pad", round(gap, 4)))
                for v in self.vias:
                    if v["net"] == net:
                        continue
                    gap = math.hypot(x - v["x"], y - v["y"]) - v["radius"] - half
                    if gap < CL_VIA_TRACK:
                        out.append(("track_to_via", round(gap, 4)))
        return out


def main():
    ap = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent.parent
    ap.add_argument("--snapshot", type=Path,
                    default=here / "hardware" / "e16-right-mid-snapshot.json")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    snapshot = json.loads(args.snapshot.read_text())
    board = Board(snapshot)
    # pour_geometry already returns millimetres, both for the fill unit and for
    # the pour border; do not rescale.
    pours = load_pours(snapshot)
    tracks, vias, chosen_report = [], [], []
    placed: list[tuple[float, float, float]] = []  # x, y, hole radius

    # Direct pour tie: U6's pad reaches ground only through a neighbouring
    # resistor pad and that resistor's single thermal spoke. Drawing a short wide
    # trace straight into the top pour removes the detour, and unlike a via it
    # only has to clear copper on one layer.
    top_pour = max(pours, key=lambda layer: len(pours[layer].regions)) if pours else None

    for ref, (px, py) in TARGET_PADS.items():
        if top_pour is not None:
            best_tie = None
            for ux, uy, r in board.pour_entry_directions(px, py, pours[top_pour]):
                end = (round(px + ux * (r + 0.15), 3), round(py + uy * (r + 0.15), 3))
                for width in (0.40, 0.30, 0.25):
                    margin = board.track_margin([(px, py), end], width, "GND")
                    if margin < MIN_TIE_MARGIN:
                        continue
                    score = (margin, -r)
                    if best_tie is None or score > best_tie[0]:
                        best_tie = (score, width, end, margin, r)
                    break
            if best_tie:
                _, width, end, margin, r = best_tie
                tracks.append({"net": "GND", "layer": top_pour, "width_mm": width,
                               "points": [[px, py], list(end)]})
                print(f"  {ref}: pour tie {width} mm on layer {top_pour} to "
                      f"({end[0]:.2f}, {end[1]:.2f}), copper {r:.3f} mm out, "
                      f"margin {margin:.3f} mm")
                chosen_report.append({"ref": ref, "kind": "pour_tie", "pad": [px, py],
                                      "end": list(end), "width_mm": width,
                                      "pour_mm": round(r, 3),
                                      "min_margin_mm": round(margin, 4)})
            else:
                print(f"  {ref}: no legal pour tie in any direction within 1.5 mm")

        picked = None
        for diameter, hole_dia, width in VIA_OPTIONS:
            candidates = []
            steps = int(SEARCH_RADIUS / GRID_STEP)
            for i in range(-steps, steps + 1):
                for j in range(-steps, steps + 1):
                    x = round(px + i * GRID_STEP, 3)
                    y = round(py + j * GRID_STEP, 3)
                    dist = math.hypot(x - px, y - py)
                    if dist < 0.25 + diameter / 2 or dist > SEARCH_RADIUS:
                        continue
                    # Already-placed vias are part of the board now. Omitting
                    # this let two vias 0.601 mm apart through at a 0.297 mm
                    # hole gap.
                    if any(math.hypot(x - vx, y - vy) - hole_dia / 2 - vh < CL_HOLE_HOLE
                           for vx, vy, vh in placed):
                        continue
                    via_m = board.via_margin(x, y, diameter, hole_dia)
                    # Demand real margin, not a placement designed to the rule
                    # limit: the pocket beside U6 is occupied by the NFC feed and
                    # its best position had 9.5 um of slack.
                    if via_m < MIN_VIA_MARGIN:
                        continue
                    track_m = board.track_margin([(px, py), (x, y)], width, "GND")
                    if track_m < MIN_VIA_MARGIN:
                        continue
                    candidates.append((dist, x, y, min(via_m, track_m)))

            # Closest is not best: prefer the pair with the largest clearance
            # margin among the positions still close enough to act as the ESD
            # return path, so the board is not designed to the rule limit.
            near = [c for c in candidates if c[0] <= 1.00] or candidates
            # Exhaustive pairs, not a greedy walk. Greedy by margin fails on
            # ties: it took the first of four equally good collinear positions
            # and then every other one was inside MIN_VIA_SPACING of it, so a
            # second via was never placed even though good pairs existed.
            chosen = []
            if TARGETS_PER_PAD == 2 and len(near) >= 2:
                best_pair = None
                for a in range(len(near)):
                    for b in range(a + 1, len(near)):
                        da, xa, ya, ma = near[a]
                        db, xb, yb, mb = near[b]
                        if math.hypot(xa - xb, ya - yb) < MIN_VIA_SPACING:
                            continue
                        score = (min(ma, mb), -(da + db))
                        if best_pair is None or score > best_pair[0]:
                            best_pair = (score, [near[a], near[b]])
                if best_pair:
                    chosen = best_pair[1]
            else:
                near.sort(key=lambda c: -c[3])
                for dist, x, y, m in near:
                    if any(math.hypot(x - qx, y - qy) < MIN_VIA_SPACING for _, qx, qy, _ in chosen):
                        continue
                    chosen.append((dist, x, y, m))
                    if len(chosen) == TARGETS_PER_PAD:
                        break
            if len(chosen) == TARGETS_PER_PAD:
                picked = (diameter, hole_dia, width,
                          [(d, x, y, m) for d, x, y, m in chosen], len(candidates))
                break
            print(f"  {ref}: {diameter}/{hole_dia} mm leaves {len(chosen)} of "
                  f"{len(candidates)} usable positions, trying a smaller via")

        if picked is None:
            print(f"  {ref}: NO legal placement found within {SEARCH_RADIUS} mm")
            continue

        diameter, hole_dia, width, chosen, legal = picked
        print(f"  {ref}: {len(chosen)} vias at {diameter}/{hole_dia} mm, "
              f"{width} mm tie track, from {legal} legal positions")
        for dist, x, y, margin in chosen:
            tracks.append({"net": "GND", "layer": 1, "width_mm": width,
                           "points": [[px, py], [x, y]]})
            vias.append({"net": "GND", "x": x, "y": y,
                         "diameter_mm": diameter, "hole_mm": hole_dia})
            placed.append((x, y, hole_dia / 2))
            chosen_report.append({"ref": ref, "pad": [px, py], "via": [x, y],
                                  "distance_mm": round(dist, 3),
                                  "diameter_mm": diameter, "hole_mm": hole_dia,
                                  "track_width_mm": width,
                                  "min_margin_mm": round(margin, 4)})
            print(f"      via ({x:.2f}, {y:.2f}) {diameter}/{hole_dia} mm, "
                  f"{dist:.3f} mm from the pad, clearance margin {margin:.3f} mm")

    plan = {"name": "e16-ground-stitch", "tracks": tracks, "vias": vias,
            "keepouts": [], "ignore_nets": []}
    if args.json:
        args.json.write_text(json.dumps(plan, indent=1, ensure_ascii=False))
        print(f"\nwrote {args.json}: {len(tracks)} tie tracks, {len(vias)} vias")
        print(f"plan: {json.dumps(chosen_report, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
