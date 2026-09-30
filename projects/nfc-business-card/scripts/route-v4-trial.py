#!/usr/bin/env python3
"""Plan only named V4 trial paths; layers and transitions are explicit inputs."""
import argparse
import heapq
import json
import math
from pathlib import Path

import numpy as np
from shapely import contains_xy
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union

from v4_geometry import geometry


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('spec', type=Path)
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[3]
    spec = json.loads(a.spec.read_text())
    _, pads, objects, _ = geometry(root / spec['board'])
    result = {k: spec[k] for k in ('board', 'description', 'record')}
    result.update(routes=[], vias=[])
    failures = []
    for hole in spec.get('vias', []):
        g = Point(hole['at']).buffer(.3)
        collisions = [o['name'] for o in objects if o['net'] != hole['net'] and o['shape'].distance(g) < .2 - 1e-6]
        # The diagnostic keeps at least 0.4 mm from any SMT copper to a drill edge.
        smt_gap = [o['name'] for o in objects if o['kind'] == 'pad' and len(o['layers']) == 1 and o['shape'].distance(Point(hole['at'])) < .55 - 1e-6]
        if collisions or smt_gap:
            failures.append({'via': hole, 'copper': collisions, 'smt_drill_gap': smt_gap})
            continue
        result['vias'].append(hole)
        objects.append({'name': 'trial via', 'net': hole['net'], 'layers': ['F.Cu', 'B.Cu'], 'shape': g, 'kind': 'via'})
    for request in spec['paths']:
        net, layer, width = request['net'], request['layer'], request['width']
        points = []
        for p in request['through']:
            if isinstance(p, str):
                assert pads[p]['net'] == net, (p, pads[p]['net'], net)
                assert layer in pads[p]['layers']
                points.append(pads[p]['at'])
            else:
                points.append(tuple(p))
        bounds = request.get('bounds', [min(p[0] for p in points) - 3, min(p[1] for p in points) - 3, max(p[0] for p in points) + 3, max(p[1] for p in points) + 3])
        region = box(*bounds)
        obstacles = unary_union([o['shape'].buffer(.205 + width / 2, quad_segs=8) for o in objects if o['net'] != net and layer in o['layers'] and o['shape'].intersects(region.buffer(1))])
        def free(p, q):
            return not LineString([p, q]).intersects(obstacles)
        path = [points[0]]
        failed = None
        for start, end in zip(points, points[1:]):
            if free(start, end):
                path.append(end)
                continue
            if obstacles.intersects(Point(start)) or obstacles.intersects(Point(end)):
                failed = {'reason': 'Endpoint blocked', 'start': start, 'end': end}
                break
            step = .1
            x0, y0, x1, y1 = bounds
            nx, ny = math.ceil((x1 - x0) / step) + 1, math.ceil((y1 - y0) / step) + 1
            xx, yy = np.meshgrid(x0 + np.arange(nx) * step, y0 + np.arange(ny) * step)
            blocked = contains_xy(obstacles, xx, yy)
            def coord(p):
                return (x0 + p[0] * step, y0 + p[1] * step)
            def nearby(p):
                cx, cy = round((p[0] - x0) / step), round((p[1] - y0) / step)
                return [(i, j) for i in range(cx - 2, cx + 3) for j in range(cy - 2, cy + 3) if 0 <= i < nx and 0 <= j < ny and not blocked[j, i] and free(p, coord((i, j)))]
            starts, ends = nearby(start), set(nearby(end))
            costs = {p: math.dist(start, coord(p)) for p in starts}
            parents = {p: None for p in starts}
            queue = [(g + math.dist(coord(p), end), p) for p, g in costs.items()]
            heapq.heapify(queue)
            visited = set()
            winner = None
            while queue:
                _, p = heapq.heappop(queue)
                if p in visited:
                    continue
                visited.add(p)
                if p in ends:
                    winner = p
                    break
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    q = p[0] + dx, p[1] + dy
                    if not (0 <= q[0] < nx and 0 <= q[1] < ny) or blocked[q[1], q[0]] or q in visited:
                        continue
                    if not free(coord(p), coord(q)):
                        continue
                    cost = costs[p] + step * math.hypot(dx, dy)
                    if cost < costs.get(q, float('inf')):
                        costs[q], parents[q] = cost, p
                        heapq.heappush(queue, (cost + math.dist(coord(q), end), q))
            if winner is None:
                failed = {'reason': 'No path in assigned corridor', 'start': start, 'end': end}
                break
            section = [end]
            while winner is not None:
                section.append(coord(winner))
                winner = parents[winner]
            section = [start] + section[::-1]
            i = 0
            while i < len(section) - 1:
                j = len(section) - 1
                while j > i + 1 and not free(section[i], section[j]):
                    j -= 1
                path.append(section[j])
                i = j
        if failed:
            failures.append({'path': request['name'], **failed})
            continue
        route = {'name': request['name'], 'net': net, 'layer': layer, 'width': width, 'points': [[round(x, 6), round(y, 6)] for x, y in path], 'length_mm': round(LineString(path).length, 3)}
        result['routes'].append(route)
        objects.append({'name': request['name'], 'net': net, 'layers': [layer], 'shape': LineString(path).buffer(width / 2), 'kind': 'track'})
    result['failures'] = failures
    output = a.spec.with_name(a.spec.stem + '-plan.json')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'routes': len(result['routes']), 'vias': len(result['vias']), 'failures': failures}, indent=2))


if __name__ == '__main__':
    main()
