#!/usr/bin/env python3
"""Check the USB4110 candidate's straight board edge and locating drills."""

import argparse
import json
import math
import re
import zipfile
from pathlib import Path


def native_vertices(polygon):
    values = polygon["polygon"]
    vertices = [(values[0] * 0.0254, values[1] * 0.0254)]
    index = 2
    while index < len(values):
        if values[index] == "L":
            index += 1
        elif values[index] == "ARC":
            index += 2
        vertices.append((values[index] * 0.0254, values[index + 1] * 0.0254))
        index += 2
    return vertices


def drill_hits(data):
    tools = {match[1]: float(match[2]) for match in re.finditer(r"(T\d+)C([\d.]+)", data)}
    active = None
    hits = []
    for line in data.splitlines():
        if re.fullmatch(r"T\d+", line):
            active = line
        match = re.fullmatch(r"X([\d.]+)Y([\d.]+)", line)
        if match:
            hits.append((float(match[1]), float(match[2]), tools[active]))
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--gerber", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    outlines = [item for item in snapshot["polylines"] if item["layer"] == 11]
    assert len(outlines) == 1
    vertices = native_vertices(outlines[0]["polygon"])
    assert math.dist(vertices[0], vertices[-1]) < 0.002
    right_x = max(vertex[0] for vertex in vertices)
    assert sum(abs(x - right_x) < 0.002 for x, _ in vertices) >= 3

    with zipfile.ZipFile(args.gerber) as archive:
        assert archive.testzip() is None
        outline = archive.read("Gerber_BoardOutlineLayer.GKO").decode()
        fmt = re.search(r"%FSLAX(\d)(\d)Y(\d)(\d)\*%", outline)
        assert fmt and "%MOMM*%" in outline
        scale = 10 ** int(fmt[2])
        paths = []
        radii = []
        previous = None
        for line in outline.splitlines():
            match = re.search(r"G0([123])X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([12])\*", line)
            if not match:
                continue
            mode, x, y, dx, dy, draw = match.groups()
            point = (int(x) / scale, int(y) / scale)
            if draw == "2":
                paths.append([point])
            else:
                paths[-1].append(point)
                if mode in ("2", "3"):
                    radius = math.hypot(int(dx), int(dy)) / scale
                    center = (previous[0] + int(dx) / scale, previous[1] + int(dy) / scale)
                    assert abs(math.dist(center, point) - radius) < 0.002
                    radii.append(radius)
            previous = point
        assert len(paths) == 1 and math.dist(paths[0][0], paths[0][-1]) < 0.002
        assert len(paths[0]) == len(vertices)
        assert all(any(math.dist(a, b) < 0.002 for b in paths[0]) for a in vertices)
        assert len(radii) == 6

        pth = archive.read("Drill_PTH_Through.DRL").decode()
        npth = drill_hits(archive.read("Drill_NPTH_Through.DRL").decode())
        assert "G85" not in pth
        assert len(npth) == 2 and all(abs(hit[2] - 0.65) < 0.002 for hit in npth)
        expected = [(77.22423, 23.109987), (77.22423, 28.890011)]
        assert all(any(math.dist(hit[:2], target) < 0.002 for hit in npth) for target in expected)

    report = {
        "ok": True,
        "board_outline_contours": len(paths),
        "right_edge_x_mm": round(right_x, 4),
        "outline_arcs": len(radii),
        "usb_plated_slots": 0,
        "usb_npth_locating_holes": [list(hit) for hit in npth],
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
