#!/usr/bin/env python3
"""Check continuous two-layer access while retaining explicitly present copper."""
import argparse
import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path

from shapely.geometry import Point, LineString
from shapely.ops import unary_union, nearest_points
from v4_geometry import geometry

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('board', type=Path)
ap.add_argument('output', type=Path)
a = ap.parse_args()
b, pads, objects, _ = geometry(a.board)
spec = importlib.util.spec_from_file_location('router', Path(__file__).with_name('route-v4-octilinear.py'))
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)
boundary = router.outline(b)
layers = ['F.Cu', 'B.Cu']
results = []
for source, target in [('U2.6', 'R19.1'), ('J1.A5', 'U6.1'), ('J1.B5', 'U6.2'),
                       ('U1.24', 'J2.9'), ('J2.12', 'U1.38'), ('R4.1', 'U5.2')]:
    net = pads[source]['net']
    assert net == pads[target]['net']
    obstacles = [o for o in objects if o['net'] != net]
    free = {l: boundary.buffer(-.375).difference(unary_union([
        o['shape'].buffer(.275, quad_segs=32) for o in obstacles if l in o['layers']])) for l in layers}
    nodes = {(l, i): g for l in layers for i, g in enumerate(getattr(free[l], 'geoms', [free[l]]))}
    via_free = boundary.buffer(-.6).difference(unary_union([
        *[o['shape'].buffer(.5, quad_segs=32) for o in obstacles],
        *[o['shape'].buffer(.55, quad_segs=32) for o in objects if o['kind'] == 'pad' and len(o['layers']) == 1]]))
    edges = {k: {} for k in nodes}
    # Each continuous legal via-center region belongs to one free component on each face.
    for g in getattr(via_free, 'geoms', [via_free]):
        if g.is_empty:
            continue
        interior = g.buffer(-.02)
        p = nearest_points(interior if not interior.is_empty else g,
                           LineString([pads[source]['at'], pads[target]['at']]))[0]
        hits = [k for k, shape in nodes.items() if shape.covers(p)]
        for n in hits:
            for m in hits:
                if n != m:
                    cost = p.distance(Point(pads[source]['at'])) + p.distance(Point(pads[target]['at']))
                    old = edges[n].get(m)
                    if old is None or cost < old['endpoint_distance_sum_mm']:
                        edges[n][m] = {'new_via_witness_mm': list(p.coords[0]), 'endpoint_distance_sum_mm': cost}
    for o in objects:
        if o['net'] != net or len(o['layers']) != 2 or o['kind'] not in ['pad', 'via']:
            continue
        p = Point(o['at'])
        hits = [k for k, shape in nodes.items() if shape.covers(p)]
        for n in hits:
            for m in hits:
                if n != m:
                    edges[n][m] = {'existing_transition': o['name'], 'at_mm': list(p.coords[0])}
    starts = [k for k, shape in nodes.items() if k[0] == 'F.Cu' and shape.covers(Point(pads[source]['at']))]
    goals = [k for k, shape in nodes.items() if k[0] == 'F.Cu' and shape.covers(Point(pads[target]['at']))]
    queue = deque(starts)
    previous = {k: None for k in starts}
    while queue:
        n = queue.popleft()
        for m in edges[n]:
            if m not in previous:
                previous[m] = n
                queue.append(m)
    reached = next((g for g in goals if g in previous), None)
    sequence = []
    while reached is not None and previous[reached] is not None:
        old = previous[reached]
        sequence.append(edges[old][reached])
        reached = old
    start_copper = unary_union([nodes[k] for k in starts])
    barriers = [dict(id=o['name'], net=o['net'], kind=o['kind']) for o in obstacles
                if 'F.Cu' in o['layers'] and o['shape'].buffer(.275, quad_segs=32).distance(start_copper) < 1e-5]
    results.append(dict(source=source, target=target, net=net,
                        source_free_area_mm2=start_copper.area,
                        source_free_bounds_mm=start_copper.bounds,
                        source_new_via_area_mm2=start_copper.intersection(via_free).area,
                        target_reachable_with_current_other_copper=any(g in previous for g in goals),
                        layer_transitions=list(reversed(sequence)), source_boundary_objects=barriers))
report = dict(board=str(a.board), sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),
              scope='Continuous buffered geometry on both layers; no grid or assigned route corridor. Existing unrelated copper remains. A positive result does not provide an octilinear route, prove return quality, or close DRC. A negative result concerns this copper arrangement, not board area or immutable placement.',
              trace_mm=.15, clearance_mm=.2, via_mm=[.6, .3], smd_drill_clearance_mm=.4, results=results)
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(report, indent=2) + '\n')
for r in results:
    print(r['source'], r['target'], r['target_reachable_with_current_other_copper'],
          'via area', round(r['source_new_via_area_mm2'], 6), 'barriers', len(r['source_boundary_objects']))
