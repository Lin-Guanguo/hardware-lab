#!/usr/bin/env python3
"""Ground-pour analysis for E16: fragmentation, coverage, and pad locality.

DRC accepts a board whose ground pours are split into unusable slivers, and the
snapshot could not even show the pour until the exporter was fixed. This answers
the rule-index questions that were blocked on pour geometry: GP-003 (fragmented
plane), GP-004 (fill ratio), BE-002 (pour ring), and the locality question that
decides ES-002 — which ground pads actually reach copper.

Geometry comes from pour_geometry, which carries the measured fill unit and the
calibration that guards it.

Usage:
    python3 scripts/analyze-e16-pour.py [--snapshot PATH] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pour_geometry import MIL, calibrate, load_pours, parse_path

BOARD_W, BOARD_H = 84.0, 52.0

# Probe points in mm, taken from the committed snapshot's pad centres.
PROBES = [
    ("U5 GND pad", 73.10, 16.60), ("U6 GND pad", 73.10, 14.90),
    ("R1 GND pad", 72.65, 14.75), ("R2 GND pad", 72.65, 17.75),
    ("J1 GND A1B12", 75.95, 12.80), ("J1 GND B1A12", 75.95, 19.20),
    ("J1 anchor 17", 77.10, 10.38), ("J1 anchor 18", 77.10, 21.62),
    ("USB DP via", 75.05, 16.75),
]


def main():
    ap = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent.parent
    ap.add_argument("--snapshot", type=Path,
                    default=here / "hardware" / "e16-right-mid-snapshot.json")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    snapshot = json.loads(args.snapshot.read_text())
    board_area = BOARD_W * BOARD_H
    pours = load_pours(snapshot)
    report = {"snapshot": str(args.snapshot), "calibration": {}, "layers": {},
              "probes": [], "findings": []}

    print(f"snapshot: {args.snapshot}")
    print(f"  board {BOARD_W} x {BOARD_H} mm = {board_area:.1f} mm^2\n")

    ok, details = calibrate(pours)
    report["calibration"] = details
    print("--- calibration: filled copper must sit just inside the pour border ---")
    for layer, pour in sorted(pours.items()):
        if layer not in details:
            continue
        xs0 = min(r.bbox[0] for r in pour.regions)
        ys0 = min(r.bbox[1] for r in pour.regions)
        xs1 = max(r.bbox[2] for r in pour.regions)
        ys1 = max(r.bbox[3] for r in pour.regions)
        print(f"  layer {layer} {pour.name:9} fill x {xs0:6.2f}..{xs1:6.2f} "
              f"y {ys0:6.2f}..{ys1:6.2f}  |  border x {pour.border_bbox[0]:6.2f}.."
              f"{pour.border_bbox[2]:6.2f} y {pour.border_bbox[1]:6.2f}.."
              f"{pour.border_bbox[3]:6.2f}  |  worst inset "
              f"{details[layer]['inset_mm']:+.2f} mm  "
              f"{'OK' if details[layer]['ok'] else 'SUSPECT'}")
    if not ok:
        print("\n  CALIBRATION FAILED: the fill unit or path grammar changed, so every")
        print("  pour-derived number is invalid. No findings are reported.")
        if args.json:
            args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        return 2
    print()

    print("--- GP-003 (regions) / GP-004 (fill ratio) / BE-002 (ring) ---")
    for layer, pour in sorted(pours.items()):
        entry = {
            "name": pour.name, "net": pour.net,
            "copper_regions": len(pour.regions),
            "thermal_spokes": len(pour.spokes),
            "area_mm2": pour.area,
            "fill_ratio_pct": 100 * pour.area / board_area,
            "largest_region_mm2": max((r.area for r in pour.regions), default=0.0),
            "regions_under_1mm2": sum(1 for r in pour.regions if r.area < 1.0),
        }
        report["layers"][layer] = entry
        report["findings"].append({
            "rule": "GP-003",
            "threshold": "more than 3 disconnected ground regions",
            "measured": f"layer {layer} {entry['name']}: {entry['copper_regions']} copper regions",
            "status": "fail" if entry["copper_regions"] > 3 else "pass",
            "source": "kicad-happy GP-003",
        })
        report["findings"].append({
            "rule": "GP-004",
            "threshold": "ground fill ratio < 60%",
            "measured": f"layer {layer} {entry['name']}: {entry['fill_ratio_pct']:.1f}%",
            "status": "fail" if entry["fill_ratio_pct"] < 60 else "pass",
            "source": "kicad-happy GP-004",
        })
        print(f"  layer {layer} {entry['name']}: {entry['copper_regions']} copper regions, "
              f"{entry['thermal_spokes']} thermal spokes, copper {pour.area:.1f} mm^2 = "
              f"{entry['fill_ratio_pct']:.1f}% of board; largest "
              f"{entry['largest_region_mm2']:.1f} mm^2; "
              f"{entry['regions_under_1mm2']} under 1 mm^2")
    print()

    # BE-002: is the board perimeter ringed by ground copper?
    print("--- BE-002: ground copper within 2 mm of the board perimeter ---")
    for layer, pour in sorted(pours.items()):
        if not pour.regions:
            continue
        xs0 = min(r.bbox[0] for r in pour.regions)
        ys0 = min(r.bbox[1] for r in pour.regions)
        xs1 = max(r.bbox[2] for r in pour.regions)
        ys1 = max(r.bbox[3] for r in pour.regions)
        gaps = {"west": xs0, "south": ys0,
                "east": BOARD_W - xs1, "north": BOARD_H - ys1}
        worst = max(gaps.items(), key=lambda kv: kv[1])
        report["layers"][layer]["perimeter_gaps_mm"] = {k: round(v, 2) for k, v in gaps.items()}
        print(f"  layer {layer} {pour.name}: copper inset from west/south/east/north = "
              f"{gaps['west']:.2f}/{gaps['south']:.2f}/{gaps['east']:.2f}/{gaps['north']:.2f} mm "
              f"(worst {worst[0]} {worst[1]:.2f} mm)")
        report["findings"].append({
            "rule": "BE-002",
            "threshold": "less than 90% of the board perimeter has ground copper within 2 mm",
            "measured": f"layer {layer} {pour.name}: worst perimeter inset {worst[1]:.2f} mm",
            "status": "fail" if worst[1] > 2.0 else "pass",
            "source": "kicad-happy BE-002",
        })
    print()

    print("--- ES-002 locality: how each ground pad reaches copper ---")
    top = min(pours) if pours else None
    for name, px, py in PROBES:
        inside = sorted(l for l, p in pours.items() if p.contains(px, py))
        row = {"probe": name, "x": px, "y": py, "inside_layers": inside}
        for layer, pour in sorted(pours.items()):
            row[f"region_mm_L{layer}"] = round(pour.nearest_region_distance(px, py), 3)
            row[f"spoke_mm_L{layer}"] = round(pour.nearest_spoke_distance(px, py), 3)
        report["probes"].append(row)
        if inside:
            print(f"  {name:16} ({px:6.2f},{py:6.2f})  inside copper, layer(s) {inside}")
        else:
            detail = ", ".join(
                f"L{l}: region {row[f'region_mm_L{l}']} mm / spoke {row[f'spoke_mm_L{l}']} mm"
                for l in sorted(pours))
            print(f"  {name:16} ({px:6.2f},{py:6.2f})  NOT inside; {detail}")
    print()

    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
