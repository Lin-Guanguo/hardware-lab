#!/usr/bin/env python3
"""Audit actual two-layer copper connectivity and the R1 screen exclusion."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from shapely import affinity, make_valid
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from pour_geometry import parse_path, load_pours, calibrate

MM = .0254
SCREEN = box(1.7, 18, 39.62, 50.4)


def pad_shape(p):
    raw = p['pad']; w = raw[1] * MM; h = raw[2] * MM if len(raw) > 2 else w
    if raw[0].upper() in ('ELLIPSE', 'CIRCLE'):
        shape = affinity.scale(Point(0, 0).buffer(1, quad_segs=24), w/2, h/2)
    else:
        shape = box(-w/2, -h/2, w/2, h/2)
    shape = affinity.rotate(shape, p.get('rotation', 0))
    return affinity.translate(shape, p['x'] * MM, p['y'] * MM)


def copper(snapshot, omit_line=None):
    shapes = defaultdict(list); nodes = defaultdict(list)
    for p in snapshot['pads']:
        if not p.get('net'): continue
        layers = (1, 2) if p['layer'] == 12 else (p['layer'],)
        g = pad_shape(p)
        label = f"{p['number']}@({p['x']*MM:.2f},{p['y']*MM:.2f})"
        for layer in layers:
            shapes[p['net'], layer].append(g)
            nodes[p['net'], layer].append((label, g, p['layer'] == 12))
    for i, t in enumerate(snapshot['lines']):
        if i == omit_line or not t.get('net') or t['layer'] not in (1, 2): continue
        shapes[t['net'], t['layer']].append(LineString([(t['x1']*MM,t['y1']*MM), (t['x2']*MM,t['y2']*MM)]).buffer(t['widthMil']*MM/2))
    for i, v in enumerate(snapshot['vias']):
        g = Point(v['x']*MM, v['y']*MM).buffer(v['diameterMil']*MM/2)
        for layer in (1, 2):
            shapes[v['net'], layer].append(g)
            nodes[v['net'], layer].append((f"via{i}", g, True))
    for pour in snapshot['poured']:
        for f in pour['fills']:
            rings = [parse_path(p, .254) for p in f.get('path', [])]
            area = [r for r in rings if len(r) > 2]
            if area:
                shapes[pour['net'], pour['layer']].append(make_valid(Polygon(area[0], area[1:])))
            for ring in rings:
                if len(ring) == 2:
                    shapes[pour['net'], pour['layer']].append(LineString(ring).buffer(f['lineWidth']*.254/2))
    return shapes, nodes


def audit(snapshot, omit_line=None):
    shapes, nodes = copper(snapshot, omit_line)
    union = {key: unary_union([s.buffer(.001) for s in items]) for key, items in shapes.items()}
    trees = {key: STRtree(items) for key, items in shapes.items()}
    dead_ends = []
    if omit_line is None:
        for t in snapshot['lines']:
            key = t['net'], t['layer']
            if key not in trees: continue
            endpoints = [(t['x1']*MM,t['y1']*MM), (t['x2']*MM,t['y2']*MM)]
            radius = t['widthMil']*MM/2
            own = LineString(endpoints).buffer(radius)
            for xy in endpoints:
                end = Point(xy)
                hits = trees[key].query(end.buffer(radius+.001))
                if not any(not shapes[key][i].equals(own) and shapes[key][i].distance(end)<=radius+.001 for i in hits):
                    dead_ends.append({'net':t['net'], 'layer':t['layer'], 'xy_mm':list(xy)})
    split = {}; groups_out = {}
    for net in sorted({key[0] for key in nodes}):
        parents = {}; labels = defaultdict(list); through = {}
        def root(x):
            parents.setdefault(x, x)
            while parents[x] != x: x = parents[x]
            return x
        def join(a, b): parents[root(a)] = root(b)
        for layer in (1, 2):
            g = union.get((net, layer))
            if g is None: continue
            pieces = list(g.geoms) if hasattr(g, 'geoms') else [g]
            for label, geom, plated in nodes.get((net, layer), []):
                hits = [(layer, i) for i,p in enumerate(pieces) if p.intersects(geom)]
                assert hits, (net, label, 'no copper')
                for hit in hits: join(hits[0], hit)
                labels[hits[0]].append(label)
                if plated:
                    if label in through: join(through[label], hits[0])
                    else: through[label] = hits[0]
        groups = defaultdict(set)
        for key, vals in labels.items(): groups[root(key)].update(vals)
        groups_out[net] = [sorted(v) for v in groups.values()]
        if len(groups) > 1: split[net] = groups_out[net]
    # Screen bounds include 0.3 mm beyond the glass; NFC is intentionally allowed.
    intrusion = {f'{net}:{layer}': round(unary_union(items).intersection(SCREEN).area, 6)
                 for (net,layer), items in shapes.items() if net != 'NFC1_TBD' and unary_union(items).intersection(SCREEN).area > .00001}
    calibration, details = calibrate(load_pours(snapshot))
    return {'ok': not split and not intrusion and calibration and not dead_ends, 'split_nets': split,
            'dead_ends': dead_ends,
            'screen_foreign_copper_mm2': intrusion, 'pour_parser_calibrated': calibration,
            'calibration': details, 'groups': groups_out}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--snapshot', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args(); report = audit(json.loads(a.snapshot.read_text()))
    text = json.dumps(report, indent=2) + '\n'
    if a.output: a.output.write_text(text)
    print(text)
    raise SystemExit(0 if report['ok'] else 1)
