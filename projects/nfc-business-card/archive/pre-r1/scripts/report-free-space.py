#!/usr/bin/env python3
"""Report free copper space in a region of the exported E16 snapshot.

Placement questions (where can a battery pad go, which corridor can an NFC feed
use) need the real occupancy of tracks, vias and pads per layer. This tool
rasters the snapshot on a grid, prints an ASCII map and lists the largest free
rectangles with the design-rule margin applied.

    python3 scripts/report-free-space.py --region 54,2,72,26 --layer 2
    python3 scripts/report-free-space.py --region 33,0,46,19 --margin 0.3

It is read-only: the snapshot comes from eda-export-e16-snapshot.js.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
DEFAULT_SNAPSHOT = REPO / "projects/nfc-business-card/hardware/e16-right-mid-snapshot.json"
MIL = 39.37007874015748


def parse_region(text: str) -> tuple[float, float, float, float]:
    values = [float(v) for v in text.split(",")]
    if len(values) != 4:
        raise argparse.ArgumentTypeError("region must be x0,y0,x1,y1")
    return values[0], values[1], values[2], values[3]


def build_grid(data: dict, region: tuple[float, float, float, float], layer: int, step: float) -> np.ndarray:
    x0, y0, x1, y1 = region
    nx = int((x1 - x0) / step) + 1
    ny = int((y1 - y0) / step) + 1
    grid = np.zeros((ny, nx), dtype=bool)

    def to_cells(x: float, y: float) -> tuple[int, int]:
        return int(round((x - x0) / step)), int(round((y - y0) / step))

    def mark(ax: float, ay: float, bx: float, by: float) -> None:
        cx0, cy0 = to_cells(min(ax, bx), min(ay, by))
        cx1, cy1 = to_cells(max(ax, bx), max(ay, by))
        cx0, cy0 = max(0, cx0), max(0, cy0)
        cx1, cy1 = min(nx - 1, cx1), min(ny - 1, cy1)
        if cx1 >= cx0 and cy1 >= cy0:
            grid[cy0:cy1 + 1, cx0:cx1 + 1] = True

    def mm(value: float) -> float:
        return value / MIL

    for line in data["lines"]:
        if line["layer"] != layer:
            continue
        half = max(mm(line["widthMil"]), 1e-3) / 2
        mark(mm(line["x1"]) - half, mm(line["y1"]) - half, mm(line["x2"]) + half, mm(line["y2"]) + half)

    for via in data["vias"]:
        radius = mm(via["diameterMil"]) / 2
        mark(mm(via["x"]) - radius, mm(via["y"]) - radius, mm(via["x"]) + radius, mm(via["y"]) + radius)

    for pad in data["pads"]:
        if pad["layer"] not in (layer, 12):
            continue
        px, py = mm(pad["x"]), mm(pad["y"])
        if not (x0 - 2 < px < x1 + 2 and y0 - 2 < py < y1 + 2):
            continue
        shape = pad.get("pad") or []
        half_w = mm(shape[1]) / 2 if len(shape) > 2 else 0.6
        half_h = mm(shape[2]) / 2 if len(shape) > 2 else 0.6
        mark(px - half_w, py - half_h, px + half_w, py + half_h)

    return grid


def print_map(grid: np.ndarray, region: tuple[float, float, float, float], step: float) -> None:
    x0, y0, x1, y1 = region
    block = max(1, int(round(0.5 / step)))
    columns = grid.shape[1] // block
    print("      " + "".join(f"{x0 + i * block * step:5.0f}" for i in range(columns)))
    for j in range(grid.shape[0] - 1, -1, -block):
        row = "".join("#" if grid[j, i:i + block].any() else "." for i in range(0, columns * block, block))
        print(f"{y0 + j * step:5.1f} {row}")


def largest_free(grid: np.ndarray, region: tuple[float, float, float, float], step: float, margin: float, limit: int) -> list[dict]:
    x0, y0, _, _ = region
    margin_cells = int(round(margin / step))
    free = ~grid
    found: list[tuple[float, list[float]]] = []
    for j in range(grid.shape[0]):
        for i in range(grid.shape[1]):
            if not free[j, i]:
                continue
            width = 0
            while i + width < grid.shape[1] and free[j, i + width]:
                width += 1
            height = 0
            while j + height < grid.shape[0] and free[j + height, i:i + width].all():
                height += 1
            inner_w = width - 2 * margin_cells
            inner_h = height - 2 * margin_cells
            if inner_w <= 0 or inner_h <= 0:
                continue
            area = inner_w * inner_h * step * step
            box = [round(x0 + (i + margin_cells) * step, 2), round(y0 + (j + margin_cells) * step, 2),
                   round(x0 + (i + width - margin_cells) * step, 2), round(y0 + (j + height - margin_cells) * step, 2)]
            found.append((area, box))
    found.sort(reverse=True, key=lambda item: item[0])
    picked: list[dict] = []
    for area, box in found:
        if any(not (box[2] <= other[0] or box[0] >= other[2] or box[3] <= other[1] or box[1] >= other[3]) for _, other in picked):
            continue
        picked.append((area, box))
        if len(picked) >= limit:
            break
    return [{"area_mm2": round(area, 2), "box_mm": box} for area, box in picked]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--region", type=parse_region, required=True, help="x0,y0,x1,y1 in mm")
    parser.add_argument("--layer", type=int, choices=[1, 2], help="1 = top, 2 = bottom; omit for both")
    parser.add_argument("--step", type=float, default=0.1, help="grid step in mm")
    parser.add_argument("--margin", type=float, default=0.25, help="design-rule margin in mm")
    parser.add_argument("--limit", type=int, default=3, help="free rectangles to report per layer")
    args = parser.parse_args()

    data = json.loads(args.snapshot.read_text())
    layers = [args.layer] if args.layer else [1, 2]
    for layer in layers:
        grid = build_grid(data, args.region, layer, args.step)
        print(f"--- layer {layer} ({'top' if layer == 1 else 'bottom'}) region {args.region} ---")
        print_map(grid, args.region, args.step)
        for entry in largest_free(grid, args.region, args.step, args.margin, args.limit):
            print(f"  free {entry['area_mm2']:7.2f} mm2  {entry['box_mm']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
