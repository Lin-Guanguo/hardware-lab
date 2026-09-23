#!/usr/bin/env python3
"""Copper-pour geometry shared by the E16 checkers.

Two properties of the exported pour data were measured on the live client, not
assumed, and the first attempt at both was wrong:

* Pour fill coordinates use a different unit from every other object in the
  snapshot. One fill unit is 0.254 mm; traces, pads, vias, outlines and the pour
  border are in mil. `calibrate` below re-checks that against the pour border so
  a future export change cannot silently mismeasure.
* `poured[].fills` is a mixed list. A ring with three or more distinct vertices
  is a copper polygon: the first ring is the region outline and later rings are
  holes. A two-point ring is a degenerate segment, which is what a thermal-relief
  spoke looks like, and it is what actually ties a ground pad to the pour.

Both mistakes produced confident, wrong numbers before the board outline was
used as a calibration reference. Keep the reference.
"""

from __future__ import annotations

import math

MIL = 0.0254
FILL_UNIT = 0.254
CALIB_TOLERANCE = 1.0


def sample_arc(p0, p1, sweep_deg, max_step_deg=6.0):
    """Sample an arc stored as (sweep, endX, endY); positive sweep is CCW."""
    x0, y0 = p0
    x1, y1 = p1
    chord = math.hypot(x1 - x0, y1 - y0)
    sweep = math.radians(sweep_deg)
    if chord == 0 or abs(sweep_deg) < 1e-9:
        return [p1]
    if abs(abs(sweep_deg) - 180.0) < 1e-9:
        radius = chord / 2
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    else:
        radius = chord / (2 * math.sin(abs(sweep) / 2))
        h = radius * math.cos(sweep / 2)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ux, uy = (x1 - x0) / chord, (y1 - y0) / chord
        nx, ny = -uy, ux
        sign = 1.0 if sweep > 0 else -1.0
        cx, cy = mx - sign * h * nx, my - sign * h * ny
    a0 = math.atan2(y0 - cy, x0 - cx)
    steps = max(2, int(abs(math.degrees(sweep)) / max_step_deg) + 1)
    return [(cx + radius * math.cos(a0 + sweep * i / steps),
             cy + radius * math.sin(a0 + sweep * i / steps))
            for i in range(1, steps + 1)]


def parse_path(arr, scale):
    """EasyEDA polygon source array -> vertices in mm.

    'L' consumes two numbers, 'ARC' consumes three (sweep, x, y), and a command
    repeats until the next letter appears.
    """
    if not arr or len(arr) < 2:
        return []
    pts = [(float(arr[0]) * scale, float(arr[1]) * scale)]
    i, cmd, cur = 2, None, pts[0]
    while i < len(arr):
        tok = arr[i]
        if isinstance(tok, str):
            cmd, i = tok, i + 1
            continue
        if cmd == "L" and i + 1 < len(arr):
            cur = (float(arr[i]) * scale, float(arr[i + 1]) * scale)
            pts.append(cur)
            i += 2
        elif cmd == "ARC" and i + 2 < len(arr):
            sweep = float(arr[i])
            end = (float(arr[i + 1]) * scale, float(arr[i + 2]) * scale)
            pts.extend(sample_arc(cur, end, sweep))
            cur = end
            i += 3
        else:
            i += 1
    uniq = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - uniq[-1][0]) > 1e-6 or abs(p[1] - uniq[-1][1]) > 1e-6:
            uniq.append(p)
    return uniq


def ring_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def point_in_ring(px, py, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if (y0 > py) != (y1 > py):
            if px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
                inside = not inside
    return inside


def point_segment_distance(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    if dx == 0 and dy == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def distance_to_ring(px, py, pts):
    if len(pts) < 2:
        return float("inf")
    return min(point_segment_distance(px, py, *pts[i], *pts[(i + 1) % len(pts)])
               for i in range(len(pts)))


class Region:
    """One copper polygon; rings after the first are holes."""

    def __init__(self, rings):
        self.outer = rings[0]
        self.holes = rings[1:]
        self.area = max(0.0, ring_area(self.outer) - sum(ring_area(h) for h in self.holes))
        xs = [p[0] for p in self.outer]
        ys = [p[1] for p in self.outer]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))

    def contains(self, px, py):
        if not point_in_ring(px, py, self.outer):
            return False
        return not any(point_in_ring(px, py, h) for h in self.holes)

    def distance(self, px, py):
        return 0.0 if self.contains(px, py) else distance_to_ring(px, py, self.outer)


class Spoke:
    """A degenerate two-point path: a thermal-relief spoke from a pad."""

    def __init__(self, pts):
        self.start, self.end = pts[0], pts[1]

    @property
    def length(self):
        return math.dist(self.start, self.end)

    def distance_to(self, px, py):
        return point_segment_distance(px, py, *self.start, *self.end)


class LayerPour:
    def __init__(self, name, net, regions, spokes, border_bbox):
        self.name = name
        self.net = net
        self.regions = regions
        self.spokes = spokes
        self.border_bbox = border_bbox

    @property
    def area(self):
        return sum(r.area for r in self.regions)

    def contains(self, px, py):
        return any(r.contains(px, py) for r in self.regions)

    def nearest_region_distance(self, px, py):
        return min((r.distance(px, py) for r in self.regions), default=float("inf"))

    def nearest_spoke_distance(self, px, py):
        return min((s.distance_to(px, py) for s in self.spokes), default=float("inf"))


def load_pours(snapshot):
    """layer -> LayerPour, for every poured object in the snapshot."""
    borders = {p.get("layer"): p for p in snapshot.get("pours", [])}
    out = {}
    for poured in snapshot.get("poured", []):
        layer = poured.get("layer")
        regions, spokes = [], []
        for fill in poured.get("fills", []):
            rings = []
            for ring in fill.get("path") or []:
                pts = parse_path(ring, FILL_UNIT)
                if len(pts) >= 3:
                    rings.append(pts)
                elif len(pts) == 2:
                    spokes.append(Spoke(pts))
            if rings:
                regions.append(Region(rings))
        border = borders.get(layer)
        border_bbox = None
        if border and border.get("complexPolygon"):
            pts = parse_path(border["complexPolygon"], MIL)
            if pts:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                border_bbox = (min(xs), min(ys), max(xs), max(ys))
        out[layer] = LayerPour(poured.get("pourName"), poured.get("net"),
                               regions, spokes, border_bbox)
    return out


def calibrate(pours):
    """Confirm the fill unit and parser against the pour border.

    Returns (ok, details). A failure means the fill unit or the path grammar
    changed, and every pour-derived number must be treated as invalid.
    """
    details = {}
    ok = True
    for layer, pour in sorted(pours.items()):
        if not pour.regions or not pour.border_bbox:
            continue
        xs0 = min(r.bbox[0] for r in pour.regions)
        ys0 = min(r.bbox[1] for r in pour.regions)
        xs1 = max(r.bbox[2] for r in pour.regions)
        ys1 = max(r.bbox[3] for r in pour.regions)
        bx0, by0, bx1, by1 = pour.border_bbox
        inset = max(bx0 - xs0, by0 - ys0, xs1 - bx1, ys1 - by1)
        good = -CALIB_TOLERANCE <= inset <= CALIB_TOLERANCE
        ok = ok and good
        details[layer] = {"inset_mm": round(inset, 3), "ok": good}
    return ok, details
