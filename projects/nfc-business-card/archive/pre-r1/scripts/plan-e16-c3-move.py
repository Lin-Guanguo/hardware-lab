#!/usr/bin/env python3
"""Place C3 beside U2 so both of its pads clear and both really connect.

C3 is the BQ25186 BAT pin capacitor. The E16 USB rearrangement left it 24.49 mm
from the pin it serves. The first attempt to move it back used a home-made
clearance test that modelled a rectangular pad as a circle of radius
max(half_w, half_h); on the 45-degree CHG_SDA trace that overestimated the gap by
about 6 mil and the placement went in violating clearance on both pads, which
native DRC reported once its verbose overload was found.

This planner uses check-proposed-route.check, which is calibrated against those
DRC findings, and it insists on a real connection for each pad: a tie trace to
existing same-net copper on the same layer, never the pour. A pad that merely
sits inside the pour is not proof of connection - C3's ground pad was inside the
pour and DRC still reported it unconnected, because the thermal spokes it depends
on were not generated.

    python3 scripts/plan-e16-c3-move.py
"""

from __future__ import annotations

import argparse
import json
import math
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pour_geometry import MIL  # noqa: E402


def _load_route_checker():
    """Import check-proposed-route.py, whose name is not a valid module name."""
    path = Path(__file__).resolve().parent / "check-proposed-route.py"
    spec = importlib.util.spec_from_file_location("check_proposed_route", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_rc = _load_route_checker()
check = _rc.check
point_to_box = _rc.point_to_box

MOVING_REF = "C3"

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "hardware" / "e16-right-mid-snapshot.json"
OUT = ROOT / "hardware" / "e16-c3-move-plan.json"

U2_BAT_PIN = (46.77, 18.91)
PAD_DX, PAD_DY = 0.701, 0.0
PAD_HW, PAD_HH = 31.5 * MIL / 2, 35.4 * MIL / 2
TIE_WIDTH = 5.9055
CL = 0.152
MARGIN = 0.05
MAX_TIE = 2.6
MIN_TIE = 0.05


def same_net_copper(snapshot, net, layer):
    lines = []
    for line in snapshot["lines"]:
        if (line.get("net") or "") != net or line["layer"] != layer:
            continue
        lines.append((line["x1"] * MIL, line["y1"] * MIL, line["x2"] * MIL, line["y2"] * MIL,
                      line["widthMil"] * MIL / 2))
    vias = []
    for via in snapshot["vias"]:
        # Vias are through-hole on this two-layer board, so they count on both.
        if (via.get("net") or "") != net:
            continue
        vias.append((via["x"] * MIL, via["y"] * MIL, via["diameterMil"] * MIL / 2))
    pads = []
    for pad in snapshot["pads"]:
        # Same-net copper only counts on the layer the pad is being placed on.
        if (pad.get("net") or "") != net or pad.get("layer") != layer:
            continue
        raw = pad.get("pad") or []
        hw, hh = float(raw[1]) * MIL / 2, float(raw[2]) * MIL / 2
        if abs(pad.get("rotation", 0)) % 180 == 90:
            hw, hh = hh, hw
        pads.append((pad["x"] * MIL, pad["y"] * MIL, hw, hh))
    return lines, vias, pads


def nearest_tie_target(px, py, hw, hh, lines, vias, pads):
    """Nearest point of same-net copper and its distance from a pad rectangle.

    The point matters as much as the distance: the tie trace has to be drawn, and
    an unchecked tie can cross the other net and short it.
    """
    best = (9e9, None)
    for (ax, ay, bx, by, half) in lines:
        length = math.hypot(bx - ax, by - ay)
        count = max(2, int(length / 0.05) + 1)
        for i in range(count + 1):
            s = i / count
            sx, sy = ax + (bx - ax) * s, ay + (by - ay) * s
            gap = point_to_box(sx, sy, (px, py, hw, hh)) - half
            if gap < best[0]:
                best = (gap, (round(sx, 3), round(sy, 3)))
    for (vx, vy, radius) in vias:
        gap = point_to_box(vx, vy, (px, py, hw, hh)) - radius
        if gap < best[0]:
            best = (gap, (round(vx, 3), round(vy, 3)))
    for (cx, cy, ohw, ohh) in pads:
        for i in range(41):
            s = i / 40
            for (ox, oy) in ((cx - ohw + 2 * ohw * s, cy - ohh), (cx - ohw + 2 * ohw * s, cy + ohh),
                             (cx - ohw, cy - ohh + 2 * ohh * s), (cx + ohw, cy - ohh + 2 * ohh * s)):
                gap = point_to_box(ox, oy, (px, py, hw, hh))
                if gap < best[0]:
                    best = (gap, (round(ox, 3), round(oy, 3)))
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=float, default=0.05)
    parser.add_argument("--coarse", type=float, default=0.30)
    args = parser.parse_args()
    raw = json.loads(SNAPSHOT.read_text())

    # C3 is moving, so its present pads must not appear on either side of the
    # test: as obstacles they would veto the search around C3's old place, and as
    # same-net copper they would count as a connection to a pad that is about to
    # leave. A pad id is its component id plus a suffix, so the component id is
    # enough to drop the right ones.
    moving = next((c["id"] for c in raw["components"] if c["ref"] == MOVING_REF), None)
    if moving is None:
        raise SystemExit(f"{MOVING_REF} not found in the snapshot")
    snapshot = dict(raw)
    snapshot["pads"] = [q for q in raw["pads"] if not str(q.get("id", "")).startswith(moving)]

    bat_lines, bat_vias, bat_pads = same_net_copper(snapshot, "BAT_PACK_TBD", 1)
    gnd_lines, gnd_vias, gnd_pads = same_net_copper(snapshot, "GND", 1)

    def evaluate(cx, cy, rot):
        # rot 0/180 place the pads along x; rot 90/270 along y, which is what the
        # U2 area wants: the BAT trace runs east at y = 18.90 and the ground
        # copper sits about 1.2 mm south of it.
        if rot in (0, 180):
            sign = -1 if rot == 0 else 1
            bat = (cx + PAD_DX * sign, cy)
            gnd = (cx - PAD_DX * sign, cy)
        else:
            sign = -1 if rot == 90 else 1
            bat = (cx, cy + PAD_DX * sign)
            gnd = (cx, cy - PAD_DX * sign)
        route = {
            "name": "c3 candidate",
            "tracks": [], "vias": [], "keepouts": [],
            "pads": [
                {"net": "BAT_PACK_TBD", "x": bat[0], "y": bat[1],
                 "half_w_mm": PAD_HW, "half_h_mm": PAD_HH, "layer": 1},
                {"net": "GND", "x": gnd[0], "y": gnd[1],
                 "half_w_mm": PAD_HW, "half_h_mm": PAD_HH, "layer": 1},
            ],
        }
        bat_tie, bat_target = nearest_tie_target(bat[0], bat[1], PAD_HW, PAD_HH,
                                                 bat_lines, bat_vias, bat_pads)
        gnd_tie, gnd_target = nearest_tie_target(gnd[0], gnd[1], PAD_HW, PAD_HH,
                                                 gnd_lines, gnd_vias, gnd_pads)
        # Require a real but short tie on both pads. Overlapping would land the
        # 0603 on top of the battery landing pads, which are soldered by hand.
        if not (MIN_TIE <= bat_tie <= MAX_TIE) or not (MIN_TIE <= gnd_tie <= MAX_TIE):
            return None
        if not bat_target or not gnd_target:
            return None
        # The ties go into the route so the checker sees them: a tie that crosses
        # the other net shorts it, and no length test would notice.
        route["tracks"] = [
            {"net": "BAT_PACK_TBD", "layer": 1, "width_mm": TIE_WIDTH * MIL,
             "points": [[bat[0], bat[1]], list(bat_target)]},
            {"net": "GND", "layer": 1, "width_mm": TIE_WIDTH * MIL,
             "points": [[gnd[0], gnd[1]], list(gnd_target)]},
        ]
        report = check(route, snapshot)
        if not report["ok"]:
            return None
        worst = min(v["gap"] for v in report["worst_gap_mm"].values() if v["gap"] < 9e8)
        if worst < CL + MARGIN:
            return None
        pin_d = math.hypot(bat[0] - U2_BAT_PIN[0], bat[1] - U2_BAT_PIN[1])
        dc001 = min(point_to_box(cx2, cy2, (bat[0], bat[1], PAD_HW, PAD_HH))
                    for (cx2, cy2, _hw, _hh) in bat_pads) if bat_pads else 9e9
        return {
            "centre": [round(cx, 3), round(cy, 3)], "rotation": rot,
            "bat_pad": [round(bat[0], 3), round(bat[1], 3)],
            "gnd_pad": [round(gnd[0], 3), round(gnd[1], 3)],
            "distance_to_u2_bat_pin_mm": round(pin_d, 3),
            "worst_clearance_mm": round(worst, 4),
            "bat_tie_mm": round(max(bat_tie, 0.0), 3),
            "gnd_tie_mm": round(max(gnd_tie, 0.0), 3),
            "bat_tie_to": list(bat_target),
            "gnd_tie_to": list(gnd_target),
            "dc001_mm": round(dc001, 3),
            "score": round(dc001 + 0.4 * bat_tie + 0.4 * gnd_tie + 0.2 * pin_d, 3),
        }

    # Coarse sweep, then refine around the best coarse hits: evaluating every
    # 0.05 mm over the whole region is tens of thousands of full checks.
    coarse = args.coarse
    seeds = []
    for rot in (0, 90, 180, 270):
        n = int(6.0 / coarse)
        for i in range(n + 1):
            for j in range(n + 1):
                hit = evaluate(45.0 + i * coarse, 18.5 + j * coarse, rot)
                if hit:
                    seeds.append(hit)
    seeds.sort(key=lambda c: c["score"])
    candidates = list(seeds)
    seen = {(c["centre"][0], c["centre"][1], c["rotation"]) for c in seeds}
    for seed in seeds[:6]:
        bx, by = seed["centre"]
        rot = seed["rotation"]
        n = int(coarse / args.step)
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                cx, cy = round(bx + i * args.step, 3), round(by + j * args.step, 3)
                if (cx, cy, rot) in seen:
                    continue
                seen.add((cx, cy, rot))
                hit = evaluate(cx, cy, rot)
                if hit:
                    candidates.append(hit)

    candidates.sort(key=lambda c: c["score"])
    report = {
        "board": "E16",
        "purpose": "move C3 (BQ25186 BAT pin capacitor) back beside U2",
        "pad_model": {"half_w_mm": round(PAD_HW, 4), "half_h_mm": round(PAD_HH, 4),
                      "pad_offset_mm": PAD_DX, "layer": 1},
        "constraints": {"clearance_mm": CL, "margin_mm": MARGIN,
                        "tie_range_mm": [MIN_TIE, MAX_TIE],
                        "connection": "a tie trace to same-net copper on layer 1, never the pour"},
        "candidates": candidates[:20],
        "candidate_count": len(candidates),
        "coarse_step_mm": args.coarse,
        "fine_step_mm": args.step,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"{len(candidates)} legal placements; wrote {OUT.relative_to(ROOT)}")
    for c in candidates[:8]:
        print(f"  centre {c['centre']} rot {c['rotation']:3}  pin {c['distance_to_u2_bat_pin_mm']:5.2f} mm"
              f"  clearance {c['worst_clearance_mm']:.4f}  ties {c['bat_tie_mm']:.3f}/{c['gnd_tie_mm']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
