"""Read native copper geometry for the explicitly scoped V4 routing experiment."""
import math

from shapely import affinity
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union

from kicad_sexpr import child, children, prop, read


def geometry(path):
    board = read(path)
    pads, objects, footprints = {}, [], {}
    for f in children(board, 'footprint'):
        ref = str(prop(f, 'Reference')[2])
        at = child(f, 'at')
        x, y = map(float, at[1:3])
        angle = float(at[3]) if len(at) > 3 else 0
        a = math.radians(angle)
        footprints[ref] = (x, y, angle)
        for p in children(f, 'pad'):
            at = child(p, 'at')
            px, py = map(float, at[1:3])
            pos = (x + px * math.cos(a) + py * math.sin(a), y - px * math.sin(a) + py * math.cos(a))
            w, h = map(float, child(p, 'size')[1:3])
            pa = float(at[3]) if len(at) > 3 else 0
            if p[3] == 'circle':
                g = Point(0, 0).buffer(w / 2, quad_segs=24)
            elif p[3] == 'oval':
                r = min(w, h) / 2
                g = LineString([(-w / 2 + r, -h / 2 + r), (w / 2 - r, h / 2 - r)]).buffer(r, quad_segs=24)
            elif p[3] in ('rect', 'roundrect'):
                ratio = child(p, 'roundrect_rratio')
                r = min(w, h) * float(ratio[1]) if ratio else 0
                g = box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, quad_segs=16) if r else box(-w / 2, -h / 2, w / 2, h / 2)
            else:
                raise ValueError(('Unsupported pad shape', ref, p[1], p[3]))
            g = affinity.translate(affinity.rotate(g, -pa, origin=(0, 0)), *pos)
            layers = child(p, 'layers')[1:]
            layers = ['F.Cu', 'B.Cu'] if '*.Cu' in layers else [s for s in layers if s in ('F.Cu', 'B.Cu')]
            net = child(p, 'net')
            item = {'name': f'{ref}.{p[1]}', 'at': pos, 'net': str(net[-1]) if net else '', 'layers': layers, 'shape': g, 'kind': 'pad'}
            pads[item['name']] = item
            objects.append(item)
    for s in children(board, 'segment'):
        points = [tuple(map(float, child(s, k)[1:3])) for k in ('start', 'end')]
        objects.append({'name': child(s, 'uuid')[1], 'net': str(child(s, 'net')[-1]), 'layers': [child(s, 'layer')[1]], 'shape': LineString(points).buffer(float(child(s, 'width')[1]) / 2), 'kind': 'track', 'points': points})
    for v in children(board, 'via'):
        at = tuple(map(float, child(v, 'at')[1:3]))
        objects.append({'name': child(v, 'uuid')[1], 'net': str(child(v, 'net')[-1]), 'layers': ['F.Cu', 'B.Cu'], 'shape': Point(at).buffer(float(child(v, 'size')[1]) / 2), 'kind': 'via', 'at': at})
    for z in children(board, 'zone'):
        ko = child(z, 'keepout')
        if ko and child(ko, 'tracks')[1] == 'not_allowed':
            g = Polygon([tuple(map(float, pt[1:3])) for pt in child(child(z, 'polygon'), 'pts')[1:]])
            layers = child(z, 'layers') or child(z, 'layer')
            objects.append({'name': child(z, 'name')[1], 'net': None, 'layers': layers[1:], 'shape': g, 'kind': 'keepout'})
    # Asymmetric imported USB and FPC geometry calibrates rotation and origin.
    assert math.dist(pads['J1.A4B9']['at'], (186.149, 106.4005)) < .002
    assert math.dist(pads['J2.2']['at'], (166.325, 100.99)) < .002
    assert abs(pads['J1.A4B9']['shape'].bounds[2] - pads['J1.A4B9']['shape'].bounds[0] - 1.1) < .002
    assert len([p for p in pads if p.startswith('U1.')]) == 61
    return board, pads, objects, footprints


def filled_ground(board, layer):
    polygons = []
    for z in children(board, 'zone'):
        if child(z, 'keepout') or child(z, 'net')[-1] != 'GND':
            continue
        for f in children(z, 'filled_polygon'):
            if child(f, 'layer')[1] == layer:
                points = [tuple(map(float, pt[1:3])) for pt in child(f, 'pts')[1:]]
                polygons.append(Polygon(points).buffer(0))
    return unary_union(polygons)
