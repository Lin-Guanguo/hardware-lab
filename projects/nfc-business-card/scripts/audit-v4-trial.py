#!/usr/bin/env python3
"""Measure saved trial copper, stencil equivalence, and layer-specific returns."""
import heapq
import json
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union, nearest_points

from gerber_geometry import flashes, positive_regions
from kicad_sexpr import child, children
from v4_geometry import geometry, filled_ground


def measured_path(data, start, end, include_path=False):
    _, pads, objects, _ = data
    net = pads[start]['net']
    assert pads[end]['net'] == net
    tracks = [o for o in objects if o['net'] == net and o['kind'] == 'track']
    vias = [o for o in objects if o['net'] == net and o['kind'] == 'via']
    netpads = [p for p in pads.values() if p['net'] == net]
    graph = defaultdict(list)
    points = {'F.Cu': set(), 'B.Cu': set()}
    def key(layer, p):
        return layer, round(p[0], 4), round(p[1], 4)
    def edge(a, b, length, changes=0):
        graph[a].append((b, length, changes))
        graph[b].append((a, length, changes))
    for t in tracks:
        points[t['layers'][0]].update(tuple(p) for p in t['points'])
    for o in vias + netpads:
        for layer in o['layers']:
            points[layer].add(tuple(o['at']))
    # Imported traces can meet at copper edges rather than centerline endpoints.
    # Node those real contacts before calculating centerline path lengths.
    for i, a in enumerate(tracks):
        layer = a['layers'][0]
        line = LineString(a['points'])
        for b in tracks[i + 1:]:
            if b['layers'] != a['layers'] or a['shape'].distance(b['shape']) > .002:
                continue
            pa, pb = nearest_points(line, LineString(b['points']))
            points[layer].update([tuple(pa.coords[0]), tuple(pb.coords[0])])
            edge(key(layer, pa.coords[0]), key(layer, pb.coords[0]), pa.distance(pb))
        for b in vias + netpads:
            if layer not in b['layers'] or a['shape'].distance(b['shape']) > .002:
                continue
            pt = line.interpolate(line.project(Point(b['at'])))
            points[layer].add(tuple(pt.coords[0]))
            edge(key(layer, pt.coords[0]), key(layer, b['at']), pt.distance(Point(b['at'])))
    for t in tracks:
        layer = t['layers'][0]
        line = LineString(t['points'])
        on = sorted((line.project(Point(p)), p) for p in points[layer] if line.distance(Point(p)) < .003)
        for (da, pa), (db, pb) in zip(on, on[1:]):
            edge(key(layer, pa), key(layer, pb), db - da)
    for pad in netpads:
        for layer in pad['layers']:
            for p in points[layer]:
                if pad['shape'].buffer(.003).covers(Point(p)):
                    edge(key(layer, pad['at']), key(layer, p), math.dist(pad['at'], p))
        if len(pad['layers']) == 2:
            edge(key('F.Cu', pad['at']), key('B.Cu', pad['at']), 0, 1)
    for v in vias:
        for layer in v['layers']:
            for p in points[layer]:
                if v['shape'].buffer(.003).covers(Point(p)):
                    edge(key(layer, v['at']), key(layer, p), math.dist(v['at'], p))
        edge(key('F.Cu', v['at']), key('B.Cu', v['at']), 0, 1)
    targets = {key(l, pads[end]['at']) for l in pads[end]['layers']}
    queue = [(0, 0, key(l, pads[start]['at']), ()) for l in pads[start]['layers']]
    heapq.heapify(queue)
    seen = set()
    while queue:
        length, changes, node, history = heapq.heappop(queue)
        if node in seen:
            continue
        seen.add(node)
        if node in targets:
            result = {'length_mm': round(length, 3), 'serial_layer_changes': changes}
            if include_path:
                result['path'] = history + (node,)
            return result
        for nxt, distance, swaps in graph[node]:
            if nxt not in seen:
                heapq.heappush(queue, (length + distance, changes + swaps, nxt, history + (node,)))
    return None


def native_paste(text):
    assert '%FSLAX46Y46*%' in text and '%MOMM*%' in text and '%LPC*%' not in text
    result = []
    for body in re.findall(r'G36\*\s*(.*?)G37\*', text, re.S):
        pts = []
        for line in body.splitlines():
            line = line.strip()
            if line == 'G01*':
                continue
            m = re.fullmatch(r'X(-?\d+)Y(-?\d+)D0([12])\*', line)
            assert m, ('Unsupported paste command', line)
            pts.append((int(m[1]) / 1e6, int(m[2]) / 1e6))
        g = Polygon(pts)
        assert g.is_valid and g.area > 0
        result.append(g)
    return result


def main():
    project = Path(__file__).resolve().parents[1]
    output = project / 'hardware/records/kicad-v4'
    current = geometry(project / 'hardware/kicad/v4/NFC-Card-V4.kicad_pcb')
    baseline = geometry(project / 'hardware/records/kicad-v4/dfm-diagnostic-02/NFC-Card-V4.kicad_pcb')
    pairs = [('C8.1', 'U2.10'), ('C8.2', 'U2.11'), ('C2.1', 'U2.1'), ('C3.1', 'U2.2'), ('C3.1', 'BP.1'), ('J1.A4B9', 'C8.1'), ('L1.2', 'Q1.3'), ('C10.1', 'L1.1'), ('Q1.2', 'R15.1'), ('R15.2', 'C10.2'), ('J2.2', 'Q1.1'), ('J2.3', 'Q1.2'), ('U1.51', 'TP4.1'), ('U1.53', 'TP3.1'), ('U1.37', 'J2.14'), ('U1.41', 'J2.10')]
    metrics = [{'start': a, 'end': b, 'D': measured_path(baseline, a, b), 'V4': measured_path(current, a, b)} for a, b in pairs]
    board, pads, objects, refs = current
    report = {'path_metrics': metrics, 'metric_scope': 'Saved track centerline plus pad-center attachments; zones excluded from shortest paths. Layer changes counted along the path, not across the whole net.', 'parts': len(refs) - 10, 'pads': len(pads), 'tracks': len(children(board, 'segment')), 'vias': len(children(board, 'via'))}
    report['boost_conduction_loop'] = {}
    for name, data in [('D', baseline), ('V4', current)]:
        chain, changes, length = [], 0, 0
        for a, b in [('C10.1', 'L1.1'), ('L1.2', 'Q1.3'), ('Q1.2', 'R15.1'), ('R15.2', 'C10.2')]:
            path = measured_path(data, a, b, include_path=True)
            assert path
            chain.extend([(x, y) for _, x, y in path['path']])
            length += path['length_mm']
            changes += path['serial_layer_changes']
        loop = Polygon(chain)
        report['boost_conduction_loop'][name] = {'projected_area_mm2': round(loop.area, 3), 'external_centerline_mm': round(length, 3), 'serial_layer_changes': changes, 'simple_polygon': loop.is_valid}
    report['boost_loop_scope'] = 'C10-L1-Q1-R15-C10 on-state conduction loop; straight internal component links, projected XY area. Does not model parasitics or prove the D1/C12 and D2/D3 charge-pump commutation loops.'
    # Exact geometry comparison of independently exported KiCad paste against D.
    source_zip = zipfile.ZipFile(project / 'hardware/records/board-review-d-diagnostic-gerber.zip')
    native_zip = zipfile.ZipFile(project / 'hardware/records/kicad-v4/dfm-diagnostic-02/NFC-V4-migration-diagnostic-gerber.zip')
    old_text = source_zip.read('Gerber_TopPasteMaskLayer.GTP').decode()
    old = unary_union([x[2] for x in flashes(old_text) + positive_regions(old_text)])
    new_openings = native_paste(native_zip.read('NFC-Card-V4-Top Paste Mask Layer.gtp').decode())
    new = unary_union(new_openings)
    mismatch = old.symmetric_difference(new).area
    bottom_text = source_zip.read('Gerber_BottomPasteMaskLayer.GBP').decode()
    bottom_old = unary_union([x[2] for x in flashes(bottom_text) + positive_regions(bottom_text)])
    bottom_openings = native_paste(native_zip.read('NFC-Card-V4-Bottom Paste Mask Layer.gbp').decode())
    bottom_new = unary_union(bottom_openings)
    assert len(new_openings) == 256 and len(bottom_openings) == 2 and mismatch < .001
    assert bottom_old.symmetric_difference(bottom_new).area < .001
    report['paste_comparison'] = {'top_openings': len(new_openings), 'bottom_openings': len(bottom_openings), 'source_area_mm2': old.area, 'kicad_area_mm2': new.area, 'symmetric_difference_mm2': mismatch, 'hausdorff_mm': old.hausdorff_distance(new), 'bottom_symmetric_difference_mm2': bottom_old.symmetric_difference(bottom_new).area}
    planes = {l: filled_ground(board, l) for l in ('F.Cu', 'B.Cu')}
    copper = {l: unary_union([planes[l], *[o['shape'] for o in objects if o['net'] == 'GND' and l in o['layers']]]) for l in planes}
    components = {l: list(g.geoms) if g.geom_type == 'MultiPolygon' else [g] for l, g in copper.items()}
    links = defaultdict(set)
    def contact_ids(shape, layers):
        return [(l, i) for l in layers for i, c in enumerate(components[l]) if c.distance(shape) < .002]
    for o in objects:
        if o['net'] == 'GND' and len(o['layers']) == 2:
            ids = contact_ids(o['shape'], o['layers'])
            for a in ids:
                links[a].update(ids)
    roots = contact_ids(pads['U2.11']['shape'], ['F.Cu'])
    reached, todo = set(), list(roots)
    while todo:
        node = todo.pop()
        if node not in reached:
            reached.add(node)
            todo.extend(links[node] - reached)
    named = ['C8.2', 'C2.2', 'C3.2', 'C10.2', 'C12.2', 'C13.2', 'R15.2', 'BN.1', 'J1.17', 'J1.18', 'J1.19', 'J1.20', 'U1.33', 'TP1.1']
    report['ground_to_U2_EP'] = {name: bool(set(contact_ids(pads[name]['shape'], pads[name]['layers'])) & reached) for name in named if pads[name]['net'] == 'GND'}
    report['ground_components'] = {l: [round(c.area, 5) for c in sorted(cs, key=lambda g: -g.area)] for l, cs in components.items()}
    report['ground_components_not_reaching_U2_EP'] = [{'layer': l, 'area_mm2': round(g.area, 5)} for l, cs in components.items() for i, g in enumerate(cs) if (l, i) not in reached]
    report['reference_plane_gaps'] = []
    for net in ('SWDIO', 'SWDCLK', 'EPD_MOSI_TBD'):
        lines = unary_union([LineString(o['points']) for o in objects if o['kind'] == 'track' and o['net'] == net and o['layers'] == ['B.Cu']])
        gap = lines.difference(copper['F.Cu'])
        pieces = list(gap.geoms) if hasattr(gap, 'geoms') else [gap]
        report['reference_plane_gaps'].append({'net': net, 'bottom_length_mm': round(lines.length, 3), 'outside_top_ground_mm': round(gap.length, 3), 'largest_segment_gap_mm': round(max((g.length for g in pieces), default=0), 3)})
    # Independent copper clearance check; keepout and holes remain native DRC duties.
    collisions = []
    for i, a in enumerate(objects):
        if a['kind'] == 'keepout':
            continue
        for b in objects[i + 1:]:
            if b['kind'] == 'keepout' or a['net'] == b['net'] or not set(a['layers']) & set(b['layers']):
                continue
            if a['kind'] == b['kind'] == 'pad' and a['name'].split('.')[0] == b['name'].split('.')[0]:
                continue
            distance = a['shape'].distance(b['shape'])
            if distance < .199:
                collisions.append({'a': a['name'], 'b': b['name'], 'gap_mm': round(distance, 6)})
    report['independent_external_copper_clearance_failures'] = collisions
    (output / 'trial-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    # Filled polygons and actual track shapes, not ratsnest or planned paths.
    views = [('overview', (110, 194, 130, 78)), ('charger', (140, 170, 116, 102)), ('display', (162, 185, 109, 83)), ('corridors', (162, 186, 126, 79))]
    for name, bounds in views:
        height = 7 * (bounds[2] - bounds[3]) / (bounds[1] - bounds[0]) + 1
        fig, axes = plt.subplots(1, 2, figsize=(14, height), constrained_layout=True)
        for ax, layer in zip(axes, ('F.Cu', 'B.Cu')):
            ground = planes[layer]
            for g in (list(ground.geoms) if hasattr(ground, 'geoms') else [ground]):
                if g.is_empty:
                    continue
                ax.add_patch(Patch(list(g.exterior.coords), color='#dce9dc', linewidth=0))
                for hole in g.interiors:
                    ax.add_patch(Patch(list(hole.coords), color='white', linewidth=0))
            for o in objects:
                if layer not in o['layers']:
                    continue
                color = '#606060' if o['kind'] == 'pad' else ('#c84035' if layer == 'F.Cu' else '#315fb3')
                if o['net'] == 'GND':
                    color = '#43845a'
                if o['kind'] == 'keepout':
                    ax.add_patch(Patch(list(o['shape'].exterior.coords), fill=False, edgecolor='#d28922', hatch='///', linewidth=.6))
                else:
                    ax.add_patch(Patch(list(o['shape'].exterior.coords), color=color, linewidth=0))
            for ref, (x, y, _) in refs.items():
                if bounds[0] < x < bounds[1] and bounds[3] < y < bounds[2]:
                    ax.text(x, y, ref, ha='center', va='center', fontsize=6 if name == 'overview' else 7, color='black', bbox=dict(facecolor='white', alpha=.7, edgecolor='none', pad=.3))
            ax.set(xlim=bounds[:2], ylim=bounds[2:], aspect='equal', title=f'{layer} — saved V4 trial / NOT FOR FABRICATION', xlabel='KiCad X (mm)', ylabel='KiCad Y (mm)')
            ax.grid(alpha=.18)
        fig.savefig(output / f'{name}.png', dpi=160)
        plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
